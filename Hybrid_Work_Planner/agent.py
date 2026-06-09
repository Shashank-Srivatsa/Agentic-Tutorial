import requests
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

# Coordinates for Bangalore (Bengaluru) Central
BANGALORE_LAT = "12.9716"
BANGALORE_LON = "77.5946"

def get_bangalore_weather_forecast() -> dict:
    """Gets the current and tomorrow's weather forecast for Bangalore, India.

    Returns:
        A dictionary containing the current conditions and tomorrow's outlook, 
        or an error message.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": BANGALORE_LAT,
        "longitude": BANGALORE_LON,
        "current": ["temperature_2m", "apparent_temperature", "precipitation", "weather_code"],
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_probability_max", "weather_code"],
        "timezone": "Asia/Kolkata",
        "forecast_days": 2
    }
    
    # Mapping standard WMO weather codes to human-readable text
    wmo_codes = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Foggy", 48: "Depositing rime fog",
        51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
        80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
        95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current_data = data.get("current", {})
        daily_data = data.get("daily", {})
        
        current_code = current_data.get("weather_code", 0)
        tomorrow_code = daily_data.get("weather_code", [0, 0])[1]

        return {
            "status": "success",
            "location": "Bangalore",
            "today": {
                "temperature": f"{current_data.get('temperature_2m')}°C",
                "feels_like": f"{current_data.get('apparent_temperature')}°C",
                "condition": wmo_codes.get(current_code, "Unknown"),
                "precipitation_mm": current_data.get("precipitation", 0)
            },
            "tomorrow": {
                "temp_range": f"{daily_data.get('temperature_2m_min', [0,0])[1]}°C to {daily_data.get('temperature_2m_max', [0,0])[1]}°C",
                "condition": wmo_codes.get(tomorrow_code, "Unknown"),
                "precipitation_probability": f"{daily_data.get('precipitation_probability_max', [0,0])[1]}%"
            }
        }
    except requests.RequestException as e:
        return {"status": "error", "message": f"Open-Meteo API failed: {e}"}


root_agent = Agent(
    name="bangalore_hybrid_work_planner",
    model=LiteLlm(model="groq/llama-3.3-70b-versatile"),
    description="An intelligent hybrid-work advisor that looks up Bangalore weather forecasts to decide between commuting to the office or opting for WFH.",
    instruction="""
You are a highly practical professional assistant helping the user optimize their hybrid work arrangements in Bangalore.

Your objective is to advise the user whether to commute to the office or stay at home (WFH) today or tomorrow based on real-time weather analytics.

Rules:
1. Always call `get_bangalore_weather_forecast` immediately when a user asks for work recommendations.
2. Evaluate the data strictly against Bangalore infrastructure realities (traffic congestion, waterlogging, etc.):
   - If there is heavy/moderate rain, high precipitation probability (>50%), or an ongoing thunderstorm, STRONGLY recommend WFH to avoid extreme commute delays and potential waterlogging.
   - If the weather is clear, partly cloudy, or light drizzle, encourage commuting to the office to complete collaborative work.
3. Be clear, concise, and explicit about your reasoning (e.g., mention exact temperatures, rainfall risk, and time of day if applicable).
4. Do not offer advice for cities outside of Bangalore, as this agent is specifically designated for local hybrid work planning.
""",
    tools=[get_bangalore_weather_forecast]
)