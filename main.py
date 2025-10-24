"""
Main script to run the entire news extraction pipeline
"""
import logging
import time
import argparse
from news_scraper import NewsScraper
from info_extractor import InfoExtractor
from db_handler import DatabaseHandler
from config import MONGO_URI, MONGO_DB, UPDATE_INTERVAL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_pipeline():
    """Run the complete news extraction pipeline"""
    logger.info("Starting news extraction pipeline")
    
    # Initialize components
    scraper = NewsScraper()
    extractor = InfoExtractor()
    db = DatabaseHandler()
    
    try:
        # Step 1: Scrape articles from RSS feeds
        logger.info("Scraping articles from RSS feeds")
        articles = scraper.parse_rss_feeds()
        logger.info(f"Found {len(articles)} articles from RSS feeds")
        
        # Step 2: Scrape full content for each article
        logger.info("Scraping full content for articles")
        enriched_articles = []
        for article in articles:
            enriched_article = scraper.scrape_article_content(article)
            enriched_articles.append(enriched_article)
            # Add a small delay to avoid overwhelming the servers
            time.sleep(0.5)
        
        # Step 3: Extract information and classify topics
        logger.info("Extracting information and classifying topics")
        processed_articles = []
        for article in enriched_articles:
            processed_article = extractor.process_article(article)
            processed_articles.append(processed_article)
        
        # Step 4: Save articles to database
        logger.info("Saving articles to database")
        saved_count = db.save_articles(processed_articles)
        logger.info(f"Successfully saved {saved_count} articles to database")
        
        return True
    except Exception as e:
        logger.error(f"Error in pipeline: {str(e)}")
        return False

def run_scheduled():
    """Run the pipeline on a schedule"""
    logger.info(f"Starting scheduled pipeline, will update every {UPDATE_INTERVAL} seconds")
    
    while True:
        success = run_pipeline()
        if success:
            logger.info(f"Pipeline completed successfully. Waiting {UPDATE_INTERVAL} seconds until next update.")
        else:
            logger.error(f"Pipeline failed. Will retry in {UPDATE_INTERVAL} seconds.")
        
        time.sleep(UPDATE_INTERVAL)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="News Data Extractor")
    parser.add_argument("--once", action="store_true", help="Run the pipeline once and exit")
    parser.add_argument("--schedule", action="store_true", help="Run the pipeline on a schedule")
    
    args = parser.parse_args()
    
    if args.once:
        run_pipeline()
    elif args.schedule:
        run_scheduled()
    else:
        # Default: run once
        run_pipeline()