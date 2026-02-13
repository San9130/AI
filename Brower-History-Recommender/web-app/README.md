# Reading Recommendations Web App

This is a simple local web UI for the Chrome history recommendation engine.

## Setup

1) Create a virtual environment (optional but recommended).
2) Install dependencies.
3) Run the server.

```bash
python3 -m venv .venv
source .venv/bin/activate
 pip install -r requirements.txt
 export OPENAI_API_KEY="your-key-here"
 export SEMANTIC_SCHOLAR_API_KEY="optional-key-here"
 export CROSSREF_MAILTO="you@example.com"
 python app.py
```

Open http://127.0.0.1:8000 in your browser.

## Notes
- This app reads the Chrome History database from your local machine only.
- Provide a full path or a profile name. If both are empty, it uses the Default profile.
 - The app uses OpenAI to infer interest topics, then fetches new recommendations from arXiv, Crossref, and Semantic Scholar.
 - `SEMANTIC_SCHOLAR_API_KEY` is optional but increases rate limits for Semantic Scholar.
 - `CROSSREF_MAILTO` is optional and identifies your email to Crossref for polite usage.
