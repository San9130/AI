# Simplify

**Simplify** is a lightweight Python tool that uses the OpenAI API to generate simplified explanations of terms, jargon, or concepts in the user's chosen language. The output can be returned as either text or spoken audio.

## Features:

- Multilingual explanations
- Option to receive output as text or audio
- Uses OpenAI API

## Requirements:

- Python 3.0+
- OpenAI Python SDK

## Install dependencies

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
