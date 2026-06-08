# ADK Learning — Agentic AI with Google Agent Development Kit

A hands-on repository for exploring Google ADK concepts: custom tools, multi-agent systems, and conversational memory. Each folder is a standalone agent.

---

## Agents

### [day_trip_genie](./day_trip_genie/)
Plans a spontaneous full-day itinerary from just a mood, interest, and budget.
Uses Google Search to find real venues, opening hours, and local events.

### [weather_aware_planner](./weather_aware_planner/)
Checks live US weather via the National Weather Service API before recommending any outdoor activity.
Demonstrates how to connect an agent to a real external API as a custom tool.

### [hotel_dining_concierge](./hotel_dining_concierge/)
Orchestrates three agents in a hierarchy — a database agent fetches hotels, a concierge agent handles recommendations, and a food critic agent picks the restaurant.
Demonstrates the Agent-as-a-Tool pattern for delegating specialized tasks.

### [adaptive_trip_planner](./adaptive_trip_planner/)
Builds a multi-day itinerary one day at a time, remembers your preferences across turns, and replaces anything you dislike.
Demonstrates how session memory enables truly conversational, adaptive agents.

