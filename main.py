import os
import threading
import time
import feedparser
import requests
from flask import Flask
from anthropic import Anthropic

app = Flask(__name__)

# --- 1. CONFIGURATION ---
# Ensure these are set in your Railway 'Variables' tab.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    """Sends the briefing with a sophisticated fallback for Telegram's strict HTML rules."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    
    try:
        res = requests.post(url, json=payload)
        if res.status_code != 200:
            # If HTML fails (common with complex tables), strip tags and send plain text
            print(f"⚠️ Telegram HTML rejection. Reason: {res.text}")
            clean_text = message.replace("<b>", "").replace("</b>", "").replace("<br>", "\n")
            payload["text"] = f"--- System Note: Formatting Refined ---\n\n{clean_text}"
            payload.pop("parse_mode")
            requests.post(url, json=payload)
        else:
            print("✅ SUCCESS: Intelligence briefing delivered.")
    except Exception as e:
        print(f"❌ CONNECTION ERROR: {str(e)}")

@app.route('/')
def home():
    return "<h1>Intelligence Hub</h1><p>Status: Monitoring Strategic UK Feeds...</p>", 200

@app.route('/run')
def manual_run():
    """Trigger a fresh briefing immediately via browser."""
    threading.Thread(target=run_curator).start()
    return "<h1>Intelligence Dispatched</h1><p>Your boardroom update is being synthesized and sent to Telegram.</p>", 200

def run_curator():
    """The core intelligence engine."""
    try:
        print("🔍 STEP 1: Scanning Strategic Sources...")
        feeds = {
            "Macro": "https://www.bankofengland.co.uk/rss/news",
            "Property": "https://propertyindustryeye.com/feed/",
            "London/City": "https://www.cityam.com/feed/"
        }
        
        raw_content = ""
        for category, url in feeds.items():
            f = feedparser.parse(url)
            for entry in f.entries[:2]: # Top 2 per source
                raw_content += f"[{category}] {entry.title}\nSource: {entry.link}\n\n"

        print("🧠 STEP 2: Claude 4.6 synthesizing insights...")
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # PROMPT: Enforcing the 'Chief of Staff' tone and 2026 blindspots
        prompt = f"""You are Remi's Chief of Staff. Review these headlines and provide a private, astute briefing.
        
        TONE: Sophisticated, British, and authoritative. Avoid cold, metallic corporate-speak. Use narrative flow.
        
        STRUCTURE:
        1. 🏛 THE MORNING TAKE: A warm but sharp overview of the current climate.
        2. 🧭 STRATEGIC DRILLS: 
           Connect the news to these 2026 priorities:
           - The shift from Bank debt to Private Credit (The €500B refinancing wall).
           - Companies House ACSP compliance (The personal liability for Directors).
           - May 2026 Renters' Rights Act (The reality of yield protection).
        3. 📊 THE DECISION MATRIX: A simple, clean text table: | Sector | Sentiment | Recommended Stance |

        Use ONLY <b> and <br> tags for formatting.
        NEWS DATA:
        {raw_content}"""

        msg = client.messages.create(
            model="claude-3-5-sonnet-20241022", # Updated to current Sonnet for reliability
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        briefing = f"<b>🏛 BOARDROOM INTELLIGENCE</b><br><br>{msg.content[0].text}"
        send_telegram(briefing)

    except Exception as e:
        error_msg = f"❌ CURATOR ERROR: {str(e)}"
        print(error_msg)
        send_telegram(error_msg)

def scheduler():
    """The 24-hour pulse."""
    time.sleep(15) 
    while True:
        run_curator()
        time.sleep(86400) # Wait 24 hours

# Start the background scheduler
threading.Thread(target=scheduler, daemon=True).start()

if __name__ == "__main__":
    # Handle the port for Railway
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
