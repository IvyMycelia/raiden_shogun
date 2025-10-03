"""
Configuration settings for the Raiden Shogun bot.
"""
import os
from typing import Optional


class Settings:
    """Bot configuration settings."""
    
    # Discord settings
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    GUILD_ID: int = int(os.getenv("GUILD_ID", "1279582264568713308"))
    
    # Politics and War API settings
    API_KEY: str = os.getenv("API_KEY", "")
    API_BASE_URL: str = "https://api.politicsandwar.com"
    API_TIMEOUT: int = 30
    
    # Alliance settings
    ALLIANCE_ID: str = os.getenv("ALLIANCE_ID", "")
    
    # Cache settings
    CACHE_TTL: int = 300  # 5 minutes
    CACHE_UPDATE_INTERVAL: int = 300  # 5 minutes
    MAX_CACHE_SIZE: int = 1000
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 25
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = "bot.log"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///bot.db")
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        missing = []
        
        if not cls.BOT_TOKEN:
            missing.append("BOT_TOKEN")
        if not cls.API_KEY:
            missing.append("API_KEY")
        if not cls.ALLIANCE_ID:
            missing.append("ALLIANCE_ID")
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    @classmethod
    def get_alliance_id_int(cls) -> int:
        """Get alliance ID as integer."""
        return int(cls.ALLIANCE_ID)


# Global settings instance
settings = Settings()
