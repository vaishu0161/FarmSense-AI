import json

import streamlit as st
from deep_translator import GoogleTranslator
from groq import Groq

from weather import get_weather
from rules2 import get_tomorrow_alert


# -----------------------------
# Groq Client
# -----------------------------
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    client = None


# -----------------------------
# Load mini-RAG knowledge base
# Cached so it only loads once
# -----------------------------
@st.cache_data(show_spinner=False)
def load_knowledge():
    with open("crop_knowledge.json", "r", encoding="utf-8") as f:
        return json.load(f)


# -----------------------------
# Retrieve crop-specific context
# -----------------------------
def retrieve_context(crop, stage, knowledge):

    # First try crop + growth stage specific advice
    for entry in knowledge:
        if (
            entry["crop"] == crop
            and entry["growth_stage"] == stage
        ):
            return (
                f"Common risk: {entry['common_risk']} "
                f"Recommended action: {entry['recommended_action']}"
            )

    # If not found, use general advice for that stage
    for entry in knowledge:
        if (
            entry["crop"] == "General"
            and entry["growth_stage"] == stage
        ):
            return (
                f"Common risk: {entry['common_risk']} "
                f"Recommended action: {entry['recommended_action']}"
            )

    return (
        "No specific historical guidance available "
        "for this crop/stage combination."
    )


# -----------------------------
# Chatbot Logic
# -----------------------------
def answer_question(
    question,
    crop,
    stage,
    weather,
    context,
    history
):

    history_text = ""

    for h in history[-3:]:
        history_text += (
            f"Farmer previously asked: {h['question']}\n"
            f"Advisor previously answered: {h['answer']}\n"
        )

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

