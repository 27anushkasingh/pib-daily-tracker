"""Settings management for PIB Daily Tracker."""

import os
from datetime import datetime
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

class Settings:
    """Configuration settings for PIB tracker."""
    
    # Basic settings
    PROJECT_NAME = "PIB Daily Tracker"
    VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # Digest settings
    DIGEST_TIME = os.getenv("PIB_DIGEST_TIME", "20:00")
    BASE_URL = os.getenv("PIB_BASE_URL", "https://pib.gov.in")
    
    # Timezone
    TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "Asia/Kolkata"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/pib_tracker.log")
    
    # Request settings
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    CONNECTION_POOL_SIZE = int(os.getenv("CONNECTION_POOL_SIZE", "10"))
    
    # Browser settings
    HEADLESS_BROWSER = os.getenv("HEADLESS_BROWSER", "true").lower() == "true"
    BROWSER_TIMEOUT = int(os.getenv("BROWSER_TIMEOUT", "60"))
    
    # Cache settings
    USE_CACHE = os.getenv("USE_CACHE", "true").lower() == "true"
    CACHE_EXPIRY_HOURS = int(os.getenv("CACHE_EXPIRY_HOURS", "24"))
    CACHE_DIRECTORY = "data/cache"
    
    # Output settings
    OUTPUT_DIRECTORY = "data/daily_digests"
    
    # API keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Database (optional)
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    @staticmethod
    def get_current_time():
        """Get current time in configured timezone."""
        return datetime.now(Settings.TIMEZONE)
    
    @staticmethod
    def ensure_directories():
        """Create necessary directories if they don't exist."""
        directories = [
            Settings.OUTPUT_DIRECTORY,
            Settings.CACHE_DIRECTORY,
            os.path.dirname(Settings.LOG_FILE)
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

# Initialize settings
settings = Settings()
