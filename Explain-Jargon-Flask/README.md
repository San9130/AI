# Explain Jargon with Flask

## Overview

**Explain Jargon** is an interactive web application built with [Flask](https://flask.palletsprojects.com/) that leverages the power of OpenAI to translate complex jargon terms into layman-friendly explanations.  
The application now features dynamic model selection, intelligently choosing between GPT-5 nano, mini, or main models based on the complexity of the user's input term to optimize both response time and cost-effectiveness.

## Features

- **Jargon Translation:** Converts technical or complex terms into simple, understandable language using OpenAI's language models.
- **Dynamic Model Selection:**  
  - The app analyzes the complexity of the entered jargon and automatically selects the most suitable GPT-5 model:
    - **GPT-5 nano:** For simple or common terms (fast and cost-efficient).
    - **GPT-5 mini:** For moderately complex terms.
    - **GPT-5 main:** For highly technical or specialized jargon to ensure thorough explanations.
- **Multiple Output Formats:**
  - **Text:** Displays the explanation in standard text.
  - **Audio:** Reads out the explanation using text-to-speech.
  - **Braille:** Renders the explanation in a Braille-like format for accessibility.
- **Interactive UI:** A friendly and responsive web interface built with Flask.
- **Accessibility Focus:** Supports users with different access needs, including those who are visually impaired.

## How It Works

1. **Enter Jargon:** Users input a jargon term into the web interface.
2. **Choose Format:** Select the desired output format: Text, Audio, or Braille.
3. **Dynamic Model Selection:**  
   - The app evaluates the complexity of the term and chooses the most appropriate GPT-5 model to generate the explanation efficiently.
4. **Get Explanation:** The app queries OpenAI to generate a layman explanation and presents it in the chosen format.

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
- The app will automatically choose the fastest and most cost-effective GPT-5 model for your term.

## Technologies Used

- **Flask** – Web framework for Python.
- **OpenAI API (GPT-5 nano/mini/main)** – For generating explanations, dynamically selected for efficiency.
- **Text-to-Speech Library** – For audio output (e.g., pyttsx3 or gTTS).
- **Braille Rendering** – Pybraille library to display Braille format.
- **Tailwind** - CSS framework used for the web UI.

## Accessibility

This project is designed to make technical language accessible to everyone, including users with visual impairments. The Braille and audio options ensure inclusivity.

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please open issues or submit pull requests to help improve functionality or accessibility.

## Contact

For questions or feedback, please reach out via [GitHub Issues](https://github.com/San9130/AI/issues).
