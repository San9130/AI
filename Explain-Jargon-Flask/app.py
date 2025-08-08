from flask import Flask, render_template, request, send_file
from pathlib import Path
from openai import OpenAI
from pybraille import convertText
import os
import re

app = Flask(__name__)
client = OpenAI()

# Paths for saving audio and Braille files
AUDIO_PATH = Path("static/answer.mp3")
BRAILLE_PATH = Path("static/answer.brl")

# --- Dynamic Model Selection Logic ---

# A basic set of common words for low complexity (can be expanded)
COMMON_WORDS = set("""
the be to of and a in that have I it for not on with he as you do at
this but his by from they we say her she or an will my one all would there
their what so up out if about who get which go me
""".split())

def local_complexity_score(term):
    """
    Quick local heuristic to assign a preliminary complexity rating.
    Returns: 'low', 'medium', or 'high'
    """
    t = term.lower().strip()
    t_clean = re.sub(r"[^a-zA-Z\s]", "", t)
    tokens = t_clean.split()

    # If all tokens are in common words → low complexity
    if all(token in COMMON_WORDS for token in tokens):
        return "low"

    # Very long/complex words → high
    if any(len(token) > 12 for token in tokens) or len(tokens) > 3:
        return "high"

    # Contains obvious domain-specific markers
    domain_keywords = [
        "syndrome", "quantum", "algorithm", "enzyme", "protocol",
        "derivative", "metabolism", "neural", "infrastructure"
    ]
    if any(word in t for word in domain_keywords):
        return "high"

    return "medium"

def ai_complexity_score(term):
    """
    Uses GPT-5-nano to classify term complexity more accurately.
    Returns: 'low', 'medium', or 'high'
    """
    prompt = (
        f"Classify the complexity of the term '{term}' for explanation to a general audience. "
        "Respond with only one word: 'low', 'medium', or 'high'. "
        "Low = very common or simple, Medium = moderately technical, High = rare or highly technical."
    )
    try:
        completion = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=3
        )
        classification = completion.choices[0].message.content.strip().lower()
        if classification in ["low", "medium", "high"]:
            return classification
    except Exception as e:
        print(f"AI scoring failed, fallback to medium: {e}")
    return "medium"  # fallback

def choose_model_for_term(term):
    # First pass: local heuristic
    local_score = local_complexity_score(term)

    # If obviously low or high → no AI check
    if local_score in ["low", "high"]:
        final_score = local_score
    else:
        # Borderline → AI-assisted classification
        ai_score = ai_complexity_score(term)
        final_score = ai_score

    # Map complexity to model
    if final_score == "low":
        return "gpt-5-nano"
    elif final_score == "medium":
        return "gpt-5-mini"
    else:
        return "gpt-5"

# --- Generate explanation text via GPT ---
def generate_text(term, language):
    model_choice = choose_model_for_term(term)
    print(f"[DEBUG] Using model: {model_choice} for term: {term}")  # Debug log

    prompt = f"Provide a simplified, one-sentence explanation of '{term}' in {language}."
    completion = client.chat.completions.create(
        model=model_choice,
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content

# --- Generate audio response and save as MP3 ---
def generate_audio(text):
    try:
        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="coral",
            input=text,
            instructions="Speak in a neutral tone and explain the term."
        ) as response:
            with open(AUDIO_PATH, "wb") as f:
                for byte in response.iter_bytes():
                    f.write(byte)
    except Exception as e:
        print(f"Error generating audio: {e}")

# --- Generate Braille response and save as .brl file ---
def generate_braille(text):
    try:
        braille_text = convertText(text)
        with open(BRAILLE_PATH, "w", encoding="utf-8") as f:
            f.write(braille_text)
        return braille_text
    except Exception as e:
        print(f"Error generating Braille: {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    explanation = None
    braille_output = None
    audio_ready = False

    if request.method == "POST":
        term = request.form["term"].strip()
        language = request.form["language"].strip()
        output_fmt = request.form["output_fmt"]

        if term and language:
            explanation = generate_text(term, language)

            if output_fmt == "A":  # Audio
                generate_audio(explanation)
                audio_ready = True
            elif output_fmt == "B":  # Braille
                braille_output = generate_braille(explanation)

    return render_template("index.html", 
                           explanation=explanation,
                           braille_output=braille_output,
                           audio_ready=audio_ready)

@app.route("/download-audio")
def download_audio():
    if AUDIO_PATH.exists():
        return send_file(AUDIO_PATH, as_attachment=True)
    return "Audio file not found.", 404

@app.route("/download-braille")
def download_braille():
    if BRAILLE_PATH.exists():
        return send_file(BRAILLE_PATH, as_attachment=True)
    return "Braille file not found.", 404

if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    app.run(debug=True)
