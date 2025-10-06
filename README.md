# PySmash Scraper

A comprehensive web scraping toolkit for Smash Up! card game data from the official wiki. This project demonstrates modern Python development practices with a clean architecture, robust error handling, and multiple interfaces (CLI and API).

## Features

- 🎯 **Multi-target scraping**: Cards, factions, sets, and bases
- 🛡️ **SQL injection protection**: Parameterized queries throughout
- 🔄 **Robust error handling**: Network timeouts, retries, and graceful failures
- 📊 **Multiple interfaces**: Command-line tool and REST API
- 🐳 **Containerized**: Docker support for easy deployment
- ✅ **Well-tested**: Comprehensive test suite with fixtures
- 📈 **CI/CD ready**: GitHub Actions workflow included

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```bash
# Scrape all data
python -m scraper.cli scrape-all

# Scrape specific faction
python -m scraper.cli scrape-faction "Robots"

# Start web API
python -m scraper.api
```

### Docker

```bash
# Build and run
docker build -t pysmash-scraper .
docker run -p 8000:8000 pysmash-scraper
```

## Architecture

```
scraper/
├── models.py           # Pydantic data models
├── cli.py             # Command line interface
├── api.py             # FastAPI web service
├── scrapers/          # Scraping logic
│   ├── base_scraper.py
│   ├── faction_scraper.py
│   ├── card_scraper.py
│   └── set_scraper.py
├── database/          # Data persistence
│   ├── models.py      # SQLAlchemy models
│   └── repository.py  # Database operations
└── utils/             # Shared utilities
    ├── text_parsing.py
    └── web_client.py
```

## API Endpoints

- `GET /factions` - List all factions
- `GET /factions/{faction_id}/cards` - Get cards for a faction
- `GET /sets` - List all sets
- `GET /bases` - List all bases
- `POST /scrape/faction/{faction_name}` - Trigger faction scraping

## Development

### Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run linting
flake8 scraper/
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=scraper

# Run specific test module
pytest tests/test_scrapers.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
