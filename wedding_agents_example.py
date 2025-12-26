"""
Example of using OpenAI Agents library for Wedding Service
Based on OpenAI's agents pattern
"""
import asyncio
from typing import Any, Dict, List
from agents import Agent, Runner, function_tool, FunctionToolResult
from agents.models import OpenAIProvider
from openai import AsyncOpenAI
import os


# Define custom tools for wedding service
@function_tool
def search_vendors(
    category: str = None,
    location: str = None,
    price_range: tuple = None
) -> FunctionToolResult:
    """
    Search for wedding vendors based on criteria.
    
    Args:
        category: Type of vendor (e.g., "photographer", "caterer", "venue")
        location: Location to search in
        price_range: Tuple of (min, max) price
    
    Returns:
        List of matching vendors
    """
    # In real implementation, this would query your database
    vendors = [
        {
            "name": "Elite Photography",
            "category": "photographer",
            "location": "New York",
            "price": 5000,
            "rating": 4.8
        },
        {
            "name": "Garden Venue",
            "category": "venue",
            "location": "New Jersey",
            "price": 15000,
            "rating": 4.9
        }
    ]
    
    # Filter based on criteria
    results = vendors
    if category:
        results = [v for v in results if v["category"] == category]
    if location:
        results = [v for v in results if location.lower() in v["location"].lower()]
    if price_range:
        min_price, max_price = price_range
        results = [v for v in results if min_price <= v["price"] <= max_price]
    
    return FunctionToolResult(
        output=f"Found {len(results)} vendors: {results}"
    )


@function_tool
def check_availability(
    vendor_id: str,
    date: str
) -> FunctionToolResult:
    """
    Check if a vendor is available on a specific date.
    
    Args:
        vendor_id: ID of the vendor
        date: Date to check (YYYY-MM-DD format)
    
    Returns:
        Availability status
    """
    # Mock implementation
    import random
    is_available = random.choice([True, False])
    
    return FunctionToolResult(
        output=f"Vendor {vendor_id} is {'available' if is_available else 'not available'} on {date}"
    )


@function_tool
def create_booking(
    vendor_id: str,
    date: str,
    service_package: str = "standard"
) -> FunctionToolResult:
    """
    Create a booking with a vendor.
    
    Args:
        vendor_id: ID of the vendor
        date: Event date
        service_package: Package type (basic, standard, premium)
    
    Returns:
        Booking confirmation
    """
    booking_id = f"BOOK-{vendor_id}-{date.replace('-', '')}"
    
    return FunctionToolResult(
        output=f"Booking created successfully! Booking ID: {booking_id}, Package: {service_package}"
    )


@function_tool
def calculate_budget(
    venue_cost: float = 0,
    catering_cost: float = 0,
    photography_cost: float = 0,
    decoration_cost: float = 0,
    other_costs: float = 0
) -> FunctionToolResult:
    """
    Calculate total wedding budget.
    
    Args:
        venue_cost: Venue rental cost
        catering_cost: Catering cost
        photography_cost: Photography/videography cost
        decoration_cost: Decoration cost
        other_costs: Miscellaneous costs
    
    Returns:
        Budget breakdown and total
    """
    costs = {
        "venue": venue_cost,
        "catering": catering_cost,
        "photography": photography_cost,
        "decoration": decoration_cost,
        "other": other_costs
    }
    
    total = sum(costs.values())
    breakdown = "\n".join([f"- {k.capitalize()}: ${v:,.2f}" for k, v in costs.items()])
    
    return FunctionToolResult(
        output=f"Budget Breakdown:\n{breakdown}\n\nTotal: ${total:,.2f}"
    )


# Create specialized agents for different tasks
def create_wedding_planner_agent():
    """Creates a wedding planner agent that can help with overall planning."""
    return Agent(
        name="Wedding Planner",
        instructions="""You are an experienced wedding planner specializing in South Asian weddings.
        You help couples plan their perfect wedding by:
        - Finding and recommending vendors
        - Managing budgets
        - Creating timelines
        - Coordinating between different vendors
        - Ensuring cultural traditions are respected
        
        Always be helpful, considerate of budget constraints, and culturally sensitive.""",
        tools=[
            search_vendors,
            check_availability,
            create_booking,
            calculate_budget
        ],
        model="gpt-4o"
    )


