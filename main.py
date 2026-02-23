import os
import threading
import time
import feedparser
import requests
from flask import Flask
from anthropic import Anthropic

app = Flask(__name__)

@app.route('/')
def home():
    return "Remi's News Fleet: ACTIVE AND DIAGNOSING", 200

def run_curator():
    try:
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # --- STRATEGIC DIAGNOSTIC: LIST AVAILABLE MODELS ---
        print("🔍 DIAGNOSTIC: Fetching available models for your API key...")
        try:
            models = client.models.list()
            model_list = [m.id for m in models.data]
            print(f"✅ Your Account Can See: {model_list}")
        except Exception as e:
            print(f"⚠️ Could not list models: {e}")

        # 1. Fetch News
        print("🔍 STEP 1: Scanning UK & Tech feeds...")
        feeds = ["https://techcrunch.com/feed/", "https://www.cityam.com/feed/"]
        all_news = ""
        for url in feeds:
            f = feedparser.parse(url)
            for entry in f.entries[:3]:
                all_news += f"Title: {entry.title}\nLink: {entry.link}\n\n"

        # 2. AI Summarization (2026 Model Selection)
        # Using the standard 3.5 Sonnet alias for 2026
        target_model = "claude-3-5-sonnet-latest" 
        print(f"🧠 STEP 2: Asking {target_model} for the Briefing...")
        
        msg = client.messages.create(
            model=target_model,
            max_tokens=1000,
            messages=[{"role": "user", "content": "Draft 3 boardroom insights for a UK Director:\n\n" + all_news}]
        )
        
        formatted_html = f"<h3>Strategic Briefing</h3><p>{msg.content[0].text.replace('\\n', '<br>')}</p>"

        # 3. Post to Beehiiv
        print("📨 STEP 3: Dispatching to Beehiiv...")
        pub_id = os.getenv("BEEHIIV_PUB_ID")
        key = os.getenv("BEEHIIV_API_KEY")
        url = f"https://api.beehiiv.com/v2/publications/{pub_id}/posts"
        
        res = requests.post(url, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json={
            "title": f"Strategic Intel: {time.strftime('%d %b %Y')}",
            "body": formatted_html,
            "status": "draft"
        })
        print(f"✅ SUCCESS: Beehiiv Status {res.status_code}")

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")

def scheduler():
    print("⏳ Waiting for initial server stability (15s)...")
    time.sleep(15)
    while True:
        run_curator()
        time.sleep(86400) # 24 hours

threading.Thread(target=scheduler, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
