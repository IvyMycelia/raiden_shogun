"""
Alliance data model.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class Alliance:
    """Alliance data model."""
    id: int
    name: str
    acronym: str
    color: str
    score: float
    flag: str
    members: List[Dict[str, Any]]
    bank: Dict[str, float]
    date: datetime
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Alliance':
        """Create Alliance from dictionary."""
        # Parse date timestamp
        date_str = data.get('date', '1970-01-01T00:00:00+00:00')
        try:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            date = datetime.fromisoformat('1970-01-01T00:00:00+00:00')
        
        return cls(
            id=data.get('id', 0),
            name=data.get('name', 'Unknown'),
            acronym=data.get('acronym', 'UNK'),
            color=data.get('color', 'gray'),
            score=float(data.get('score', 0)),
            flag=data.get('flag', ''),
            members=data.get('members', []),
            bank=data.get('bank', {}),
            date=date
        )
    
    def get_member_count(self) -> int:
        """Get total member count."""
        return len(self.members)
    
    def get_members_by_position(self, position: str) -> List[Dict[str, Any]]:
        """Get members by alliance position."""
        return [member for member in self.members if member.get('alliance_position') == position]
    
    def get_applicants(self) -> List[Dict[str, Any]]:
        """Get applicant members."""
        return self.get_members_by_position('APPLICANT')
    
    def get_members(self) -> List[Dict[str, Any]]:
        """Get non-applicant members."""
        return [member for member in self.members if member.get('alliance_position') != 'APPLICANT']
    
    def get_member_by_id(self, nation_id: int) -> Optional[Dict[str, Any]]:
        """Get member by nation ID."""
        for member in self.members:
            if int(member.get('id', 0)) == nation_id:
                return member
        return None
    
    def get_total_score(self) -> float:
        """Get total alliance score."""
        return sum(float(member.get('score', 0)) for member in self.get_members())
    
    def get_average_score(self) -> float:
        """Get average member score."""
        members = self.get_members()
        if not members:
            return 0.0
        return self.get_total_score() / len(members)
    
    def get_bank_value(self) -> float:
        """Get total bank value in money."""
        return float(self.bank.get('money', 0))
    
    def get_bank_resources(self) -> Dict[str, float]:
        """Get bank resources."""
        return {
            'money': float(self.bank.get('money', 0)),
            'coal': float(self.bank.get('coal', 0)),
            'oil': float(self.bank.get('oil', 0)),
            'uranium': float(self.bank.get('uranium', 0)),
            'iron': float(self.bank.get('iron', 0)),
            'bauxite': float(self.bank.get('bauxite', 0)),
            'lead': float(self.bank.get('lead', 0)),
            'gasoline': float(self.bank.get('gasoline', 0)),
            'munitions': float(self.bank.get('munitions', 0)),
            'steel': float(self.bank.get('steel', 0)),
            'aluminum': float(self.bank.get('aluminum', 0)),
            'food': float(self.bank.get('food', 0))
        }