def create_vendor_specialist_agent():
    """Creates an agent specialized in vendor management."""
    return Agent(
        name="Vendor Specialist",
        instructions="""You are a vendor relationship specialist who helps couples find and book 
        the perfect vendors for their wedding. You have deep knowledge of:
        - Different vendor categories and their typical services
        - Price ranges and negotiation tips
        - Questions to ask vendors
        - Red flags to watch out for
        
        Focus on matching couples with vendors that fit their style, budget, and cultural needs.""",
        tools=[
            search_vendors,
            check_availability
        ],
        model="gpt-4o"
    )


def create_budget_advisor_agent():
    """Creates an agent specialized in budget management."""
    return Agent(
        name="Budget Advisor",
        instructions="""You are a wedding budget advisor who helps couples manage their wedding 
        expenses effectively. You:
        - Create detailed budget breakdowns
        - Suggest cost-saving strategies
        - Prioritize expenses based on couple's values
        - Track spending throughout the planning process
        
        Always be transparent about costs and provide realistic estimates.""",
        tools=[
            calculate_budget,
            search_vendors  # Can search with price filters
        ],
        model="gpt-4o"
    )


# Agent handoff example - agents can transfer control to each other
def create_coordinated_wedding_system():
    """Creates a system where agents can hand off tasks to each other."""
    
    # Create the agents
    planner = create_wedding_planner_agent()
    vendor_specialist = create_vendor_specialist_agent()
    budget_advisor = create_budget_advisor_agent()
    
    # Add handoff capabilities
    from agents import handoff
    
    # Planner can hand off to specialists
    planner.handoffs = [
        handoff(
            vendor_specialist,
            description="Hand off to vendor specialist for detailed vendor selection"
        ),
        handoff(
            budget_advisor,
            description="Hand off to budget advisor for financial planning"
        )
    ]
    
    # Specialists can hand back to planner
    vendor_specialist.handoffs = [
        handoff(
            planner,
            description="Return to main planner for coordination"
        )
    ]
    
    budget_advisor.handoffs = [
        handoff(
            planner,
            description="Return to main planner after budget analysis"
        )
    ]
    
    return planner, vendor_specialist, budget_advisor


# Example usage
async def main():
    # Initialize OpenAI client
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Create agents
    wedding_planner = create_wedding_planner_agent()
    
    # Create a runner to execute the agent
    runner = Runner(client=client)
    
    # Example conversation
    messages = [
        {
            "role": "user",
            "content": "I'm planning a wedding in New York for next June. My budget is around $50,000. Can you help me find photographers and venues?"
        }
    ]
    
    # Run the agent
    result = await runner.run(
        agent=wedding_planner,
        messages=messages
    )
    
    # Print the response
    print(result.messages[-1]["content"])
    
    # Example with streaming
    print("\n--- Streaming Example ---")
    stream = await runner.run_stream(
        agent=wedding_planner,
        messages=[
            {
                "role": "user",
                "content": "Calculate a budget breakdown for a 200-person wedding"
            }
        ]
    )
    
    async for chunk in stream:
        if chunk.event == "agent_response":
            print(chunk.data.content, end="", flush=True)


# Advanced example with custom context
class WeddingContext:
    """Custom context to maintain wedding planning state"""
    def __init__(self):
        self.couple_names: tuple = None
        self.wedding_date: str = None
        self.guest_count: int = None
        self.budget: float = None
        self.booked_vendors: List[Dict] = []
        self.style_preferences: List[str] = []


async def run_with_context():
    """Example using custom context to maintain state across conversations"""
    from agents import RunContextWrapper
    
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    runner = Runner(client=client)
    
    # Create agent with context awareness
    contextual_planner = Agent[WeddingContext](
        name="Contextual Wedding Planner",
        instructions="""You are a wedding planner who remembers details about the couple's wedding.
        Keep track of their preferences, budget, and bookings throughout the conversation.""",
        tools=[search_vendors, create_booking, calculate_budget],
        model="gpt-4o"
    )
    
    # Initialize context
    context = WeddingContext()
    context.couple_names = ("Sarah", "Raj")
    context.wedding_date = "2024-06-15"
    context.budget = 75000
    
    # Run with context
    result = await runner.run(
        agent=contextual_planner,
        messages=[
            {
                "role": "user",
                "content": f"We are {context.couple_names[0]} and {context.couple_names[1]}. Help us plan our wedding on {context.wedding_date} with a budget of ${context.budget}"
            }
        ],
        context=context
    )
    
    print(result.messages[-1]["content"])


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
    
    # Uncomment to run context example
    # asyncio.run(run_with_context())