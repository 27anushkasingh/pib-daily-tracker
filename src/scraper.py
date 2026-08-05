"""Web scraper for PIB press releases."""

import logging
import time
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pytz

from config.constants import (
    PIB_RELEASES_URL,
    DEFAULT_HEADERS,
    PARSER,
    TIME_FORMAT,
    MAX_RETRIES,
    RETRY_BACKOFF_FACTOR,
    REQUEST_TIMEOUT
)
from config.settings import settings

logger = logging.getLogger(__name__)


class PIBScraper:
    """Scraper for PIB press releases."""
    
    def __init__(self):
        """Initialize the scraper with a session."""
        self.session = self._create_session()
        self.base_url = settings.BASE_URL
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=RETRY_BACKOFF_FACTOR,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update(DEFAULT_HEADERS)
        
        return session
    
    def scrape_daily_releases(self, date: Optional[datetime] = None) -> List[Dict]:
        """Scrape all PIB releases for a specific date.
        
        Args:
            date: Date to scrape releases for. If None, uses today's date.
            
        Returns:
            List of release dictionaries containing title, link, date, and ministry.
        """
        if date is None:
            date = datetime.now(settings.TIMEZONE).date()
        else:
            date = date.date() if isinstance(date, datetime) else date
        
        logger.info(f"Starting scrape for releases on {date}")
        releases = []
        page = 1
        max_pages = 10  # Safety limit to prevent infinite loops
        
        while page <= max_pages:
            try:
                logger.debug(f"Scraping page {page}")
                page_releases = self._scrape_page(page, date)
                
                if not page_releases:
                    logger.info(f"No more releases found. Total releases: {len(releases)}")
                    break
                
                releases.extend(page_releases)
                page += 1
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error scraping page {page}: {e}")
                if page == 1:  # If first page fails, re-raise
                    raise
                break
        
        logger.info(f"Scraping complete. Total releases collected: {len(releases)}")
        return releases
    
    def _scrape_page(self, page: int, date) -> List[Dict]:
        """Scrape a single page of releases.
        
        Args:
            page: Page number to scrape.
            date: Date to filter releases for.
            
        Returns:
            List of releases from the page.
        """
        url = PIB_RELEASES_URL
        params = {
            "Ptype": "rel",
            "Page": page,
        }
        
        try:
            response = self.session.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch page {page}: {e}")
            raise
        
        soup = BeautifulSoup(response.content, PARSER)
        releases = []
        
        # Try multiple selectors - PIB website structure may vary
        # First try table structure (most common)
        table_rows = soup.find_all("tr")
        
        if table_rows:
            logger.debug(f"Found {len(table_rows)} table rows")
            for row in table_rows:
                try:
                    release = self._parse_table_row(row, date)
                    if release:
                        releases.append(release)
                except Exception as e:
                    logger.debug(f"Error parsing table row: {e}")
                    continue
        
        # If no table rows, try div-based structure
        if not releases:
            logger.debug("No table rows found, trying div-based structure")
            release_items = soup.find_all("div", class_="content")
            
            for item in release_items:
                try:
                    release = self._parse_release_item(item, date)
                    if release:
                        releases.append(release)
                except Exception as e:
                    logger.debug(f"Error parsing div item: {e}")
                    continue
        
        return releases
    
    def _parse_table_row(self, row, target_date) -> Optional[Dict]:
        """Parse a table row containing release information.
        
        Args:
            row: BeautifulSoup tr element.
            target_date: Date to filter for.
            
        Returns:
            Dictionary with release details or None if date doesn't match.
        """
        try:
            cells = row.find_all("td")
            if len(cells) < 3:
                return None
            
            # Typical structure: Date | Ministry | Title (as link)
            date_str = cells[0].get_text(strip=True)
            ministry = cells[1].get_text(strip=True) if len(cells) > 1 else "Unknown"
            
            # Find link in title cell
            title_cell = cells[2] if len(cells) > 2 else cells[-1]
            link_elem = title_cell.find("a", class_=["linkNews", "news-link"])
            
            # If no specific class, try any link
            if not link_elem:
                link_elem = title_cell.find("a")
            
            if not link_elem:
                return None
            
            title = link_elem.get_text(strip=True)
            link = link_elem.get("href", "")
            
            # Construct full URL if relative
            if link and not link.startswith("http"):
                link = self.base_url + link
            
            # Parse date
            release_date = self._parse_date(date_str)
            
            if not release_date:
                return None
            
            # Filter by date
            if release_date.date() != target_date.date():
                return None
            
            return {
                "title": title,
                "link": link,
                "date": release_date,
                "ministry": ministry,
                "description": "",
                "source": "PIB"
            }
        
        except Exception as e:
            logger.debug(f"Error parsing table row: {e}")
            return None
    
    def _parse_release_item(self, item, target_date) -> Optional[Dict]:
        """Parse a single release item from HTML (div-based structure).
        
        Args:
            item: BeautifulSoup element containing release info.
            target_date: Date to filter for.
            
        Returns:
            Dictionary with release details or None if date doesn't match.
        """
        try:
            # Extract title
            title_elem = item.find("a", class_=["newstitle", "linkNews"])
            if not title_elem:
                title_elem = item.find("a")
            
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            link = title_elem.get("href", "")
            
            # Construct full URL if relative
            if link and not link.startswith("http"):
                link = self.base_url + link
            
            # Extract date
            date_elem = item.find("span", class_="newsupdatedate")
            if not date_elem:
                # Try to find any date-like text
                date_elem = item.find("span")
            
            if not date_elem:
                return None
            
            date_str = date_elem.get_text(strip=True)
            release_date = self._parse_date(date_str)
            
            if not release_date:
                return None
            
            # Filter by date
            if release_date.date() != target_date.date():
                return None
            
            # Extract ministry/department
            ministry_elem = item.find("span", class_="ministry")
            ministry = ministry_elem.get_text(strip=True) if ministry_elem else "Unknown"
            
            # Extract preview/description
            desc_elem = item.find("p", class_="description")
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            return {
                "title": title,
                "link": link,
                "date": release_date,
                "ministry": ministry,
                "description": description,
                "source": "PIB"
            }
        
        except Exception as e:
            logger.debug(f"Error parsing release item: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object.
        
        Args:
            date_str: Date string to parse.
            
        Returns:
            Datetime object or None if parsing fails.
        """
        try:
            # Try multiple date formats
            date_formats = [
                "%d-%b-%Y %H:%M",      # 05-Aug-2026 14:30
                "%d-%B-%Y %H:%M",      # 05-August-2026 14:30
                "%d/%m/%Y %H:%M",      # 05/08/2026 14:30
                "%d %b %Y",            # 05 Aug 2026
                "%d %B %Y",            # 05 August 2026
                "%d-%m-%Y",            # 05-08-2026
                "%d/%m/%Y",            # 05/08/2026
                "%d %b %Y %H:%M",      # 05 Aug 2026 14:30
            ]
            
            for fmt in date_formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    # If no time specified, use noon
                    if dt.hour == 0 and dt.minute == 0:
                        dt = dt.replace(hour=12)
                    # Localize to configured timezone
                    return settings.TIMEZONE.localize(dt)
                except ValueError:
                    continue
            
            logger.warning(f"Could not parse date: {date_str}")
            return None
        
        except Exception as e:
            logger.error(f"Error parsing date {date_str}: {e}")
            return None
    
    def get_release_full_content(self, url: str) -> Optional[str]:
        """Fetch full content of a release.
        
        Args:
            url: URL of the release.
            
        Returns:
            Full text content of the release or None if fetch fails.
        """
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, PARSER)
            
            # Extract main content
            content_div = soup.find("div", class_="content-area")
            if not content_div:
                content_div = soup.find("div", id="content")
            
            if content_div:
                return content_div.get_text(separator="\n", strip=True)
            
            return None
        
        except Exception as e:
            logger.error(f"Error fetching release content from {url}: {e}")
            return None
    
    def close(self):
        """Close the session."""
        self.session.close()
        logger.debug("Scraper session closed")
