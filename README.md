# News Data Extractor

A lightweight Flask + MongoDB application and pipeline to ingest news articles from RSS/CSV, extract information, and visualize aggregates on a dashboard. It includes scripts for importing data, endpoints for summaries, and a simple UI using Chart.js.

## Features

- Flask web app with a dashboard and topic/source pages
- MongoDB-backed article storage with helper utilities
- CSV ingestion script to bulk import scraped items
- Basic information extraction with room to plug in LLMs
- JSON APIs for topic and source summaries
- Chart.js visualizations: mentions over time, top persons, top locations

## Architecture

- `app.py`: Flask app, routes for pages and JSON APIs
- `db_handler.py`: MongoDB connection and helpers (save/query)
- `info_extractor.py`: heuristic entity extraction (extensible)
- `scripts/ingest_csv.py`: CLI to import CSV rows as articles
- `scripts/print_recent.py`: helper to print recent DB entries
- `templates/`: Jinja templates (`dashboard.html`, `index.html`, `topic.html`, `source.html`, `article.html`, `base.html`)
- `static/css/style.css`: minimal styling for pages

## Getting Started

### Prerequisites

- Python 3.9+ (recommended)
- MongoDB (local or remote)

### Installation

```bash
# From project root
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configuration

- Check `config.py` for database settings.
- Defaults typically point to a local MongoDB instance.
- If needed, set environment variables or update `config.py` to your connection string.

## Running the App

```bash
# Ensure MongoDB is running
# Start the Flask app
PYTHONPATH=. python app.py
# or
python app.py
```

- App runs on `http://127.0.0.1:5000/` by default.
- Open `/dashboard` for charts and summaries.

## Data Ingestion

### CSV Import

Use the ingestion script to import CSV rows as articles:

```bash
python scripts/ingest_csv.py --help
python scripts/ingest_csv.py --csv path/to/news.csv
```

Notes:
- The script expects specific columns; see `scripts/ingest_csv.py` for details.
- If your CSV is an iCloud placeholder (`*.icloud`), first open or download the real file.
- The script will enrich and save into MongoDB.

### Inspect Recent Articles

```bash
python scripts/print_recent.py
```

This prints a sample of recent articles and counts by topic and source.

## Database

- Articles are stored in MongoDB (collection name defined in `db_handler.py`).
- Basic fields include source, topic, timestamps, and text.
- Extraction fields (entities, locations, persons) depend on `info_extractor.py` logic.

## API Endpoints

- `GET /api/topics` — topic summary (topic + count)
- `GET /api/sources` — source summary (source + count)

Pages:
- `/` — index page
- `/dashboard` — charts for mentions over time, top persons, top locations
- `/topic/<topic>` — list articles by topic
- `/source/<source>` — list articles by source
- `/article/<id>` — article detail (if implemented)

## Dashboard

- `templates/dashboard.html` renders three Chart.js charts:
  - Mentions over time (line chart), computed in `/dashboard` route in `app.py`.
  - Top persons (bar chart), derived from entities extraction.
  - Top locations (bar chart), also derived from extraction.
- Data is passed from Flask using `pakistan_series`, `top_persons`, `top_locations`, and totals.

## Development

- Edit templates under `templates/` for UI changes.
- Update `info_extractor.py` to improve entity detection or plug in LLM.
- Add new routes in `app.py` and extend `db_handler.py` for queries.

### Improving Extraction (Optional Roadmap)

You can integrate a small LLM to extract structured facts and canonical entities. Consider:
- Call a local model (e.g., via `ollama` or `transformers`) or a hosted API.
- Define a JSON schema for entities and facts (person, org, location, event, claim).
- Add a new module (e.g., `llm_extractor.py`) and wire it into the ingestion pipeline.
- Store extracted structures in the article document for richer analytics.

## Scripts

- `scripts/ingest_csv.py` — import CSV to DB
- `scripts/print_recent.py` — quick DB inspection
- `scripts/test_db.py` — simple DB connectivity checks

## Common Tasks

- Remove all articles from a source (example):

```python
# Python REPL example
from db_handler import DatabaseHandler

db = DatabaseHandler()
result = db.collection.delete_many({"source": "The Economist (World)"})
print("Deleted:", result.deleted_count)
```

- Verify source/topic summaries:

```bash
curl http://127.0.0.1:5000/api/sources
curl http://127.0.0.1:5000/api/topics
```

## Contributing

- Fork the repo and create a feature branch.
- Keep changes minimal and consistent with project style.
- Open a PR with a clear description and screenshots or logs where helpful.

## License

Not specified. If you need a specific license, add a `LICENSE` file.