Give practical, concise farming advice based on the crop,
growth stage, weather, and any relevant crop knowledge above.
"""

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert agricultural advisor."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                },
            ],
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Groq Error: {e}"


# -----------------------------
# Google Translation
# Cached for 1 hour
# -----------------------------
@st.cache_data(show_spinner=False, ttl=3600)
def translate_text(text, target_language):

    # No translation needed for English
    if target_language == "en":
        return text

    translator = GoogleTranslator(
        source="auto",
        target=target_language
    )

    return translator.translate(text)


# -----------------------------
# Streamlit Configuration
# -----------------------------
st.set_page_config(
    page_title="Crop Advisory System",
    page_icon="🌾",
    layout="centered"
)


# -----------------------------
# App Header
# -----------------------------
st.title("🌾 Crop Advisory System")

st.write(
    "📍 Demo Location: Kumbakonam, Tamil Nadu"
)


# -----------------------------
# Crop Selection
# -----------------------------
crop = st.selectbox(
    "🌱 Select Your Crop",
    [
        "Paddy 🌾",
        "Sugarcane 🎋",
        "Groundnut 🥜",
        "Maize 🌽",
        "Wheat 🌾",
        "Cotton ☁️",
        "Banana 🍌",
        "Coconut 🥥",
        "Tomato 🍅",
        "Onion 🧅",
        "Potato 🥔",
        "Brinjal 🍆",
        "Chilli 🌶️",
        "Millets 🌾",
        "Mango 🥭",
        "Papaya 🍈",
        "Guava 🍏",
        "Turmeric 🌿",
        "Ginger 🫚",
        "Black Gram",
        "Green Gram",
        "Red Gram",
        "Sesame",
        "Sunflower 🌻",
        "Soybean",
        "Ragi",
        "Cabbage 🥬",
        "Cauliflower 🥦",
        "Carrot 🥕",
        "Beans",
        "Cucumber 🥒"
    ]
)


# -----------------------------
# Growth Stage
# -----------------------------
growth_stage = st.selectbox(
    "🌿 Growth Stage",
    [
        "Sowing",
        "Vegetative",
        "Flowering",
        "Harvest"
    ]
)


st.success(
    f"You selected: {crop} — {growth_stage} stage"
)


# -----------------------------
# Location
# -----------------------------
lat = 10.9601
lon = 79.3788


# -----------------------------
# Get Weather
# -----------------------------
weather_data = get_weather(lat, lon)

knowledge = load_knowledge()


# -----------------------------
# Main Application
# -----------------------------
if weather_data and len(weather_data) >= 2:

    today = weather_data[0]
    tomorrow = weather_data[1]


    # -----------------------------
    # Today's Weather
    # -----------------------------
    st.subheader("🌤 Today's Weather")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Max Temp",
            f"{today['temp_max']} °C"
        )

    with c2:
        st.metric(
            "Min Temp",
            f"{today['temp_min']} °C"
        )

    with c3:
        st.metric(
            "Rainfall",
            f"{today['rainfall_mm']} mm"
        )


    st.divider()


    # -----------------------------
    # Tomorrow Advisory
    # -----------------------------
    st.subheader("📢 Tomorrow's Advisory")

    advisory = get_tomorrow_alert(
        tomorrow,
        crop
    )

    st.info(advisory)


    st.divider()


    # -----------------------------
    # Chatbot
    # -----------------------------
    st.subheader("💬 Ask a Farming Question")


    # Initialize session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


    if "answer" not in st.session_state:
        st.session_state.answer = ""


    if "feedback" not in st.session_state:
        st.session_state.feedback = {
            "up": 0,
            "down": 0
        }


    # Farmer question
    question = st.text_input(
        "Type your question",
        placeholder="Example: Should I irrigate today?"
    )


    # -----------------------------
    # Ask Button
    # -----------------------------
    if st.button("Ask"):

        if question.strip():

            if client is None:

                st.error(
                    "Groq API key not found. "
                    "Please add GROQ_API_KEY "
                    "to Streamlit Secrets."
                )

            else:

                context = retrieve_context(
                    crop,
                    growth_stage,
                    knowledge
                )


                st.session_state.answer = answer_question(
                    question,
                    crop,
                    growth_stage,
                    today,
                    context,
                    st.session_state.chat_history
                )


                # Save conversation
                st.session_state.chat_history.append(
                    {
                        "question": question,
                        "answer": st.session_state.answer
                    }
                )

        else:

            st.warning(
                "Please enter a question."
            )


    # -----------------------------
    # Show Latest Answer
    # -----------------------------
    if st.session_state.answer:

        with st.chat_message("assistant"):
            st.write(
                st.session_state.answer
            )


        # -----------------------------
        # Feedback
        # -----------------------------
        fb_col1, fb_col2 = st.columns(2)


        with fb_col1:

            if st.button("👍 Helpful"):

                st.session_state.feedback["up"] += 1


        with fb_col2:

            if st.button("👎 Not helpful"):

                st.session_state.feedback["down"] += 1


        st.caption(
            f"Feedback so far — "
            f"👍 {st.session_state.feedback['up']}  "
            f"👎 {st.session_state.feedback['down']}"
        )


    # -----------------------------
    # Recent Conversation History
    # -----------------------------
    if st.session_state.chat_history:

        with st.expander("🕘 Recent Questions"):

            for h in reversed(
                st.session_state.chat_history[-3:]
            ):

                st.markdown(
                    f"**Q:** {h['question']}"
                )

                st.markdown(
                    f"**A:** {h['answer']}"
                )

                st.markdown("---")


    # -----------------------------
    # Translation Feature
    # -----------------------------
    if st.session_state.answer:

        st.divider()

        st.subheader(
            "🌐 Translate Advisory"
        )


        # Supported languages
        languages = {
            "Tamil": "ta",
            "Hindi": "hi",
            "Telugu": "te",
            "Malayalam": "ml",
            "Kannada": "kn",
            "English": "en"
        }


        selected_language = st.selectbox(
            "Select Language",
            list(languages.keys())
        )


        # -----------------------------
        # Translate Button
        # -----------------------------
        if st.button("Translate Answer"):

            try:

                with st.spinner(
                    "Translating..."
                ):

                    translated_text = translate_text(
                        st.session_state.answer,
                        languages[selected_language]
                    )


                st.success(
                    translated_text
                )


            except Exception as e:

                error_message = str(e).lower()


                # Handle rate limiting
                if (
                    "too many requests"
                    in error_message
                    or "429"
                    in error_message
                ):

                    st.warning(
                        "⚠️ Google Translate is "
                        "temporarily rate-limiting "
                        "requests. Please wait a few "
                        "seconds and try again."
                    )

                else:

                    st.error(
                        f"Translation failed: {e}"
                    )


# -----------------------------
# Weather Error
# -----------------------------
else:

    st.error(
        "Unable to fetch weather data."
    )
