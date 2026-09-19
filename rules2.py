def get_advisory(question, weather, crop):

    rainfall = weather["rainfall_mm"]
    temp = weather["temp_max"]

    question = question.lower()

    # Irrigation
    if any(word in question for word in [
        "irrigation", "irrigate", "water", "watering"
    ]):

        if rainfall > 10:
            return f"🌧️ Heavy rain expected. Do not irrigate your {crop} field today."

        elif rainfall > 2:
            return f"🌦️ Light rain expected. Reduce irrigation for {crop}."

        else:
            return f"☀️ No rain expected. Irrigation is recommended for {crop}."

    # Pest
    elif any(word in question for word in [
        "pest", "disease", "insect", "bug"
    ]):

        if rainfall > 5 and temp > 30:
            return f"⚠️ High pest risk for {crop}. Inspect your field."

        elif rainfall > 2:
            return f"⚠️ Moderate pest risk for {crop}."

        else:
            return f"✅ Low pest risk for {crop}."

    # Weather
    elif any(word in question for word in [
        "weather", "temperature", "rain", "forecast"
    ]):

        return f"""
🌤 Weather Today

🌡️ Maximum Temperature: {temp}°C
🌡️ Minimum Temperature: {weather['temp_min']}°C
🌧️ Rainfall: {rainfall} mm
"""

    # Advisory
    elif any(word in question for word in [
        "advisory", "today", "advice", "recommend"
    ]):

        if rainfall > 10:
            return f"🌾 Heavy rain expected. Ensure proper drainage in your {crop} field."

        elif temp > 35:
            return f"🌞 High temperature today. Irrigate your {crop} during the morning or evening."

        else:
            return f"✅ Weather conditions are favourable for {crop}."

    else:
        return (
            "I can answer questions about:\n\n"
            "• Should I irrigate today?\n"
            "• Any pest risk?\n"
            "• What's the weather today?\n"
            "• Give today's advisory."
        )

def get_tomorrow_alert(tomorrow_weather, crop):

    rainfall = tomorrow_weather["rainfall_mm"]
    temp = tomorrow_weather["temp_max"]

    if rainfall > 10:
        return f"🌧️ Tomorrow: Heavy rain expected. Avoid irrigation for {crop}."

    elif temp > 35:
        return f"🌞 Tomorrow: High temperature expected. Irrigate {crop} early morning or evening."

    elif rainfall <= 2 and temp > 33:
        return f"☀️ Dry and hot conditions expected tomorrow. Ensure sufficient water for {crop} today."

    else:
        return f"✅ Tomorrow: Weather looks favourable for {crop}."