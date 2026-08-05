"""Process and deduplicate PIB releases."""

import logging
from typing import List, Dict, Set
from difflib import SequenceMatcher
from datetime import datetime
import hashlib

from config.constants import DUPLICATE_THRESHOLD

logger = logging.getLogger(__name__)


class ReleaseProcessor:
    """Process and deduplicate releases."""
    
    def __init__(self):
        """Initialize processor."""
        self.seen_hashes: Set[str] = set()
    
    def process_releases(self, raw_releases: List[Dict]) -> List[Dict]:
        """Process and deduplicate releases.
        
        Args:
            raw_releases: List of raw release dictionaries from scraper.
            
        Returns:
            Deduplicated and processed releases sorted chronologically.
        """
        logger.info(f"Processing {len(raw_releases)} raw releases")
        
        # Remove duplicates
        unique_releases = self._remove_duplicates(raw_releases)
        logger.info(f"After deduplication: {len(unique_releases)} releases")
        
        # Normalize and enrich data
        processed_releases = [
            self._normalize_release(release)
            for release in unique_releases
        ]
        
        # Sort by date (chronological order)
        processed_releases.sort(key=lambda x: x["date"])
        
        logger.info(f"Processing complete. Final count: {len(processed_releases)}")
        return processed_releases
    
    def _remove_duplicates(self, releases: List[Dict]) -> List[Dict]:
        """Remove duplicate releases based on title and content similarity.
        
        Args:
            releases: List of releases to deduplicate.
            
        Returns:
            List of unique releases.
        """
        unique_releases = []
        
        for release in releases:
            if not self._is_duplicate(release, unique_releases):
                unique_releases.append(release)
            else:
                logger.debug(f"Duplicate detected: {release['title']}")
        
        return unique_releases
    
    def _is_duplicate(self, release: Dict, existing_releases: List[Dict]) -> bool:
        """Check if a release is a duplicate of existing releases.
        
        Args:
            release: Release to check.
            existing_releases: List of existing releases.
            
        Returns:
            True if duplicate, False otherwise.
        """
        current_title = release.get("title", "").lower()
        
        for existing in existing_releases:
            existing_title = existing.get("title", "").lower()
            
            # Exact match
            if current_title == existing_title:
                return True
            
            # Similarity-based match
            similarity = SequenceMatcher(None, current_title, existing_title).ratio()
            if similarity > DUPLICATE_THRESHOLD:
                return True
        
        return False
    
    def _normalize_release(self, release: Dict) -> Dict:
        """Normalize and enrich release data.
        
        Args:
            release: Raw release dictionary.
            
        Returns:
            Normalized release dictionary.
        """
        normalized = {
            "id": self._generate_release_id(release),
            "title": release.get("title", "").strip(),
            "link": release.get("link", "").strip(),
            "date": release.get("date"),
            "ministry": release.get("ministry", "Unknown").strip(),
            "description": release.get("description", "").strip(),
            "source": release.get("source", "PIB"),
            "summary": None,  # To be filled by summarizer
            "processed_at": datetime.now()
        }
        
        return normalized
    
    def _generate_release_id(self, release: Dict) -> str:
        """Generate unique ID for a release.
        
        Args:
            release: Release dictionary.
            
        Returns:
            Unique ID string.
        """
        id_source = f"{release.get('title', '')}{release.get('link', '')}"
        return hashlib.md5(id_source.encode()).hexdigest()
    
    def filter_by_date(self, releases: List[Dict], target_date: datetime) -> List[Dict]:
        """Filter releases by a specific date.
        
        Args:
            releases: List of releases.
            target_date: Date to filter for.
            
        Returns:
            Releases matching the target date.
        """
        target_date = target_date.date() if isinstance(target_date, datetime) else target_date
        
        filtered = [
            r for r in releases
            if r["date"].date() == target_date
        ]
        
        logger.info(f"Filtered to {len(filtered)} releases for {target_date}")
        return filtered
