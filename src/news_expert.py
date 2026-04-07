import requests
from bs4 import BeautifulSoup
import schedule
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
import pandas as pd
import re
from typing import List, Dict

class IndianNewsExpert:
    def __init__(self):
        self.email_to = os.getenv('EMAIL_TO')
        self.email_from = os.getenv('EMAIL_FROM')
        self.email_password = os.getenv('EMAIL_PASS')
        self.news_sources = {
            'Economic Times': 'https://economictimes.indiatimes.com/',
            'The Hindu': 'https://www.thehindu.com/',
            'In42Shots': 'https://inshorts.com/'  # Assuming this is the correct URL
        }
        self.topics = [
            'governance', 'government jobs', 'weather', 'gold price', 
            'silver price', 'stock market', 'tax', 'budget', 'economy'
        ]
    
    def search_news(self, url: str, source_name: str) -> List[Dict]:
        """Search and extract relevant news articles"""
        news_items = []
        
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
except Exception as e:
    print(f"Skipping {source_name}: {e}")
    return []

soup = BeautifulSoup(response.content, 'html.parser')
            
            # Source-specific parsing
            articles = self.parse_source(source_name, soup)
            
            for article in articles[:10]:  # Limit to top 10 per source
                title = article.get('title', '')
                link = article.get('link', '')
                summary = article.get('summary', '')
                
                # Filter by relevant topics
                if self.is_relevant_news(title + ' ' + summary):
                    news_items.append({
                        'source': source_name,
                        'title': title,
                        'link': link,
                        'summary': self.truncate_summary(summary, 120),
                        'time': datetime.now().strftime('%Y-%m-%d %H:%M')
                    })
                    
        except Exception as e:
            print(f"Error fetching {source_name}: {str(e)}")
        
        return news_items
    
    def parse_source(self, source_name: str, soup: BeautifulSoup) -> List[Dict]:
        """Parse different news sources"""
        articles = []
        
        if source_name == 'Economic Times':
            # ET specific selectors
            article_elements = soup.find_all('h3', class_=re.compile('.*title.*')) or \
                             soup.find_all('a', href=re.compile('/news/'))
            for elem in article_elements:
                title = elem.get_text(strip=True)
                link = 'https://economictimes.indiatimes.com' + elem.get('href', '') if elem.get('href') else ''
                articles.append({'title': title, 'link': link, 'summary': title})
                
        elif source_name == 'The Hindu':
            # The Hindu selectors
            article_elements = soup.find_all('h2') or soup.find_all('h3')
            for elem in article_elements:
                title = elem.get_text(strip=True)
                link_elem = elem.find_parent('a')
                link = link_elem.get('href', '') if link_elem else ''
                if link.startswith('/'):
                    link = 'https://www.thehindu.com' + link
                articles.append({'title': title, 'link': link, 'summary': title})
                
        elif source_name == 'In42Shots':
            # InShorts selectors
            article_elements = soup.find_all('div', {'itemprop': 'itemListElement'})
            for elem in article_elements:
                title_elem = elem.find('p', {'itemprop': 'headline'})
                summary_elem = elem.find('div', {'itemprop': 'articleBody'})
                title = title_elem.get_text(strip=True) if title_elem else ''
                summary = summary_elem.get_text(strip=True) if summary_elem else ''
                link = elem.find('a').get('href', '') if elem.find('a') else ''
                articles.append({'title': title, 'link': link, 'summary': summary})
        
        return articles
    
    def is_relevant_news(self, text: str) -> bool:
        """Check if news is relevant to our topics"""
        text_lower = text.lower()
        relevant_keywords = [
            'government', 'governance', 'jobs', 'weather', 'gold', 'silver',
            'stock', 'market', 'sensex', 'nifty', 'tax', 'income tax', 'gst',
            'budget', 'economy', 'finance', 'rbi', 'monsoon'
        ]
        return any(keyword in text_lower for keyword in relevant_keywords)
    
    def truncate_summary(self, text: str, max_length: int) -> str:
        """Truncate summary to specified length"""
        if len(text) <= max_length:
            return text
        return text[:max_length].rsplit(' ', 1)[0] + '...'
    
    def compile_daily_news(self) -> str:
        """Compile all news into formatted report"""
        all_news = []
        
        print("🔍 Fetching news from sources...")
        for source_name, url in self.news_sources.items():
            print(f"  📱 {source_name}...")
            news = self.search_news(url, source_name)
            all_news.extend(news)
        
        # Sort by source and time
        all_news.sort(key=lambda x: x['source'])
        
        # Format report
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
        """Send compiled news via email"""
        try:
            msg = MimeMultipart()
            msg['From'] = self.email_from
            msg['To'] = self.email_to
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'html'))
            
            # Gmail SMTP
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.email_from, self.email_password)
            server.sendmail(self.email_from, self.email_to, msg.as_string())
            server.quit()
            
            print("✅ Email sent successfully!")
            
        except Exception as e:
            print(f"❌ Email failed: {str(e)}")

def job():
    """Daily news compilation job"""
    expert = IndianNewsExpert() 
    
    report = expert.compile_daily_news()
    subject = f"📰 Daily India News Expert - {date.today().strftime('%d/%m/%Y')}"
    expert.send_email(subject, report)

# Schedule daily at 5 AM
if __name__ == "__main__":
    print("🚀 Indian News Expert Started!")
    print("📅 Scheduled for 5:00 AM daily")
    
    # Schedule job at 5 AM every day
    schedule.every().day.at("05:00").do(job)
    
    # Run immediately for testing (comment out for production)
    # job()
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
