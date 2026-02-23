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
    """Sends the briefing to your private Telegram channel."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, json=payload)

@app.route('/')
def home():
    return "Intelligence Feed: ACTIVE", 200

@app.route('/run')
def manual_run():
    """Trigger a briefing immediately via your-url.railway.app/run"""
    threading.Thread(target=run_curator).start()
    return "<h1>Briefing Triggered</h1><p>Check Telegram in 10 seconds.</p>", 200

def run_curator():
    try:
        print("🔍 STEP 1: Scanning UK & Tech feeds...")
        feeds = ["https://techcrunch.com/feed/", "https://www.cityam.com/feed/"]
        all_news = ""
        for url in feeds:
            f = feedparser.parse(url)
            for entry in f.entries[:3]:
                all_news += f"Source: {url.split('.')[1].upper()}\nTitle: {entry.title}\nLink: {entry.link}\n\n"

        print("🧠 STEP 2: Claude 4.6 generating Strategic Briefing...")
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # Using the whitelisted Sonnet 4.6 model
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            messages=[{
                "role": "user", 
                "content": f"You are a Strategic Advisor for a UK Director. Summarise these headlines into 3 actionable boardroom insights. Use bold headers and HTML line breaks (<br>):\n\n{all_news}"
            }]
        )
        
        briefing = f"<b>🏛 BOARDROOM INTELLIGENCE</b><br><br>{msg.content[0].text}"

        print("📨 STEP 3: Dispatching to Telegram...")
        send_telegram(briefing)
        print("✅ SUCCESS: Briefing delivered.")

    except Exception as e:
        error_msg = f"❌ CURATOR ERROR: {str(e)}"
        print(error_msg)
        send_telegram(error_msg)

def scheduler():
    """Automated daily run."""
    time.sleep(15) 
    while True:
        run_curator()
        time.sleep(86400) # 24 hours

threading.Thread(target=scheduler, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
