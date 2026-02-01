"""
Obscuras Campaign Manager - Logging Configuration
Zentrale Logging-Konfiguration für Entwicklung und Produktion.
"""

import logging
import logging.handlers
import sys
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Log files
APP_LOG_FILE = LOGS_DIR / "app.log"
ERROR_LOG_FILE = LOGS_DIR / "error.log"
SMTP_LOG_FILE = LOGS_DIR / "smtp.log"
DEBUG_LOG_FILE = LOGS_DIR / "debug.log"

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

# Log levels: DEBUG < INFO < WARNING < ERROR < CRITICAL
DEFAULT_LEVEL = logging.INFO
DEBUG_MODE = True  # Set to False in production

# File rotation settings
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 5  # Keep 5 backup files

# ═══════════════════════════════════════════════════════════════════
# CUSTOM FORMATTERS
# ═══════════════════════════════════════════════════════════════════

class ColoredFormatter(logging.Formatter):
    """Colored console output for development."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[1;31m', # Bold Red
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color to level name
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname_colored = f"{color}{record.levelname:8}{self.RESET}"  # type: ignore[attr-defined]
        
        # Format the message
        formatted = super().format(record)
        return formatted


class DetailedFormatter(logging.Formatter):
    """Detailed formatter for file logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Add extra context
        record.module_path = f"{record.name}.{record.funcName}"  # type: ignore[attr-defined]
        return super().format(record)


# ═══════════════════════════════════════════════════════════════════
# LOG FORMATS
# ═══════════════════════════════════════════════════════════════════

# Console format (colored, compact)
CONSOLE_FORMAT = "%(levelname_colored)s │ %(name)-20s │ %(message)s"

# File format (detailed)
FILE_FORMAT = "%(asctime)s │ %(levelname)-8s │ %(name)-25s │ %(funcName)-20s │ %(message)s"

# Error format (with traceback context)
ERROR_FORMAT = """
════════════════════════════════════════════════════════════════════
%(asctime)s │ %(levelname)s
Module: %(name)s.%(funcName)s (Line %(lineno)d)
────────────────────────────────────────────────────────────────────
%(message)s
════════════════════════════════════════════════════════════════════
"""

# Simple format for SMTP logs
SMTP_FORMAT = "%(asctime)s │ %(levelname)-8s │ %(message)s"

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ═══════════════════════════════════════════════════════════════════
# LOGGER SETUP
# ═══════════════════════════════════════════════════════════════════

