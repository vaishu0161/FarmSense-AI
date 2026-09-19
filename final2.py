import json
from io import BytesIO

import streamlit as st
from groq import Groq
from gtts import gTTS

from weather import get_weather, geocode_location, get_current_weather, describe_weather_code
from rules2 import get_tomorrow_alert

# -----------------------------
# Groq Client
# -----------------------------
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    client = None

# -----------------------------
# Load mini-RAG knowledge base (cached so it only loads once)
# -----------------------------
@st.cache_data(show_spinner=False)
def load_knowledge():
    with open("crop_knowledge.json", "r", encoding="utf-8") as f:
        return json.load(f)


def retrieve_context(crop, stage, knowledge):
    """Find crop+stage specific advice, falling back to general advice for that stage."""
    for entry in knowledge:
        if entry["crop"] == crop and entry["growth_stage"] == stage:
            return f"Common risk: {entry['common_risk']} Recommended action: {entry['recommended_action']}"

    for entry in knowledge:
        if entry["crop"] == "General" and entry["growth_stage"] == stage:
            return f"Common risk: {entry['common_risk']} Recommended action: {entry['recommended_action']}"

    return "No specific historical guidance available for this crop/stage combination."


# -----------------------------
# Chatbot logic
# -----------------------------
def answer_question(question, crop, stage, weather, context, history):

    history_text = ""
    for h in history[-3:]:
        history_text += f"Farmer previously asked: {h['question']}\nAdvisor previously answered: {h['answer']}\n"

    prompt = f"""
    Crop: {crop}
    Growth Stage: {stage}

    Today's Weather:
    Maximum Temperature: {weather['temp_max']}°C
    Minimum Temperature: {weather['temp_min']}°C
    Rainfall: {weather['rainfall_mm']} mm

    Relevant Crop Knowledge:
    {context}

    Recent Conversation:
    {history_text if history_text else "No prior questions this session."}

    Farmer Question:
    {question}

    Give practical, concise farming advice based on the crop, growth stage, weather,
    and any relevant crop knowledge above.
    """

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "You are an expert agricultural advisor."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"Groq Error: {e}"


def translate_text(text, target_language):
    """Translate text using Groq instead of a separate translation library."""
    if client is None:
        return "Groq API key not found. Please add GROQ_API_KEY to Streamlit Secrets."

    prompt = f"""
    Translate the following farming advisory into {target_language}.
    Keep the meaning accurate and the tone practical for a farmer.
    Return only the translated text, with no extra commentary.

    Text to translate:
    {text}
    """

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "You are a precise translator for agricultural advisory text."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"Translation failed: {e}"


# gTTS language codes for each supported language
LANGUAGE_CODES = {
    "Tamil": "ta",
    "Hindi": "hi",
    "Telugu": "te",
    "Malayalam": "ml",
    "Kannada": "kn",
    "English": "en",
    "Bengali": "bn",
    "Gujarati": "gu",
    "Marathi": "mr",
    "Punjabi": "pa",
    "Urdu": "ur",
}


def text_to_speech(text, language_name):
    """Converts text into spoken audio bytes using gTTS."""
    lang_code = LANGUAGE_CODES.get(language_name, "en")
    try:
        tts = gTTS(text=text, lang=lang_code)
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer
    except Exception as e:
        st.warning(f"Voice generation failed: {e}")
        return None


# -----------------------------
# Streamlit Configuration
# -----------------------------
st.set_page_config(
    page_title="Crop Advisory System",
    page_icon="🌾",
    layout="centered"
)

st.title("🌾 Crop Advisory System")

# -----------------------------
# Location Input
# -----------------------------
st.subheader("📍 Your Location")

if "location_name" not in st.session_state:
    st.session_state.location_name = "Kumbakonam"
    st.session_state.lat = 10.9601
    st.session_state.lon = 79.3788

location_input = st.text_input("Enter your city or town", value=st.session_state.location_name)

if st.button("Set Location"):
    geo = geocode_location(location_input)
    if geo:
        st.session_state.lat = geo["lat"]
        st.session_state.lon = geo["lon"]
        display_name = geo["name"]
        if geo.get("admin1"):
            display_name += f", {geo['admin1']}"
        st.session_state.location_name = display_name
        st.success(f"📍 Location set to: {st.session_state.location_name}")
    else:
        st.warning(f"Couldn't find '{location_input}'. Keeping previous location: {st.session_state.location_name}")
else:
    st.caption(f"Current location: {st.session_state.location_name}")

