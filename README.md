# AI-Powered Task Scheduler

AI-Powered Task Scheduler is an intelligent task scheduling system that optimizes your daily routine based on your physical and mental stamina. It uses Large Language Models (LLMs) to categorize tasks and a custom algorithm to prevent burnout by tracking fatigue levels.

## 🚀 Features

- **LLM-Based Task Classification**: Automatically categorizes tasks into "Brain", "Body", or "Rest" and determines their "Intensity" (Low, Medium, High) using the Groq API.
- **Fatigue Tracking**: Real-time simulation of mental (Brain) and physical (Body) fatigue levels.
- **Dynamic Scheduling**: Prioritizes tasks based on deadlines and current stamina levels.
- **Smart Task Splitting**: Automatically pauses and splits long, demanding tasks if fatigue exceeds safe thresholds.
- **Recovery Management**: Suggests rest periods and "rest-type" tasks (like reading or sleeping) to recover stamina.

## 🛠️ Tech Stack

- **Backend**: Python, Flask
- **AI/LLM**: Groq API (`llama-3.3-70b-versatile`)
- **Frontend**: Vanilla HTML5, CSS3, JavaScript
- **Configuration**: `python-dotenv` for environment management

## 📦 Project Structure

```text
Tiny_Project/
├── backend/
│   ├── app.py           # Flask server & API endpoints
│   ├── llm.py           # Groq LLM integration & task classifier
│   └── scheduler.py     # Core scheduling logic & fatigue engine
├── frontend/
│   ├── templates/       # HTML view files
│   └── static/          # CSS styles & client-side JS logic
├── .env                 # Environment variables (API keys)
├── .gitignore           # Files excluded from Git
├── requirements.txt     # Python dependencies
└── README.md            # You are here!
```

## ⚙️ Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/MoyukHNaskaR/AI-Powered-Task-Scheduler
   cd AI-Powered-Task-Scheduler
   ```

2. **Set up Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in the root directory and add your Groq API key:
   ```env
   GROQ_API_KEY=your_api_key_here
   ```

## 🏃 Usage

1. **Start the Backend**:
   ```bash
   python backend/app.py
   ```
2. **Access the Web Interface**:
   Open your browser and navigate to `http://127.0.0.1:5000`.
3. **Input Tasks**:
   - Set your name and stamina levels.
   - Add tasks with names, durations, and optional deadlines.
   - Run the scheduler to see your optimized timeline!

