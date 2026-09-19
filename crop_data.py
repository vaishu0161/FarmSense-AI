import streamlit as st

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
