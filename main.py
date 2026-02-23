def run_curator():
    try:
        # 1. Fetch News
        print("🔍 STEP 1: Scanning UK & Tech feeds...")
        feeds = ["https://techcrunch.com/feed/", "https://www.cityam.com/feed/"]
        all_news = ""
        for url in feeds:
            f = feedparser.parse(url)
            for entry in f.entries[:3]:
                all_news += f"Source: {url.split('.')[1].upper()}\nTitle: {entry.title}\nLink: {entry.link}\n\n"

        # 2. AI Summarization (Claude 4.5)
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
        
        # Format the content into HTML for Beehiiv
        draft_content = msg.content[0].text.replace('\n', '<br>')
        formatted_html = f"<h3>Strategic Briefing</h3><p>{draft_content}</p>"

        # 3. Post to Beehiiv
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
            "body": formatted_html, # THE FIX: Changed from body_content to body
            "status": "draft"
        }
        
        res = requests.post(url, headers=headers, json=payload)
        
        if res.status_code in [201, 200]:
            print(f"✅ SUCCESS: Draft created in Beehiiv (Code: {res.status_code})")
        else:
            print(f"❌ ERROR: Beehiiv rejected the post. Code: {res.status_code}")
            print(f"Response text: {res.text}")

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
