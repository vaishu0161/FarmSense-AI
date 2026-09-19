import os

import gradio as gr
from deep_translator import GoogleTranslator
from groq import Groq

from weather import get_weather
from rules2 import get_tomorrow_alert

# -----------------------------
# Groq Client
# -----------------------------
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

try:
    client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
except Exception:
    client = None

# -----------------------------
# Static Data
# -----------------------------
CROPS = [
    "Paddy 🌾", "Sugarcane 🎋", "Groundnut 🥜", "Maize 🌽", "Wheat 🌾",
    "Cotton ☁️", "Banana 🍌", "Coconut 🥥", "Tomato 🍅", "Onion 🧅",
    "Potato 🥔", "Brinjal 🍆", "Chilli 🌶️", "Millets 🌾", "Mango 🥭",
    "Papaya 🍈", "Guava 🍏", "Turmeric 🌿", "Ginger 🫚", "Black Gram",
    "Green Gram", "Red Gram", "Sesame", "Sunflower 🌻", "Soybean",
    "Ragi", "Cabbage 🥬", "Cauliflower 🥦", "Carrot 🥕", "Beans", "Cucumber 🥒",
]

LANGUAGES = {
    "Tamil": "ta",
    "Hindi": "hi",
    "Telugu": "te",
    "Malayalam": "ml",
    "Kannada": "kn",
    "English": "en",
}

# Demo location: Kumbakonam, Tamil Nadu
LAT, LON = 10.9601, 79.3788


# -----------------------------
# Core Logic (unchanged from the Streamlit version)
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
                {"role": "system", "content": "You are an expert agricultural advisor."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Groq Error: {e}"


def load_weather_and_advisory(crop):
    """Fetches weather + builds tomorrow's advisory for the selected crop."""
    weather_data = get_weather(LAT, LON)

    if not weather_data or len(weather_data) < 2:
        return "Unable to fetch weather data.", "", None

    today = weather_data[0]
    tomorrow = weather_data[1]

    weather_text = (
        f"Max Temp: {today['temp_max']} °C   |   "
        f"Min Temp: {today['temp_min']} °C   |   "
        f"Rainfall: {today['rainfall_mm']} mm"
    )

    advisory = get_tomorrow_alert(tomorrow, crop)

    return weather_text, advisory, today


def ask_question(question, crop, today_weather):
    if not question or not question.strip():
        return "Please enter a question."
    if today_weather is None:
        return "Weather data isn't loaded yet — click 'Load Weather & Advisory' first."
    if client is None:
        return "Groq API key not found. Please add GROQ_API_KEY as a secret."
    return answer_question(question, crop, today_weather)


def translate_answer(answer, language):
    if not answer or not answer.strip():
        return "No answer to translate yet."
    try:
        return GoogleTranslator(source="auto", target=LANGUAGES[language]).translate(answer)
    except Exception as e:
        return f"Translation failed: {e}"


# -----------------------------
# Gradio UI
# -----------------------------
with gr.Blocks(title="Crop Advisory System") as demo:
    gr.Markdown("# 🌾 Crop Advisory System")
    gr.Markdown("📍 Demo Location: Kumbakonam, Tamil Nadu")

    crop = gr.Dropdown(choices=CROPS, value=CROPS[0], label="🌱 Select Your Crop")

    with gr.Row():
        weather_box = gr.Textbox(label="🌤 Today's Weather", interactive=False)
    advisory_box = gr.Textbox(label="📢 Tomorrow's Advisory", interactive=False)
    today_state = gr.State()

    refresh_btn = gr.Button("🔄 Load Weather & Advisory")

    gr.Markdown("### 💬 Ask a Farming Question")
    question = gr.Textbox(label="Your question", placeholder="Example: Should I irrigate today?")
    ask_btn = gr.Button("Ask")
    answer_box = gr.Textbox(label="Answer", interactive=False, lines=6)

    gr.Markdown("### 🌐 Translate Advisory")
    language = gr.Dropdown(choices=list(LANGUAGES.keys()), value="English", label="Select Language")
    translate_btn = gr.Button("Translate Answer")
    translated_box = gr.Textbox(label="Translated Answer", interactive=False, lines=6)

    # Wiring
    demo.load(load_weather_and_advisory, inputs=[crop], outputs=[weather_box, advisory_box, today_state])
    crop.change(load_weather_and_advisory, inputs=[crop], outputs=[weather_box, advisory_box, today_state])
    refresh_btn.click(load_weather_and_advisory, inputs=[crop], outputs=[weather_box, advisory_box, today_state])
    ask_btn.click(ask_question, inputs=[question, crop, today_state], outputs=[answer_box])
    translate_btn.click(translate_answer, inputs=[answer_box, language], outputs=[translated_box])

if __name__ == "__main__":
    demo.launch()