def setup_logging(
    level: int | None = None,
    debug_mode: bool | None = None,
    log_to_console: bool = True,
    log_to_file: bool = True,
) -> logging.Logger:
    """
    Setup the logging system.
    
    Args:
        level: Logging level (default: INFO, DEBUG if debug_mode)
        debug_mode: Enable debug mode (verbose logging)
        log_to_console: Enable console output
        log_to_file: Enable file logging
        
    Returns:
        Root logger instance
    """
    if debug_mode is None:
        debug_mode = DEBUG_MODE
    
    if level is None:
        level = logging.DEBUG if debug_mode else DEFAULT_LEVEL
    
    # Get root logger for our application
    root_logger = logging.getLogger("obscuras")
    root_logger.setLevel(logging.DEBUG)  # Capture all, handlers filter
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # ═══════════════════════════════════════════════════════════════
    # CONSOLE HANDLER
    # ═══════════════════════════════════════════════════════════════
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = ColoredFormatter(CONSOLE_FORMAT, datefmt=DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # ═══════════════════════════════════════════════════════════════
    # FILE HANDLERS
    # ═══════════════════════════════════════════════════════════════
    if log_to_file:
        # Main application log (INFO+)
        app_handler = logging.handlers.RotatingFileHandler(
            APP_LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        app_handler.setLevel(logging.INFO)
        app_handler.setFormatter(DetailedFormatter(FILE_FORMAT, datefmt=DATE_FORMAT))
        root_logger.addHandler(app_handler)
        
        # Error log (WARNING+)
        error_handler = logging.handlers.RotatingFileHandler(
            ERROR_LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.WARNING)
        error_handler.setFormatter(DetailedFormatter(ERROR_FORMAT, datefmt=DATE_FORMAT))
        root_logger.addHandler(error_handler)
        
        # Debug log (DEBUG+) - only in debug mode
        if debug_mode:
            debug_handler = logging.handlers.RotatingFileHandler(
                DEBUG_LOG_FILE,
                maxBytes=MAX_LOG_SIZE,
                backupCount=BACKUP_COUNT,
                encoding='utf-8'
            )
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.setFormatter(DetailedFormatter(FILE_FORMAT, datefmt=DATE_FORMAT))
            root_logger.addHandler(debug_handler)
    
    # Log startup
    root_logger.info("=" * 60)
    root_logger.info("Obscuras Campaign Manager gestartet")
    root_logger.info(f"Log-Level: {logging.getLevelName(level)}")
    root_logger.info(f"Debug-Modus: {'Aktiv' if debug_mode else 'Inaktiv'}")
    root_logger.info("=" * 60)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name: Module name (e.g., 'gui.main_window', 'models.campaign')
        
    Returns:
        Logger instance for the module
    """
    return logging.getLogger(f"obscuras.{name}")


def get_smtp_logger() -> logging.Logger:
    """
    Get a specialized logger for SMTP operations.
    
    Returns:
        Logger instance for SMTP operations
    """
    smtp_logger = logging.getLogger("obscuras.smtp")
    
    # Add dedicated SMTP file handler if not already added
    if not any(isinstance(h, logging.handlers.RotatingFileHandler) 
               and h.baseFilename == str(SMTP_LOG_FILE) 
               for h in smtp_logger.handlers):
        smtp_handler = logging.handlers.RotatingFileHandler(
            SMTP_LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        smtp_handler.setLevel(logging.DEBUG)
        smtp_handler.setFormatter(logging.Formatter(SMTP_FORMAT, datefmt=DATE_FORMAT))
        smtp_logger.addHandler(smtp_handler)
    
    return smtp_logger


# ═══════════════════════════════════════════════════════════════════
# CONVENIENCE DECORATORS
# ═══════════════════════════════════════════════════════════════════

from typing import Any, Callable, TypeVar
from functools import wraps

F = TypeVar('F', bound=Callable[..., Any])


def log_function_call(logger: logging.Logger | None = None) -> Callable[[F], F]:
    """
    Decorator to log function entry and exit.
    
    Usage:
        @log_function_call()
        def my_function():
            pass
    """
    def decorator(func: F) -> F:
        nonlocal logger
        _logger = logger if logger is not None else get_logger(func.__module__)
        
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            func_name = func.__name__
            _logger.debug(f"→ {func_name}() aufgerufen")
            try:
                result = func(*args, **kwargs)
                _logger.debug(f"← {func_name}() erfolgreich")
                return result
            except Exception as e:
                _logger.error(f"✗ {func_name}() fehlgeschlagen: {e}")
                raise
        
        return wrapper  # type: ignore[return-value]
    
    return decorator


def log_exceptions(logger: logging.Logger | None = None, reraise: bool = True) -> Callable[[F], F]:
    """
    Decorator to log exceptions.
    
    Usage:
        @log_exceptions()
        def risky_function():
            pass
    """
    def decorator(func: F) -> F:
        nonlocal logger
        _logger = logger if logger is not None else get_logger(func.__module__)
        
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                _logger.exception(f"Exception in {func.__name__}: {e}")
                if reraise:
                    raise
                return None
        
        return wrapper  # type: ignore[return-value]
    
    return decorator


# ═══════════════════════════════════════════════════════════════════
# SPECIALIZED LOG FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def log_email_sent(recipient: str, campaign: str, success: bool, error: str | None = None) -> None:
    """Log an email send attempt."""
    smtp_logger = get_smtp_logger()
    if success:
        smtp_logger.info(f"✓ SENT │ {recipient} │ Kampagne: {campaign}")
    else:
        smtp_logger.warning(f"✗ FAIL │ {recipient} │ Kampagne: {campaign} │ {error}")


def log_bounce(recipient: str, campaign: str, smtp_code: str, message: str):
    """Log a bounce event."""
    smtp_logger = get_smtp_logger()
    smtp_logger.warning(f"⚡ BOUNCE │ {recipient} │ Code: {smtp_code} │ {message}")


def log_campaign_event(campaign: str, event: str, details: str | None = None) -> None:
    """Log a campaign lifecycle event."""
    logger = get_logger("campaigns")
    msg = f"📧 {campaign} │ {event}"
    if details:
        msg += f" │ {details}"
    logger.info(msg)


def log_db_operation(operation: str, model: str, record_id: int | None = None, success: bool = True) -> None:
    """Log a database operation."""
    logger = get_logger("database")
    status = "✓" if success else "✗"
    msg = f"{status} {operation.upper()} │ {model}"
    if record_id:
        msg += f" │ ID: {record_id}"
    if success:
        logger.debug(msg)
    else:
        logger.error(msg)


def log_user_action(action: str, details: str | None = None) -> None:
    """Log a user action in the GUI."""
    logger = get_logger("gui.actions")
    msg = f"👤 {action}"
    if details:
        msg += f" │ {details}"
    logger.info(msg)


# ═══════════════════════════════════════════════════════════════════
# INITIALIZE ON IMPORT (optional)
# ═══════════════════════════════════════════════════════════════════

# Uncomment to auto-initialize logging on import:
# _root_logger = setup_logging()