# -----------------------------
# Crop & Growth Stage Selection
# -----------------------------
crop = st.selectbox(
    "🌱 Select Your Crop",
    [
        "Paddy 🌾", "Sugarcane 🎋", "Groundnut 🥜", "Maize 🌽", "Wheat 🌾",
        "Cotton ☁️", "Banana 🍌", "Coconut 🥥", "Tomato 🍅", "Onion 🧅",
        "Potato 🥔", "Brinjal 🍆", "Chilli 🌶️", "Millets 🌾", "Mango 🥭",
        "Papaya 🍈", "Guava 🍏", "Turmeric 🌿", "Ginger 🫚", "Black Gram",
        "Green Gram", "Red Gram", "Sesame", "Sunflower 🌻", "Soybean",
        "Ragi", "Cabbage 🥬", "Cauliflower 🥦", "Carrot 🥕", "Beans", "Cucumber 🥒"
    ]
)

growth_stage = st.selectbox(
    "🌿 Growth Stage",
    ["Sowing", "Vegetative", "Flowering", "Harvest"]
)

st.success(f"You selected: {crop} — {growth_stage} stage")

lat = st.session_state.lat
lon = st.session_state.lon

weather_data = get_weather(lat, lon)
knowledge = load_knowledge()

if weather_data and len(weather_data) >= 2:

    today = weather_data[0]
    tomorrow = weather_data[1]

    # -----------------------------
    # Current Conditions (real-time)
    # -----------------------------
    current = get_current_weather(lat, lon)

    if current:
        st.subheader("🌡 Current Conditions")

        cc1, cc2, cc3, cc4 = st.columns(4)

        with cc1:
            st.metric("Temperature", f"{current['temperature']} °C")
        with cc2:
            st.metric("Humidity", f"{current['humidity']} %")
        with cc3:
            st.metric("Wind Speed", f"{current['wind_speed']} km/h")
        with cc4:
            st.metric("Conditions", describe_weather_code(current["weather_code"]))

        st.caption(f"As of {current['time']} (local time)")

        st.divider()

    # -----------------------------
    # Weather Section
    # -----------------------------
    st.subheader("🌤 Today's Weather")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Max Temp", f"{today['temp_max']} °C")
    with c2:
        st.metric("Min Temp", f"{today['temp_min']} °C")
    with c3:
        st.metric("Rainfall", f"{today['rainfall_mm']} mm")

    st.divider()

    # -----------------------------
    # Tomorrow Advisory
    # -----------------------------
    st.subheader("📢 Tomorrow's Advisory")

    advisory = get_tomorrow_alert(tomorrow, crop)
    st.info(advisory)

    st.divider()

    # -----------------------------
    # Chatbot
    # -----------------------------
    st.subheader("💬 Ask a Farming Question")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "answer" not in st.session_state:
        st.session_state.answer = ""

    if "feedback" not in st.session_state:
        st.session_state.feedback = {"up": 0, "down": 0}

    question = st.text_input(
        "Type your question",
        placeholder="Example: Should I irrigate today?"
    )

    if st.button("Ask"):

        if question.strip():

            if client is None:
                st.error("Groq API key not found. Please add GROQ_API_KEY to Streamlit Secrets.")

            else:
                context = retrieve_context(crop, growth_stage, knowledge)

                st.session_state.answer = answer_question(
                    question, crop, growth_stage, today, context, st.session_state.chat_history
                )

                st.session_state.chat_history.append({
                    "question": question,
                    "answer": st.session_state.answer
                })

        else:
            st.warning("Please enter a question.")

    # Show the latest exchange
    if st.session_state.answer:
        with st.chat_message("assistant"):
            st.write(st.session_state.answer)

        fb_col1, fb_col2 = st.columns(2)
        with fb_col1:
            if st.button("👍 Helpful"):
                st.session_state.feedback["up"] += 1
        with fb_col2:
            if st.button("👎 Not helpful"):
                st.session_state.feedback["down"] += 1

        st.caption(
            f"Feedback so far — 👍 {st.session_state.feedback['up']}  "
            f"👎 {st.session_state.feedback['down']}"
        )

    # Show recent conversation history
    if st.session_state.chat_history:
        with st.expander("🕘 Recent Questions"):
            for h in reversed(st.session_state.chat_history[-3:]):
                st.markdown(f"**Q:** {h['question']}")
                st.markdown(f"**A:** {h['answer']}")
                st.markdown("---")

    # -----------------------------
    # Translation Feature
    # -----------------------------
    if st.session_state.answer:

        st.divider()
        st.subheader("🌐 Translate Advisory")

        languages = list(LANGUAGE_CODES.keys())

        selected_language = st.selectbox("Select Language", languages)

        if st.button("Translate Answer"):
            translated_text = translate_text(st.session_state.answer, selected_language)
            st.success(translated_text)

            audio_buffer = text_to_speech(translated_text, selected_language)
            if audio_buffer:
                st.audio(audio_buffer, format="audio/mp3")

else:
    st.error("Unable to fetch weather data.")
