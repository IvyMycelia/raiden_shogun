"""
User data model.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class User:
    """User data model."""
    discord_id: int
    discord_name: str
    nation_id: int
    nation_name: str
    registered_at: datetime
    last_active: datetime
    preferences: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create User from dictionary."""
        # Parse timestamps
        registered_str = data.get('registered_at', '1970-01-01T00:00:00+00:00')
        last_active_str = data.get('last_active', '1970-01-01T00:00:00+00:00')
        
        try:
            registered_at = datetime.fromisoformat(registered_str.replace('Z', '+00:00'))
        except ValueError:
            registered_at = datetime.fromisoformat('1970-01-01T00:00:00+00:00')
        
        try:
            last_active = datetime.fromisoformat(last_active_str.replace('Z', '+00:00'))
        except ValueError:
            last_active = datetime.fromisoformat('1970-01-01T00:00:00+00:00')
        
        return cls(
            discord_id=int(data.get('discord_id', 0)),
            discord_name=data.get('discord_name', 'Unknown'),
            nation_id=int(data.get('nation_id', 0)),
            nation_name=data.get('nation_name', 'Unknown'),
            registered_at=registered_at,
            last_active=last_active,
            preferences=data.get('preferences', {})
        )
    
    def is_active(self) -> bool:
        """Check if user is active (logged in within last 24 hours)."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return (now - self.last_active).total_seconds() < 86400  # 24 hours
    
    def get_nation_url(self) -> str:
        """Get Politics and War nation URL."""
        return f"https://politicsandwar.com/nation/id={self.nation_id}"
    
    def get_discord_mention(self) -> str:
        """Get Discord mention string."""
        return f"<@{self.discord_id}>"




