import requests
import streamlit as st


@st.cache_data(ttl=1800, show_spinner=False)
def get_weather(lat, lon):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "forecast_days": 4,
        "timezone": "auto"
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return None

    data = response.json()
    daily = data["daily"]

    weather = []

    for i in range(len(daily["time"])):
        weather.append({
            "date": daily["time"][i],
            "temp_max": daily["temperature_2m_max"][i],
            "temp_min": daily["temperature_2m_min"][i],
            "rainfall_mm": daily["precipitation_sum"][i]
        })

    return weather


@st.cache_data(ttl=600, show_spinner=False)
def get_current_weather(lat, lon):
    """Fetches real-time current conditions (not the daily forecast)."""
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
        "timezone": "auto",
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return None

    data = response.json()
    current = data.get("current")

    if not current:
        return None

    return {
        "temperature": current.get("temperature_2m"),
        "humidity": current.get("relative_humidity_2m"),
        "precipitation": current.get("precipitation"),
        "wind_speed": current.get("wind_speed_10m"),
        "weather_code": current.get("weather_code"),
        "time": current.get("time"),
    }


WEATHER_CODE_DESCRIPTIONS = {
    0: "Clear sky ☀️",
    1: "Mainly clear 🌤",
    2: "Partly cloudy ⛅",
    3: "Overcast ☁️",
    45: "Fog 🌫",
    48: "Depositing rime fog 🌫",
    51: "Light drizzle 🌦",
    53: "Moderate drizzle 🌦",
    55: "Dense drizzle 🌧",
    61: "Slight rain 🌧",
    63: "Moderate rain 🌧",
    65: "Heavy rain 🌧",
    71: "Slight snow 🌨",
    73: "Moderate snow 🌨",
    75: "Heavy snow 🌨",
    80: "Slight rain showers 🌦",
    81: "Moderate rain showers 🌧",
    82: "Violent rain showers ⛈",
    95: "Thunderstorm ⛈",
    96: "Thunderstorm with hail ⛈",
    99: "Thunderstorm with heavy hail ⛈",
}


def describe_weather_code(code):
    return WEATHER_CODE_DESCRIPTIONS.get(code, "Conditions unavailable")


@st.cache_data(ttl=86400, show_spinner=False)
def geocode_location(place_name):
    """Convert a place name typed by the user into latitude/longitude."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": place_name, "count": 1, "language": "en", "format": "json"}

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return None

    data = response.json()
    results = data.get("results")

    if not results:
        return None

    result = results[0]
    return {
        "lat": result["latitude"],
        "lon": result["longitude"],
        "name": result.get("name", place_name),
        "admin1": result.get("admin1", ""),
        "country": result.get("country", ""),
    }
