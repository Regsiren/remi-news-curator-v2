import os
import threading
import time
import feedparser
import requests
from flask import Flask
from anthropic import Anthropic

app = Flask(__name__)

# --- CONFIGURATION (Ensure these are in your Railway Variables) ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    """Sends the briefing with a formatted Plain-Text fallback."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    res = requests.post(url, json=payload)
    
    if res.status_code != 200:
        # Fallback: Strip HTML tags and send as plain text
        clean_text = message.replace("<b>", "").replace("</b>", "").replace("<br>", "\n")
        payload["text"] = clean_text
        payload.pop("parse_mode")
        requests.post(url, json=payload)
        print("✅ SUCCESS: Plain-text fallback delivered.")
    else:
        print("✅ SUCCESS: HTML briefing delivered.")

@app.route('/')
def home():
    return "Intelligence Hub: ACTIVE", 200

@app.route('/run')
def manual_run():
    threading.Thread(target=run_curator).start()
    return "<h1>Intelligence Triggered</h1><p>Check Telegram in 15 seconds.</p>", 200

def run_curator():
    try:
        print("🔍 STEP 1: Scanning Strategic UK Sources...")
        feeds = {
            "Finance": "https://www.bankofengland.co.uk/rss/news",
            "Property": "https://propertyindustryeye.com/feed/",
            "Business": "https://www.cityam.com/feed/"
        }
        
        all_news = ""
        for cat, url in feeds.items():
            f = feedparser.parse(url)
            for entry in f.entries[:2]:
                all_news += f"[{cat}] {entry.title}\nLink: {entry.link}\n\n"

        print("🧠 STEP 2: Claude 4.6 synthesizing Decision Intelligence...")
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # PROMPT UPGRADE: Focused on 2026 Blindspots and Table generation
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            messages=[{
                "role": "user", 
                "content": f"""Summarise these headlines for a UK Director. 
                Structure for maximum 'stickiness' and authority:

                1. 🏛 THE BOARDROOM BRIEF: One sentence explaining 'Why this matters today'.
                2. 🔍 TOP 3 STRATEGIC DRILLS:
                   - DRILL A: THE REFINANCING GATE. Focus on Private Credit vs Bank Debt (Base rate: 3.75%).
                   - DRILL B: GOVERNANCE SHOCKS. Focus on ACSP registration and Companies House 'Personal Codes'.
                   - DRILL C: THE RENTER'S RIGHTS PIVOT. Impact of Section 21 abolition on yield.
                3. 📊 DECISION MATRIX:
                   Create a text-based table with headers: | SECTOR | RISK LEVEL | ACTION |
                
                Keep HTML limited to <b> and <br>. No other tags.
                NEWS FEED:
                {all_news}"""
            }]
        )
        
        briefing = f"<b>🏛 BOARDROOM INTELLIGENCE</b><br><br>{msg.content[0].text}"
        send_telegram(briefing)

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def scheduler():
    """Daily Pulse: Runs every 24 hours."""
    time.sleep(15)
    while True:
        run_curator()
        time.sleep(86400)

threading.Thread(target=scheduler, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
