"""Main entry point for PIB Daily Tracker."""

import logging
import logging.handlers
import sys
import os
from datetime import datetime
import click
import pytz

from config.settings import settings
from src.scraper import PIBScraper
from src.processor import ReleaseProcessor
from src.summarizer import ReleaseSummarizer
from src.digest import DigestGenerator
from src.scheduler import DigestScheduler

# Configure logging
def setup_logging():
    """Configure logging for the application."""
    settings.ensure_directories()
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    file_handler = logging.handlers.RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()


def generate_digest(date=None, use_openai=False):
    """Generate PIB digest for a specific date.
    
    Args:
        date: Date to generate digest for (YYYY-MM-DD format). If None, uses today.
        use_openai: Whether to use OpenAI for summarization.
    """
    try:
        # Parse date if provided
        if date:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            date_obj = settings.TIMEZONE.localize(date_obj)
        else:
            date_obj = datetime.now(settings.TIMEZONE)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Generating digest for {date_obj.strftime('%Y-%m-%d')}")
        logger.info(f"{'='*60}\n")
        
        # Initialize components
        scraper = PIBScraper()
        processor = ReleaseProcessor()
        summarizer = ReleaseSummarizer(use_openai=use_openai)
        digest_gen = DigestGenerator()
        
        try:
            # Step 1: Scrape releases
            logger.info("Step 1: Scraping PIB website...")
            raw_releases = scraper.scrape_daily_releases(date_obj)
            logger.info(f"Found {len(raw_releases)} releases on PIB website")
            
            # Step 2: Process and deduplicate
            logger.info("\nStep 2: Processing and deduplicating releases...")
            processed_releases = processor.process_releases(raw_releases)
            logger.info(f"After processing: {len(processed_releases)} unique releases")
            
            # Step 3: Summarize releases
            logger.info("\nStep 3: Summarizing releases...")
            summarized_releases = summarizer.summarize_releases(
                processed_releases,
                content_fetcher=scraper.get_release_full_content
            )
            logger.info(f"Summarized {len(summarized_releases)} releases")
            
            # Step 4: Generate digest
            logger.info("\nStep 4: Generating digest...")
            digest_content = digest_gen.generate_digest(summarized_releases, date_obj)
            
            # Step 5: Save digest
            logger.info("\nStep 5: Saving digest...")
            filepath = digest_gen.save_digest(digest_content, date_obj)
            logger.info(f"Digest saved to: {filepath}")
            
            logger.info(f"\n{'='*60}")
            logger.info("Digest generation completed successfully!")
            logger.info(f"{'='*60}\n")
            
            return filepath
        
        finally:
            scraper.close()
    
    except Exception as e:
        logger.error(f"Error generating digest: {e}", exc_info=True)
        raise


@click.group()
def cli():
    """PIB Daily Tracker - Monitor and digest PIB press releases."""
    pass


@cli.command()
@click.option('--date', default=None, help='Date in YYYY-MM-DD format (default: today)')
@click.option('--openai', is_flag=True, help='Use OpenAI for summarization')
def generate(date, openai):
    """Generate a digest for a specific date."""
    try:
        generate_digest(date=date, use_openai=openai)
    except Exception as e:
        logger.error(f"Failed to generate digest: {e}")
        sys.exit(1)


@cli.command()
@click.option('--time', default=None, help='Digest generation time (HH:MM format, default: 20:00)')
@click.option('--openai', is_flag=True, help='Use OpenAI for summarization')
def schedule(time, openai):
    """Start the scheduler for automatic digest generation."""
    try:
        logger.info("Starting PIB Daily Tracker scheduler...")
        logger.info(f"Digest time: {time or settings.DIGEST_TIME}")
        
        scheduler = DigestScheduler()
        scheduler.schedule_daily_digest(
            lambda: generate_digest(use_openai=openai),
            digest_time=time
        )
        
        next_run = scheduler.get_next_run()
        logger.info(f"Next digest generation scheduled for: {next_run}")
        
        scheduler.start()
        logger.info("Scheduler started. Press Ctrl+C to stop.")
        
        # Keep the scheduler running
        import time as time_module
        while True:
            time_module.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
        scheduler.stop()
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option('--days', default=7, help='Number of days to check (default: 7)')
def status(days):
    """Check status of recent digests."""
    try:
        import glob
        
        digests_dir = settings.OUTPUT_DIRECTORY
        if not os.path.exists(digests_dir):
            logger.info("No digests directory found")
            return
        
        digest_files = sorted(
            glob.glob(os.path.join(digests_dir, "*.md")),
            reverse=True
        )[:days]
        
        logger.info(f"\nRecent digests (last {days} days):\n")
        for filepath in digest_files:
            filename = os.path.basename(filepath)
            file_size = os.path.getsize(filepath)
            logger.info(f"  - {filename} ({file_size} bytes)")
        
        if not digest_files:
            logger.info("No digests found")
    
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
