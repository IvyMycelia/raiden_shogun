"""
Service for audit-related operations.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import time

from models.alliance import Alliance, AllianceMember
from models.nation import Nation
from services.nation_service import NationService
from services.cache_service import CacheService
from config.constants import GameConstants


class AuditService:
    """Service for audit-related business logic."""
    
    def __init__(self, nation_service: NationService, cache_service: CacheService):
        self.nation_service = nation_service
        self.cache_service = cache_service
        
        # MMR requirements for different roles
        self.mmr_requirements = {
            "Raider": {
                "barracks": 5,
                "factory": 0,
                "hangar": 5,
                "drydock": 0
            },
            "Whale": {
                "barracks": 0,
                "factory": 2,
                "hangar": 5,
                "drydock": 0
            }
        }
        
        # Resource thresholds for deposit excess check (in thousands)
        self.deposit_thresholds = {
            "money": 100000,  # $100M
            "coal": 1000,     # 1M coal
            "oil": 1000,      # 1M oil
            "uranium": 100,   # 100k uranium
            "iron": 1000,     # 1M iron
            "bauxite": 1000,  # 1M bauxite
            "lead": 1000,     # 1M lead
            "gasoline": 100,  # 100k gasoline
            "munitions": 100, # 100k munitions
            "steel": 100,     # 100k steel
            "aluminum": 100,  # 100k aluminum
            "food": 1000,     # 1M food
        }
    
    async def audit_alliance_members(
        self, 
        alliance_id: int, 
        audit_type: str, 
        cities_limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Audit alliance members based on different criteria."""
        # Get alliance members
        members_data = await self.cache_service.get_alliance_members(alliance_id)
        if not members_data:
            return []
        
        audit_results = []
        current_time = time.time()
        one_day_seconds = 86400
        
        # Pre-fetch alliance color for bloc audit
        alliance_color = None
        if audit_type == "bloc":
            alliance_data = await self.nation_service.api_client.get_alliance_data(alliance_id)
            if alliance_data:
                alliance_color = alliance_data.get('color', 'gray')
            else:
                # Fallback: use the first member's color as reference
                alliance_color = members_data[0].get('color', 'gray') if members_data else 'gray'
        
        for member_data in members_data:
            if member_data.get("alliance_position", "") != "APPLICANT":
                nation_id = member_data.get('id')
                if not nation_id:
                    continue
                
                # Get Discord username from registrations
                discord_username = await self._get_discord_username(nation_id)
                
                if audit_type == "activity":
                    result = await self._audit_activity(member_data, discord_username, current_time, one_day_seconds)
                    if result:
                        audit_results.append(result)
                
                elif audit_type == "warchest":
                    if cities_limit >= len(member_data.get("cities", [])):
                        result = await self._audit_warchest(member_data, discord_username)
                        if result:
                            audit_results.append(result)
                
                elif audit_type == "spies":
                    result = await self._audit_spies(member_data, discord_username, nation_id)
                    if result:
                        audit_results.append(result)
                
                elif audit_type == "projects":
                    result = await self._audit_projects(member_data, discord_username)
                    if result:
                        audit_results.append(result)
                
                elif audit_type == "bloc":
                    result = await self._audit_bloc(member_data, discord_username, alliance_color)
                    if result:
                        audit_results.append(result)
                
                elif audit_type == "deposit":
                    if cities_limit >= len(member_data.get("cities", [])):
                        result = await self._audit_deposit(member_data, discord_username)
                        if result:
                            audit_results.append(result)
                
                elif audit_type == "mmr":
                    result = await self._audit_mmr(member_data, discord_username, nation_id)
                    if result:
                        audit_results.append(result)
        
        return audit_results
    
    async def _get_discord_username(self, nation_id: str) -> str:
        """Get Discord username from registered nations data."""
        # This would load from registrations.json
        # For now, return a placeholder
        return 'N/A'
    
    async def _audit_activity(
        self, 
        member: Dict[str, Any], 
        discord_username: str, 
        current_time: float, 
        one_day_seconds: int
    ) -> Optional[Dict[str, Any]]:
        """Audit member activity."""
        last_active_str = member.get("last_active", "1970-01-01T00:00:00+00:00")
        try:
            last_active_dt = datetime.fromisoformat(last_active_str.replace("Z", "+00:00"))
            last_active_unix = last_active_dt.timestamp()
            
            if (current_time - last_active_unix) >= one_day_seconds:
                return {
                    'type': 'activity',
                    'nation_id': member['id'],
                    'nation_name': member['nation_name'],
                    'leader_name': member['leader_name'],
                    'discord_username': discord_username,
                    'last_active': last_active_unix,
                    'defensive_wars': member['defensive_wars_count']
                }
        except ValueError:
            return {
                'type': 'activity',
                'nation_id': member['id'],
                'nation_name': member['nation_name'],
                'leader_name': member['leader_name'],
                'discord_username': discord_username,
                'error': 'Error parsing last_active'
            }
        
        return None
    
    async def _audit_warchest(self, member: Dict[str, Any], discord_username: str) -> Optional[Dict[str, Any]]:
        """Audit member warchest."""
        # This would integrate with the existing calculate module
        # For now, return a simplified check
        money = member.get('money', 0)
        cities = len(member.get('cities', []))
        
        # Simple warchest calculation
        required_warchest = cities * 1000 * 5  # 5 days of city upkeep
        
        if money < required_warchest:
            return {
                'type': 'warchest',
                'nation_id': member['id'],
                'nation_name': member['nation_name'],
                'leader_name': member['leader_name'],
                'discord_username': discord_username,
                'current_money': money,
                'required_warchest': required_warchest,
                'deficit': required_warchest - money
            }
        
        return None
    
    async def _audit_spies(self, member: Dict[str, Any], discord_username: str, nation_id: str) -> Optional[Dict[str, Any]]:
        """Audit member spies."""
        # Get nation data to check for Intelligence Agency project
        nation_data = await self.nation_service.api_client.get_nation_data(int(nation_id))
        if not nation_data:
            return None
        
        # Check if nation has Intelligence Agency project
        has_intel_agency = any(
            project.get('name') == 'Intelligence Agency' 
            for project in nation_data.get('projects', [])
        )
        required_spies = 60 if has_intel_agency else 50
        
        # Check if nation has enough spies
        current_spies = member.get("spies", 0)
        if current_spies < required_spies:
            return {
                'type': 'spies',
                'nation_id': member['id'],
                'nation_name': member['nation_name'],
                'leader_name': member['leader_name'],
                'discord_username': discord_username,
                'current_spies': current_spies,
                'required_spies': required_spies,
                'has_intel_agency': has_intel_agency
            }
        
        return None
    
    async def _audit_projects(self, member: Dict[str, Any], discord_username: str) -> Optional[Dict[str, Any]]:
        """Audit member projects."""
        current_projects = member.get("projects", 0)
        if current_projects < 10:
            return {
                'type': 'projects',
                'nation_id': member['id'],
                'nation_name': member['nation_name'],
                'leader_name': member['leader_name'],
                'discord_username': discord_username,
                'current_projects': current_projects,
                'required_projects': 10
            }
        
        return None
    
    async def _audit_bloc(
        self, 
        member: Dict[str, Any], 
        discord_username: str, 
        alliance_color: str
    ) -> Optional[Dict[str, Any]]:
        """Audit member color bloc."""
        member_color = member.get('color', 'gray')
        is_beige = member_color.lower() == 'beige'
        
        # Check if member's color matches alliance color
        if not is_beige and member_color.lower() != alliance_color.lower():
            return {
                'type': 'bloc',
                'nation_id': member['id'],
                'nation_name': member['nation_name'],
                'leader_name': member['leader_name'],
                'discord_username': discord_username,
                'current_color': member_color,
                'alliance_color': alliance_color
            }
        
        return None
    
    async def _audit_deposit(self, member: Dict[str, Any], discord_username: str) -> Optional[Dict[str, Any]]:
        """Audit member resource deposits."""
        excess_resources = []
        for resource, threshold in self.deposit_thresholds.items():
            current_amount = member.get(resource, 0)
            if current_amount > threshold:
                excess_resources.append({
                    'resource': resource,
                    'current': current_amount,
                    'threshold': threshold
                })
        
        if excess_resources:
            return {
                'type': 'deposit',
                'nation_id': member['id'],
                'nation_name': member['nation_name'],
                'leader_name': member['leader_name'],
                'discord_username': discord_username,
                'excess_resources': excess_resources
            }
        
        return None
    
    async def _audit_mmr(self, member: Dict[str, Any], discord_username: str, nation_id: str) -> Optional[Dict[str, Any]]:
        """Audit member MMR."""
        # Get city data for MMR check
        nation_data = await self.nation_service.api_client.get_nation_data(int(nation_id))
        if not nation_data:
            return None
        
        cities_data = nation_data.get("cities", [])
        if not cities_data:
            return None
        
        role = "Whale" if len(cities_data) >= 15 else "Raider"
        mmr_violations = []
        
        for city in cities_data:
            city_name = city.get("name", "Unknown")
            missing = []
            
            requirements = self.mmr_requirements[role]
            for building, required in requirements.items():
                current = city.get(building, 0)
                if current < required:
                    missing.append(f"{building}: {current}/{required}")
            
            if missing:
                mmr_violations.append({
                    'city_name': city_name,
                    'missing': missing
                })
        
        if mmr_violations:
            return {
                'type': 'mmr',
                'nation_id': member['id'],
                'nation_name': member['nation_name'],
                'leader_name': member['leader_name'],
                'discord_username': discord_username,
                'role': role,
                'violations': mmr_violations
            }
        
        return None
