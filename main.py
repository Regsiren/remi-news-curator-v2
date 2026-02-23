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
    """Sends briefings with a sophisticated fallback for complex Markdown/HTML."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    # We send as HTML for Telegram formatting, but fallback to plain text for the Beehiiv Markdown
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    
    try:
        res = requests.post(url, json=payload)
        if res.status_code != 200:
            # Fallback for the long Beehiiv Markdown draft
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
    return "<h1>Dual Briefing Dispatched</h1><p>Telegram summary and Beehiiv draft are being synthesized.</p>", 200

def run_curator():
    """The dual-output engine with split-message delivery."""
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

        print("🧠 STEP 2: Claude 4.6 generating Dual Briefings...")
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # PROMPT: Asking for two separate blocks we can split easily
        prompt = f"""You are Remi's Chief of Staff. Review these headlines:
        {raw_content}

        Produce TWO distinct outputs separated by the word 'SPLIT_HERE':
        
        OUTPUT 1 (TELEGRAM BRIEF): 
        A sophisticated 3-sentence summary for mobile. Use <b> and <br> tags.

        SPLIT_HERE

        OUTPUT 2 (BEEHIIV DRAFT):
        A full newsletter draft in clean Markdown for copy-pasting. 
        Focus on: Private Credit trends, ACSP compliance for Directors, and Renters' Rights (May 2026).
        """

        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # --- THE FIX: SPLIT AND SEND SEPARATELY ---
        full_response = msg.content[0].text
        parts = full_response.split('SPLIT_HERE')
        
        for part in parts:
            if part.strip():
                send_telegram(part.strip())
                time.sleep(1) # Small pause to ensure correct order

        print("✅ SUCCESS: Both parts delivered separately.")

    except Exception as e:
        send_telegram(f"⚠️ Error: {str(e)}")
        
        raw_content = ""
        for cat, url in feeds.items():
            f = feedparser.parse(url)
            for entry in f.entries[:2]:
                raw_content += f"[{cat}] {entry.title}\n"

        print("🧠 STEP 2: Claude 4.6 generating Dual Briefings...")
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        
        prompt = f"""You are Remi's Chief of Staff. Review these headlines:
        {raw_content}

        Produce TWO distinct outputs in ONE message:
        
        OUTPUT 1 (TELEGRAM BRIEF): 
        A sophisticated 3-sentence summary for mobile. Use <b> and <br> tags only.

        OUTPUT 2 (BEEHIIV DRAFT):
        A full newsletter draft. Use H1 for titles (#), H2 for sections (##), and bullet points (-) for insights. 
        Focus on: Private Credit trends, ACSP compliance for Directors, and Renters' Rights (May 2026).
        Format this as clean Markdown so I can copy-paste it directly into a Beehiiv editor.
        """

        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Delivering the complete package
        send_telegram(msg.content[0].text)
        print("✅ SUCCESS: Dual Briefings delivered.")

    except Exception as e:
        send_telegram(f"⚠️ Error: {str(e)}")

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
