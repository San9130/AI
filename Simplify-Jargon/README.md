# Simplify-Jargon

**Simplify-Jargon** is a lightweight Python tool that uses the OpenAI API to generate simplified explanations of terms, jargon, or concepts in the user's chosen language. The output can be returned as either text or spoken audio.

## Features:

- Multilingual explanations
- Option to receive output as text or audio
- Uses OpenAI API

## Requirements:

- Python 3.0+
- OpenAI Python SDK

## Install dependencies:

**Run the following commands in your system's command line interface (CLI):**

- Download the latest version of Python from here: https://www.python.org/downloads/

- Check your installed Python version:

    **On Linux/MacOS (Terminal):**
    ```bash
    python --version
    # or
    python3 --version
    ```

    **On Windows (Command Prompt or PowerShell):**
    ```powershell
    python --version
    ```

- Install the latest OpenAI SDK (run in your CLI):

    ```bash
    pip install openai
    ```
## Environment setup:

1. Create an OpenAI API key by going to this link: https://platform.openai.com/api-keys. Login or create an account as required, then click on "Create a new secret key". Set an optional name, project, and desired permissions as needed, then click "Create secret key". Be sure to save this key temporarily to the side.

2. Store your API key to your local environment variable.
	
	On Linux/MacOS CLI:
	```bash
	export OPENAI_API_KEY=<Your API Key>
 	```
 	```bash
	source ~/.bashrc #or source ~/.zshrc
  	```
	
	On Windows CLI:
	```powershell
	set OPENAI_API_KEY=<Your API Key>
 	```
	Add OPENAI_API_KEY to "User Variables" in "Environment Variables" from your settings
## Usage:

Execute the script with the following command:
```bash
python simplify_jargon.py #or python3 simplify_jargon.py
```

Enter the term or jargon you want simplified (or "quit" to exit):
```bash
Enter a term or phrase to explain in simpler terms (or type 'quit' to exit):
> LLM
```

Enter the desired language to get the explanation:
```bash
Enter the language for the explanation:
> Spanish
```

Choose either text or audio format for the explanation:
```bash
Choose output format - Text (T) or Audio (A):
> T
```

Example output generated with these inputs:
```bash
LLM, en el contexto de la inteligencia artificial, se refiere a un "Modelo de Lenguaje Extenso" que se utiliza para procesar y generar texto a nivel avanzado.
```
NOTE: This tool saves audio output to an MP3 file that is generated in the same directory as the Python script.



