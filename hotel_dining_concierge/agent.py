from google.adk.agents import Agent
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool

# ─── Specialist Sub-Agents ───────────────────────────────────────────────────

food_critic_agent = Agent(
    name="food_critic_agent",
    model="gemini-2.0-flash",
    description="Gives witty, opinionated restaurant recommendations.",
    instruction=(
        "You are a snobby but brilliant food critic. "
        "Respond with exactly ONE witty restaurant suggestion near the provided location. "
        "Include: restaurant name, cuisine type, signature dish, and one sentence on why it is worth visiting."
    ),
)

concierge_agent = Agent(
    name="concierge_agent",
    model="gemini-2.0-flash",
    description="A five-star hotel concierge who handles dining and travel recommendations.",
    instruction=(
        "You are a five-star hotel concierge. "
        "For any restaurant or dining question, you MUST call food_critic_agent first. "
        "Present recommendations warmly and with helpful context."
    ),
    tools=[AgentTool(agent=food_critic_agent)],
)

db_agent = Agent(
    name="db_agent",
    model="gemini-2.0-flash",
    description="Returns mock hotel and landmark data from the internal database.",
    instruction=(
        "You are a database agent. When asked for places, return ONLY this mock JSON: "
        "{'status': 'success', 'data': ["
        "{'name': 'The Grand Hotel', 'rating': 5, 'reviews': 450, 'location': 'Downtown', 'price_per_night': '$320'}, "
        "{'name': 'Seaside Inn', 'rating': 4, 'reviews': 620, 'location': 'Waterfront', 'price_per_night': '$180'}, "
        "{'name': 'The Boutique Loft', 'rating': 4, 'reviews': 310, 'location': 'Arts District', 'price_per_night': '$140'}"
        "]}"
    ),
)


# ─── Orchestrator Tools ──────────────────────────────────────────────────────

async def call_db_agent(question: str, tool_context: ToolContext) -> str:
    """Queries the database for hotels or places. Call this FIRST before asking for recommendations.

    Args:
        question: e.g., "top-rated hotels in San Francisco".

    Returns:
        JSON string with matching places.
    """
    agent_tool = AgentTool(agent=db_agent)
    result = await agent_tool.run_async(
        args={"request": question}, tool_context=tool_context
    )
    tool_context.state["retrieved_data"] = result
    return result


async def call_concierge_agent(question: str, tool_context: ToolContext) -> str:
    """Gets curated dining or travel recommendations based on previously fetched hotel data.

    Call this AFTER call_db_agent. It uses the stored database results as context.

    Args:
        question: e.g., "suggest dinner near the most-reviewed hotel".

    Returns:
        A polished recommendation from the concierge.
    """
    context_data = tool_context.state.get("retrieved_data", "No prior data found.")
    enriched = (
        f"Context — database results: {context_data}\n\n"
        f"User request: {question}"
    )
    agent_tool = AgentTool(agent=concierge_agent)
    return await agent_tool.run_async(
        args={"request": enriched}, tool_context=tool_context
    )


# ─── Root Agent ──────────────────────────────────────────────────────────────

root_agent = Agent(
    name="trip_data_concierge",
    model="gemini-2.0-flash",
    description="Orchestrates hotel database lookup and concierge recommendations using a multi-agent hierarchy.",
    instruction="""
You are a master travel planner who uses a multi-agent team to answer questions.

Workflow:
1. ALWAYS call call_db_agent first to fetch hotels or places from the database.
2. THEN call call_concierge_agent to get dining suggestions or curated recommendations based on that data.

The concierge internally consults a food critic agent for restaurant picks — you do not need to handle that yourself.

Always present the final answer in a friendly, structured format.
""",
    tools=[call_db_agent, call_concierge_agent],
)
