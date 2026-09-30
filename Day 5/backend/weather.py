import requests
from backend.config import settings
from backend.utils import logger, format_unix_time

def get_weather_data(city: str) -> dict:
    """
    Fetches weather data for a given city from OpenWeatherMap API.
    Returns a dictionary of standardized weather indicators.
    """
    if not settings.OPENWEATHER_API_KEY:
        logger.error("OpenWeatherMap API Key is missing.")
        raise ValueError("OpenWeatherMap API Key is not configured. Please add OPENWEATHER_API_KEY to your .env file.")

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric" # Metric units for Celsius, m/s, etc.
    }

    try:
        logger.info(f"Fetching weather for city: {city}")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 404:
            logger.warning(f"City not found: {city}")
            raise ValueError(f"City '{city}' not found. Please verify the city name and try again.")
        elif response.status_code != 200:
            logger.error(f"Weather API error: {response.status_code} - {response.text}")
            raise ValueError(f"Failed to fetch weather data. API returned status code {response.status_code}.")

        data = response.json()
        
        # OpenWeatherMap times are UTC. The API returns a 'timezone' shift in seconds.
        # We pass timezone to helper function to represent local time in target city.
        timezone_offset = data.get("timezone", 0)
        sys_data = data.get("sys", {})
        main_data = data.get("main", {})
        wind_data = data.get("wind", {})
        weather_arr = data.get("weather", [])
        weather_details = weather_arr[0] if len(weather_arr) > 0 else {}

        weather_info = {
            "city": data.get("name", city),
            "temperature": float(main_data.get("temp", 0)),
            "feels_like": float(main_data.get("feels_like", 0)),
            "humidity": int(main_data.get("humidity", 0)),
            "pressure": int(main_data.get("pressure", 0)),
            "visibility": int(data.get("visibility", 0)),
            "wind_speed": float(wind_data.get("speed", 0)),
            "sunrise": format_unix_time(sys_data.get("sunrise", 0), timezone_offset),
            "sunset": format_unix_time(sys_data.get("sunset", 0), timezone_offset),
            "clouds": int(data.get("clouds", {}).get("all", 0)),
            "condition": weather_details.get("main", "Unknown"),
            "description": weather_details.get("description", "N/A").capitalize(),
            "icon": weather_details.get("icon", "01d") # default sunny icon
        }
        
        logger.info(f"Successfully retrieved weather for {weather_info['city']}: {weather_info['temperature']}°C")
        return weather_info

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during weather lookup: {e}")
        raise RuntimeError("Failed to connect to the weather service. Please check your internet connection.")
    except Exception as e:
        logger.error(f"Unexpected error in weather lookup: {e}")
        raise e
