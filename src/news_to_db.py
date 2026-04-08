import requests
from supabase import create_client, Client
import os
from datetime import datetime 
import time

# Environment variables
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Use SERVICE_ROLE key for GitHub Actions

print(f"🔑 NEWS_API_KEY: {'✅ Found' if NEWS_API_KEY else '❌ Missing'}")
print(f"🔑 SUPABASE_URL: {'✅ Found' if SUPABASE_URL else '❌ Missing'}")
print(f"🔑 SUPABASE_KEY: {'✅ Found' if SUPABASE_KEY else '❌ Missing'}")

if not all([NEWS_API_KEY, SUPABASE_URL, SUPABASE_KEY]):
    raise ValueError("❌ Missing required environment variables!")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# News API call
url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"
print(f"🌐 Fetching news from: {url}")

response = requests.get(url)
data = response.json()

if response.status_code != 200:
    print(f"❌ News API Error: {data}")
    exit(1)

articles = data.get("articles", [])
print(f"📊 Found {len(articles)} articles")

if not articles:
    print("❌ No articles found!")
    exit(1)

# Test Supabase connection first
try:
    print("🔍 Testing Supabase connection...")
    tables = supabase.rpc("ping").execute()  # Simple ping test
    print("✅ Supabase connection OK!")
except Exception as e:
    print(f"❌ Supabase connection failed: {e}")
    exit(1)

inserted_count = 0
for i, item in enumerate(articles[:5]):
    title = item.get("title", "No title")
    summary = item.get("description", "No summary") or "No description available"
    link = item.get("url", "")
    published = item.get("publishedAt", "")
    
    print(f"\n📝 [{i+1}] Title: {title[:50]}...")
    print(f"   Summary: {summary[:50]}...")
    print(f"   Link: {link}")

    try:
        # Insert with error handling
        response = supabase.table("news").insert({
            "title": title,
            "summary": summary,
            "link": link,
            "published_at": published,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        
        print(f"✅ Insert response: {response.data}")
        inserted_count += 1
        
        # Small delay to avoid rate limits
        time.sleep(0.5)
        
    except Exception as e:
        print(f"❌ Insert failed: {e}")
        print(f"   Response: {e}")

print(f"\n🎉 Successfully inserted {inserted_count}/5 articles!")

# Verify insertion
print("\n🔍 Verifying data in Supabase...")
verify = supabase.table("news").select("title, created_at").limit(5).execute()
print(f"📋 Latest records: {verify.data}")
