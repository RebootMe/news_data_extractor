"""
Information extraction module for classifying news articles by topic
and extracting relevant entities and keywords
"""
import nltk
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
from config import TOPICS
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Download required NLTK resources
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('maxent_ne_chunker', quiet=True)
    nltk.download('words', quiet=True)
except Exception as e:
    logger.warning(f"Error downloading NLTK resources: {str(e)}")

class InfoExtractor:
    """Class for extracting information and classifying news articles"""
    
    def __init__(self):
        self.topics = TOPICS
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        
        # Topic keywords dictionary
        self.topic_keywords = {
            'politics': ['government', 'president', 'election', 'vote', 'policy', 'minister', 
                        'parliament', 'senate', 'congress', 'democrat', 'republican', 'law', 
                        'legislation', 'political', 'campaign', 'candidate', 'party', 'bill',
                        'constitution', 'diplomat', 'foreign policy', 'domestic policy'],
            'business': ['economy', 'market', 'stock', 'trade', 'company', 'industry', 'investment',
                        'finance', 'bank', 'dollar', 'euro', 'profit', 'revenue', 'economic', 
                        'corporate', 'CEO', 'startup', 'investor', 'business', 'commercial',
                        'enterprise', 'merger', 'acquisition', 'IPO', 'shares', 'venture capital'],
            'technology': ['tech', 'software', 'hardware', 'internet', 'app', 'digital', 'computer',
                          'AI', 'artificial intelligence', 'robot', 'smartphone', 'cyber', 'code',
                          'innovation', 'startup', 'algorithm', 'data', 'technology', 'silicon valley',
                          'programming', 'developer', 'cloud', 'machine learning', 'neural network',
                          'automation', 'computing', 'interface', 'platform', 'Google', 'Microsoft',
                          'Apple', 'Facebook', 'Amazon', 'Tesla', 'engineering'],
            'health': ['medical', 'doctor', 'hospital', 'patient', 'disease', 'treatment', 'drug',
                      'vaccine', 'healthcare', 'virus', 'pandemic', 'medicine', 'health', 'symptom',
                      'clinical', 'therapy', 'diagnosis', 'surgery', 'physician', 'nurse', 'cancer',
                      'diabetes', 'heart disease', 'mental health', 'psychiatry', 'wellness'],
            'science': ['research', 'scientist', 'study', 'discovery', 'experiment', 'space', 
                       'physics', 'biology', 'chemistry', 'astronomy', 'climate', 'environment',
                       'laboratory', 'theory', 'scientific', 'academic', 'journal', 'hypothesis',
                       'evidence', 'data', 'analysis', 'quantum', 'molecular', 'ecosystem',
                       'evolution', 'genetics', 'particle', 'NASA', 'SpaceX'],
            'sports': ['team', 'player', 'game', 'match', 'tournament', 'championship', 'score',
                      'win', 'lose', 'football', 'soccer', 'basketball', 'baseball', 'tennis',
                      'olympic', 'athlete', 'coach', 'league', 'sports', 'competition', 'fitness',
                      'stadium', 'race', 'medal', 'victory', 'defeat', 'NHL', 'NBA', 'NFL', 'MLB'],
            'entertainment': ['movie', 'film', 'actor', 'actress', 'director', 'music', 'song',
                            'celebrity', 'star', 'TV', 'show', 'award', 'performance', 'concert',
                            'festival', 'album', 'Hollywood', 'entertainment', 'streaming', 'Netflix',
                            'Disney', 'HBO', 'theater', 'premiere', 'box office', 'Grammy', 'Oscar',
                            'Emmy', 'artist', 'band', 'singer', 'producer']
        }
    
    def preprocess_text(self, text):
        """Preprocess text for analysis"""
        if not text:
            return []
            
        # Tokenize and lowercase
        tokens = word_tokenize(text.lower())
        
        # Remove stopwords and non-alphabetic tokens
        filtered_tokens = [
            self.lemmatizer.lemmatize(token) 
            for token in tokens 
            if token.isalpha() and token not in self.stop_words
        ]
        
        return filtered_tokens
    
    def extract_named_entities(self, text):
        """Extract named entities from text"""
        entities = {
            'PERSON': [],
            'ORGANIZATION': [],
            'LOCATION': [],
            'DATE': [],
            'MONEY': [],
            'GPE': []  # Geo-Political Entity
        }
        
        if not text:
            return entities
            
        try:
            sentences = sent_tokenize(text)
            for sentence in sentences:
                words = word_tokenize(sentence)
                tagged = nltk.pos_tag(words)
                chunks = nltk.ne_chunk(tagged)
                
                for chunk in chunks:
                    if hasattr(chunk, 'label'):
                        entity_type = chunk.label()
                        if entity_type in entities:
                            entity_name = ' '.join([c[0] for c in chunk])
                            if entity_name not in entities[entity_type]:
                                entities[entity_type].append(entity_name)
        except Exception as e:
            logger.error(f"Error extracting named entities: {str(e)}")
        
        return entities
    
    def classify_topic(self, article):
        """Classify article into topics based on content and keywords"""
        if not article.get('content') and not article.get('title'):
            return []
        
        # Combine title, content and existing keywords for classification
        text = f"{article.get('title', '')} {article.get('content', '')}"
        tokens = self.preprocess_text(text)
        
        # Count topic keyword occurrences
        topic_scores = {topic: 0 for topic in self.topics}
        
        # Give more weight to title matches
        title_tokens = self.preprocess_text(article.get('title', ''))
        for token in title_tokens:
            for topic, keywords in self.topic_keywords.items():
                if token in keywords:
                    topic_scores[topic] += 3  # Higher weight for title matches
        
        # Content token matches
        for token in tokens:
            for topic, keywords in self.topic_keywords.items():
                if token in keywords:
                    topic_scores[topic] += 1
                    
        # Also check for exact phrases in the original text
        for topic, keywords in self.topic_keywords.items():
            for keyword in keywords:
                if ' ' in keyword and keyword.lower() in text.lower():
                    topic_scores[topic] += 2  # Give more weight to multi-word matches
        
        # Consider existing keywords from the article - give these highest weight
        for keyword in article.get('keywords', []):
            keyword_lower = keyword.lower()
            for topic, topic_keywords in self.topic_keywords.items():
                if any(kw.lower() == keyword_lower for kw in topic_keywords):
                    topic_scores[topic] += 4  # Highest weight for exact keyword matches
        
        # Sort topics by score in descending order and filter by threshold
        min_score = 1
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
        relevant_topics = [topic for topic, score in sorted_topics if score > min_score]
        
        # Take top 2 topics maximum to avoid irrelevant classifications
        return relevant_topics[:2] if relevant_topics else ['general']
    
    def process_article(self, article):
        """Process an article to extract information and classify topics"""
        # Extract named entities
        entities = self.extract_named_entities(article.get('content', ''))
        
        # Classify topics
        topics = self.classify_topic(article)
        
        # Update article with extracted information
        enriched_article = article.copy()
        enriched_article['topics'] = topics
        enriched_article['entities'] = entities
        
        return enriched_article


if __name__ == "__main__":
    # Test the extractor
    test_article = {
        'title': 'Tech Giants Announce New AI Research Partnership',
        'content': 'Silicon Valley tech companies announced today a new partnership focused on artificial intelligence research. Google, Microsoft, and Facebook will collaborate on developing ethical AI standards. The announcement came during a technology conference in San Francisco, where industry leaders discussed the future of machine learning and data privacy concerns.',
        'keywords': ['AI', 'technology', 'partnership']
    }
    
    extractor = InfoExtractor()
    processed = extractor.process_article(test_article)
    
    print(f"Detected topics: {processed['topics']}")
    print(f"Named entities: {processed['entities']}")