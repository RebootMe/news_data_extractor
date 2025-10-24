"""
File-based storage system as an alternative to MongoDB
"""
import os
import json
import logging
import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FileStorage:
    """Class for handling file-based storage operations for news articles"""
    
    def __init__(self, storage_dir="data"):
        """Initialize the file storage with a directory to store data"""
        self.storage_dir = storage_dir
        self.articles_dir = os.path.join(storage_dir, "articles")
        self.ensure_directories()
        logger.info(f"File storage initialized at {self.storage_dir}")
    
    def ensure_directories(self):
        """Ensure the necessary directories exist"""
        Path(self.storage_dir).mkdir(exist_ok=True)
        Path(self.articles_dir).mkdir(exist_ok=True)
    
    def _serialize_article(self, article):
        """Convert article object to JSON-serializable format"""
        serialized = article.copy()
        
        # Convert datetime objects to ISO format strings
        if 'published_date' in serialized and isinstance(serialized['published_date'], datetime.datetime):
            serialized['published_date'] = serialized['published_date'].isoformat()
        
        if 'scraped_at' in serialized and isinstance(serialized['scraped_at'], datetime.datetime):
            serialized['scraped_at'] = serialized['scraped_at'].isoformat()
            
        return serialized
    
    def _deserialize_article(self, article_data):
        """Convert JSON data back to article with proper types"""
        if article_data is None:
            return None
            
        article = article_data.copy()
        
        # Convert ISO format strings back to datetime objects
        if 'published_date' in article and isinstance(article['published_date'], str):
            try:
                article['published_date'] = datetime.datetime.fromisoformat(article['published_date'])
            except ValueError:
                pass
        
        if 'scraped_at' in article and isinstance(article['scraped_at'], str):
            try:
                article['scraped_at'] = datetime.datetime.fromisoformat(article['scraped_at'])
            except ValueError:
                pass
                
        return article
    
    def save_article(self, article):
        """Save or update a single article in the file storage"""
        if not article or not article.get('article_id'):
            logger.warning("Cannot save article: Missing article_id")
            return False
        
        try:
            article_path = os.path.join(self.articles_dir, f"{article['article_id']}.json")
            
            # Add timestamp if not present
            if 'scraped_at' not in article:
                article['scraped_at'] = datetime.datetime.now()
                
            # Serialize and save
            with open(article_path, 'w', encoding='utf-8') as f:
                json.dump(self._serialize_article(article), f, ensure_ascii=False, indent=2)
            
            logger.info(f"Article saved: {article['article_id']}")
            return True
        except Exception as e:
            logger.error(f"Error saving article: {str(e)}")
            return False
    
    def get_article_by_id(self, article_id):
        """Retrieve an article by its ID"""
        try:
            article_path = os.path.join(self.articles_dir, f"{article_id}.json")
            
            if not os.path.exists(article_path):
                return None
                
            with open(article_path, 'r', encoding='utf-8') as f:
                article_data = json.load(f)
                
            return self._deserialize_article(article_data)
        except Exception as e:
            logger.error(f"Error retrieving article {article_id}: {str(e)}")
            return None
    
    def get_articles_by_topic(self, topic, limit=20, skip=0):
        """Get articles by topic with pagination"""
        try:
            articles = []
            count = 0
            skipped = 0
            
            # Iterate through all article files
            for filename in os.listdir(self.articles_dir):
                if not filename.endswith('.json'):
                    continue
                    
                article_path = os.path.join(self.articles_dir, filename)
                
                with open(article_path, 'r', encoding='utf-8') as f:
                    article_data = json.load(f)
                
                # Check if article has the requested topic
                if 'topics' in article_data and topic in article_data['topics']:
                    if skipped < skip:
                        skipped += 1
                        continue
                        
                    articles.append(self._deserialize_article(article_data))
                    count += 1
                    
                    if count >= limit:
                        break
            
            return articles
        except Exception as e:
            logger.error(f"Error retrieving articles by topic {topic}: {str(e)}")
            return []
    
    def get_articles_by_source(self, source, limit=20, skip=0):
        """Get articles by source with pagination"""
        try:
            articles = []
            count = 0
            skipped = 0
            
            # Iterate through all article files
            for filename in os.listdir(self.articles_dir):
                if not filename.endswith('.json'):
                    continue
                    
                article_path = os.path.join(self.articles_dir, filename)
                
                with open(article_path, 'r', encoding='utf-8') as f:
                    article_data = json.load(f)
                
                # Check if article has the requested source
                if 'source' in article_data and article_data['source'] == source:
                    if skipped < skip:
                        skipped += 1
                        continue
                        
                    articles.append(self._deserialize_article(article_data))
                    count += 1
                    
                    if count >= limit:
                        break
            
            return articles
        except Exception as e:
            logger.error(f"Error retrieving articles by source {source}: {str(e)}")
            return []
    
    def get_recent_articles(self, limit=20, skip=0):
        """Get recent articles with pagination"""
        try:
            # Get all article files
            article_files = []
            for filename in os.listdir(self.articles_dir):
                if filename.endswith('.json'):
                    article_path = os.path.join(self.articles_dir, filename)
                    article_files.append(article_path)
            
            # Sort by modification time (most recent first)
            article_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # Apply pagination
            paginated_files = article_files[skip:skip+limit]
            
            # Load articles
            articles = []
            for article_path in paginated_files:
                with open(article_path, 'r', encoding='utf-8') as f:
                    article_data = json.load(f)
                articles.append(self._deserialize_article(article_data))
            
            return articles
        except Exception as e:
            logger.error(f"Error retrieving recent articles: {str(e)}")
            return []
    
    def get_topics_summary(self):
        """Get summary of article counts by topic"""
        try:
            topic_counts = {}
            
            # Iterate through all article files
            for filename in os.listdir(self.articles_dir):
                if not filename.endswith('.json'):
                    continue
                    
                article_path = os.path.join(self.articles_dir, filename)
                
                with open(article_path, 'r', encoding='utf-8') as f:
                    article_data = json.load(f)
                
                # Count articles by topic
                if 'topics' in article_data:
                    for topic in article_data['topics']:
                        if topic not in topic_counts:
                            topic_counts[topic] = 0
                        topic_counts[topic] += 1
            
            # Format results similar to MongoDB aggregation
            result = [{"_id": topic, "count": count} for topic, count in topic_counts.items()]
            return sorted(result, key=lambda x: x["count"], reverse=True)
        except Exception as e:
            logger.error(f"Error getting topics summary: {str(e)}")
            return []
    
    def get_sources_summary(self):
        """Get summary of article counts by source"""
        try:
            source_counts = {}
            
            # Iterate through all article files
            for filename in os.listdir(self.articles_dir):
                if not filename.endswith('.json'):
                    continue
                    
                article_path = os.path.join(self.articles_dir, filename)
                
                with open(article_path, 'r', encoding='utf-8') as f:
                    article_data = json.load(f)
                
                # Count articles by source
                if 'source' in article_data:
                    source = article_data['source']
                    if source not in source_counts:
                        source_counts[source] = 0
                    source_counts[source] += 1
            
            # Format results similar to MongoDB aggregation
            result = [{"_id": source, "count": count} for source, count in source_counts.items()]
            return sorted(result, key=lambda x: x["count"], reverse=True)
        except Exception as e:
            logger.error(f"Error getting sources summary: {str(e)}")
            return []
    
    def count_articles(self):
        """Count total number of articles"""
        try:
            count = 0
            for filename in os.listdir(self.articles_dir):
                if filename.endswith('.json'):
                    count += 1
            return count
        except Exception as e:
            logger.error(f"Error counting articles: {str(e)}")
            return 0