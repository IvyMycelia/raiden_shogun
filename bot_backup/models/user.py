"""
User data model and related classes.
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    """Represents a Discord user and their registered nation."""
    
    # Discord info
    discord_id: int
    discord_name: str
    
    # Nation info
    nation_id: Optional[int]
    nation_name: Optional[str]
    
    # Registration info
    registered_at: datetime
    last_updated: datetime
    
    # Preferences
    notifications_enabled: bool
    auto_update_cache: bool
    
    def __post_init__(self):
        """Validate user data after initialization."""
        if self.discord_id <= 0:
            raise ValueError("Discord ID must be positive")
        if self.nation_id is not None and self.nation_id <= 0:
            raise ValueError("Nation ID must be positive")
    
    @property
    def is_registered(self) -> bool:
        """Check if user has registered a nation."""
        return self.nation_id is not None
    
    @property
    def registration_age_days(self) -> int:
        """Get registration age in days."""
        return (datetime.now() - self.registered_at).days
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary."""
        return {
            'discord_id': self.discord_id,
            'discord_name': self.discord_name,
            'nation_id': self.nation_id,
            'nation_name': self.nation_name,
            'registered_at': self.registered_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'notifications_enabled': self.notifications_enabled,
            'auto_update_cache': self.auto_update_cache
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create user from dictionary."""
        return cls(
            discord_id=data['discord_id'],
            discord_name=data['discord_name'],
            nation_id=data.get('nation_id'),
            nation_name=data.get('nation_name'),
            registered_at=datetime.fromisoformat(data.get('registered_at', '1970-01-01T00:00:00+00:00')),
            last_updated=datetime.fromisoformat(data.get('last_updated', '1970-01-01T00:00:00+00:00')),
            notifications_enabled=data.get('notifications_enabled', True),
            auto_update_cache=data.get('auto_update_cache', False)
        )
    
    def update_nation(self, nation_id: int, nation_name: str) -> None:
        """Update user's registered nation."""
        self.nation_id = nation_id
        self.nation_name = nation_name
        self.last_updated = datetime.now()
    
    def unregister(self) -> None:
        """Unregister user's nation."""
        self.nation_id = None
        self.nation_name = None
        self.last_updated = datetime.now()
