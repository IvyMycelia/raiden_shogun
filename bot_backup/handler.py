import datetime
import sys
import os
import time
import logging
from typing import Optional, Any

class LogColors:
    """Color codes for console output."""
    RESET = '\033[0m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    
    @classmethod
    def get_color(cls, level: str) -> str:
        """Get color code based on log level."""
        colors = {
            'DEBUG': cls.CYAN,
            'INFO': cls.WHITE,
            'SUCCESS': cls.GREEN,
            'WARNING': cls.YELLOW,
            'ERROR': cls.RED,
            'FATAL': cls.MAGENTA
        }
        return colors.get(level.upper(), cls.WHITE)

def timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _format(level: str, message: str, tag: Optional[str] = None) -> str:
    """Format log message with color and timestamp."""
    color = LogColors.get_color(level)
    tag_str = f"[{tag}] " if tag else ""
    return f"{LogColors.BOLD}{color}[{timestamp()}] [{level}]{LogColors.RESET} {tag_str}{message}{LogColors.RESET}"

def debug(message: str, tag: Optional[str] = None) -> None:
    """Log a debug message."""
    print(_format("DEBUG", message, tag))

def info(message: str, tag: Optional[str] = None) -> None:
    """Log an info message."""
    print(_format("INFO", message, tag))

def success(message: str, tag: Optional[str] = None) -> None:
    """Log a success message."""
    print(_format("SUCCESS", message, tag))

def warning(message: str, tag: Optional[str] = None) -> None:
    """Log a warning message."""
    print(_format("WARNING", message, tag))

def error(message: str, tag: Optional[str] = None) -> None:
    """Log an error message."""
    print(_format("ERROR", message, tag))

def fatal(message: str, tag: Optional[str] = None) -> None:
    """Log a fatal error message and exit."""
    print(_format("FATAL", message, tag))
    sys.exit(1)  # immediately stop the program

def missing_data(detail: str, tag: str = "DATA") -> None:
    """Log a data-related warning."""
    warning(f"Missing or invalid data: {detail}", tag)

def latency_check(latency_ms: float, tag: Optional[str] = None) -> None:
    """Logs latency with color based on severity."""
    msg = f"Latency: {latency_ms:,.2f} ms"
    
    if latency_ms < 100:
        debug(msg, tag)
    elif latency_ms < 200:
        info(msg, tag)
    elif latency_ms < 500:
        warning(msg, tag)
    else:
        error(msg, tag)

def setup_logging(log_file: str = "bot.log") -> None:
    """Set up file logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def log_exception(e: Exception, tag: Optional[str] = None) -> None:
    """Log an exception with traceback."""
    error(f"Exception: {str(e)}", tag)
    error(f"Traceback: {traceback.format_exc()}", tag)