import os
import threading
import time
import feedparser
import requests
from flask import Flask
from anthropic import Anthropic

# --- THIS IS THE LINE GUNICORN IS LOOKING FOR ---
app = Flask(__name__)

# --- THE HEARTBEAT ---
@app.route('/')
def home():
    return "Remi's News Curator is Active", 200

# --- THE BOT LOGIC ---
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
        
        msg = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
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

def scheduler():
    """Background task: Runs once at startup, then every 24 hours."""
    print("⏳ Scheduler initialized. Waiting for stability...")
    time.sleep(30) # Short wait for server to settle
    while True:
        try:
            print("🚀 Executing scheduled daily news scan...")
            run_curator()
            time.sleep(86400) # 24 hours
        except Exception as e:
            print(f"Error in scheduler: {e}")
            time.sleep(600)

# --- START THE BACKGROUND THREAD ---
threading.Thread(target=scheduler, daemon=True).start()

if __name__ == "__main__":
    # This block is only used if you run the script manually
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
