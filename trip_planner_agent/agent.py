import requests
from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool

# ─── Search Sub-Agent ────────────────────────────────────────────────────────
# google_search is a Gemini built-in tool and cannot be mixed with custom
# function tools in the same agent. Wrapping it in a dedicated sub-agent
# isolates it so the root agent only sees custom function tools.

_search_agent = Agent(
    name="search_agent",
    model="gemini-2.5-flash",
    description="Performs real-time web searches and returns a concise summary.",
    instruction=(
        "You are a web search assistant. Use google_search to answer the query "
        "and return a concise, factual summary with the most relevant details."
    ),
    tools=[google_search],
)

# ─── Weather Tool ────────────────────────────────────────────────────────────

LOCATION_COORDINATES = {
    "sunnyvale": "37.3688,-122.0363",
    "san francisco": "37.7749,-122.4194",
    "lake tahoe": "39.0968,-120.0324",
    "new york": "40.7128,-74.0060",
    "los angeles": "34.0522,-118.2437",
    "chicago": "41.8781,-87.6298",
    "seattle": "47.6062,-122.3321",
    "miami": "25.7617,-80.1918",
    "boston": "42.3601,-71.0589",
    "denver": "39.7392,-104.9903",
}


def get_live_weather_forecast(location: str) -> dict:
    """Gets the current, real-time weather forecast for a specified US location.

    Args:
        location: The city name, e.g., "San Francisco" or "Lake Tahoe".

    Returns:
        A dictionary with temperature and a detailed forecast, or an error message.
    """
    normalized = location.lower()
    coords = None
    for key, val in LOCATION_COORDINATES.items():
        if key in normalized:
            coords = val
            break

    if not coords:
        return {
            "status": "error",
            "message": f"No coordinates available for '{location}'. Try: San Francisco, Lake Tahoe, New York, Los Angeles, Chicago, Seattle, Miami, Boston, or Denver.",
        }

    try:
        headers = {"User-Agent": "ADK-TripPlanner/1.0"}
        points = requests.get(
            f"https://api.weather.gov/points/{coords}", headers=headers, timeout=10
        )
        points.raise_for_status()
        forecast_url = points.json()["properties"]["forecast"]

        forecast = requests.get(forecast_url, headers=headers, timeout=10)
        forecast.raise_for_status()
        period = forecast.json()["properties"]["periods"][0]

        return {
            "status": "success",
            "location": location,
            "temperature": f"{period['temperature']}°{period['temperatureUnit']}",
            "forecast": period["detailedForecast"],
        }
    except requests.RequestException as e:
        return {"status": "error", "message": f"Weather API request failed: {e}"}


# ─── Specialist Sub-Agents ───────────────────────────────────────────────────

food_critic_agent = Agent(
    name="food_critic_agent",
    model="gemini-2.5-flash",
    description="Gives witty, opinionated restaurant recommendations for a given location.",
    instruction=(
        "You are a snobby but brilliant food critic. "
        "Respond with exactly ONE witty restaurant suggestion near the provided location. "
        "Include the restaurant name, cuisine type, signature dish, and one sentence on why it is worth visiting."
    ),
)

concierge_agent = Agent(
    name="concierge_agent",
    model="gemini-2.5-flash",
    description="A five-star hotel concierge who handles travel and dining recommendations.",
    instruction=(
        "You are a five-star hotel concierge. "
        "For any restaurant or dining question, you MUST call the food_critic_agent tool first. "
        "Present recommendations warmly, politely, and with helpful context."
    ),
    tools=[AgentTool(agent=food_critic_agent)],
)

db_agent = Agent(
    name="db_agent",
    model="gemini-2.5-flash",
    description="Returns mock hotel and landmark data from the internal database.",
    instruction=(
        "You are a database agent. When asked for places, always return this exact mock JSON and nothing else: "
        "{'status': 'success', 'data': ["
        "{'name': 'The Grand Hotel', 'rating': 5, 'reviews': 450, 'location': 'Downtown', 'price_per_night': '$320'}, "
        "{'name': 'Seaside Inn', 'rating': 4, 'reviews': 620, 'location': 'Waterfront', 'price_per_night': '$180'}, "
        "{'name': 'The Boutique Loft', 'rating': 4, 'reviews': 310, 'location': 'Arts District', 'price_per_night': '$140'}"
        "]}"
    ),
)


