import os
import threading
import time
import feedparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask
from anthropic import Anthropic

app = Flask(__name__)

@app.route('/')
def home():
    return "Remi's News Fleet: EMAIL BRIDGE ACTIVE", 200

def send_email(subject, body):
    sender = os.getenv("SENDER_EMAIL")
    password = os.getenv("SENDER_PASSWORD") # Use an 'App Password', not your main one
    recipient = os.getenv("RECIPIENT_EMAIL")
    
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        # Standard Gmail/Outlook SMTP settings
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        print("✅ SUCCESS: Briefing sent to your inbox.")
    except Exception as e:
        print(f"❌ EMAIL ERROR: {e}")

def run_curator():
    try:
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        print("🔍 STEP 1: Scanning feeds...")
        feeds = ["https://techcrunch.com/feed/", "https://www.cityam.com/feed/"]
        all_news = ""
        for url in feeds:
            f = feedparser.parse(url)
            for entry in f.entries[:3]:
                all_news += f"Title: {entry.title}\nLink: {entry.link}\n\n"

        print("🧠 STEP 2: Asking Claude 4.6 for Briefing...")
        msg = client.messages.create(
            model="claude-sonnet-4-6", 
            max_tokens=1000,
            messages=[{"role": "user", "content": "Draft 3 boardroom insights for a UK Director:\n\n" + all_news}]
        )
        
        briefing_html = f"<h2>Strategic Intel: {time.strftime('%d %b')}</h2><p>{msg.content[0].text.replace('\\n', '<br>')}</p>"

        print("📨 STEP 3: Sending to Inbox via Email Bridge...")
        send_email(f"Strategic Briefing: {time.strftime('%d %b %Y')}", briefing_html)

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")

def scheduler():
    print("⏳ Waiting for initial stability (15s)...")
    time.sleep(15)
    while True:
        run_curator()
        time.sleep(86400)

threading.Thread(target=scheduler, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
