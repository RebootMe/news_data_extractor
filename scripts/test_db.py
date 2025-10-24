import sys
from datetime import datetime
from db_handler import DatabaseHandler


def main():
    db = DatabaseHandler()

    article = {
        "article_id": "db_test_001",
        "title": "DB Connectivity Test",
        "content": "Testing MongoDB connection from DatabaseHandler.",
        "source": "LocalTest",
        "topics": ["technology"],
        "scraped_at": datetime.utcnow().isoformat()
    }

    print("Saving test article...")
    saved = db.save_article(article)
    print("saved:", saved)

    print("Fetching test article...")
    fetched = db.get_article_by_id(article["article_id"])
    print("fetched_title:", fetched["title"] if fetched else None)

    print("Counting articles...")
    count = db.get_article_count()
    print("count:", count)


if __name__ == "__main__":
    main()