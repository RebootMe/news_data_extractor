"""
News scraper module for extracting articles from RSS feeds
"""
import feedparser
import requests
from bs4 import BeautifulSoup
from newspaper import Article
import datetime
import hashlib
import logging
from config import RSS_FEEDS, REQUEST_HEADERS, REQUEST_TIMEOUT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NewsScraper:
    """Class for scraping news from RSS feeds and extracting article content"""
    
    def __init__(self):
        self.feeds = RSS_FEEDS
        self.headers = REQUEST_HEADERS
        self.timeout = REQUEST_TIMEOUT
    
    def parse_rss_feeds(self):
        """Parse all configured RSS feeds and return a list of article metadata"""
        all_articles = []
        
        for feed_info in self.feeds:
            try:
                logger.info(f"Parsing RSS feed: {feed_info['name']}")
                feed = feedparser.parse(feed_info['url'])
                
                for entry in feed.entries:
                    article = {
                        'title': entry.get('title', ''),
                        'link': entry.get('link', ''),
                        'published': entry.get('published', ''),
                        'summary': entry.get('summary', ''),
                        'source': feed_info['name'],
                        'article_id': self._generate_article_id(entry.get('link', '')),
                        'scraped_at': datetime.datetime.now().isoformat(),
                        'content': None,
                        'keywords': [],
                        'topics': []
                    }
                    all_articles.append(article)
                
                logger.info(f"Found {len(feed.entries)} articles from {feed_info['name']}")
            except Exception as e:
                logger.error(f"Error parsing feed {feed_info['name']}: {str(e)}")
        
        return all_articles
    
    def scrape_article_content(self, article):
        """Scrape full content from an article URL using newspaper3k"""
        if not article['link']:
            logger.warning(f"No URL provided for article: {article['title']}")
            return article
        
        try:
            news_article = Article(article['link'])
            news_article.download()
            news_article.parse()
            news_article.nlp()  # Extract keywords and summary
            
            article['content'] = news_article.text
            article['keywords'] = news_article.keywords
            article['top_image'] = news_article.top_image
            article['authors'] = news_article.authors
            
            logger.info(f"Successfully scraped content for: {article['title']}")
        except Exception as e:
            logger.error(f"Error scraping article {article['link']}: {str(e)}")
        
        return article
    
    def scrape_all_articles(self):
        """Parse RSS feeds and scrape full content for all articles"""
        articles = self.parse_rss_feeds()
        
        # Scrape full content for each article
        enriched_articles = []
        for article in articles:
            enriched_article = self.scrape_article_content(article)
            enriched_articles.append(enriched_article)
        
        return enriched_articles
    
    def _generate_article_id(self, url):
        """Generate a unique ID for an article based on its URL"""
        return hashlib.md5(url.encode()).hexdigest()


if __name__ == "__main__":
    # Test the scraper
    scraper = NewsScraper()
    articles = scraper.parse_rss_feeds()
    print(f"Found {len(articles)} articles from RSS feeds")
    
    # Test scraping content for the first article
    if articles:
        enriched = scraper.scrape_article_content(articles[0])
        print(f"Title: {enriched['title']}")
        print(f"Content length: {len(enriched.get('content', '')) if enriched.get('content') else 0} characters")
        print(f"Keywords: {enriched.get('keywords', [])}")