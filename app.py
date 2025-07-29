import streamlit as st
from groq import Groq
import datetime
import pandas as pd
import os
import requests
from textblob import TextBlob # Import TextBlob

# --- API Key Handling ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

if not GROQ_API_KEY:
    st.error("❌ GROQ_API_KEY not found. Please set it as an environment variable.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

if not UNSPLASH_ACCESS_KEY:
    print("Unsplash API key not found. Image fetching will be skipped.")
# --- End API Key Handling ---

# --- Define a default AI model ---
DEFAULT_AI_MODEL = "llama3-8b-8192"
# --- End Default AI Model ---

# Helper to fetch dish image from Unsplash
def get_dish_image(query):
    if not UNSPLASH_ACCESS_KEY:
        return None
    url = "https://api.unsplash.com/search/photos"
    params = {
        "query": query,
        "per_page": 1,
        "client_id": UNSPLASH_ACCESS_KEY
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        if data["results"]:
            return data["results"][0]["urls"]["regular"]
    except Exception as e:
        st.error(f"Error fetching image: {e}")
        return None

# --- Robust AI Response Parsing Function ---
def parse_ai_response(text):
    data = {}
    keys_order = ["Comfort", "Recipe", "Vibe", "Song", "Anti-Stress Activity"]
    current_key = None
    current_value_lines = []
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        found_key = False
        for key in keys_order:
            if line.startswith(f"**{key}:**"):
                if current_key:
                    data[current_key] = "\n".join(current_value_lines).strip()
                current_key = key
                current_value_lines = [line[len(f"**{key}:**"):].strip()]
                found_key = True
                break
        if not found_key and current_key:
            current_value_lines.append(line)
    if current_key:
        data[current_key] = "\n".join(current_value_lines).strip()
    return data
# --- End Robust AI Response Parsing Function ---

# Helper to convert color names to approximate hex codes for display
COLOR_MAP = {
    "red": "#FF0000", "blue": "#0000FF", "green": "#008000", "yellow": "#FFFF00",
    "orange": "#FFA500", "purple": "#800080", "pink": "#FFC0CB", "brown": "#A52A2A",
    "black": "#000000", "white": "#FFFFFF", "gray": "#808080", "grey": "#808080",
    "cyan": "#00FFFF", "magenta": "#FF00FF", "#00FF00": "lime", "teal": "#008080",
    "navy": "#000080", "maroon": "#800000", "olive": "#808000", "silver": "#C0C0C0",
    "gold": "#FFD700", "indigo": "#4B0082", "violet": "#EE82EE", "cream": "#FFFDD0",
    "beige": "#F5F5DC", "peach": "#FFE5B4", "lavender": "#E6E6FA", "turquoise": "#40E0D0",
    "chartreuse": "#7FFF00", "coral": "#FF7F50", "khaki": "#F0E68C"
}
def display_color_palette(vibe_text):
    colors_str = vibe_text.split("—")[-1].strip()
    color_names = [c.strip().lower() for c in colors_str.split(",")]
    
    html_colors = ""
    for name in color_names:
        hex_code = COLOR_MAP.get(name, "#CCCCCC")
        html_colors += f'<div style="width: 30px; height: 30px; background-color: {hex_code}; border-radius: 50%; display: inline-block; margin: 0 5px; border: 1px solid rgba(255,255,255,0.5);" title="{name.capitalize()}"></div>'
    return html_colors

# Function to get sentiment label - IMPROVED with more keywords
def get_sentiment_label(polarity, mood_text):
    mood_text_lower = mood_text.lower()
        # Expanded lists for strong keywords
    strong_negative_keywords = [
        "depressed", "suicidal", "hopeless", "devastated", "miserable", "despair", "broken",
        "crushed", "grief", "sorrow", "anguish", "dread", "heartbroken", "downhearted",
        "distraught", "agonizing", "shattered", "desperate", "overwhelmed", "anxious",
        "stressed", "terrible", "awful", "horrible", "sad", "unhappy", "lonely", "exhausted",
        "tired", "worn out", "burnt out", "frustrated", "angry", "furious", "irritated",
        "annoyed", "bitter", "resentful", "lost", "confused", "empty", "worthless",
        "guilty", "ashamed", "scared", "fearful", "terrified", "panicked", "nervous"
    ]
    strong_positive_keywords = [
        "ecstatic", "euphoric", "elated", "overjoyed", "thrilled", "jubilant", "blissful",
        "fantastic", "amazing", "wonderful", "great", "excellent", "superb", "brilliant",
        "happy", "joyful", "excited", "optimistic", "hopeful", "grateful", "blessed",
        "proud", "confident", "energetic", "refreshed", "peaceful", "calm", "serene",
        "loved", "appreciated", "inspired", "motivated", "content", "satisfied"
    ]
    # Check for strong negative keywords first
    for keyword in strong_negative_keywords:
        if keyword in mood_text_lower:
            return "Very Negative 😥" # Override to very negative if such words are present
    # Check for strong positive keywords
    for keyword in strong_positive_keywords:
        if keyword in mood_text_lower:
            return "Very Positive 😄" # Override to very positive if such words are present
    # Fallback to polarity score if no strong keywords are found
    if polarity <= -0.5:
        return "Very Negative 😔"
    elif polarity <= -0.1:
        return "Negative 😞"
    elif polarity >= 0.5:
        return "Very Positive 😄"
    elif polarity >= 0.1:
        return "Positive 🙂"
    else:
        return "Neutral 😐"

# --- Session State Initialization ---
if "journal" not in st.session_state:
    st.session_state.journal = []
if "mood" not in st.session_state:
    st.session_state.mood = ""
if "last_response_data" not in st.session_state:
    st.session_state.last_response_data = None
if "last_who_selected" not in st.session_state:
    st.session_state.last_who_selected = None
if "last_sentiment_polarity" not in st.session_state:
    st.session_state.last_sentiment_polarity = None
if "last_sentiment_label" not in st.session_state:
    st.session_state.last_sentiment_label = None
# --- End Session State Initialization ---

st.set_page_config(page_title="Comfort-Buddy", page_icon="🧠", layout="centered")

# 💫 Refined Styling
st.markdown("""
<style>
/* 🔥 Modern Animated Gradient Background */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(-45deg, #ff9a9e, #fad0c4, #a18cd1, #fbc2eb);
    background-size: 400% 400%;
    animation: gradientShift 12s ease infinite;
    min-height: 100vh;
    position: relative; /* For the subtle overlay */
}

/* Subtle Overlay for better readability */
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.15); /* Semi-transparent dark overlay */
    z-index: -1; /* Below content but above background */
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* ✨ Glowing, Breathing Title */
.big-title {
    color: #ffffff;
    font-size: clamp(30px, 5vw, 52px);
    text-align: center;
    font-weight: 800;
    letter-spacing: 1px;
    text-transform: uppercase;
    -webkit-text-fill-color: white;
    text-shadow: 0 0 15px rgba(155, 135, 245, 0.7), 0 0 25px rgba(155, 135, 245, 0.5);
    animation: titleMove 6s linear infinite;
    padding: 10px 0;
}

@keyframes titleMove {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Soft Subtitle */
.subtitle {
    text-align: center;
    font-size: clamp(15px, 2.5vw, 22px);
    color: rgba(255, 255, 255, 0.95);
    margin-bottom: 2em;
    font-weight: 400;
    letter-spacing: 0.6px;
    text-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
    animation: fadeIn 2s ease-in;
}

/* 🪩 Neon Glass Cards with Floating Effect */
.card {
    background: rgba(255, 255, 255, 0.18);
    backdrop-filter: blur(18px);
    border-radius: 20px;
    padding: 25px;
    border: 2px solid transparent;
    box-shadow: 0 10px 35px rgba(0, 0, 0, 0.2);
    animation: fadeIn 1.2s ease-in;
    position: relative;
    transition: all 0.4s ease-in-out;
    margin-bottom: 20px;
}

.card::before {
    content: '';
    position: absolute;
    top: -2px; left: -2px; right: -2px; bottom: -2px;
    background: linear-gradient(45deg, #ff9a9e, #fad0c4, #a18cd1, #fbc2eb);
    background-size: 300% 300%;
    z-index: -1;
    border-radius: 22px;
    animation: borderGlow 5s linear infinite;
}

@keyframes borderGlow {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.card:hover {
    transform: translateY(-6px) scale(1.02);
    box-shadow: 0 20px 50px rgba(255, 182, 193, 0.4);
}

/* 🖱️ Gradient Animated Buttons - Apply to ALL st.button elements */
.stButton > button {
    background: linear-gradient(90deg, #ff758c, #ff7eb3, #fad0c4);
    background-size: 200% 200%;
    color: white;
    border: none;
    border-radius: 15px;
    padding: 14px 26px;
    font-size: 16px;
    font-weight: bold;
    box-shadow: 0 6px 20px rgba(255, 182, 193, 0.3);
    transition: all 0.4s ease-in-out;
    animation: pulse 2s infinite;
    cursor: pointer;
}

.stButton > button:hover {
    background-position: 100% 0;
    transform: translateY(-3px);
    box-shadow: 0 10px 30px rgba(255, 182, 193, 0.6);
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}

/* 🖼️ Floating Images */
.full-width-image-container {
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 20px 0;
    width: 100%;
}

.full-width-image-container img {
    max-width: 90%;
    height: auto;
    border-radius: 14px;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease-in-out;
}

.full-width-image-container img:hover {
    transform: translateY(-5px) scale(1.03);
    box-shadow: 0 15px 40px rgba(255, 182, 193, 0.5);
}

/* General image styling */
img {
    border-radius: 14px;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease-in-out;
}

img:hover {
    transform: translateY(-5px) scale(1.03);
    box-shadow: 0 15px 40px rgba(255, 182, 193, 0.5);
}

/* 🔥 Inputs & Widgets - Enhanced Focus/Hover */
.stTextInput > div > div > input {
    background: rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 12px;
    color: black; /* FIX: Set text color to black for visibility on light background */
    padding: 10px;
    transition: all 0.3s ease;
}

.stTextInput > div > div > input::placeholder {
    color: rgba(0, 0, 0, 0.7); /* FIX: Set placeholder color to dark for visibility */
}

.stTextInput > div > div > input:focus {
    box-shadow: 0 0 0 3px rgba(255, 182, 193, 0.7); /* Soft glow on focus */
    border-color: rgba(255, 182, 193, 0.7);
}

/* Selectbox and Radio - Enhanced */
.stSelectbox > div > div, .stRadio > div {
    background: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 12px;
    color: white;
    transition: all 0.3s ease;
}

.stSelectbox > div > div:hover, .stRadio > div:hover {
    background: rgba(255, 255, 255, 0.25);
}

/* Specific styling for radio buttons to match card aesthetic */
div.stRadio > label {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(8px);
    border-radius: 10px;
    padding: 10px 15px;
    margin: 5px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    transition: all 0.3s ease;
    color: white; /* Ensure text is white */
}

div.stRadio > label:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: scale(1.02);
}

div.stRadio > label > div > p {
    color: white !important; /* Force text color white for radio options */
    font-size: 0.9em; /* Smaller font for radio options */
}

/* Fade-in Animation */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(15px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Gradient Text for Main Headings */
.gradient-text-heading {
    background: linear-gradient(90deg, #ff758c, #ff7eb3, #fad0c4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: bold;
    font-size: clamp(24px, 4vw, 36px);
    text-align: center;
    margin-top: 2em; /* More space above these headers */
    margin-bottom: 1em;
    animation: fadeIn 1.5s ease-in-out;
}

/* Custom Divider Style */
.custom-divider {
    border: none;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
    margin: 3em 0; /* More space around dividers */
    animation: fadeIn 2s ease-in;
}

/* Expander Header Style */
.st-emotion-cache-p2s0s8 { /* Target Streamlit expander header directly */
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border-radius: 15px;
    padding: 10px 20px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    transition: all 0.3s ease-in-out;
    color: white !important; /* Ensure text is white */
}

.st-emotion-cache-p2s0s8:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: translateY(-2px);
}

.st-emotion-cache-p2s0s8 p {
    color: white !important; /* Force text color inside expander header */
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# --- Title and Subtitle ---
st.markdown('<div class="big-title">Comfort-Buddy</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">✨ Tell me how you feel — I’ll comfort you, feed you, and vibe with you ✨</div>', unsafe_allow_html=True)
st.write("") # Add some space

# --- Main Input Section ---
mood = st.text_input(
    "💬 How are you feeling today?",
    placeholder="e.g., Feeling a bit low, could use a pick-me-up. Or perhaps, I'm soaring high!",
    key="mood_input",
    value=st.session_state.mood)
who = st.radio("👥 Who should comfort you?", ["🤖 AI", "🧑 Human Friend"], horizontal=True)

# Main action button
if st.button("🌟 Get Comfort & Recipe", key="get_comfort_button"):
    if mood:
        # Clear previous response data from session state before generating new one
        st.session_state.last_response_data = None
        st.session_state.last_who_selected = None
        st.session_state.last_sentiment_polarity = None
        st.session_state.last_sentiment_label = None
                
        # --- Perform Sentiment Analysis ---
        text_blob_mood = TextBlob(mood)
        sentiment_polarity = text_blob_mood.sentiment.polarity
        sentiment_label = get_sentiment_label(sentiment_polarity, mood) # Pass mood text for keyword check
                
        st.session_state.last_sentiment_polarity = sentiment_polarity
        st.session_state.last_sentiment_label = sentiment_label
        # --- End Sentiment Analysis ---

        with st.spinner("✨ Crafting your comfort & vibes... Please wait a moment..."):
            response_text = ""
            if who == "🧑 Human Friend":
                # For human friend, keep it simple and universally comforting
                comfort = "I’m here for you. It sounds like you're going through a lot. Let’s talk, cry, laugh — whatever you need, I’m with you. ❤️"
                recipe = "Warm, homemade Chicken Noodle Soup — perfect for when you need a gentle hug in a bowl."
                vibe = "☔️🌧️✨ — Blue, Grey, Warm Yellow" # Updated vibe for depressive mood
                song = "'Fix You' — Coldplay" # More comforting song
                anti_stress_activity = ""
                response_text = f"""
                **Comfort:** {comfort}
                **Recipe:** {recipe}
                **Vibe:** {vibe}
                **Song:** {song}
                """
                if anti_stress_activity:
                    response_text += f"\n**Anti-Stress Activity:** {anti_stress_activity}"
            else: # User selected "🤖 AI"
                selected_model = DEFAULT_AI_MODEL
                                
                # --- Refined Sentiment Adjective for AI Prompt ---
                sentiment_adjective = ""
                if "very negative" in sentiment_label.lower():
                    sentiment_adjective = "feeling very low and needs extremely gentle, empathetic, and uplifting support"
                elif "negative" in sentiment_label.lower():
                    sentiment_adjective = "feeling negative and needs understanding and uplifting support"
                elif "very positive" in sentiment_label.lower():
                    sentiment_adjective = "feeling very positive and wants enthusiastic, joyful suggestions"
                elif "positive" in sentiment_label.lower():
                    sentiment_adjective = "feeling positive and needs supportive, encouraging messages"
                else:
                    sentiment_adjective = "feeling neutral and needs a general supportive and positive message"

                # Check for stress keywords
                is_stressed = any(keyword in mood.lower() for keyword in ["stressed", "anxious", "overwhelmed", "tense", "nervous"])
                
                prompt = f"""
                I am an emotionally intelligent assistant. A person just said: '{mood}'.
                Based on my analysis, their mood suggests they are {sentiment_adjective}.
                Please respond with the following in a friendly, soulful tone, specifically tailored to provide comfort and upliftment for their current emotional state:
                1. Comfort: A short, kind, comforting message, explicitly acknowledging the depth of their feelings if negative.
                2. Recipe: A recipe suggestion that gently matches their mood, focusing on comfort food if negative, or celebratory food if positive. Include dish name + short description.
                3. Vibe: A string of 3–5 relevant emojis and a color palette (3 colors, names not codes) that genuinely reflects a pathway to positive emotion or acknowledges the current state with hope.
                4. Song: A song title + artist that is genuinely soothing and uplifting for their specific mood.
                """
                if is_stressed:
                    prompt += """
                    5. Anti-Stress Activity: A short, interactive prompt or simple activity to help alleviate stress (e.g., a 2-minute mindful breathing guide, or "Describe your ideal calm place in three words.").
                    """
                                
                prompt += """
                Format:
                **Comfort:** ...
                **Recipe:** ...
                **Vibe:** ...
                **Song:** ...
                """
                if is_stressed:
                    prompt += "**Anti-Stress Activity:** ..."

                response = client.chat.completions.create(
                    model=selected_model,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.choices[0].message.content

            # Store the generated data in session state for persistent display
            st.session_state.last_response_data = response_text
            st.session_state.mood = mood # Store the mood for journaling
            st.session_state.last_who_selected = who # Store who provided comfort for explanation
        
        st.balloons()
        st.rerun() # Rerun to display new content and clear spinner
    else:
        st.warning("Please tell me how you’re feeling first. Your comfort awaits!")

# --- Display Results Section (conditionally shown after generation) ---
if st.session_state.last_response_data:
    parsed_data = parse_ai_response(st.session_state.last_response_data)
    comfort_text = parsed_data.get("Comfort", "No comfort provided.")
    recipe_part = parsed_data.get("Recipe", "No recipe provided.")
    vibe_part = parsed_data.get("Vibe", "No vibe provided.")
    song_part = parsed_data.get("Song", "No song provided.")
    anti_stress_activity = parsed_data.get("Anti-Stress Activity", "")

    st.markdown('<div class="gradient-text-heading">🌸 Here’s what I have for you:</div>', unsafe_allow_html=True)
        
    # Display Sentiment if available
    if st.session_state.last_sentiment_label:
        st.markdown(f"""
        <div class="card" style="background: rgba(255, 255, 255, 0.1); border: none; box-shadow: none; padding: 15px;">
        <h4 style="margin-top: 0;">Your Mood Sentiment: {st.session_state.last_sentiment_label}</h4>
        <p style="font-size: 0.9em; color: rgba(255,255,255,0.8);">
            (Polarity score: {st.session_state.last_sentiment_polarity:.2f} - a value between -1 (negative) and +1 (positive))
        </p>
        </div>
        """, unsafe_allow_html=True)

    # Display Comfort and Recipe in two columns
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="card">
        <h4>🌸 Comfort</h4>
        <p>{comfort_text}</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="card">
        <h4>🍲 Recipe</h4>
        <p>{recipe_part}</p>
        </div>
        """, unsafe_allow_html=True)
            
    # Extract dish name & fetch image
    dish_name = recipe_part.split("—")[0].strip() if "—" in recipe_part else recipe_part
    image_url = get_dish_image(dish_name)
        
    # Display image in a full-width section below the two columns
    if image_url:
        st.markdown(f"""
        <div class="full-width-image-container">
            <img src="{image_url}"
                    alt="{dish_name}">
        </div>
        <p style="text-align:center; color:white; font-style:italic; font-size: 0.9em; margin-top: 10px;">📷 {dish_name} (via Unsplash)</p>
        """, unsafe_allow_html=True)
    else:
        st.write("📷 No image available for this dish.")
        
    # Display other cards (Mood Vibes, Song, Anti-Stress Activity)
    st.markdown(f"""
    <div class="card">
    <h4>🎨 Mood Vibes</h4>
    <p>{vibe_part}</p>
    <div style="text-align: center; margin-top: 10px;">
        {display_color_palette(vibe_part)}
    </div>
    </div>
    """, unsafe_allow_html=True)
        
    st.markdown(f"""
    <div class="card">
    <h4>🎵 Song</h4>
    <p>{song_part}</p>
    </div>
    """, unsafe_allow_html=True)

    if anti_stress_activity:
        st.markdown(f"""
        <div class="card">
        <h4>🧘‍♀️ Anti-Stress Activity</h4>
        <p>{anti_stress_activity}</p>
        </div>
        """, unsafe_allow_html=True)

    # --- Human vs. AI Comfort Explanation ---
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    with st.expander("🤔 Why this comfort? Understanding Human vs. AI"):
        current_who_selected = st.session_state.get('last_who_selected', '🤖 AI')
        if current_who_selected == "🧑 Human Friend":
            st.markdown("""
            <div class="card" style="background: rgba(255, 255, 255, 0.1); border: none; box-shadow: none; padding: 15px;">
            <p style="color: white; font-size: 0.95em; line-height: 1.6;">
            When you choose a **Human Friend** for comfort, you're tapping into the unique empathy, shared experiences, and intuitive understanding that only another human can offer. This comfort comes from genuine connection, personal wisdom, and the ability to relate on a deeply emotional level, without algorithms or data processing. It's about genuine presence and heartfelt support.
            </p>
            </div>
            """, unsafe_allow_html=True)
        else: # AI
            st.markdown(f"""
            <div class="card" style="background: rgba(255, 255, 255, 0.1); border: none; box-shadow: none; padding: 15px;">
            <p style="color: white; font-size: 0.95em; line-height: 1.6;">
            When you choose **AI** for comfort, you're receiving a response generated by advanced algorithms like the **{DEFAULT_AI_MODEL.replace('-', ' ').upper()}** model. This AI processes vast amounts of text data to understand your mood and generate relevant, supportive messages, recipes, and activity suggestions. It excels at pattern recognition and providing structured information, offering a unique form of comfort based on its intelligence. While it lacks personal experience or genuine emotions, it aims to be helpful and supportive based on its intelligence.
            <br><br>
            For your comfort, the AI also considered that your mood's sentiment was perceived as **{st.session_state.last_sentiment_label.lower()}**.
            </p>
            </div>
            """, unsafe_allow_html=True)
    # --- End Human vs. AI Comfort Explanation ---

    # --- Feeling Better? Section and Reset Button ---
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    st.markdown("## Feeling Better?")
    st.write("I hope this helped brighten your day. Remember to check your journal below or share your mood again!")
    if st.button("🔄 Clear Mood & Start Over", key="reset_button"):
        st.session_state.mood = ""
        st.session_state.last_response_data = None
        st.session_state.last_who_selected = None
        st.session_state.last_sentiment_polarity = None
        st.session_state.last_sentiment_label = None
        st.rerun()
    # --- End Feeling Better Section ---

    # Save to journal after successful display
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    st.session_state.journal.append({
        "time": now,
        "mood": st.session_state.mood,
        "who": st.session_state.last_who_selected,
        "sentiment_polarity": st.session_state.last_sentiment_polarity, # Save sentiment
        "sentiment_label": st.session_state.last_sentiment_label,        # Save sentiment label
        "response": st.session_state.last_response_data,
    })

# --- End Display Results Section ---

# --- Mood Journal Section ---
if st.session_state.journal:
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    st.markdown('<div class="gradient-text-heading">📔 Mood Journal</div>', unsafe_allow_html=True)
    for entry in st.session_state.journal[::-1]:
        # Display sentiment in the journal entry
        sentiment_info = f" (Sentiment: {entry['sentiment_label']} / {entry['sentiment_polarity']:.2f})" if entry.get('sentiment_label') else ""
        st.markdown(f"""
        <div class="card">
        <b>{entry['time']}</b> — *{entry['mood']}*{sentiment_info} ({entry['who']})<br>
        <div style="margin-top:5px">{entry['response']}</div>
        </div>
        """, unsafe_allow_html=True)
    if st.button("📥 Download Mood Journal", key="download_journal_button"):
        df = pd.DataFrame(st.session_state.journal)
        st.download_button("Download as CSV", df.to_csv(index=False), file_name="mood_journal.csv")

# --- About / Footer Section ---
st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
with st.expander("✨ About Comfort-Buddy"):
    st.markdown("""
    <div class="card" style="background: rgba(255, 255, 255, 0.1); border: none; box-shadow: none; padding: 15px;">
    <p style="color: white; font-size: 0.95em; line-height: 1.6;">
    Comfort-Buddy is designed to be your emotional companion, offering personalized comfort, delightful recipe suggestions, mood-matching vibes, and uplifting songs. Whether you need a virtual hug from an AI or a relatable message from a "human friend," this app is here to brighten your day.
    </p>
    <p style="color: white; font-size: 0.95em; line-height: 1.6;">
    Powered by **Groq** for fast AI responses and **Unsplash** for beautiful food imagery. Sentiment analysis is provided by **TextBlob**. Created with ❤️ for your well-being.
    </p>
    </div>
    """, unsafe_allow_html=True)