"""
Alliance data model and related classes.
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Alliance:
    """Represents an alliance in Politics and War."""
    
    # Basic info
    alliance_id: int
    alliance_name: str
    acronym: str
    color: str
    flag_url: str
    
    # Stats
    score: float
    member_count: int
    rank: int
    
    # Members
    members: List[Dict[str, Any]]
    
    def __post_init__(self):
        """Validate alliance data after initialization."""
        if self.alliance_id <= 0:
            raise ValueError("Alliance ID must be positive")
        if self.score < 0:
            raise ValueError("Score cannot be negative")
        if self.member_count < 0:
            raise ValueError("Member count cannot be negative")
    
    @property
    def is_top_alliance(self) -> bool:
        """Check if alliance is in top 60 (rank <= 60)."""
        return self.rank <= 60
    
    @property
    def average_score(self) -> float:
        """Calculate average score of alliance members."""
        if not self.members:
            return 0.0
        total_score = sum(member.get('score', 0) for member in self.members)
        return total_score / len(self.members)
    
    def get_members_by_position(self, position: str) -> List[Dict[str, Any]]:
        """Get members by alliance position."""
        return [member for member in self.members if member.get('alliance_position') == position]
    
    def get_members_in_range(self, min_score: float, max_score: float) -> List[Dict[str, Any]]:
        """Get members within score range."""
        return [
            member for member in self.members 
            if min_score <= member.get('score', 0) <= max_score
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alliance to dictionary."""
        return {
            'alliance_id': self.alliance_id,
            'alliance_name': self.alliance_name,
            'acronym': self.acronym,
            'color': self.color,
            'flag_url': self.flag_url,
            'score': self.score,
            'member_count': self.member_count,
            'rank': self.rank,
            'members': self.members
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Alliance':
        """Create alliance from dictionary."""
        return cls(
            alliance_id=data['alliance_id'],
            alliance_name=data['alliance_name'],
            acronym=data.get('acronym', ''),
            color=data.get('color', 'gray'),
            flag_url=data.get('flag_url', ''),
            score=data['score'],
            member_count=data.get('member_count', 0),
            rank=data.get('rank', 999),
            members=data.get('members', [])
        )


@dataclass
class AllianceMember:
    """Represents an alliance member."""
    
    nation_id: int
    nation_name: str
    leader_name: str
    alliance_position: str
    score: float
    cities: int
    color: str
    last_active: datetime
    
    def __post_init__(self):
        """Validate member data after initialization."""
        if self.nation_id <= 0:
            raise ValueError("Nation ID must be positive")
        if self.score < 0:
            raise ValueError("Score cannot be negative")
        if self.cities < 0:
            raise ValueError("Cities cannot be negative")
    
    @property
    def is_leader(self) -> bool:
        """Check if member is alliance leader."""
        return self.alliance_position.upper() == 'LEADER'
    
    @property
    def is_officer(self) -> bool:
        """Check if member is alliance officer."""
        return self.alliance_position.upper() in ['LEADER', 'HEIR', 'OFFICER']
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert member to dictionary."""
        return {
            'nation_id': self.nation_id,
            'nation_name': self.nation_name,
            'leader_name': self.leader_name,
            'alliance_position': self.alliance_position,
            'score': self.score,
            'cities': self.cities,
            'color': self.color,
            'last_active': self.last_active.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AllianceMember':
        """Create member from dictionary."""
        return cls(
            nation_id=data['nation_id'],
            nation_name=data['nation_name'],
            leader_name=data['leader_name'],
            alliance_position=data.get('alliance_position', 'MEMBER'),
            score=data['score'],
            cities=data.get('cities', 0),
            color=data.get('color', 'gray'),
            last_active=datetime.fromisoformat(data.get('last_active', '1970-01-01T00:00:00+00:00'))
        )
