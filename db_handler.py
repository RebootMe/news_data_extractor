"""
Database handler for storing and retrieving news articles
"""
import pymongo
from pymongo import MongoClient
import logging
from config import MONGO_URI, MONGO_DB, MONGO_COLLECTION

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseHandler:
    """Class for handling database operations for news articles"""
    
    def __init__(self, mongo_uri=MONGO_URI, mongo_db=MONGO_DB, mongo_collection=MONGO_COLLECTION):
        try:
            self.client = MongoClient(mongo_uri)
            self.db = self.client[mongo_db]
            self.collection = self.db[mongo_collection]
            
            # Create indexes for faster queries
            self.collection.create_index([("article_id", pymongo.ASCENDING)], unique=True)
            self.collection.create_index([("topics", pymongo.ASCENDING)])
            self.collection.create_index([("source", pymongo.ASCENDING)])
            self.collection.create_index([("scraped_at", pymongo.DESCENDING)])
            
            logger.info(f"Connected to MongoDB: {MONGO_DB}.{MONGO_COLLECTION}")
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {str(e)}")
            raise
    
    def save_article(self, article):
        """Save or update a single article in the database"""
        if not article or not article.get('article_id'):
            logger.warning("Cannot save article: Missing article_id")
            return False
        
        try:
            # Use upsert to update if exists, insert if not
            result = self.collection.update_one(
                {"article_id": article["article_id"]},
                {"$set": article},
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"Inserted new article: {article['title']}")
                return True
            elif result.modified_count > 0:
                logger.info(f"Updated existing article: {article['title']}")
                return True
            else:
                logger.info(f"Article unchanged: {article['title']}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving article {article.get('title', '')}: {str(e)}")
            return False
    
    def save_articles(self, articles):
        """Save multiple articles to the database"""
        if not articles:
            logger.warning("No articles to save")
            return 0
        
        success_count = 0
        for article in articles:
            if self.save_article(article):
                success_count += 1
        
        logger.info(f"Saved {success_count} out of {len(articles)} articles")
        return success_count
    
    def get_articles(self, filters=None, limit=50, skip=0, sort_by=None):
        """Get articles from the database with optional filtering"""
        if filters is None:
            filters = {}
            
        if sort_by is None:
            sort_by = [("scraped_at", pymongo.DESCENDING)]
        
        try:
            cursor = self.collection.find(filters).sort(sort_by).skip(skip).limit(limit)
            articles = list(cursor)
            logger.info(f"Retrieved {len(articles)} articles from database")
            return articles
        except Exception as e:
            logger.error(f"Error retrieving articles: {str(e)}")
            return []
    
    def get_article_by_id(self, article_id):
        """Get a specific article by its ID"""
        try:
            article = self.collection.find_one({"article_id": article_id})
            return article
        except Exception as e:
            logger.error(f"Error retrieving article {article_id}: {str(e)}")
            return None
    
    def get_articles_by_topic(self, topic, limit=50, skip=0):
        """Get articles filtered by topic"""
        return self.get_articles(
            filters={"topics": topic},
            limit=limit,
            skip=skip
        )
    
    def get_articles_by_source(self, source, limit=50, skip=0):
        """Get articles filtered by source"""
        return self.get_articles(
            filters={"source": source},
            limit=limit,
            skip=skip
        )
    
    def get_recent_articles(self, limit=50, skip=0):
        """Get most recent articles with pagination support"""
        return self.get_articles(limit=limit, skip=skip)
    
    def get_article_count(self, filters=None):
        """Get count of articles matching filters"""
        if filters is None:
            filters = {}
            
        try:
            count = self.collection.count_documents(filters)
            return count
        except Exception as e:
            logger.error(f"Error counting articles: {str(e)}")
            return 0
    
    def get_topics_summary(self):
        """Get summary of article counts by topic"""
        try:
            pipeline = [
                {"$unwind": "$topics"},
                {"$group": {"_id": "$topics", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            result = list(self.collection.aggregate(pipeline))
            return result
        except Exception as e:
            logger.error(f"Error getting topics summary: {str(e)}")
            return []
    
    def get_sources_summary(self):
        """Get summary of article counts by source"""
        try:
            pipeline = [
                {"$group": {"_id": "$source", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            result = list(self.collection.aggregate(pipeline))
            return result
        except Exception as e:
            logger.error(f"Error getting sources summary: {str(e)}")
            return []


if __name__ == "__main__":
    # Test the database handler
    db = DatabaseHandler()
    
    # Test article
    test_article = {
        "article_id": "test123",
        "title": "Test Article",
        "content": "This is a test article content",
        "source": "Test Source",
        "topics": ["technology", "science"],
        "scraped_at": "2023-01-01T12:00:00"
    }
    
    # Save test article
    db.save_article(test_article)
    
    # Retrieve and print
    retrieved = db.get_article_by_id("test123")
    if retrieved:
        print(f"Retrieved article: {retrieved['title']}")
    
    # Get count
    count = db.get_article_count()
    print(f"Total articles in database: {count}")