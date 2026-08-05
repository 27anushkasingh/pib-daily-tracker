"""Constants and URLs for PIB Daily Tracker."""

# PIB Website URLs
PIB_BASE_URL = "https://pib.gov.in"
PIB_RELEASES_URL = "https://pib.gov.in/allRelease.aspx"
PIB_PRESS_RELEASES_URL = "https://pib.gov.in/PressReleaseIframePage.aspx"

# Selectors for web scraping
RELEASE_CONTAINER_SELECTOR = "div.content"
RELEASE_TITLE_SELECTOR = "a.newstitle"
RELEASE_DATE_SELECTOR = "span.newsupdatedate"
RELEASE_LINK_SELECTOR = "a.newstitle"
RELEASE_MINISTRY_SELECTOR = "span.ministry"

# HTTP Headers
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# Parsing settings
PARSER = "html.parser"
TIME_FORMAT = "%d-%b-%Y %H:%M"
OUTPUT_DATE_FORMAT = "%d %B %Y"  # e.g., "05 August 2026"

# Summarization settings
SUMMARY_MIN_WORDS = 40
SUMMARY_MAX_WORDS = 60
SUMMARY_MIN_SENTENCES = 3
SUMMARY_MAX_SENTENCES = 4

# Retry settings
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2  # Exponential backoff: 1s, 2s, 4s
REQUEST_TIMEOUT = 30

# Deduplication settings
DUPLICATE_THRESHOLD = 0.95  # Similarity threshold for considering releases as duplicates

# Output settings
DIGEST_TITLE_FORMAT = "PIB Daily Digest – {date}"
OUTPUT_DIRECTORY = "data/daily_digests"
CACHE_DIRECTORY = "data/cache"
LOG_DIRECTORY = "logs"
