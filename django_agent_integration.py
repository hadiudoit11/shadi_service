"""
Django Integration with OpenAI Agents
Connects agents to your existing Django models and APIs
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from agents import Agent, function_tool, FunctionToolResult
from authentication.models import Vendor, VendorCategory, EventUser
from typing import Optional, List, Dict
import json


# Django Model Tools
@function_tool
def search_django_vendors(
    category: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    is_featured: Optional[bool] = None,
    limit: int = 10
) -> FunctionToolResult:
    """
    Search for vendors in the Django database.
    
    Args:
        category: Vendor category slug (e.g., 'catering', 'photography')
        city: City name
        state: State abbreviation
        min_price: Minimum price
        max_price: Maximum price
        is_featured: Filter for featured vendors only
        limit: Maximum number of results
    
    Returns:
        List of matching vendors with details
    """
    queryset = Vendor.objects.filter(is_active=True, is_verified=True)
    
    if category:
        queryset = queryset.filter(category__slug=category)
    if city:
        queryset = queryset.filter(city__icontains=city)
    if state:
        queryset = queryset.filter(state=state)
    if min_price is not None:
        queryset = queryset.filter(price_range_min__gte=min_price)
    if max_price is not None:
        queryset = queryset.filter(price_range_max__lte=max_price)
    if is_featured is not None:
        queryset = queryset.filter(is_featured=is_featured)
    
    vendors = queryset[:limit]
    
    results = []
    for vendor in vendors:
        results.append({
            "id": vendor.id,
            "name": vendor.business_name,
            "category": vendor.category.name if vendor.category else "Uncategorized",
            "location": f"{vendor.city}, {vendor.state}",
            "description": vendor.description[:200] + "..." if len(vendor.description) > 200 else vendor.description,
            "services": vendor.services_offered[:5] if vendor.services_offered else [],
            "rating": vendor.rating_average,
            "website": vendor.website
        })
    
    if results:
        output = f"Found {len(results)} vendors:\n\n"
        for v in results:
            output += f"📍 **{v['name']}** ({v['category']})\n"
            output += f"   Location: {v['location']}\n"
            output += f"   Rating: {v['rating']}/5\n"
            output += f"   Services: {', '.join(v['services'][:3])}\n\n"
    else:
        output = "No vendors found matching your criteria."
    
    return FunctionToolResult(output=output)


@function_tool
def get_vendor_details(vendor_id: int) -> FunctionToolResult:
    """
    Get detailed information about a specific vendor.
    
    Args:
        vendor_id: The ID of the vendor
    
    Returns:
        Detailed vendor information
    """
    try:
        vendor = Vendor.objects.get(id=vendor_id, is_active=True)
        
        details = {
            "id": vendor.id,
            "name": vendor.business_name,
            "category": vendor.category.name if vendor.category else "Uncategorized",
            "description": vendor.description,
            "location": f"{vendor.city}, {vendor.state}",
            "services": vendor.services_offered,
            "price_range": f"${vendor.price_range_min or 'N/A'} - ${vendor.price_range_max or 'N/A'}",
            "rating": vendor.rating_average,
            "reviews": vendor.review_count,
            "website": vendor.website,
            "phone": vendor.business_phone,
            "email": vendor.business_email,
            "featured": vendor.is_featured,
            "years_in_business": vendor.years_in_business
        }
        
        output = f"**{details['name']}**\n"
        output += f"Category: {details['category']}\n"
        output += f"Location: {details['location']}\n"
        output += f"Price Range: {details['price_range']}\n"
        output += f"Rating: {details['rating']}/5 ({details['reviews']} reviews)\n\n"
        output += f"Description:\n{details['description']}\n\n"
        output += f"Services Offered:\n"
        for service in details['services'][:10]:
            output += f"• {service}\n"
        
        if details['website']:
            output += f"\nWebsite: {details['website']}\n"
        if details['phone']:
            output += f"Phone: {details['phone']}\n"
            
        return FunctionToolResult(output=output)
        
    except Vendor.DoesNotExist:
        return FunctionToolResult(output=f"Vendor with ID {vendor_id} not found.")


@function_tool
def list_vendor_categories() -> FunctionToolResult:
    """
    List all available vendor categories.
    
    Returns:
        List of vendor categories with counts
    """
    categories = VendorCategory.objects.all()
    
    output = "Available Vendor Categories:\n\n"
    for cat in categories:
        vendor_count = Vendor.objects.filter(category=cat, is_active=True).count()
        output += f"• **{cat.name}** ({cat.slug}): {vendor_count} vendors\n"
    
    return FunctionToolResult(output=output)


@function_tool
def check_user_permissions(user_email: str) -> FunctionToolResult:
    """
    Check Auth0 roles and permissions for a user.
    
    Args:
        user_email: Email of the user
    
    Returns:
        User's roles and permissions
    """
    try:
        user = EventUser.objects.get(email=user_email)
        
        output = f"User: {user.display_name} ({user.email})\n\n"
        output += f"Auth0 Roles:\n"
        for role in (user.auth0_roles or []):
            output += f"• {role}\n"
        
        output += f"\nAuth0 Permissions:\n"
        for perm in (user.auth0_permissions or [])[:10]:
            output += f"• {perm}\n"
        
        output += f"\nVendor Access:\n"
        if user.is_vendor_representative:
            output += "✓ Can manage vendors\n"
            vendors = user.managed_vendors.all()
            if vendors:
                output += f"  Manages: {', '.join([v.vendor.business_name for v in vendors[:5]])}\n"
        else:
            output += "✗ Not a vendor representative\n"
            
        return FunctionToolResult(output=output)
        
    except EventUser.DoesNotExist:
        return FunctionToolResult(output=f"User with email {user_email} not found.")


@function_tool
def create_vendor_note(
    vendor_id: int,
    note: str,
    user_email: str
) -> FunctionToolResult:
    """
    Create a note about a vendor (for wedding planning).
    
    Args:
        vendor_id: ID of the vendor
        note: Note content
        user_email: Email of the user creating the note
    
    Returns:
        Confirmation of note creation
    """
    try:
        vendor = Vendor.objects.get(id=vendor_id)
        user = EventUser.objects.get(email=user_email)
        
        # In a real implementation, you'd have a Note model
        # For now, we'll just simulate it
        output = f"Note created for {vendor.business_name}:\n"
        output += f"'{note}'\n"
        output += f"Created by: {user.display_name}"
        
        return FunctionToolResult(output=output)
        
    except (Vendor.DoesNotExist, EventUser.DoesNotExist) as e:
        return FunctionToolResult(output=f"Error: {str(e)}")


# Create Django-integrated agents
def create_vendor_search_agent():
    """Agent that searches and recommends vendors from your Django database."""
    return Agent(
        name="Django Vendor Search Agent",
        instructions="""You are a vendor search specialist with access to a real database of 
        wedding vendors. You help couples find the perfect vendors by:
        
        1. Understanding their needs and preferences
        2. Searching the database with appropriate filters
        3. Providing detailed information about vendors
        4. Making personalized recommendations
        
        Always provide specific vendor IDs when recommending vendors so users can get more details.
        Be helpful in narrowing down choices based on location, budget, and style preferences.""",
        tools=[
            search_django_vendors,
            get_vendor_details,
            list_vendor_categories
        ],
        model="gpt-4o"
    )


def create_permission_checker_agent():
    """Agent that helps with Auth0 permissions and access control."""
    return Agent(
        name="Permission Checker",
        instructions="""You help users understand their Auth0 permissions and what they can 
        access in the wedding planning system. You can:
        
        1. Check user permissions
        2. Explain what different roles mean
        3. Help troubleshoot access issues
        
        Be clear about what permissions are needed for different actions.""",
        tools=[
            check_user_permissions
        ],
        model="gpt-4o"
    )


# Example usage with Django data
async def search_real_vendors():
    """Example of searching real vendors from your Django database."""
    from openai import AsyncOpenAI
    from agents import Runner
    
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    runner = Runner(client=client)
    
    agent = create_vendor_search_agent()
    
    # Search for vendors
    result = await runner.run(
        agent=agent,
        messages=[
            {
                "role": "user",
                "content": "I need a photographer in New York. Show me what's available."
            }
        ]
    )
    
    print(result.messages[-1]["content"])
    
    # Get details about a specific vendor
    result = await runner.run(
        agent=agent,
        messages=result.messages + [
            {
                "role": "user",
                "content": "Tell me more about vendor ID 73"
            }
        ]
    )
    
    print(result.messages[-1]["content"])


# REST API Integration
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import asyncio


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def agent_chat(request):
    """
    Django view to interact with agents via REST API.
    
    POST /api/agent-chat/
    {
        "agent_type": "vendor_search",
        "message": "Find me caterers in New Jersey"
    }
    """
    from openai import OpenAI
    
    agent_type = request.data.get('agent_type', 'vendor_search')
    message = request.data.get('message', '')
    
    # Select agent based on type
    if agent_type == 'vendor_search':
        agent = create_vendor_search_agent()
    elif agent_type == 'permissions':
        agent = create_permission_checker_agent()
    else:
        return Response({'error': 'Invalid agent type'}, status=400)
    
    # Create synchronous client for Django view
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Run agent (simplified for sync context)
    # In production, you'd want to use async views or Celery for this
    try:
        # Note: This is a simplified example
        # The actual agents library requires async handling
        response = "Agent response would go here"
        
        return Response({
            'success': True,
            'response': response,
            'agent': agent.name
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


if __name__ == "__main__":
    # Test the Django integration
    import asyncio
    asyncio.run(search_real_vendors())