import os
import threading
import time
import feedparser
import requests
from flask import Flask
from anthropic import Anthropic

# --- 1. GLOBAL APP DEFINITION ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Remi's News Fleet: ACTIVE", 200

# --- 2. THE CURATOR LOGIC ---
def run_curator():
    try:
        print("🔍 STEP 1: Scanning UK & Tech feeds...")
        feeds = ["https://techcrunch.com/feed/", "https://www.cityam.com/feed/"]
        all_news = ""
        for url in feeds:
            f = feedparser.parse(url)
            for entry in f.entries[:3]:
                all_news += f"Source: {url.split('.')[1].upper()}\nTitle: {entry.title}\nLink: {entry.link}\n\n"

        print("🧠 STEP 2: Asking Claude (Haiku) to draft the Briefing...")
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Using HAIKU: The most compatible and accessible model for all API tiers
        msg = client.messages.create(
            model="claude-3-haiku-20240307", 
            max_tokens=1000,
            messages=[{"role": "user", "content": "You are a Strategic Advisor. Summarise these headlines for a UK Director:\n\n" + all_news}]
        )
        
        formatted_html = f"<h3>Strategic Briefing</h3><p>{msg.content[0].text.replace('\\n', '<br>')}</p>"

        print("📨 STEP 3: Sending draft to Beehiiv...")
        pub_id = os.getenv("BEEHIIV_PUB_ID")
        key = os.getenv("BEEHIIV_API_KEY")
        url = f"https://api.beehiiv.com/v2/publications/{pub_id}/posts"
        
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "title": f"Boardroom Intelligence: {time.strftime('%d %b %Y')}",
            "body": formatted_html, 
            "status": "draft"
        }
        
        res = requests.post(url, headers=headers, json=payload)
        
        if res.status_code in [201, 200]:
            print(f"✅ SUCCESS: Draft created in Beehiiv (Code: {res.status_code})")
        else:
            print(f"❌ ERROR: Beehiiv rejected the post. Code: {res.status_code}")
            print(f"Reason: {res.text}")

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")

# --- 3. THE BACKGROUND SCHEDULER ---
def scheduler():
    print("⏳ Waiting for initial server stability (15s)...")
    time.sleep(15) 
    while True:
        try:
            run_curator()
            time.sleep(86400) # 24 hours
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(600)

threading.Thread(target=scheduler, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
