from pathlib import Path
from openai import OpenAI
import sys

client = OpenAI()

def get_user_input():
    try:
        term = input("Enter a term or phrase to explain in simpler terms (or type 'quit' to exit):\n").strip()

        # Exit condition for the loop
        if term.lower() == 'quit':
            return None, None, None

        language = input("Enter the language for the explanation:\n").strip()
        output_fmt = input("Choose output format - Text (T) or Audio (A):\n").strip().upper()

        if not term or not language:
            raise ValueError("Term and language must not be empty.")

        if output_fmt not in ("T", "A"):
            raise ValueError("Output format must be 'T' for Text or 'A' for Audio.")

        return term, language, output_fmt

    except ValueError as ve:
        print(f"Input error: {ve}")
        return None, None, None

def generate_prompt(term, language):
    return f"Provide a simplified, one-sentence explanation of '{term}' in {language}."

def text_response(prompt):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        print("\nExplanation:")
        print(completion.choices[0].message.content)
    except Exception as e:
        print(f"Error retrieving text response: {e}")

def audio_response(prompt):
    speech_file_path = Path(__file__).parent / "answer.mp3"

    try:
        chat_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        text_to_speech = chat_response.choices[0].message.content

        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="coral",
            input=text_to_speech,
            instructions="Speak in a neutral tone and explain the term."
        ) as response:
            with open(speech_file_path, "wb") as f:
                for byte in response.iter_bytes():
                    f.write(byte)
                    
        print(f"\nAudio explanation saved to: {speech_file_path}")

    except Exception as e:
        print(f"Error generating or saving audio: {e}")

def main():
    while True:
        term, language, output_fmt = get_user_input()
        
        # If the user chooses to quit
        if term is None:
            print("Exiting the program.")
            break
        
        prompt = generate_prompt(term, language)

        if output_fmt == "A":
            audio_response(prompt)
        else:
            text_response(prompt)

if __name__ == "__main__":
    main()
