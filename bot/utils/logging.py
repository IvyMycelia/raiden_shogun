"""
Logging utilities with color support.
"""

import logging
import sys
from datetime import datetime
from typing import Optional

# Color codes for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors."""
    
    COLORS = {
        'DEBUG': Colors.CYAN,
        'INFO': Colors.GREEN,
        'WARNING': Colors.YELLOW,
        'ERROR': Colors.RED,
        'CRITICAL': Colors.RED + Colors.BOLD,
    }
    
    def format(self, record):
        # Add color to level name
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{Colors.END}"
        
        # Add color to logger name
        record.name = f"{Colors.BLUE}{record.name}{Colors.END}"
        
        return super().format(record)

def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration with colors."""
    # Create logger
    logger = logging.getLogger('raiden_shogun')
    logger.setLevel(level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create colored formatter for console
    colored_formatter = ColoredFormatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create plain formatter for file
    plain_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(colored_formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(plain_formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get logger for specific module."""
    return logging.getLogger(f'raiden_shogun.{name}')

class Logger:
    """Simple logger wrapper for easy use."""
    
    def __init__(self, name: str):
        self.logger = get_logger(name)
    
    def debug(self, message: str, tag: str = ""):
        """Log debug message."""
        if tag:
            self.logger.debug(f"[{tag}] {message}")
        else:
            self.logger.debug(message)
    
    def info(self, message: str, tag: str = ""):
        """Log info message."""
        if tag:
            self.logger.info(f"[{tag}] {message}")
        else:
            self.logger.info(message)
    
    def warning(self, message: str, tag: str = ""):
        """Log warning message."""
        if tag:
            self.logger.warning(f"[{tag}] {message}")
        else:
            self.logger.warning(message)
    
    def error(self, message: str, tag: str = ""):
        """Log error message."""
        if tag:
            self.logger.error(f"[{tag}] {message}")
        else:
            self.logger.error(message)
    
    def critical(self, message: str, tag: str = ""):
        """Log critical message."""
        if tag:
            self.logger.critical(f"[{tag}] {message}")
        else:
            self.logger.critical(message)


