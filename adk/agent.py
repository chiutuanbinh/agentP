from google.adk.agents import Agent


def get_weather(city: str) -> dict:
    """Returns mock weather data for a city."""
    weather_data = {
        "san francisco": {"temp_c": 16, "condition": "Foggy"},
        "new york": {"temp_c": 22, "condition": "Partly Cloudy"},
        "tokyo": {"temp_c": 28, "condition": "Sunny"},
    }
    key = city.lower()
    if key in weather_data:
        data = weather_data[key]
        return {
            "city": city,
            "temperature_celsius": data["temp_c"],
            "condition": data["condition"],
        }
    return {"city": city, "error": "Weather data not available"}


root_agent = Agent(
    name="assistant",
    model="gemini-1.5-flash",
    description="A helpful assistant that can answer questions and check the weather.",
    instruction="You are a helpful assistant. Use the available tools to answer user questions accurately.",  # noqa: E501
    tools=[],
)
