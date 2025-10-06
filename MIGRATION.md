# Migration Guide

This document explains how to migrate from the original `refresh_data.py` script to the new modular architecture.

## What Changed

### Original Structure
```
pysmash-scrapper/
└── refresh_data.py  # Everything in one file
```

### New Structure
```
pysmash-scrapper/
├── scraper/
│   ├── models.py           # Data validation models
│   ├── cli.py              # Command line interface
│   ├── api.py              # Web API
│   ├── scrapers/           # Scraping logic
│   ├── database/           # Database operations
│   └── utils/              # Shared utilities
├── tests/                  # Comprehensive test suite
├── examples/               # Usage examples
└── requirements.txt        # Dependencies
```

## Migration Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Replace Direct Script Usage

**Old way:**
```bash
python refresh_data.py
```

**New way (CLI):**
```bash
python -m scraper.cli scrape-all
```

**New way (Modernized script):**
```bash
python refresh_data_modern.py
```

### 3. API Access (New Feature)

Start the web API:
```bash
python -m scraper.api
```

Access endpoints:
- `GET /health` - Health check
- `GET /sets` - List all sets
- `POST /scrape/all` - Trigger full scraping

### 4. Programmatic Usage

**Old way:**
```python
# Everything was in global functions
pull_wiki_data(db)
pull_base_data()
```

**New way:**
```python
from scraper.database.repository import SmashUpRepository
from scraper.scrapers.set_scraper import SetScraper

repository = SmashUpRepository()
scraper = SetScraper()
result = scraper.scrape()
```

## Key Improvements

1. **Modularity**: Code is split into focused modules
2. **Error Handling**: Robust error handling throughout
3. **Testing**: Comprehensive test suite
4. **API**: RESTful web interface
5. **CLI**: Rich command-line interface
6. **Documentation**: Extensive documentation
7. **Docker**: Containerization support
8. **CI/CD**: GitHub Actions workflow

## Compatibility

The `refresh_data_modern.py` script provides the same functionality as the original but uses the new architecture internally. Use this for drop-in replacement.

## Examples

See the `examples/` directory for:
- `basic_usage.py` - Simple scraping example
- `export_to_json.py` - Data export example
