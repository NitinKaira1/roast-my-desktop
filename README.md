# ⚖️ Desktop Court AI
 
**🔗 Live: [roast-my-desktop.onrender.com](https://roast-my-desktop.onrender.com/)**
 
Upload a screenshot of your desktop. A panel of twelve AI "judges" — a savage
roaster, an FBI profiler, a strict Indian mom, a disappointed teacher, and more —
will pass judgment on your life choices.
 
Built with **Flask** + **Gemini 2.5 Flash**. No Gradio — plain HTML/CSS/JS frontend,
so it runs anywhere a Python web app runs.
 
> Hosted on Render's free tier, so it sleeps after inactivity — the first
> request after a while may take ~30s to wake up. Be patient with it, it's
> deliberating.
 
## Features
 
- **Single Judge** — pick one of 12 personas
- **Random Judge** — let fate decide
- **Full Tribunal** — every judge weighs in at once
- Drag-and-drop or paste-to-upload
- Clean, dependency-free frontend (no build step, no npm)
## Project structure
 
```
desktop-court-ai/
├── app.py              # Flask app (routes + request handling)
├── judges.py           # Gemini API wrapper
├── prompts.py          # All judge personas live here
├── requirements.txt
├── .env.example
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── script.js
```
 
## Setup
 
Want to just try it instead of running it locally? Use the
[live demo](https://roast-my-desktop.onrender.com/) — no setup needed.
 
To run it yourself:
 
**1. Clone and enter the project**
 
```bash
git clone https://github.com/YOUR_USERNAME/desktop-court-ai.git
cd desktop-court-ai
```
 
**2. Create a virtual environment**
 
```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```
 
**3. Install dependencies**
 
```bash
pip install -r requirements.txt
```
 
**4. Add your API key**
 
```bash
cp .env.example .env
```
 
Edit `.env` and paste your key:
 
```
GEMINI_API_KEY=your_actual_key_here
```
 
Get a free key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
 
**5. Run it**
 
```bash
python app.py
```
 
Open **http://localhost:5000**
 
## Adding a new judge
 
Open `prompts.py` and add an entry to the `JUDGES` dict:
 
```python
JUDGES = {
    # ...existing judges...
    "🦊 Detective": """
You are a sharp-eyed detective.
 
Analyze the desktop screenshot.
 
Output:
- Case Summary
- Key Clues
- Suspect Profile
- Closing Statement
 
Funny and noir.
""",
}
```
 
It will automatically show up in the dropdown and in "Full Tribunal" mode
(if you also add a matching section to `ALL_JUDGES_SYSTEM`).
 
## Deploying
 
### Render / Railway / Fly.io (easiest)
 
1. Push this repo to GitHub.
2. Create a new web service pointing at the repo.
3. Set the **start command** to:
```
   gunicorn app:app
```
4. Add the `GEMINI_API_KEY` environment variable in the dashboard.
### Docker
 
```bash
docker build -t desktop-court-ai .
docker run -p 5000:5000 --env-file .env desktop-court-ai
```
 
## Notes
 
- Max upload size is 10MB (configurable in `app.py` via `MAX_CONTENT_LENGTH`).
- Accepted formats: PNG, JPG, JPEG, WEBP.
- Uploaded images are written to a temp file for the API call and deleted
  immediately after — nothing is stored on disk long-term.
## License
 
MIT — do whatever you want with it.
 
