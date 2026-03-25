import json
from groq import Groq

import os
from dotenv import load_dotenv, find_dotenv
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '..', '.env')
load_dotenv(env_path, override=True)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY not found in environment!")
else:
    print(f"GROQ_API_KEY loaded successfully (starts with {GROQ_API_KEY[:4]}...)")

MODEL_NAME = "llama-3.3-70b-versatile"
client = Groq(api_key=GROQ_API_KEY)


def fallback_categorize(task_name):
    task_name_lower = task_name.lower()
    if any(k in task_name_lower for k in ['sleep', 'nap', 'movie', 'watch', 'relax', 'rest', 'break', 'meditat', 'chill', 'game', 'music']):
        return {"type": "rest", "intensity": "low"}
    elif any(k in task_name_lower for k in ['study', 'read', 'code', 'math', 'ai', 'write', 'learn']):
        return {"type": "brain", "intensity": "high"}
    elif any(k in task_name_lower for k in ['assignment', 'homework', 'report', 'email']):
        return {"type": "brain", "intensity": "medium"}
    elif any(k in task_name_lower for k in ['gym', 'workout', 'run', 'lift', 'sport', 'train']):
        return {"type": "body", "intensity": "high"}
    elif any(k in task_name_lower for k in ['chore', 'clean', 'cook', 'walk', 'shop', 'laundry']):
        return {"type": "body", "intensity": "low"}
    else:
        return {"type": "brain", "intensity": "medium"}


def _parse_response(response_text):
    import re
    try:
        match = re.search(r'\{.*"type".*?\}', response_text, re.DOTALL | re.IGNORECASE)
        if match:
            result = json.loads(match.group(0).replace('\n', ''))
            if result.get("type") in ["brain", "body", "rest"] and result.get("intensity") in ["low", "medium", "high"]:
                return result
    except Exception:
        pass

    try:
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        if start != -1 and end != 0:
            result = json.loads(response_text[start:end])
            if result.get("type") in ["brain", "body", "rest"] and result.get("intensity") in ["low", "medium", "high"]:
                return result
    except Exception:
        pass
    return None


def categorize_task(task_name):
    prompt = f"""You are a task classifier.
Categorize the following task: "{task_name}"

You MUST output ONLY a JSON object. No other text.
KEYS:
"type": choose exactly one of "brain", "body", "rest"
"intensity": choose exactly one of "low", "medium", "high"

RULES:
- Physical workouts (Gym, Running, Heavy lifting) MUST be "body" and "high".
- Mental studying/coding MUST be "brain" and "high".
- Casual reading/emails MUST be "brain" and "low" or "medium".
- Leisure/Sleeping/Movies (Watch movie, Sleep, Relax) MUST be "rest" and "low".

Examples:
"Running 5k" -> {{"type": "body", "intensity": "high"}}
"Gym workout" -> {{"type": "body", "intensity": "high"}}
"Watch movie" -> {{"type": "rest", "intensity": "low"}}
"Sleep" -> {{"type": "rest", "intensity": "low"}}

JSON Output ONLY:
"""

    try:
        chat = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=60
        )
        text = chat.choices[0].message.content.strip()
        result = _parse_response(text)
        if result:
            return result
    except Exception as e:
        print(f"Groq API error for task '{task_name}': {e}")

    print(f"Using fallback for task '{task_name}'")
    return fallback_categorize(task_name)
