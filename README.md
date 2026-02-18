# Avito.ru Scraper

A Python-based web scraper for collecting and analyzing product listings from avito.ru, designed with anti-detection measures and rate limiting to avoid IP bans.

## Overview

This scraper consists of two main components that work together as a producer-consumer system:
- **URL Grabber**: Continuously collects item URLs from avito.ru's main page
- **Item Analyzers**: Process URLs from a queue to extract detailed information from each listing

The system is deliberately throttled to process approximately 1000 ads over 8 hours to avoid triggering Avito's protection (HTTP 429 errors), which would result in a 5-minute ban.

## Features

- **Anti-detection measures**: Uses Playwright with stealth plugins and rotating user agents
- **Firewall detection**: Automatically detects when the scraper is blocked and raises appropriate exceptions
- **Concurrent processing**: Supports multiple analyzer instances for parallel processing
- **Persistent storage**: Saves extracted data in JSONL format for easy processing
- **Rate limiting**: Built-in delays to mimic human browsing behavior

## Requirements

- Python 3.7+
- Playwright
- BeautifulSoup4
- playwright-stealth

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install playwright beautifulsoup4 playwright-stealth
playwright install firefox
```

## Configuration

Edit `config.py` to adjust:
- Number of analyzer instances (`DEFAULT_NUM_ANALYZERS`)
- Maximum URLs to collect (`MAX_URLS_TO_COLLECT`)
- Queue size (`QUEUE_MAXSIZE`)
- Output file name (`OUTPUT_JSONL_FILE_NAME`)

## Usage

Run the scraper:
```bash
python main.py
```

## Data Output

Extracted data is saved in JSONL format with the following fields:
- `url`: The item's URL
- `title`: Item title
- `price`: Item price
- `description`: Item description
- `seller`: Seller name

## Limitations

- Maximum processing rate: ~1000 ads per 8 hours
- Firefox browser is launched in visible mode (headless=False), otherwise you get 429
- Each analyzer maintains its own browser instance
- Using more than one analyzer is putting you at risk of getting 429'ed

## Error Handling

- Custom `AvitoFirewallException` when the scraper is detected
- Automatic retry mechanism for failed item analysis
- Graceful shutdown on interrupt signals

## Project Structure

- `grabber.py`: URL collection logic
- `analyzer.py`: Item detail extraction
- `scraper.py`: Main orchestration class
- `exceptions.py`: Custom exceptions
- `config.py`: Configuration settings
- `user_agents.py`: Rotating user agent list
- `main.py`: Starts the entire thing

## Notes

*This scraper is designed for educational purposes and personal use. Always respect the website's terms of service and robots.txt when scraping. The slow processing rate is intentional to minimize server impact and avoid detection.*

## License

MIT License. *Happiness to everyone!*