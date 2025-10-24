import csv
import hashlib
import logging
import os
import sys
from argparse import ArgumentParser
from datetime import datetime
from urllib.parse import urlparse

from db_handler import DatabaseHandler
from info_extractor import InfoExtractor
from news_scraper import NewsScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def md5_id(text: str) -> str:
    try:
        return hashlib.md5((text or '').encode()).hexdigest()
    except Exception:
        return hashlib.md5(b'').hexdigest()


def guess_source_from_url(url: str) -> str:
    try:
        netloc = urlparse(url).netloc
        return netloc or 'Unknown'
    except Exception:
        return 'Unknown'


def read_rows(csv_path: str):
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


def row_to_article(row: dict) -> dict:
    # Try multiple common column names
    title = row.get('title') or row.get('Title') or ''
    link = row.get('link') or row.get('url') or row.get('Link') or ''
    published = row.get('published') or row.get('Published') or row.get('pubDate') or ''
    summary = row.get('summary') or row.get('Summary') or row.get('description') or ''
    content = row.get('content') or row.get('Content') or summary
    source = row.get('source') or row.get('Source') or guess_source_from_url(link)

    article = {
        'title': title,
        'link': link,
        'published': published,
        'content': content,
        'source': source,
        'article_id': md5_id(link),
        'scraped_at': datetime.utcnow().isoformat(),
        'keywords': [],
        'topics': []
    }
    return article


def ingest_csv(csv_path: str) -> int:
    logger.info(f"Reading CSV: {csv_path}")
    scraper = NewsScraper()
    extractor = InfoExtractor()
    db = DatabaseHandler()

    saved = 0
    total = 0

    for row in read_rows(csv_path):
        total += 1
        article = row_to_article(row)

        if not article.get('link'):
            logger.warning(f"Row {total} missing link; skipping")
            continue

        # Enrich with scraped content if content is missing
        if not article.get('content'):
            article = scraper.scrape_article_content(article)

        # Process through extractor to get entities and topics
        processed = extractor.process_article(article)

        if db.save_article(processed):
            saved += 1

    logger.info(f"Processed {total} rows; saved {saved} articles")
    return saved


def main():
    parser = ArgumentParser(description='Ingest RSS CSV and run through pipeline')
    parser.add_argument('--csv', dest='csv_path', default=os.path.join('data', 'rss_news_2025-10-24_00-00.csv'), help='Path to CSV file to ingest')
    args = parser.parse_args()

    if not os.path.exists(args.csv_path):
        logger.error(f"CSV not found: {args.csv_path}")
        sys.exit(1)

    ingest_csv(args.csv_path)


if __name__ == '__main__':
    main()