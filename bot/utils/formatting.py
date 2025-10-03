"""
Text formatting utilities.
"""

def format_number(number: float, precision: int = 0) -> str:
    """Format number with appropriate suffixes (K, M, B)."""
    if number >= 1_000_000_000:
        return f"{number/1_000_000_000:.{precision}f}B"
    elif number >= 1_000_000:
        return f"{number/1_000_000:.{precision}f}M"
    elif number >= 1_000:
        return f"{number/1_000:.{precision}f}K"
    else:
        return f"{number:.{precision}f}"

def format_currency(amount: float, precision: int = 2) -> str:
    """Format currency amount."""
    return f"${format_number(amount, precision)}"

def format_percentage(value: float, precision: int = 1) -> str:
    """Format percentage value."""
    return f"{value:.{precision}f}%"

def format_time_ago(timestamp: float) -> str:
    """Format timestamp as time ago."""
    import time
    from datetime import datetime, timezone
    
    current_time = time.time()
    time_diff = current_time - timestamp
    
    if time_diff < 60:
        return f"{int(time_diff)}s ago"
    elif time_diff < 3600:
        return f"{int(time_diff/60)}m ago"
    elif time_diff < 86400:
        return f"{int(time_diff/3600)}h ago"
    else:
        return f"{int(time_diff/86400)}d ago"

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds}s"
    elif seconds < 86400:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        return f"{hours}h {remaining_minutes}m"
    else:
        days = seconds // 86400
        remaining_hours = (seconds % 86400) // 3600
        return f"{days}d {remaining_hours}h"

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def format_list(items: list, max_items: int = 10, separator: str = ", ") -> str:
    """Format list with maximum items."""
    if len(items) <= max_items:
        return separator.join(str(item) for item in items)
    else:
        visible_items = items[:max_items]
        return separator.join(str(item) for item in visible_items) + f" and {len(items) - max_items} more"




