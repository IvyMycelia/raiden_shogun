import os
from typing import Optional

class Config:
    """Configuration class for the bot."""
    
    def __init__(self):
        self.BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
        self.API_KEY: str = os.getenv("API_KEY", "")
        self.ALLIANCE_ID: str = os.getenv("ALLIANCE_ID", "")
        
        # Discord channel IDs
        self.SUGGESTIONS_CHANNEL_ID: int = int(os.getenv("SUGGESTIONS_CHANNEL_ID", "0"))
        self.BUG_REPORTS_CHANNEL_ID: int = int(os.getenv("BUG_REPORTS_CHANNEL_ID", "0"))
        self.DEVELOPER_ROLE_ID: int = int(os.getenv("DEVELOPER_ROLE_ID", "0"))
        self.IVY_ID: int = int(os.getenv("IVY_ID", "860564164828725299"))
        
        # Validate required environment variables
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate that all required configuration values are set."""
        required_vars = {
            "BOT_TOKEN": self.BOT_TOKEN,
            "API_KEY": self.API_KEY,
            "ALLIANCE_ID": self.ALLIANCE_ID,
        }
        
        missing = [var for var, value in required_vars.items() if not value]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

# Create a global config instance
config = Config() 