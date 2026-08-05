"""Task scheduling for PIB Daily Tracker."""

import logging
from datetime import datetime, time
from typing import Callable
import schedule
import threading
import pytz

from config.settings import settings

logger = logging.getLogger(__name__)


class DigestScheduler:
    """Scheduler for daily digest generation."""
    
    def __init__(self):
        """Initialize scheduler."""
        self.schedule = schedule.Scheduler()
        self.is_running = False
        self.thread = None
    
    def schedule_daily_digest(self, task_func: Callable, digest_time: str = None):
        """Schedule daily digest generation.
        
        Args:
            task_func: Function to call for digest generation.
            digest_time: Time in HH:MM format (e.g., "20:00"). If None, uses configured time.
        """
        if digest_time is None:
            digest_time = settings.DIGEST_TIME
        
        logger.info(f"Scheduling daily digest at {digest_time}")
        self.schedule.every().day.at(digest_time).do(self._run_task, task_func)
    
    def _run_task(self, task_func: Callable):
        """Run a scheduled task with error handling.
        
        Args:
            task_func: Function to execute.
        """
        try:
            logger.info("Starting scheduled digest generation")
            task_func()
            logger.info("Scheduled digest generation completed successfully")
        except Exception as e:
            logger.error(f"Error in scheduled task: {e}", exc_info=True)
    
    def start(self):
        """Start the scheduler in a background thread."""
        if self.is_running:
            logger.warning("Scheduler already running")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("Scheduler started")
    
    def _run_scheduler(self):
        """Run scheduler loop."""
        while self.is_running:
            try:
                self.schedule.run_pending()
                # Check every minute
                self.schedule.idle_seconds
                import time as time_module
                time_module.sleep(60)
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
    
    def stop(self):
        """Stop the scheduler."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Scheduler stopped")
    
    def get_next_run(self) -> datetime:
        """Get time of next scheduled run.
        
        Returns:
            Datetime of next scheduled run.
        """
        if not self.schedule.jobs:
            return None
        
        next_job = min(self.schedule.jobs, key=lambda j: j.next_run)
        return next_job.next_run
    
    def get_jobs(self):
        """Get list of scheduled jobs.
        
        Returns:
            List of scheduled jobs.
        """
        return self.schedule.jobs
