import os
import threading
import time
import feedparser
import requests
from flask import Flask
from anthropic import Anthropic

# --- 1. GLOBAL APP DEFINITION (Essential for Railway/Gunicorn) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Remi's Boardroom Intelligence Bot: ONLINE", 200

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

        print("🧠 STEP 2: Asking Claude to draft the Boardroom Briefing...")
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        prompt = (
            "You are a Strategic Advisor. Summarise these headlines into 3 key boardroom "
            "insights for a UK-based Director. Focus on opportunities and risks.\n\n"
            f"RAW NEWS:\n{all_news}"
        )
        
        # Using the most stable 2026 model alias
        msg = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Convert text to HTML for Beehiiv
        draft_content = msg.content[0].text.replace('\n', '<br>')
        formatted_html = f"<h3>Strategic Briefing</h3><p>{draft_content}</p>"

        print("📨 STEP 3: Sending draft to Beehiiv...")
        pub_id = os.getenv("BEEHIIV_PUB_ID")
        key = os.getenv("BEEHIIV_API_KEY")
        url = f"https://api.beehiiv.com/v2/publications/{pub_id}/posts"
        
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        
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
            print(f"Response text: {res.text}")

    except Exception as e:
        print(f"❌ CRITICAL ERROR in curator: {str(e)}")

# --- 3. THE BACKGROUND SCHEDULER ---
def scheduler():
    print("⏳ Scheduler initialized. Waiting for stability...")
    time.sleep(30) 
    while True:
        try:
            print("🚀 Executing scheduled daily news scan...")
            run_curator()
            print("✅ Scan complete. Next run in 24 hours.")
            time.sleep(86400) # 24 hours
        except Exception as e:
            print(f"Error in scheduler: {e}")
            time.sleep(600)

# Start the background work as a separate thread
threading.Thread(target=scheduler, daemon=True).start()

if __name__ == "__main__":
    # Use Railway's port or default to 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
