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
    """Delivers the briefing with an elegant fallback for readability."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    
    try:
        res = requests.post(url, json=payload)
        if res.status_code != 200:
            # Fallback if HTML is too complex
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
    return "<h1>Intelligence Dispatched</h1><p>The Chief of Staff is synthesizing your update.</p>", 200

def run_curator():
    """The core intelligence engine."""
    try:
        print("🔍 STEP 1: Scanning Strategic Sources...")
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

        print("🧠 STEP 2: Synthesizing with Claude 4.6...")
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # PERSONA: Chief of Staff | TONE: Astute, British, Peer-to-Peer
        prompt = f"""You are Remi's Chief of Staff. Review these headlines for a strategic UK Director.
        
        TONE: Sophisticated, astute, and British. Avoid cold, 'metallic' corporate-speak. Use narrative flow.
        
        STRUCTURE:
        1. ☕ THE MORNING TAKE: A warm but sharp overview of the current landscape.
        2. 🧭 NAVIGATING THE NOISE: 
           Connect news to 2026 boardroom priorities:
           - The €500B refinancing wall and the pivot to Private Credit.
           - Director liability under new Companies House ACSP compliance.
           - Yield protection strategies for the May 2026 Renters' Rights Act.
        3. 📊 THE PERSPECTIVE MATRIX: A clean text table: | Sector | Sentiment | Recommended Stance |

        Use ONLY <b> and <br> tags.
        NEWS DATA: {raw_content}"""

        msg = client.messages.create(
            model="claude-sonnet-4-6", # UPDATED FEB 2026 MODEL ID
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        briefing = f"<b>🏛 BOARDROOM INTELLIGENCE</b><br><br>{msg.content[0].text}"
        send_telegram(briefing)
        print("✅ SUCCESS: Intelligence delivered.")

    except Exception as e:
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
