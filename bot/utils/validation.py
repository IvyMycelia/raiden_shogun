"""
Input validation utilities.
"""

import re
from typing import Any, Optional

def validate_nation_id(nation_id: Any) -> Optional[int]:
    """Validate and convert nation ID to integer."""
    try:
        nation_id_int = int(nation_id)
        if nation_id_int <= 0:
            return None
        return nation_id_int
    except (ValueError, TypeError):
        return None

def validate_user_input(text: str, max_length: int = 1000) -> bool:
    """Validate user input text."""
    if not text or not isinstance(text, str):
        return False
    
    if len(text) > max_length:
        return False
    
    # Check for potentially harmful content
    dangerous_patterns = [
        r'<script.*?>.*?</script>',
        r'javascript:',
        r'data:',
        r'vbscript:',
        r'onload=',
        r'onerror=',
        r'onclick='
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False
    
    return True

def validate_discord_id(discord_id: Any) -> Optional[int]:
    """Validate Discord ID."""
    try:
        discord_id_int = int(discord_id)
        if discord_id_int <= 0:
            return None
        return discord_id_int
    except (ValueError, TypeError):
        return None

def validate_alliance_id(alliance_id: Any) -> Optional[int]:
    """Validate alliance ID."""
    try:
        alliance_id_int = int(alliance_id)
        if alliance_id_int <= 0:
            return None
        return alliance_id_int
    except (ValueError, TypeError):
        return None

def validate_war_id(war_id: Any) -> Optional[int]:
    """Validate war ID."""
    try:
        war_id_int = int(war_id)
        if war_id_int <= 0:
            return None
        return war_id_int
    except (ValueError, TypeError):
        return None

def validate_score_range(min_score: float, max_score: float) -> bool:
    """Validate score range."""
    if min_score < 0 or max_score < 0:
        return False
    
    if min_score >= max_score:
        return False
    
    # Reasonable score limits
    if min_score > 100000 or max_score > 100000:
        return False
    
    return True

def validate_city_count(city_count: int) -> bool:
    """Validate city count."""
    return 0 <= city_count <= 50  # Reasonable city limits

def validate_military_units(units: dict) -> bool:
    """Validate military unit counts."""
    for unit_type, count in units.items():
        if not isinstance(count, int) or count < 0:
            return False
        
        # Reasonable unit limits
        if count > 1000000:  # 1M units max
            return False
    
    return True

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations."""
    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'\.\.+', '.', filename)  # Remove multiple dots
    filename = filename.strip('. ')  # Remove leading/trailing dots and spaces
    
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename or "unnamed"




