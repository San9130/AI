from flask import Flask, render_template, request, send_file
from pathlib import Path
from openai import OpenAI
from pybraille import convertText
import os

app = Flask(__name__)
client = OpenAI()

# Paths for saving audio and Braille files
AUDIO_PATH = Path("static/answer.mp3")
BRAILLE_PATH = Path("static/answer.brl")

# Generate explanation text via GPT
def generate_text(term, language):
    prompt = f"Provide a simplified, one-sentence explanation of '{term}' in {language}."
    completion = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content

# Generate audio response and save as MP3
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

# Generate Braille response and save as .brl file
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
