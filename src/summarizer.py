"""Summarize PIB releases."""

import logging
from typing import List, Dict, Optional
from abc import ABC, abstractmethod
import re

from config.constants import (
    SUMMARY_MIN_WORDS,
    SUMMARY_MAX_WORDS,
    SUMMARY_MIN_SENTENCES,
    SUMMARY_MAX_SENTENCES
)
from config.settings import settings

logger = logging.getLogger(__name__)


class BaseSummarizer(ABC):
    """Base class for summarizers."""
    
    @abstractmethod
    def summarize(self, text: str, title: str = "") -> Optional[str]:
        """Summarize text.
        
        Args:
            text: Text to summarize.
            title: Title of the release (for context).
            
        Returns:
            Summarized text or None if summarization fails.
        """
        pass
    
    def _validate_summary(self, summary: str) -> bool:
        """Validate summary meets requirements.
        
        Args:
            summary: Summary text to validate.
            
        Returns:
            True if summary meets requirements, False otherwise.
        """
        if not summary:
            return False
        
        words = summary.split()
        word_count = len(words)
        
        # Check word count
        if word_count < SUMMARY_MIN_WORDS or word_count > SUMMARY_MAX_WORDS:
            logger.warning(
                f"Summary word count {word_count} outside range "
                f"[{SUMMARY_MIN_WORDS}, {SUMMARY_MAX_WORDS}]"
            )
            return False
        
        # Check sentence count
        sentences = re.split(r'[.!?]+', summary)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences)
        
        if sentence_count < SUMMARY_MIN_SENTENCES or sentence_count > SUMMARY_MAX_SENTENCES:
            logger.warning(
                f"Summary sentence count {sentence_count} outside range "
                f"[{SUMMARY_MIN_SENTENCES}, {SUMMARY_MAX_SENTENCES}]"
            )
            return False
        
        return True


class SimpleSummarizer(BaseSummarizer):
    """Simple extractive summarizer using sentence selection."""
    
    def summarize(self, text: str, title: str = "") -> Optional[str]:
        """Summarize text using extractive method.
        
        Args:
            text: Text to summarize.
            title: Title of the release.
            
        Returns:
            Summarized text or None if summarization fails.
        """
        if not text or len(text.strip()) < 50:
            logger.warning("Text too short to summarize")
            return None
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) < 3:
            # If less than 3 sentences, return as-is (truncated if needed)
            summary = ".".join(sentences[:4])
            if not summary.endswith("."):
                summary += "."
            return summary if self._validate_summary(summary) else None
        
        # Score sentences based on relevance to title and position
        scored_sentences = []
        for idx, sentence in enumerate(sentences):
            score = self._score_sentence(sentence, title, idx, len(sentences))
            scored_sentences.append((sentence, score))
        
        # Select top sentences
        num_sentences = min(4, len(scored_sentences))
        top_sentences = sorted(
            scored_sentences,
            key=lambda x: sentences.index(x[0])  # Sort by original order
        )[:num_sentences]
        
        summary = ". ".join([s[0] for s in top_sentences])
        if not summary.endswith("."):
            summary += "."
        
        return summary if self._validate_summary(summary) else None
    
    def _score_sentence(self, sentence: str, title: str, position: int, total: int) -> float:
        """Score a sentence based on relevance and position.
        
        Args:
            sentence: Sentence to score.
            title: Release title.
            position: Position in document.
            total: Total sentences.
            
        Returns:
            Relevance score.
        """
        score = 0.0
        
        # Title relevance (words from title appearing in sentence)
        title_words = set(title.lower().split())
        sentence_words = set(sentence.lower().split())
        overlap = len(title_words & sentence_words)
        score += overlap * 2
        
        # Position bias (first and last sentences score higher)
        if position == 0 or position == total - 1:
            score += 3
        elif position == 1 or position == total - 2:
            score += 2
        
        # Length preference (medium-length sentences score higher)
        word_count = len(sentence.split())
        if 10 <= word_count <= 25:
            score += 1
        
        # Key phrases
        key_phrases = [
            "announced", "launched", "approved", "released",
            "decision", "scheme", "agreement", "report",
            "ministry", "department", "government"
        ]
        for phrase in key_phrases:
            if phrase.lower() in sentence.lower():
                score += 1
        
        return score