# ─── Orchestrator Tools (wrapping sub-agents) ────────────────────────────────

async def call_db_agent(question: str, tool_context: ToolContext) -> str:
    """Queries the internal database for hotels, landmarks, or places.

    Use this tool FIRST whenever the user asks about hotels, places to stay, or top-rated spots.
    Stores the results in context so call_concierge_agent can reference them.

    Args:
        question: The search query, e.g., "top-rated hotels in San Francisco".

    Returns:
        A JSON string with the list of matching places.
    """
    agent_tool = AgentTool(agent=db_agent)
    result = await agent_tool.run_async(
        args={"request": question}, tool_context=tool_context
    )
    tool_context.state["retrieved_data"] = result
    return result


async def call_search_agent(query: str, tool_context: ToolContext) -> str:
    """Searches the web for real-time information: events, opening hours, ticket prices, local tips.

    Args:
        query: The search query, e.g., "free events in San Francisco this weekend".

    Returns:
        A concise summary of the search results.
    """
    agent_tool = AgentTool(agent=_search_agent)
    return await agent_tool.run_async(
        args={"request": query}, tool_context=tool_context
    )


async def call_concierge_agent(question: str, tool_context: ToolContext) -> str:
    """Gets personalized travel advice, opinions, or dining recommendations.

    Use this tool AFTER call_db_agent. It uses the previously fetched database
    results as context to give curated, informed recommendations.

    Args:
        question: The user's request for advice, e.g., "suggest a dinner spot near the most-reviewed hotel".

    Returns:
        A polished recommendation string from the concierge.
    """
    context_data = tool_context.state.get("retrieved_data", "No prior data found.")
    enriched_question = (
        f"Context — database results: {context_data}\n\n"
        f"User request: {question}"
    )
    agent_tool = AgentTool(agent=concierge_agent)
    return await agent_tool.run_async(
        args={"request": enriched_question}, tool_context=tool_context
    )


# ─── Root Agent ──────────────────────────────────────────────────────────────

root_agent = Agent(
    name="adaptive_trip_planner",
    model="gemini-2.5-flash",
    description="A comprehensive AI travel planner with real-time weather, hotel search, multi-agent dining recommendations, and adaptive multi-day itinerary planning.",
    instruction="""
You are the "Adaptive Trip Planner" — a smart, friendly AI travel assistant that combines four superpowers:

## Your Tools & When to Use Them

1. **get_live_weather_forecast** — Call this FIRST for any trip involving outdoor activities.
   - Works for US cities: San Francisco, Lake Tahoe, New York, Los Angeles, Chicago, Seattle, Miami, Boston, Denver.

2. **call_db_agent** — Call this when the user asks about hotels or top-rated places.
   - Always call this BEFORE call_concierge_agent.

3. **call_concierge_agent** — Call this AFTER call_db_agent for dining suggestions or curated recommendations.
   - It internally consults a food critic for restaurant picks.

4. **call_search_agent** — Call this for real-time information: events, ticket prices, opening hours, local tips.

## Behavior Rules

- For outdoor activity requests: check weather first, then plan activities around the forecast.
- For "best hotel + dinner" requests: call call_db_agent → call_concierge_agent, in that order.
- For multi-day itineraries: plan ONE day at a time in Markdown format, then ask for user confirmation before moving to the next day.
- Remember everything from this conversation — destinations chosen, preferences stated, feedback given.
- If the user dislikes a suggestion, acknowledge it and offer a specific alternative. Never repeat rejected ideas.

## Budget Awareness

- "cheap" / "budget" / "affordable" → free parks, local markets, food trucks, happy-hour spots
- "splurge" / "luxury" / "treat yourself" → upscale venues, fine dining, premium experiences

## Output Format

Always return itineraries in **Markdown** with clear time blocks:
- **Morning** (9am–12pm)
- **Afternoon** (12pm–5pm)
- **Evening** (5pm–9pm)

Include venue names, estimated costs, and why each fits the user's mood or preference.
""",
    tools=[call_search_agent, get_live_weather_forecast, call_db_agent, call_concierge_agent],
)
