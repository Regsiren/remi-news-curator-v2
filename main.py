import os
import threading
import time
import feedparser
import requests
from flask import Flask
from anthropic import Anthropic

app = Flask(__name__)

# --- THE HEARTBEAT ---
@app.route('/')
def home():
    return "Remi's News Curator is Active", 200

# --- THE BOT LOGIC ---
def run_curator():
    # 1. Fetch News
    feeds = ["https://techcrunch.com/feed/", "https://www.cityam.com/feed/"]
    all_news = ""
    for url in feeds:
        f = feedparser.parse(url)
        for entry in f.entries[:2]:
            all_news += f"Title: {entry.title}\nLink: {entry.link}\n\n"

    # 2. AI Summarization (Claude 4.5)
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    prompt = f"Summarize these UK and tech headlines for a Board of Directors. Focus on strategic moves:\n\n{all_news}"
    
    msg = client.messages.create(
        model="claude-3-5-sonnet-20241022", # Reliable stable model
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    content_html = f"<p>{msg.content[0].text.replace('\\n', '<br>')}</p>"

    # 3. Post to Beehiiv
    pub_id = os.getenv("BEEHIIV_PUB_ID")
    key = os.getenv("BEEHIIV_API_KEY")
    url = f"https://api.beehiiv.com/v2/publications/{pub_id}/posts"
    
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "title": "Strategic Briefing: " + time.strftime("%d %b %Y"),
        "body": content_html,
        "status": "draft"
    }
    
    res = requests.post(url, headers=headers, json=payload)
    print(f"Beehiiv Response: {res.status_code}")

def scheduler():
    """Runs the scan immediately, then every 24 hours."""
    while True:
        try:
            print("🚀 Starting daily news scan...")
            run_curator()
            time.sleep(86400) # Wait 24 hours
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(300)

if __name__ == "__main__":
    threading.Thread(target=scheduler, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
