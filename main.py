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

def send_telegram(message, mode="HTML"):
    """Precision delivery: Sends as HTML or Markdown depending on the content."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": mode}
    
    try:
        res = requests.post(url, json=payload)
        # Fallback: If formatting fails, send as plain text so you at least get the data
        if res.status_code != 200:
            payload.pop("parse_mode")
            requests.post(url, json=payload)
    except Exception as e:
        print(f"Connection error: {e}")

@app.route('/')
def home():
    return "<h1>Intelligence Hub</h1><p>Status: Monitoring Strategic UK Feeds...</p>", 200

@app.route('/run')
def manual_run():
    threading.Thread(target=run_curator).start()
    return "<h1>Dual Briefing Dispatched</h1><p>Check Telegram for your Brief and Beehiiv Draft.</p>", 200

def run_curator():
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
        
        prompt = f"""You are Remi's Chief of Staff. Review these headlines:
        {raw_content}

        Produce TWO distinct outputs separated by '---SPLIT---':
        
        PART 1 (The Telegram Brief): 
        A sophisticated 3-sentence summary for mobile. Use <b> and <br> tags correctly for bold and lines. 
        DO NOT include the words 'PART 1' or 'TELEGRAM BRIEF'.

        ---SPLIT---

        PART 2 (The Beehiiv Draft):
        A full newsletter draft in clean Markdown (# for headers, - for bullets). 
        Focus on: Private Credit trends, ACSP compliance for Directors, and Renters' Rights (May 2026).
        DO NOT include the words 'PART 2' or 'BEEHIIV DRAFT'.
        """

        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        full_response = msg.content[0].text
        parts = full_response.split('---SPLIT---')
        
        # --- PART 1: MOBILE BRIEF (HTML) ---
        if len(parts) > 0:
            brief = "🏛 <b>BOARDROOM INTELLIGENCE</b><br><br>" + parts[0].strip()
            send_telegram(brief, mode="HTML")
            
        # --- PART 2: BEEHIIV DRAFT (MARKDOWN) ---
        if len(parts) > 1:
            time.sleep(2) # Prevent message collision
            draft = "✍️ <b>BEEHIIV DRAFT (Copy & Paste)</b>\n\n" + parts[1].strip()
            send_telegram(draft, mode="Markdown")

        print("✅ SUCCESS: Dual dispatch complete.")

    except Exception as e:
        send_telegram(f"⚠️ Curator Error: {str(e)}", mode=None)

# (Scheduler remains 24h)
def scheduler():
    time.sleep(15) 
    while True:
        run_curator()
        time.sleep(86400)

threading.Thread(target=scheduler, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
