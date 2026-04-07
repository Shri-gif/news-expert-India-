import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
import re
from typing import List, Dict

# Supabase setup
try:
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)
    SUPABASE_AVAILABLE = True
except ImportError:
    print("⚠️ Supabase not available - continuing without DB")
    SUPABASE_AVAILABLE = False

class IndianNewsExpert:
    def __init__(self):
        self.email_to = os.getenv('EMAIL_TO')
        self.email_from = os.getenv('EMAIL_FROM')
        self.email_password = os.getenv('EMAIL_PASS')
        self.news_sources = {
            'Economic Times': 'https://economictimes.indiatimes.com/',
            'The Hindu': 'https://www.thehindu.com/',
            'InShorts': 'https://www.inshorts.com/'
        }
    
    def search_news(self, url: str, source_name: str) -> List[Dict]:
        news_items = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = self.parse_source(source_name, soup)
            
            for article in articles[:10]:
                title = article.get('title', '').strip()
                link = article.get('link', '').strip()
                summary = article.get('summary', '').strip()
                
                # Check relevance
                if self.is_relevant_news(title + ' ' + summary):
                    news_item = {
                        'source': source_name,
                        'title': title,
                        'link': link,
                        'summary': self.truncate_summary(summary, 120),
                        'time': datetime.now().strftime('%Y-%m-%d %H:%M')
                    }
                    news_items.append(news_item)
                    
                    # ✅ Supabase Save (Fixed Indentation)
                    if SUPABASE_AVAILABLE:
                        try:
                            supabase.table("news").insert({
                                "title": title[:255],  # Supabase limit
                                "summary": summary[:500],
                                "source": source_name,
                                "link": link,
                                "created_at": datetime.now().isoformat()
                            }).execute()
                            print(f"✅ Saved to Supabase: {title[:50]}...")
                        except Exception as db_error:
                            print(f"⚠️ Supabase error: {db_error}")
                            
        except Exception as e:
            print(f"❌ Error fetching {source_name}: {str(e)}")
            
        return news_items
    
    def parse_source(self, source_name: str, soup: BeautifulSoup) -> List[Dict]:
        articles = []
        if source_name == 'Economic Times':
            article_elements = (soup.find_all('h3', class_=re.compile('.*title.*')) or 
                              soup.find_all('a', href=re.compile('/news/')))
            for elem in article_elements:
                title = elem.get_text(strip=True)
                link = ('https://economictimes.indiatimes.com' + elem.get('href', '') 
                       if elem.get('href') else '')
                if title:
                    articles.append({'title': title, 'link': link, 'summary': title})
                    
        elif source_name == 'The Hindu':
            article_elements = soup.find_all(['h2', 'h3'])
            for elem in article_elements:
                title = elem.get_text(strip=True)
                link_elem = elem.find_parent('a')
                link = link_elem.get('href', '') if link_elem else ''
                if link.startswith('/'):
                    link = 'https://www.thehindu.com' + link
                if title:
                    articles.append({'title': title, 'link': link, 'summary': title})
                    
        elif source_name == 'InShorts':
            article_elements = soup.find_all('div', {'itemprop': 'itemListElement'})
            for elem in article_elements:
                title_elem = elem.find('p', {'itemprop': 'headline'})
                summary_elem = elem.find('div', {'itemprop': 'articleBody'})
                title = title_elem.get_text(strip=True) if title_elem else ''
                summary = summary_elem.get_text(strip=True) if summary_elem else ''
                link_elem = elem.find('a')
                link = link_elem.get('href', '') if link_elem else ''
                if title:
                    articles.append({'title': title, 'link': link, 'summary': summary})
        
        return articles[:15]  # Limit articles
    
    def is_relevant_news(self, text: str) -> bool:
        text_lower = text.lower()
        relevant_keywords = [
            'government', 'governance', 'jobs', 'weather', 'gold', 'silver',
            'stock', 'market', 'sensex', 'nifty', 'tax', 'income tax', 'gst',
            'budget', 'economy', 'finance', 'rbi', 'monsoon', 'crude'
        ]
        return any(keyword in text_lower for keyword in relevant_keywords)
    
    def truncate_summary(self, text: str, max_length: int) -> str:
        if len(text) <= max_length:
            return text
        return text[:max_length].rsplit(' ', 1)[0] + '...'
    
    def compile_daily_news(self) -> str:
        all_news = []
        print("🔍 Fetching news from sources...")
        
        for source_name, url in self.news_sources.items():
            print(f"  📱 {source_name}...")
            news = self.search_news(url, source_name)
            all_news.extend(news)
        
        all_news.sort(key=lambda x: x['source'])
        
        report = f"""
📰 **DAILY INDIA NEWS EXPERT** 
📅 {date.today().strftime('%B %d, %Y')} | ⏰ {datetime.now().strftime('%H:%M IST')}

"""
        
        if not all_news:
            report += "❌ No relevant news found today.\n\n"
        else:
            for item in all_news:
                report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📢 **{item['title'][:80]}{'...' if len(item['title']) > 80 else ''}**

{item['summary']}

🔗 {item['link']}
📱 {item['source']} | 🕒 {item['time']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            report += f"\n\n🤖 Powered by Indian News Expert | Total: {len(all_news)} stories"
        
        return report
    
    def send_email(self, subject: str, body: str):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = self.email_to
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.email_from, self.email_password)
            server.sendmail(self.email_from, self.email_to, msg.as_string())
            server.quit()
            print("✅ Email sent successfully!")
            return True
        except Exception as e:
            print(f"❌ Email failed: {str(e)}")
            return False

def job():
    print("🚀 Starting Daily India News Expert...")
    expert = IndianNewsExpert() 
    report = expert.compile_daily_news()
    subject = f"📰 Daily India News Expert - {date.today().strftime('%d/%m/%Y')}"
    
    if expert.send_email(subject, report):
        print("🎉 Daily job completed successfully!")
    else:
        print("❌ Job failed - check email settings")

if __name__ == "__main__":
    job()
