# AI Message Clarity Assistant

Paste a message → get a clarity score, flagged confusing parts, a rewritten
clearer version, and an explanation of what changed.

Powered by **Groq** (Llama 3.3 70B) for fast inference.

## Run locally
```bash
pip install -r requirements.txt
export GROQ_API_KEY=gsk_...
streamlit run app.py
```

## Deploy on Streamlit Community Cloud
1. Push this folder to a GitHub repo.
2. Go to https://share.streamlit.io → "New app" → point it at `app.py`.
3. In the app's **Settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "gsk_..."
   ```
4. Deploy. If no secret is set, the app falls back to an in-sidebar API key
   input for local/demo use.

## Files
- `app.py` — Streamlit UI
- `workflow.py` — clarity-analysis workflow (calls Groq, parses structured JSON)
- `requirements.txt` — dependencies

## Notes
- Model used: `llama-3.3-70b-versatile`. Swap `MODEL` in `workflow.py` for
  `llama-3.1-8b-instant` if you want an even faster/cheaper option for demos.
- Get a free Groq API key at https://console.groq.com/keys
