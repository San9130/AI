# Simplify

**Simplify** is a lightweight Python tool that uses the OpenAI API to generate simplified explanations of terms, jargon, or concepts in the user's chosen language. The output can be returned as either text or spoken audio.

## Features:

- Multilingual explanations
- Option to receive output as text or audio
- Uses OpenAI API

## Requirements:

- Python 3.7+
- OpenAI Python SDK

## Install dependencies:

- Download latest version of Python from here: https://www.python.org/downloads/
- Check for installed Python version:

	Linux/MacOS:
	bash$ python --version (or python3 --version)
	
	Windows:
	$ python -version

- Install latest OpenAI version from CLI:

	pip install openai
## Environment setup:

1. Create an OpenAI API key by going to this link: https://platform.openai.com/api-keys. Login or create an account as required, then click on "Create a new secret key". Set an optional name, project, and desired permissions as needed, then click "Create secret key". Be sure to save this key temporarily to the side.

2. Store your API key to your local environment variable.
	
	On Linux/MacOS CLI:
	
	export OPENAI_API_KEY=<Your API Key>
	source ~/.bashrc #or source ~/.zshrc
	
	On Windows CLI:
	
	set OPENAI_API_KEY=<Your API Key>
	Add OPENAI_API_KEY to "User Variables" in "Environment Variables" from your settings
