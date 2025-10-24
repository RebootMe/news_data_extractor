from db_handler import DatabaseHandler
from datetime import datetime


def fmt_date(val):
    try:
        if isinstance(val, str):
            return val
        return val.isoformat()
    except Exception:
        return str(val)


def main():
    db = DatabaseHandler()
    print("Connected. Counting articles...")
    total = db.get_article_count()
    print(f"Total articles: {total}")

    print("\nRecent articles:")
    articles = db.get_recent_articles(limit=10, skip=0)
    if not articles:
        print("No articles found.")
    else:
        for i, a in enumerate(articles, 1):
            title = a.get("title", "<no title>")
            source = a.get("source", "<no source>")
            topics = ", ".join(a.get("topics", [])) or "<no topics>"
            scraped_at = fmt_date(a.get("scraped_at"))
            print(f"{i:02d}. {title}\n    source: {source}\n    topics: {topics}\n    scraped_at: {scraped_at}\n    id: {a.get('article_id','<no id>')}\n")

    print("\nTopic summary:")
    for t in db.get_topics_summary()[:10]:
        print(f" - {t.get('_id')}: {t.get('count')}")

    print("\nSource summary:")
    for s in db.get_sources_summary()[:10]:
        print(f" - {s.get('_id')}: {s.get('count')}")


if __name__ == "__main__":
    main()