class OpenAISummarizer(BaseSummarizer):
    """Summarizer using OpenAI API."""
    
    def __init__(self):
        """Initialize OpenAI summarizer."""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        
        try:
            import openai
            openai.api_key = settings.OPENAI_API_KEY
            self.client = openai
        except ImportError:
            raise ImportError("openai package not installed")
    
    def summarize(self, text: str, title: str = "") -> Optional[str]:
        """Summarize text using OpenAI.
        
        Args:
            text: Text to summarize.
            title: Title of the release.
            
        Returns:
            Summarized text or None if summarization fails.
        """
        if not text or len(text.strip()) < 50:
            logger.warning("Text too short to summarize")
            return None
        
        prompt = f"""Summarize the following PIB press release in exactly 3-4 sentences (40-60 words total).
Cover: what was announced, who announced it, key decision/scheme/agreement/event, important numbers/dates/institutions.
Do not add analysis, opinions, or background context. Keep it factual and clear.

Title: {title}

Content:
{text[:2000]}  # Limit to first 2000 chars

Summary:"""
        
        try:
            response = self.client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a PIB press release summarizer. Create concise, factual summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.5
            )
            
            summary = response.choices[0].message.content.strip()
            
            return summary if self._validate_summary(summary) else None
        
        except Exception as e:
            logger.error(f"Error with OpenAI summarization: {e}")
            return None


class ReleaseSummarizer:
    """Main summarizer orchestrator."""
    
    def __init__(self, use_openai: bool = False):
        """Initialize summarizer.
        
        Args:
            use_openai: Whether to use OpenAI (requires API key).
        """
        if use_openai and settings.OPENAI_API_KEY:
            try:
                self.summarizer = OpenAISummarizer()
                logger.info("Using OpenAI summarizer")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI summarizer: {e}. Falling back to simple summarizer.")
                self.summarizer = SimpleSummarizer()
        else:
            self.summarizer = SimpleSummarizer()
            logger.info("Using simple extractive summarizer")
    
    def summarize_releases(self, releases: List[Dict], content_fetcher=None) -> List[Dict]:
        """Summarize a list of releases.
        
        Args:
            releases: List of releases to summarize.
            content_fetcher: Optional function to fetch full content.
            
        Returns:
            Releases with summaries added.
        """
        logger.info(f"Summarizing {len(releases)} releases")
        
        for i, release in enumerate(releases):
            try:
                # Use description or fetch full content
                text_to_summarize = release.get("description", "")
                
                if not text_to_summarize and content_fetcher:
                    text_to_summarize = content_fetcher(release["link"])
                
                if text_to_summarize:
                    summary = self.summarizer.summarize(
                        text_to_summarize,
                        release.get("title", "")
                    )
                    
                    if summary:
                        release["summary"] = summary
                        logger.debug(f"Summarized release {i+1}/{len(releases)}: {release['title'][:50]}...")
                    else:
                        logger.warning(f"Could not summarize release: {release['title']}")
                        release["summary"] = self._create_fallback_summary(release)
                else:
                    logger.warning(f"No content available for: {release['title']}")
                    release["summary"] = self._create_fallback_summary(release)
            
            except Exception as e:
                logger.error(f"Error summarizing release: {e}")
                release["summary"] = self._create_fallback_summary(release)
        
        logger.info("Summarization complete")
        return releases
    
    def _create_fallback_summary(self, release: Dict) -> str:
        """Create a fallback summary from release metadata.
        
        Args:
            release: Release dictionary.
            
        Returns:
            Fallback summary.
        """
        return f"Press release from {release.get('ministry', 'PIB')}: {release.get('title', 'No title available')}."
