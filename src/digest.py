"""Generate PIB daily digest."""

import logging
import os
from datetime import datetime
from typing import List, Dict

from config.constants import DIGEST_TITLE_FORMAT, OUTPUT_DATE_FORMAT
from config.settings import settings

logger = logging.getLogger(__name__)


class DigestGenerator:
    """Generate formatted PIB daily digests."""
    
    def __init__(self):
        """Initialize digest generator."""
        settings.ensure_directories()
    
    def generate_digest(self, releases: List[Dict], date: datetime = None) -> str:
        """Generate a formatted digest from releases.
        
        Args:
            releases: List of processed and summarized releases.
            date: Date for the digest. If None, uses today.
            
        Returns:
            Formatted digest as markdown string.
        """
        if date is None:
            date = datetime.now(settings.TIMEZONE)
        
        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        
        # Format date string
        date_str = date.strftime(OUTPUT_DATE_FORMAT)
        
        # Create digest title
        digest_title = DIGEST_TITLE_FORMAT.format(date=date_str)
        
        # Build digest content
        digest_lines = [digest_title, ""]
        
        if not releases:
            digest_lines.append("No press releases published on this date.")
            logger.info(f"Generated empty digest for {date_str}")
        else:
            # Add releases
            for idx, release in enumerate(releases, 1):
                digest_lines.append(f"## {idx}. {release['title']}")
                digest_lines.append("")
                
                if release.get("ministry"):
                    digest_lines.append(f"**Ministry/Department:** {release['ministry']}")
                    digest_lines.append("")
                
                if release.get("summary"):
                    digest_lines.append(release["summary"])
                    digest_lines.append("")
                
                if release.get("link"):
                    digest_lines.append(f"[Read full release]({release['link']})")
                    digest_lines.append("")
                
                digest_lines.append("---")
                digest_lines.append("")
            
            logger.info(f"Generated digest for {date_str} with {len(releases)} releases")
        
        return "\n".join(digest_lines)
    
    def save_digest(self, digest_content: str, date: datetime = None) -> str:
        """Save digest to file.
        
        Args:
            digest_content: Formatted digest content.
            date: Date for the digest.
            
        Returns:
            Path to saved digest file.
        """
        if date is None:
            date = datetime.now(settings.TIMEZONE)
        
        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        
        # Create filename
        filename = date.strftime("%Y-%m-%d") + "_pib_digest.md"
        filepath = os.path.join(settings.OUTPUT_DIRECTORY, filename)
        
        try:
            os.makedirs(settings.OUTPUT_DIRECTORY, exist_ok=True)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(digest_content)
            
            logger.info(f"Digest saved to {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Error saving digest: {e}")
            raise
    
    def get_digest_path(self, date: datetime = None) -> str:
        """Get the path where digest would be saved.
        
        Args:
            date: Date for the digest.
            
        Returns:
            Path to digest file.
        """
        if date is None:
            date = datetime.now(settings.TIMEZONE)
        
        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        
        filename = date.strftime("%Y-%m-%d") + "_pib_digest.md"
        return os.path.join(settings.OUTPUT_DIRECTORY, filename)
