# PIB Daily Tracker

Automated monitoring and digestion of Press Information Bureau (PIB) press releases.

## Overview

This project monitors the PIB website throughout the day and generates an end-of-day digest containing summaries of all press releases published that day.

## Features

- **Automated Monitoring**: Continuously monitors PIB website for new releases
- **Comprehensive Coverage**: Captures ALL releases published that day (no filtering or omissions)
- **Structured Summaries**: Each release summarized in 40-60 words covering key facts
- **Chronological Organization**: Digest organized by publication time
- **Duplicate Detection**: Automatically removes duplicate entries
- **End-of-Day Digest**: Single digest generated at 8 PM daily

## Project Structure

```
pib-daily-tracker/
├── src/
│   ├── scraper.py          # PIB website scraper
│   ├── processor.py        # Release processing and deduplication
│   ├── summarizer.py       # AI-powered summarization
│   ├── digest.py           # Digest generation
│   └── scheduler.py        # Task scheduling
├── config/
│   ├── settings.py         # Configuration settings
│   └── constants.py        # Constants and URLs
├── data/
│   ├── daily_digests/      # Generated digests directory
│   └── cache/              # Caching for releases
├── logs/
│   └── pib_tracker.log    # Application logs
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
└── main.py                 # Entry point
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/27anushkasingh/pib-daily-tracker.git
   cd pib-daily-tracker
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

## Usage

### Run as a scheduled service (recommended):
```bash
python main.py --mode scheduled
```

### Run once immediately:
```bash
python main.py --mode once
```

### Run with manual date:
```bash
python main.py --date 2026-08-05
```

## Configuration

Edit `.env` file to configure:
- `PIB_DIGEST_TIME`: Time to generate digest (default: 20:00)
- `PIB_BASE_URL`: PIB website URL
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `MAX_RETRIES`: Number of retry attempts for failed requests
- `REQUEST_TIMEOUT`: Request timeout in seconds

## Output Format

Digests are saved as markdown files in `data/daily_digests/`:

```
PIB Daily Digest – [Date]

**Release 1 Title**
[Summary paragraph 40-60 words]

**Release 2 Title**
[Summary paragraph 40-60 words]
```

## Dependencies

- `requests`: HTTP requests for web scraping
- `beautifulsoup4`: HTML parsing
- `selenium`: Dynamic content handling
- `openai`: AI-powered summarization (optional)
- `python-dateutil`: Date/time utilities
- `pytz`: Timezone handling
- `schedule`: Task scheduling
- `python-dotenv`: Environment variable management

## Logging

All operations are logged to `logs/pib_tracker.log` with timestamps and severity levels.

## License

MIT
