import os
import requests
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"
data = requests.get(url).json()

for article in data.get("articles", [])[:10]:
    title = article.get("title", "")
    summary = article.get("description", "")
    link = article.get("url", "")

    if title and summary:
        try:
            supabase.table("news").insert({
                "title": title,
                "summary": summary,
                "link": link
            }).execute()
            print("Saved:", title)
        except Exception as e:
            print("Error:", e)
