# Explain Jargon with Flask

## Overview

**Explain Jargon** is an interactive web application built with [Flask](https://flask.palletsprojects.com/) that leverages the power of OpenAI to translate complex jargon terms into layman-friendly explanations. Users enter a jargon term, and the app provides an accessible explanation in one of three formats: **text**, **audio**, or **Braille**, based on user selection.

## Features

- **Jargon Translation:** Converts technical or complex terms into simple, understandable language using OpenAI's language model.
- **Multiple Output Formats:**
  - **Text:** Displays the explanation in standard text.
  - **Audio:** Reads out the explanation using text-to-speech.
  - **Braille:** Renders the explanation in a Braille-like format for accessibility.
- **Interactive UI:** A friendly and responsive web interface built with Flask.
- **Accessibility Focus:** Supports users with different access needs, including those who are visually impaired.

## How It Works

1. **Enter Jargon:** Users input a jargon term into the web interface.
2. **Choose Format:** Select the desired output format: Text, Audio, or Braille.
3. **Get Explanation:** The app queries OpenAI to generate a layman explanation and presents it in the chosen format.

## Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/San9130/AI.git
   cd AI/Explain-Jargon-Flask
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set your OpenAI API key:**
   - Create a `.env` file or set the `OPENAI_API_KEY` environment variable.

4. **Run the app:**
   ```bash
   flask run
   ```

5. **Access the UI:**
   - Open your browser and go to `http://localhost:5000`

## Usage

- Enter any jargon or technical term in the input box.
- Select your preferred output format (Text, Audio, or Braille).
- Click "Explain" to receive an accessible explanation.

## Technologies Used

- **Flask** – Web framework for Python.
- **OpenAI API** – For generating explanations.
- **Text-to-Speech Library** – For audio output (e.g., pyttsx3 or gTTS).
- **Braille Rendering** – Custom logic or library to display Braille format.

## Accessibility

This project is designed to make technical language accessible to everyone, including users with visual impairments. The Braille and audio options ensure inclusivity.

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please open issues or submit pull requests to help improve functionality or accessibility.

## Contact

For questions or feedback, please reach out via [GitHub Issues](https://github.com/San9130/AI/issues).
