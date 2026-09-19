import streamlit as st
from deep_translator import GoogleTranslator
from weather import get_weather
from rules2 import get_tomorrow_alert
from groq import Groq




try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    client = None

# -----------------------------
# Rule-Based Chatbot
# -----------------------------
def answer_question(question, crop, weather):

    prompt = f"""
    Crop: {crop}

    Today's Weather:
    Maximum Temperature: {weather['temp_max']}°C
    Minimum Temperature: {weather['temp_min']}°C
    Rainfall: {weather['rainfall_mm']} mm

    Farmer Question:
    {question}

    Give practical farming advice based on the crop and weather.
    """

    try:
        response = client.chat.completions.create(
           model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert agricultural advisor."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Groq Error: {e}"

# -----------------------------
# Streamlit Configuration
# -----------------------------
st.set_page_config(
    page_title="Crop Advisory System",
    page_icon="🌾",
    layout="centered"
)


st.title("🌾 Crop Advisory System")
st.write("📍 Demo Location: Kumbakonam, Tamil Nadu")


# -----------------------------
# Crop Selection
# -----------------------------

st.set_page_config(page_title="Crop Advisory System", page_icon="🌾")

st.title("🌾 Crop Advisory System")

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

st.success(f"You selected: {crop}")


# Location
lat = 10.9601
lon = 79.3788


weather_data = get_weather(lat, lon)


if weather_data and len(weather_data) >= 2:

    today = weather_data[0]
    tomorrow = weather_data[1]


    # -----------------------------
    # Weather Section
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

    question = st.text_input(
        "Type your question",
        placeholder="Example: Should I irrigate today?"
    )


    if "answer" not in st.session_state:
        st.session_state.answer = ""


    if st.button("Ask"):

        if question.strip():

            if client is None:
                st.error(
                    "Gemini API key not found. Please add GEMINI_API_KEY to Streamlit Secrets."
                )

            else:
                st.session_state.answer = answer_question(
                    question,
                    crop,
                    today
                )

                with st.chat_message("user"):
                    st.write(question)

                with st.chat_message("assistant"):
                    st.write(st.session_state.answer)

        else:
            st.warning("Please enter a question.")


    # -----------------------------
    # Translation Feature
    # -----------------------------
    if st.session_state.answer:

        st.divider()

        st.subheader("🌐 Translate Advisory")


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


        if st.button("Translate Answer"):

            try:

                translated_text = GoogleTranslator(
                    source="auto",
                    target=languages[selected_language]
                ).translate(
                    st.session_state.answer
                )


                st.success(translated_text)


            except Exception as e:
                st.error(f"Translation failed: {e}")


else:

    st.error("Unable to fetch weather data.")