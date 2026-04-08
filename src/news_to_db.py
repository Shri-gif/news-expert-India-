import requests
from supabase import create_client
import os
from datetime import datetime 

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"

response = requests.get(url)
data = response.json()

articles = data.get("articles", [])

for item in articles[:5]:
    title = item.get("title")
    summary = item.get("description")
    link = item.get("url")

    print(title, summary, link)

    response = supabase.table("news").insert({
        "title": title,
        "summary": summary,
        "link": link,
    }).execute()

    print(response)
