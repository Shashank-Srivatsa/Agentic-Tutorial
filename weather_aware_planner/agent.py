import requests
from google.adk.agents import Agent

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
            "message": (
                f"No coordinates for '{location}'. "
                "Supported cities: San Francisco, Lake Tahoe, New York, Los Angeles, "
                "Chicago, Seattle, Miami, Boston, Denver, Sunnyvale."
            ),
        }

    try:
        headers = {"User-Agent": "ADK-WeatherAgent/1.0"}
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
        return {"status": "error", "message": f"Weather API failed: {e}"}


root_agent = Agent(
    name="weather_aware_planner",
    model="gemini-2.0-flash",
    description="A trip planner that checks real-time weather before making outdoor activity suggestions.",
    instruction="""
You are a cautious trip planner with access to live US weather data.

Rules:
- Before suggesting ANY outdoor activity, you MUST call get_live_weather_forecast first.
- Incorporate the actual temperature and forecast into your recommendation.
- If weather is bad (rain, snow, extreme heat/cold), suggest indoor alternatives.
- Supported cities: San Francisco, Lake Tahoe, New York, Los Angeles, Chicago, Seattle, Miami, Boston, Denver, Sunnyvale.
""",
    tools=[get_live_weather_forecast],
)
