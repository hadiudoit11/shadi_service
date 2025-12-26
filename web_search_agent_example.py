"""
WebSearchTool Example - How to use web search in agents
"""
from agents import Agent, WebSearchTool, Runner
from openai import AsyncOpenAI
import asyncio
import os


# Create an agent with web search capability
def create_wedding_research_agent():
    """Agent that can search the web for wedding-related information."""
    return Agent(
        name="Wedding Research Assistant",
        instructions="""You are a wedding research assistant who helps couples research 
        vendors, venues, and wedding trends. You can search the web to find:
        
        - Current wedding trends and styles
        - Vendor reviews and recommendations
        - Venue availability and pricing
        - Wedding planning tips and timelines
        - Cultural wedding traditions
        
        Always provide accurate, up-to-date information and cite sources when possible.""",
        tools=[
            WebSearchTool(
                # Optional: Customize search location
                user_location={
                    "city": "New York",
                    "state": "NY",
                    "country": "US"
                },
                # Search context - how much info to include
                search_context_size="medium"
            )
        ],
        model="gpt-4o"  # Requires OpenAI models
    )


# Example with filters
def create_venue_scout_agent():
    """Agent that searches for wedding venues with specific criteria."""
    return Agent(
        name="Venue Scout",
        instructions="""You are a venue scouting specialist who helps couples find 
        the perfect wedding venue. Research venues, read reviews, check availability, 
        and provide comprehensive information about pricing and amenities.""",
        tools=[
            WebSearchTool(
                user_location={
                    "city": "Los Angeles", 
                    "state": "CA"
                },
                filters={
                    # Filter by file types (if needed)
                    "include_file_types": ["pdf", "docx"],  # For venue brochures
                    "exclude_file_types": ["mp4", "mov"]    # Skip videos
                },
                search_context_size="high"  # More detailed results
            )
        ],
        model="gpt-4o"
    )


async def demo_web_search():
    """Demo the web search functionality."""
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    runner = Runner(client=client)
    
    # Create research agent
    research_agent = create_wedding_research_agent()
    
    # Test queries
    queries = [
        "What are the latest 2024 wedding trends for South Asian weddings?",
        "Find reviews for wedding photographers in Brooklyn, NY",
        "What is the average cost of a wedding venue in New York City?",
        "Traditional Bengali wedding ceremony timeline and rituals"
    ]
    
    for query in queries:
        print(f"\n🔍 Query: {query}")
        print("-" * 50)
        
        result = await runner.run(
            agent=research_agent,
            messages=[
                {
                    "role": "user",
                    "content": query
                }
            ]
        )
        
        print(result.messages[-1]["content"])
        print("\n")


# Integration with your Django backend
def create_hybrid_wedding_agent():
    """Agent that combines Django database search with web research."""
    from django_agent_integration import search_django_vendors
    
    return Agent(
        name="Hybrid Wedding Assistant",
        instructions="""You are a comprehensive wedding assistant with access to both:
        1. A curated database of verified wedding vendors
        2. The ability to search the web for additional information
        
        First, search the internal database for vendors. If you need more information 
        or can't find what the user needs, search the web for additional options or details.
        
        Always prioritize the verified database vendors but supplement with web research.""",
        tools=[
            search_django_vendors,  # Your Django function
            WebSearchTool(
                search_context_size="medium"
            )
        ],
        model="gpt-4o"
    )


# Advanced: Custom search contexts
def create_trend_analyst_agent():
    """Agent specialized in wedding trend analysis."""
    return Agent(
        name="Wedding Trend Analyst",
        instructions="""You analyze current wedding trends by searching recent articles, 
        social media posts, and industry publications. Focus on:
        
        - Color schemes and decoration trends
        - Popular venue types
        - Food and catering trends
        - Technology integration in weddings
        - Cultural fusion trends
        
        Provide data-driven insights with specific examples and sources.""",
        tools=[
            WebSearchTool(
                search_context_size="high",  # More comprehensive results
                filters={
                    "time_range": "recent",  # Focus on recent content
                    "include_domains": [
                        "theknot.com",
                        "brides.com", 
                        "marthastewartweddings.com"
                    ]
                }
            )
        ],
        model="gpt-4o"
    )


# How the tool works internally:
"""
When you add WebSearchTool to an agent:

1. User asks: "Find wedding photographers in Brooklyn"
2. LLM recognizes it needs web search
3. LLM calls the web_search tool with query: "wedding photographers Brooklyn NY reviews"
4. OpenAI's web search service:
   - Searches the web
   - Filters results based on your settings
   - Returns relevant content
5. LLM processes the search results
6. LLM responds with synthesized information

The tool automatically handles:
- Query optimization
- Result filtering
- Content extraction
- Relevance ranking
"""

if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_web_search())