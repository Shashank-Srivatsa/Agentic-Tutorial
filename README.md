# ADK Learning — Agentic AI with Google Agent Development Kit

A hands-on repository for exploring Google ADK concepts: custom tools, multi-agent systems, and conversational memory. Each folder is a standalone agent.

---

## Agents

### [weather_aware_planner](./weather_aware_planner/)
Checks live US weather via the National Weather Service API before recommending any outdoor activity.
Demonstrates how to connect an agent to a real external API as a custom tool.

### [trip_planner_agent](./trip_planner_agent/)
Orchestrates three agents in a hierarchy — a database agent fetches hotels, a concierge agent handles recommendations, and a food critic agent picks the restaurant.
Demonstrates the **Agent-as-a-Tool** pattern for delegating specialized tasks.

### [Hybrid_Work_Planner](./trip_planner_agent/)
Checks the weather in Bangalore and gives an indication to either work from home or work from the office. 

