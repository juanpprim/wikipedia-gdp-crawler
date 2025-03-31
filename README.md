# Wikipedia GDP Crawler

A Python tool that crawls Wikipedia pages to extract GDP-related data.

## Features

- Extracts data from GDP-related Wikipedia pages
- Supports GDP nominal per capita and real GDP growth rate data
- Asynchronous crawling using asyncio and httpx
- Structured data using msgspec

## Requirements

- Python 3.9+
- Poetry for dependency management
- Make (for running common tasks)

## Installation

```bash
# Clone the repository
git clone https://github.com/username/wikipedia-gdp-crawler.git
cd wikipedia-gdp-crawler

# Install dependencies
make setup
```

## Usage

```bash
# Run the crawler
make run

# Or directly with Poetry
poetry run wiki-gdp
```

## Development

```bash
# Run tests
make test

# Run linter
make lint

# Run type checker
make type-check

# Run test coverage
make coverage

# Format code
make format
```

## Project Structure

```
wikipedia-gdp-crawler/
├── src/                    # Source code
├── tests/                  # Test directory
├── pyproject.toml          # Poetry configuration
└── Makefile                # Make tasks
```

## License

MIT 