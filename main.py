import os
import threading
import time
import feedparser
import requests
from flask import Flask
from anthropic import Anthropic

# --- 1. GLOBAL APP DEFINITION ---
app = Flask(__name__)

# Config from Railway Variables
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    """Sends the briefing and logs the exact response from Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": message, 
        "parse_mode": "HTML"
    }
    
    try:
        res = requests.post(url, json=payload)
        data = res.json()
        if res.status_code == 200:
            print("✅ TELEGRAM CONFIRMED: Message delivered to chat.")
            return True
        else:
            print(f"❌ TELEGRAM REJECTED: {data.get('description', 'Unknown Error')}")
            return False
    except Exception as e:
        print(f"❌ CONNECTION ERROR: {str(e)}")
        return False

# --- 2. THE COMMAND ROUTES ---
@app.route('/')
def home():
    return "<h1>Intelligence Feed: ACTIVE</h1><p>Status: Ready for deployment.</p>", 200

@app.route('/run')
def manual_run():
    """Manual trigger: Visit your-url.railway.app/run to force a briefing."""
    print("🚀 MANUAL TRIGGER: Starting curator process...")
    # Using a thread so the webpage loads immediately while Claude thinks
    threading.Thread(target=run_curator).start()
    return "<h1>Briefing Triggered</h1><p>Check Telegram in 10-15 seconds.</p>", 200

# --- 3. THE CORE CURATOR LOGIC ---
def run_curator():
    try:
        print("🔍 STEP 1: Scanning UK & Tech feeds...")
        feeds = ["https://techcrunch.com/feed/", "https://www.cityam.com/feed/"]
        all_news = ""
        
        for url in feeds:
            f = feedparser.parse(url)
            # Take the top 3 articles from each feed
            for entry in f.entries[:3]:
                all_news += f"Source: {url.split('.')[1].upper()}\nTitle: {entry.title}\nLink: {entry.link}\n\n"

        if not all_news:
            print("⚠️ No news found in feeds.")
            return

        print("🧠 STEP 2: Claude 4.6 generating Strategic Briefing...")
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # Using your confirmed Sonnet 4.6 model
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            messages=[{
                "role": "user", 
                "content": f"You are a Strategic Advisor for a UK Director. Summarise these headlines into 3 actionable boardroom insights. Use bold headers and HTML line breaks (<br>) for formatting. Keep it high-level and professional:\n\n{all_news}"
            }]
        )
        
        # Format the final Telegram payload
        briefing = f"<b>🏛 BOARDROOM INTELLIGENCE</b><br><br>{msg.content[0].text}"

        print("📨 STEP 3: Dispatching to Telegram...")
        send_telegram(briefing)

    except Exception as e:
        error_msg = f"❌ CURATOR ERROR: {str(e)}"
        print(error_msg)
        send_telegram(error_msg)

# --- 4. THE AUTOMATED SCHEDULER ---
def scheduler():
    """Automated daily run (starts 15s after boot)."""
    time.sleep(15) 
    print("⏳ Scheduler active: Bot will run automatically every 24 hours.")
    while True:
        try:
            run_curator()
            time.sleep(86400) # Wait 24 hours
        except Exception as e:
            print(f"Scheduler loop error: {e}")
            time.sleep(600)

# Start background scheduler
threading.Thread(target=scheduler, daemon=True).start()

if __name__ == "__main__":
    # Handle port for Railway environment
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
