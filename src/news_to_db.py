import requests
from supabase import create_client, Client
import os
from datetime import datetime 
import time
import json

# Multiple news sources
NEWS_SOURCES = [
    {
         "name": "UPSC Filtered News",
         "url": lambda key: f"https://newsapi.org/v2/everything?q=India government economy policy UPSC&language=en&sortBy=publishedAt&pageSize=10&apiKey={key}"
    }   
]

# Environment variables
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print(f"🔑 NEWS_API_KEY: {'✅ Found' if NEWS_API_KEY else '❌ Missing'}")
print(f"🔑 SUPABASE_URL: {'✅ Found' if SUPABASE_URL else '❌ Missing'}")
print(f"🔑 SUPABASE_KEY: {'✅ Found' if SUPABASE_KEY else '❌ Missing'}")

if not all([NEWS_API_KEY, SUPABASE_URL, SUPABASE_KEY]):
    print("❌ Missing required environment variables!")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_news(source):
    """Fetch news from a source with detailed error info"""
    try:
        url = source["url"](NEWS_API_KEY)
        print(f"🌐 Trying {source['name']}: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get("articles", [])
            print(f"   ✅ Found {len(articles)} articles")
            return articles
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return []
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return []

# Try multiple sources
all_articles = []
for source in NEWS_SOURCES:
    articles = fetch_news(source)
    if articles:
        all_articles.extend(articles[:5])  # Take top 5 from first working source
        print(f"🎉 Using {source['name']} - got {len(articles)} articles")
        break
    time.sleep(1)  # Rate limit protection

if not all_articles:
    print("❌ All news sources failed! Check your NEWS_API_KEY")
    print("\n🔍 NewsAPI Key Status Check:")
    status_url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"
    status_resp = requests.get(status_url, timeout=5)
    print(f"Status check: {status_resp.status_code}")
    print(f"Response preview: {status_resp.text[:300]}")
    exit(1)

print(f"📊 Total articles to process: {len(all_articles)}")

# Test Supabase connection
try:
    print("\n🔍 Testing Supabase...")
    # Check if table exists
    tables = supabase.rpc("get_tables").execute()
    print("✅ Supabase OK!")
except:
    print("⚠️ Supabase test failed, continuing...")

# Insert articles
inserted_count = 0
for i, item in enumerate(all_articles[:5]):
    title = (item.get("title") or "No title")[:255]  # Truncate
    summary = (item.get("description") or "No description")[:500]
    link = item.get("url", "")
    published = item.get("publishedAt", "")
    source = item.get("source", {}).get("name", "") 
    
    if not link:  # Skip invalid articles
        continue
        
    print(f"\n📝 [{i+1}] {title[:60]}...")
    
    try:
        # Use upsert to avoid duplicates
        response = supabase.table("news").upsert({
            "title": title,
            "summary": summary,
            "link": link,
            "source": source, 
            "published_at": published,
            "created_at": datetime.utcnow().isoformat()
        }, on_conflict="link").execute()
        
        print(f"   ✅ Saved! ID: {response.data[0]['id'] if response.data else 'N/A'}")
        inserted_count += 1
        time.sleep(0.3)
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

print(f"\n🎉 Successfully inserted {inserted_count} articles!")

# Final verification
try:
    verify = supabase.table("news").select("count").execute()
    total = verify.data[0]['count'] if verify.data else 0
    print(f"📊 Total news in DB: {total}")
    
    recent = supabase.table("news").select("title").limit(3).execute()
    print("📋 Recent titles:")
    for item in recent.data:
        print(f"   • {item['title'][:50]}...")
        
except Exception as e:
    print(f"⚠️ Verification failed: {e}")
