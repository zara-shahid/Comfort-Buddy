# 🌸 Comfort-Buddy

✨ **Comfort-Buddy** is an emotionally intelligent web app that provides personalized comfort, mood-matching recipes, uplifting songs, and anti-stress activities based on your current feelings. It also keeps a mood journal with sentiment analysis.

---

## 📖 About the Project

I created **Comfort-Buddy** to help people feel supported during moments of stress, sadness, or even joy.  

- **Inspiration:** Mental well-being is often overlooked. I wanted to create a virtual companion that comforts and motivates users.  
- **What I Learned:**  
  - Integrating **AI models (LLaMA via Groq)** with **Streamlit**  
  - Performing **sentiment analysis** using **TextBlob**  
  - Fetching external images using the **Unsplash API**  
  - Building modern, animated **Streamlit UIs** with CSS  
- **Challenges Faced:**  
  - Crafting empathetic AI prompts for meaningful responses  
  - Handling different emotional states with accurate sentiment detection  
  - Fetching and displaying suitable images seamlessly  

---

## 🖥️ Features

- 🌈 **Mood Detection & Sentiment Analysis** (via TextBlob)  
- 🧠 **AI Comfort Messages** (powered by Groq LLaMA3)  
- 🍲 **Mood-Matching Recipe Suggestions** with Unsplash images  
- 🎵 **Song Recommendations** to lift your mood  
- 🧘 **Anti-Stress Activity Prompts** for relaxation  
- 📔 **Mood Journal** to track emotions and export as CSV  
- ✨ **Animated Gradient UI** with glassmorphism design  

---

## 🛠️ Built With

- **Python** — Core programming language  
- **Streamlit** — Web app framework  
- **Groq API (LLaMA3)** — For AI-generated comfort responses  
- **Pandas** — For mood journal storage and CSV export  
- **Unsplash API** — For fetching recipe and vibe images  
- **TextBlob** — For sentiment analysis and NLP  
- **CSS & Markdown** — For modern, glowing UI elements  

---

## 🚀 Installation & Setup

1. **Clone this repository:**
   ```bash
   git clone https://github.com/zara-shahid/Comfort-Buddy.git
   cd Comfort-Buddy

Install dependencies:


pip install -r requirements.txt
Set environment variables:


export GROQ_API_KEY="your_groq_api_key"
export UNSPLASH_ACCESS_KEY="your_unsplash_access_key"
Run the app:


streamlit run app.py

✨ Future Enhancements
🎤 Voice-based interaction for comfort responses

🎶 Background music that adapts to your mood

📊 Advanced mood analytics with charts and insights

📜 License
This project is licensed under the MIT License — feel free to use and modify it.

