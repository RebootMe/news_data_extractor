"""
Configuration settings for the News Data Extractor
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB settings
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
MONGO_DB = os.getenv('MONGO_DB', 'news_data')
MONGO_COLLECTION = os.getenv('MONGO_COLLECTION', 'articles')

# RSS Feed sources
RSS_FEEDS = [
    {'name': 'BBC News', 'url': 'http://feeds.bbci.co.uk/news/rss.xml'},
    {'name': 'CNN', 'url': 'http://rss.cnn.com/rss/edition.rss'},
    {'name': 'Reuters', 'url': 'http://feeds.reuters.com/reuters/topNews'},
    {'name': 'New York Times', 'url': 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml'},
]

# Topics for information extraction
TOPICS = [
    'politics',
    'business',
    'technology',
    'health',
    'science',
    'sports',
    'entertainment'
]

# Web app settings
FLASK_HOST = os.getenv('FLASK_HOST', '127.0.0.1')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

# Scraping settings
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
REQUEST_TIMEOUT = 10  # seconds

# Update frequency
UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', 3600))  # seconds