import os
import threading
import time
import feedparser
import requests
from flask import Flask
from anthropic import Anthropic

app = Flask(__name__)

# --- CONFIGURATION ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    """Delivers the briefing with a sophisticated fallback."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    
    try:
        res = requests.post(url, json=payload)
        if res.status_code != 200:
            # Fallback: Strip HTML tags if Telegram's strict parser rejects them
            clean_text = message.replace("<b>", "").replace("</b>", "").replace("<br>", "\n")
            payload["text"] = f"--- Refined Executive Briefing ---\n\n{clean_text}"
            payload.pop("parse_mode")
            requests.post(url, json=payload)
    except Exception as e:
        print(f"Connection error: {e}")

@app.route('/')
def home():
    return "<h1>Intelligence Hub</h1><p>Status: Monitoring Strategic UK Feeds...</p>", 200

@app.route('/run')
def manual_run():
    """Trigger a fresh briefing immediately."""
    threading.Thread(target=run_curator).start()
    return "<h1>Intelligence Dispatched</h1><p>Your update is being synthesized by the Chief of Staff.</p>", 200

def run_curator():
    """The core intelligence engine."""
    try:
        feeds = {
            "Finance": "https://www.bankofengland.co.uk/rss/news",
            "Property": "https://propertyindustryeye.com/feed/",
            "London Business": "https://www.cityam.com/feed/"
        }
        
        raw_content = ""
        for cat, url in feeds.items():
            f = feedparser.parse(url)
            for entry in f.entries[:2]:
                raw_content += f"[{cat}] {entry.title}\n"

        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # Persona: Chief of Staff | Tone: British, Astute, and Narrative
        prompt = f"""You are Remi's Chief of Staff. Review these headlines for a strategic UK Director.
        
        TONE: Sophisticated, astute, and British. Avoid cold 'metallic' corporate-speak. Use a narrative flow.
        
        STRUCTURE:
        1. ☕ THE MORNING TAKE: A warm but sharp overview of the current landscape.
        2. 🧭 NAVIGATING THE NOISE: 
           Connect news to 2026 priorities:
           - The Private Credit shift as the €500B refinancing wall looms.
           - Personal liability for Directors under new ACSP rules.
           - Impact of the May 2026 Renters' Rights Act on yield protection.
        3. 📊 THE PERSPECTIVE MATRIX: A clean summary: | Sector | Sentiment | Recommended Stance |

        Use ONLY <b> and <br> tags.
        NEWS DATA: {raw_content}"""

        msg = client.messages.create(
            model="claude-sonnet-4-6", # UPDATED: The active Feb 2026 model ID
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        briefing = f"<b>🏛 BOARDROOM INTELLIGENCE</b><br><br>{msg.content[0].text}"
        send_telegram(briefing)

    except Exception as e:
        # Send error to Telegram for immediate visibility
        send_telegram(f"⚠️ Chief of Staff Note: Intelligence brief paused. Error: {str(e)}")

def scheduler():
    """Daily pulse: runs every 24 hours."""
    time.sleep(15) 
    while True:
        run_curator()
        time.sleep(86400)

threading.Thread(target=scheduler, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
