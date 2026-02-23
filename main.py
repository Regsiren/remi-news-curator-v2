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
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") # Must be the long API Token string
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    """Sends the briefing with a plain-text fallback for safety."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # Try sending with HTML first
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    res = requests.post(url, json=payload)
    
    # Fallback: If Telegram rejects the HTML, send as plain text
    if res.status_code != 200:
        print(f"⚠️ HTML failed, stripping tags. Reason: {res.text}")
        clean_text = message.replace("<b>", "").replace("</b>", "").replace("<br>", "\n")
        payload["text"] = clean_text
        payload.pop("parse_mode") # Remove HTML mode
        requests.post(url, json=payload)
        print("✅ SUCCESS: Plain-text briefing delivered.")
    else:
        print("✅ SUCCESS: HTML briefing delivered.")

@app.route('/')
def home():
    return "Intelligence Feed: ACTIVE", 200

@app.route('/run')
def manual_run():
    threading.Thread(target=run_curator).start()
    return "<h1>Briefing Triggered</h1><p>Check Telegram in 10-15 seconds.</p>", 200

def run_curator():
    try:
        print("🔍 STEP 1: Scanning UK feeds...")
        feeds = ["https://techcrunch.com/feed/", "https://www.cityam.com/feed/"]
        all_news = ""
        for url in feeds:
            f = feedparser.parse(url)
            for entry in f.entries[:2]:
                all_news += f"Title: {entry.title}\nLink: {entry.link}\n\n"

        print("🧠 STEP 2: Claude 4.6 generating Briefing...")
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # Explicit instruction to only use Telegram-supported tags
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            messages=[{
                "role": "user", 
                "content": f"Summarise these headlines for a UK Director into 3 insights. Use ONLY <b> tags for headers and <br> for new lines. No other tags allowed:\n\n{all_news}"
            }]
        )
        
        briefing = f"<b>🏛 BOARDROOM INTELLIGENCE</b><br><br>{msg.content[0].text}"
        send_telegram(briefing)

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def scheduler():
    time.sleep(15)
    while True:
        run_curator()
        time.sleep(86400)

threading.Thread(target=scheduler, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
