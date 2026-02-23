# 2. AI Summarization (Claude)
        print("🧠 STEP 2: Asking Claude to draft the Boardroom Briefing...")
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Using the standard 'latest' alias for maximum compatibility
        msg = client.messages.create(
            model="claude-3-5-sonnet-latest", 
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
