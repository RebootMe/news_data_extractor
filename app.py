"""
Flask web application for displaying news articles
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
import logging
import datetime
import math
from db_handler import DatabaseHandler
from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, TOPICS
from collections import Counter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

@app.template_filter('format_dt')
def format_dt(value):
    try:
        if value is None:
            return 'Unknown date'
        if isinstance(value, datetime.datetime):
            return value.strftime('%Y-%m-%d %H:%M')
        if isinstance(value, str):
            try:
                dt = datetime.datetime.fromisoformat(value)
                return dt.strftime('%Y-%m-%d %H:%M')
            except Exception:
                return value
        return str(value)
    except Exception:
        return 'Unknown date'

class Pagination:
    def __init__(self, page: int, per_page: int, total: int):
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = math.ceil(total / per_page) if per_page else 1
    @property
    def has_prev(self):
        return self.page > 1
    @property
    def has_next(self):
        return self.page < self.pages
    @property
    def prev_num(self):
        return self.page - 1
    @property
    def next_num(self):
        return self.page + 1
    def iter_pages(self):
        return range(1, self.pages + 1)

db = DatabaseHandler()


def _get_per_page(default: int = 10):
    val = request.args.get('per_page', str(default))
    if isinstance(val, str) and val.lower() == 'all':
        return 1000
    try:
        num = int(val)
        return max(1, min(num, 1000))
    except Exception:
        return default















@app.route('/')
def index():
    """Home page with recent articles"""
    page = request.args.get('page', 1, type=int)
    per_page = _get_per_page(10)
    skip = (page - 1) * per_page
    articles = db.get_recent_articles(limit=per_page, skip=skip)
    total_articles = db.get_article_count()
    topics_summary = db.get_topics_summary()
    sources_summary = db.get_sources_summary()
    pagination = Pagination(page, per_page, total_articles)
    return render_template(
        'index.html',
        articles=articles,
        topics=TOPICS,
        topics_summary=topics_summary,
        sources_summary=sources_summary,
        pagination=pagination,
        active_page='home'
    )

@app.route('/topic/<topic>')
def topic_articles(topic):
    """Page showing articles for a specific topic"""
    if topic not in TOPICS:
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    per_page = _get_per_page(20)
    skip = (page - 1) * per_page
    articles = db.get_articles_by_topic(topic, limit=per_page, skip=skip)
    total_articles = db.get_article_count({"topics": topic})
    topics_summary = db.get_topics_summary()
    sources_summary = db.get_sources_summary()
    pagination = Pagination(page, per_page, total_articles)
    return render_template(
        'topic.html',
        articles=articles,
        topics=TOPICS,
        topics_summary=topics_summary,
        sources_summary=sources_summary,
        current_topic=topic,
        pagination=pagination,
        active_page='topic'
    )

@app.route('/source/<source>')
def source_articles(source):
    """Page showing articles from a specific source"""
    page = request.args.get('page', 1, type=int)
    per_page = _get_per_page(20)
    skip = (page - 1) * per_page
    articles = db.get_articles_by_source(source, limit=per_page, skip=skip)
    total_articles = db.get_article_count({"source": source})
    topics_summary = db.get_topics_summary()
    sources_summary = db.get_sources_summary()
    pagination = Pagination(page, per_page, total_articles)
    return render_template(
        'source.html',
        articles=articles,
        topics=TOPICS,
        topics_summary=topics_summary,
        sources_summary=sources_summary,
        current_source=source,
        pagination=pagination,
        active_page='source'
    )

@app.route('/article/<article_id>')
def article_detail(article_id):
    """Page showing a single article in detail"""
    article = db.get_article_by_id(article_id)
    
    if not article:
        return redirect(url_for('index'))
    
    # Get topic and source summaries for sidebar
    topics_summary = db.get_topics_summary()
    sources_summary = db.get_sources_summary()
    
    return render_template(
        'article.html',
        article=article,
        topics=TOPICS,
        topics_summary=topics_summary,
        sources_summary=sources_summary,
        active_page='article'
    )

@app.route('/api/articles')
def api_articles():
    """API endpoint for getting articles"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    topic = request.args.get('topic')
    source = request.args.get('source')
    
    skip = (page - 1) * per_page
    filters = {}
    
    if topic:
        filters["topics"] = topic
    
    if source:
        filters["source"] = source
    
    articles = db.get_articles(filters=filters, limit=per_page, skip=skip)
    total_articles = db.get_article_count(filters)
    
    return jsonify({
        "articles": articles,
        "page": page,
        "per_page": per_page,
        "total_articles": total_articles,
        "total_pages": (total_articles // per_page) + (1 if total_articles % per_page > 0 else 0)
    })

@app.route('/api/article/<article_id>')
def api_article_detail(article_id):
    """API endpoint for getting a single article"""
    article = db.get_article_by_id(article_id)
    
    if not article:
        return jsonify({"error": "Article not found"}), 404
    
    return jsonify(article)

@app.route('/api/topics')
def api_topics():
    """API endpoint for getting topic summary"""
    topics_summary = db.get_topics_summary()
    return jsonify(topics_summary)

@app.route('/api/sources')
def api_sources():
    """API endpoint for getting source summary"""
    sources_summary = db.get_sources_summary()
    return jsonify(sources_summary)

@app.route('/dashboard')
def dashboard():
    """Dashboard page with aggregated stats and charts"""
    # Fetch a reasonable number of recent articles for stats
    articles = db.get_articles(limit=1000)

    def parse_dt(val):
        if not val:
            return None
        if isinstance(val, datetime.datetime):
            return val
        if isinstance(val, str):
            try:
                return datetime.datetime.fromisoformat(val)
            except Exception:
                return None
        return None

    def mentions_pakistan(a):
        text = f"{a.get('title','')} {a.get('content','')}".lower()
        if 'pakistan' in text:
            return True
        ents = a.get('entities', {}) or {}
        for key in ('GPE', 'LOCATION'):
            for e in ents.get(key, []) or []:
                if isinstance(e, str) and e.lower() == 'pakistan':
                    return True
        return False

    # Time series for Pakistan mentions by date
    pakistan_dates = []
    for a in articles:
        if mentions_pakistan(a):
            dt = parse_dt(a.get('published_date') or a.get('scraped_at'))
            if dt:
                pakistan_dates.append(dt.date().isoformat())
    pakistan_by_day = Counter(pakistan_dates)
    pakistan_series = sorted(
        [{'date': d, 'count': c} for d, c in pakistan_by_day.items()],
        key=lambda x: x['date']
    )

    # Top persons and locations
    persons_counter = Counter()
    locations_counter = Counter()
    for a in articles:
        ents = a.get('entities', {}) or {}
        for p in ents.get('PERSON', []) or []:
            if isinstance(p, str) and p.strip():
                persons_counter[p] += 1
        for loc in (ents.get('GPE', []) or []) + (ents.get('LOCATION', []) or []):
            if isinstance(loc, str) and loc.strip():
                locations_counter[loc] += 1
    top_persons = [{'label': k, 'count': v} for k, v in persons_counter.most_common(10)]
    top_locations = [{'label': k, 'count': v} for k, v in locations_counter.most_common(10)]

    # Summaries for sidebar reuse
    topics_summary = db.get_topics_summary()
    sources_summary = db.get_sources_summary()

    return render_template(
        'dashboard.html',
        topics=TOPICS,
        topics_summary=topics_summary,
        sources_summary=sources_summary,
        pakistan_series=pakistan_series,
        top_persons=top_persons,
        top_locations=top_locations,
        pakistan_total=sum(x['count'] for x in pakistan_series),
        active_page='dashboard'
    )

if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)