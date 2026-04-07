import os
from datetime import date

class Config:
    EMAIL_TO = os.getenv('EMAIL_TO')
    EMAIL_FROM = os.getenv('EMAIL_FROM') 
    EMAIL_PASSWORD = os.getenv('EMAIL_PASS')
    
    NEWS_SOURCES = {
        'Economic Times': 'https://economictimes.indiatimes.com/',
        'The Hindu': 'https://www.thehindu.com/',
        'InShorts': 'https://www.inshorts.com/'
    }
    
    TODAY = date.today().strftime('%d/%m/%Y')
