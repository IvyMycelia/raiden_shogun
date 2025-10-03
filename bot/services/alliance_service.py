"""
Alliance service for business logic.
"""

from typing import Dict, List, Optional, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.alliance import Alliance
from api.politics_war_api import api
from config.constants import GameConstants

class AllianceService:
    """Service for alliance-related business logic."""
    
    def __init__(self):
        self.api = api
    
    async def get_alliance(self, alliance_id: int) -> Optional[Alliance]:
        """Get alliance data by ID."""
        data = await self.api.get_alliance_data(alliance_id, "alliance_scope")
        if data:
            return Alliance.from_dict(data)
        return None
    
    async def get_alliance_members(self, alliance_id: int) -> Optional[List[Dict]]:
        """Get alliance members."""
        return await self.api.get_alliance_members(alliance_id, "alliance_scope")
    
    def audit_activity(self, members: List[Dict]) -> List[Dict]:
        """Audit member activity."""
        violations = []
        for member in members:
            if member.get("alliance_position", "") != "APPLICANT":
                # Check if member has been inactive for 24+ hours
                last_active_str = member.get("last_active", "1970-01-01T00:00:00+00:00")
                try:
                    from datetime import datetime, timezone
                    last_active = datetime.fromisoformat(last_active_str.replace("Z", "+00:00"))
                    current_time = datetime.now(timezone.utc)
                    
                    if (current_time - last_active).total_seconds() >= GameConstants.ACTIVITY_THRESHOLD:
                        violations.append({
                            'member': member,
                            'last_active': last_active,
                            'days_inactive': (current_time - last_active).days
                        })
                except ValueError:
                    violations.append({
                        'member': member,
                        'error': 'Invalid date format'
                    })
        return violations
    
    def audit_spies(self, members: List[Dict]) -> List[Dict]:
        """Audit member spy counts."""
        violations = []
        for member in members:
            if member.get("alliance_position", "") != "APPLICANT":
                spies = member.get("spies", 0)
                projects = member.get("projects", 0)
                
                # Check if member has Intelligence Agency project
                has_intel_agency = any(
                    project.get('name') == 'Intelligence Agency' 
                    for project in member.get('projects_list', [])
                )
                
                required_spies = GameConstants.SPY_REQUIREMENTS["with_intelligence_agency"] if has_intel_agency else GameConstants.SPY_REQUIREMENTS["base"]
                
                if spies < required_spies:
                    violations.append({
                        'member': member,
                        'current_spies': spies,
                        'required_spies': required_spies,
                        'has_intel_agency': has_intel_agency
                    })
        return violations
    
    def audit_projects(self, members: List[Dict]) -> List[Dict]:
        """Audit member project counts."""
        violations = []
        for member in members:
            if member.get("alliance_position", "") != "APPLICANT":
                projects = member.get("projects", 0)
                if projects < GameConstants.MIN_PROJECTS:
                    violations.append({
                        'member': member,
                        'current_projects': projects,
                        'required_projects': GameConstants.MIN_PROJECTS
                    })
        return violations
    
    def audit_color_bloc(self, members: List[Dict], alliance_color: str) -> List[Dict]:
        """Audit member color bloc compliance."""
        violations = []
        for member in members:
            if member.get("alliance_position", "") != "APPLICANT":
                member_color = member.get('color', 'gray')
                is_beige = member_color.lower() == 'beige'
                
                if not is_beige and member_color.lower() != alliance_color.lower():
                    violations.append({
                        'member': member,
                        'current_color': member_color,
                        'alliance_color': alliance_color
                    })
        return violations
    
    def audit_deposits(self, members: List[Dict]) -> List[Dict]:
        """Audit member resource deposits."""
        violations = []
        for member in members:
            if member.get("alliance_position", "") != "APPLICANT":
                excess_resources = []
                for resource, threshold in GameConstants.DEPOSIT_THRESHOLDS.items():
                    current_amount = member.get(resource, 0)
                    if current_amount > threshold:
                        excess_resources.append({
                            'resource': resource,
                            'current': current_amount,
                            'threshold': threshold
                        })
                
                if excess_resources:
                    violations.append({
                        'member': member,
                        'excess_resources': excess_resources
                    })
        return violations
    
    def audit_warchest(self, members: List[Dict], max_cities: int = 100) -> List[Dict]:
        """Audit member warchest requirements."""
        violations = []
        for member in members:
            if member.get("alliance_position", "") != "APPLICANT":
                cities = member.get("cities", 0)
                if cities <= max_cities and cities > 0:
                    # Use simple city-based warchest formula
                    aluminum_required = cities * 500
                    steel_required = cities * 1000
                    gasoline_required = cities * 600
                    munitions_required = cities * 600
                    
                    current_aluminum = member.get("aluminum", 0)
                    current_steel = member.get("steel", 0)
                    current_gasoline = member.get("gasoline", 0)
                    current_munitions = member.get("munitions", 0)
                    
                    # Check if any resource is below 25% of required
                    deficits = []
                    if current_aluminum < aluminum_required * GameConstants.WARCHEST_DEFICIT_THRESHOLD:
                        deficits.append(f"Aluminum: {current_aluminum:,}/{aluminum_required:,}")
                    if current_steel < steel_required * GameConstants.WARCHEST_DEFICIT_THRESHOLD:
                        deficits.append(f"Steel: {current_steel:,}/{steel_required:,}")
                    if current_gasoline < gasoline_required * GameConstants.WARCHEST_DEFICIT_THRESHOLD:
                        deficits.append(f"Gasoline: {current_gasoline:,}/{gasoline_required:,}")
                    if current_munitions < munitions_required * GameConstants.WARCHEST_DEFICIT_THRESHOLD:
                        deficits.append(f"Munitions: {current_munitions:,}/{munitions_required:,}")
                    
                    if deficits:
                        violations.append({
                            'member': member,
                            'deficits': deficits,
                            'cities': cities
                        })
        return violations
    
    def audit_military(self, members: List[Dict]) -> List[Dict]:
        """Audit member military capacity and usage."""
        violations = []
        for member in members:
            if member.get("alliance_position", "") != "APPLICANT":
                # Calculate military capacity from cities (simplified)
                cities = member.get("cities", 0)
                if cities > 0:
                    # Estimate capacity based on city count (simplified)
                    estimated_capacity = {
                        "soldiers": cities * 15000,  # 5 barracks * 3000 per city
                        "tanks": cities * 500,       # 2 factories * 250 per city
                        "aircraft": cities * 75,     # 5 hangars * 15 per city
                        "ships": cities * 10         # 2 drydocks * 5 per city
                    }
                    
                    current_military = {
                        "soldiers": member.get("soldiers", 0),
                        "tanks": member.get("tanks", 0),
                        "aircraft": member.get("aircraft", 0),
                        "ships": member.get("ships", 0)
                    }
                    
                    usage_issues = []
                    for unit_type, capacity in estimated_capacity.items():
                        current = current_military[unit_type]
                        if capacity > 0:
                            usage_percentage = current / capacity
                            if usage_percentage > GameConstants.MILITARY_HIGH_USAGE:
                                usage_issues.append(f"{unit_type.title()}: {usage_percentage:.1%} (High usage)")
                            elif usage_percentage < GameConstants.MILITARY_LOW_USAGE:
                                usage_issues.append(f"{unit_type.title()}: {usage_percentage:.1%} (Low usage)")
                    
                    if usage_issues:
                        violations.append({
                            'member': member,
                            'usage_issues': usage_issues,
                            'capacity': estimated_capacity,
                            'current': current_military
                        })
        return violations
    
    def audit_mmr(self, members: List[Dict]) -> List[Dict]:
        """Audit member MMR (Military Manufacturing Ratio) compliance."""
        violations = []
        for member in members:
            if member.get("alliance_position", "") != "APPLICANT":
                cities = member.get("cities", 0)
                if cities > 0:
                    # Determine role based on city count
                    role = "Whale" if cities >= 15 else "Raider"
                    requirements = GameConstants.MMR_REQUIREMENTS[role]
                    
                    # Get building counts (simplified - would need city data in real implementation)
                    # For now, we'll use estimated values based on city count
                    estimated_buildings = {
                        "barracks": cities * 2,  # Estimated
                        "factory": cities * 1,   # Estimated
                        "hangar": cities * 3,    # Estimated
                        "drydock": cities * 0    # Estimated
                    }
                    
                    missing_buildings = []
                    for building, required in requirements.items():
                        current = estimated_buildings.get(building, 0)
                        if current < required:
                            missing_buildings.append(f"{building.title()}: {current}/{required}")
                    
                    if missing_buildings:
                        violations.append({
                            'member': member,
                            'role': role,
                            'missing_buildings': missing_buildings,
                            'cities': cities
                        })
        return violations
