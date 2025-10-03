"""
Base model classes and common functionality.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime


class BaseModel(ABC):
    """Base class for all data models."""
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """Create model from dictionary."""
        pass
    
    def __str__(self) -> str:
        """String representation of the model."""
        return f"{self.__class__.__name__}({self.to_dict()})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the model."""
        return f"{self.__class__.__name__}({self.to_dict()})"


class TimestampedModel(BaseModel):
    """Base class for models with timestamps."""
    
    created_at: datetime
    updated_at: datetime
    
    def __post_init__(self):
        """Set timestamps after initialization."""
        now = datetime.now()
        if not hasattr(self, 'created_at') or self.created_at is None:
            self.created_at = now
        if not hasattr(self, 'updated_at') or self.updated_at is None:
            self.updated_at = now
    
    def touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()


class ValidatedModel(BaseModel):
    """Base class for models with validation."""
    
    def validate(self) -> None:
        """Validate the model data."""
        # Override in subclasses to add specific validation
        pass
    
    def is_valid(self) -> bool:
        """Check if the model is valid."""
        try:
            self.validate()
            return True
        except Exception:
            return False


class CacheableModel(BaseModel):
    """Base class for models that can be cached."""
    
    cache_key: str
    cache_ttl: int = 3600  # 1 hour default
    
    def get_cache_key(self) -> str:
        """Get the cache key for this model."""
        return self.cache_key
    
    def get_cache_ttl(self) -> int:
        """Get the cache TTL for this model."""
        return self.cache_ttl
