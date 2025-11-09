"""
Centralized Logging & Observability
Structured logging with correlation IDs, performance tracking, and multi-destination output
"""

import logging
import sys
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from contextvars import ContextVar
from functools import wraps
import traceback

# Context variables for correlation
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
user_id: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
session_id: ContextVar[Optional[str]] = ContextVar('session_id', default=None)


class StructuredFormatter(logging.Formatter):
    """JSON formatter with context injection"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add context
        if cid := correlation_id.get():
            log_data['correlation_id'] = cid
        if uid := user_id.get():
            log_data['user_id'] = uid
        if sid := session_id.get():
            log_data['session_id'] = sid
        
        # Add exception info
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data['data'] = record.extra_data
        
        return json.dumps(log_data)


class HumanFormatter(logging.Formatter):
    """Human-readable formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S.%f')[:-3]
        
        # Build context string
        context_parts = []
        if cid := correlation_id.get():
            context_parts.append(f"corr={cid[:8]}")
        if uid := user_id.get():
            context_parts.append(f"user={uid[:8]}")
        
        context = f"[{' '.join(context_parts)}] " if context_parts else ""
        
        base_msg = f"{color}{timestamp}{reset} {color}{record.levelname:8}{reset} {record.name:20} {context}{record.getMessage()}"
        
        if record.exc_info:
            base_msg += f"\n{self.formatException(record.exc_info)}"
        
        return base_msg


class PerformanceLogger:
    """Track operation performance metrics"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.metrics: Dict[str, list] = {}
    
    def track(self, operation: str, duration: float, success: bool = True, **kwargs):
        """Track a single operation"""
        if operation not in self.metrics:
            self.metrics[operation] = []
        
        self.metrics[operation].append({
            'duration': duration,
            'success': success,
            'timestamp': datetime.utcnow().isoformat(),
            **kwargs
        })
        
        self.logger.info(
            f"Operation completed: {operation}",
            extra={
                'extra_data': {
                    'operation': operation,
                    'duration_ms': round(duration * 1000, 2),
                    'success': success,
                    **kwargs
                }
            }
        )
    
    def get_stats(self, operation: str) -> Dict[str, Any]:
        """Get statistics for an operation"""
        if operation not in self.metrics:
            return {}
        
        durations = [m['duration'] for m in self.metrics[operation]]
        successes = sum(1 for m in self.metrics[operation] if m['success'])
        
        return {
            'count': len(durations),
            'success_rate': successes / len(durations),
            'avg_duration_ms': round(sum(durations) / len(durations) * 1000, 2),
            'min_duration_ms': round(min(durations) * 1000, 2),
            'max_duration_ms': round(max(durations) * 1000, 2),
        }


def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    enable_console: bool = True,
    enable_json: bool = True
) -> logging.Logger:
    """
    Setup comprehensive logging infrastructure
    
    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (creates if needed)
        enable_console: Enable human-readable console output
        enable_json: Enable structured JSON log files
    
    Returns:
        Root logger instance
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler (human-readable)
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(HumanFormatter())
        root_logger.addHandler(console_handler)
    
    # JSON file handler (structured logs)
    if enable_json and log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        json_handler = logging.FileHandler(
            log_dir / f"pm_agent_{datetime.now().strftime('%Y%m%d')}.jsonl"
        )
        json_handler.setLevel(logging.DEBUG)
        json_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(json_handler)
    
    # Error file handler (separate error log)
    if log_dir:
        error_handler = logging.FileHandler(
            log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(HumanFormatter())
        root_logger.addHandler(error_handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


def log_function_call(logger: Optional[logging.Logger] = None):
    """Decorator to log function entry/exit with timing"""
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"
            logger.debug(f"→ Entering {func_name}")
            start = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                logger.debug(
                    f"← Exiting {func_name}",
                    extra={'extra_data': {'duration_ms': round(duration * 1000, 2)}}
                )
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(
                    f"✗ Exception in {func_name}",
                    exc_info=True,
                    extra={'extra_data': {'duration_ms': round(duration * 1000, 2)}}
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"
            logger.debug(f"→ Entering {func_name}")
            start = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                logger.debug(
                    f"← Exiting {func_name}",
                    extra={'extra_data': {'duration_ms': round(duration * 1000, 2)}}
                )
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(
                    f"✗ Exception in {func_name}",
                    exc_info=True,
                    extra={'extra_data': {'duration_ms': round(duration * 1000, 2)}}
                )
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# Performance tracking singleton
_perf_logger: Optional[PerformanceLogger] = None

def get_perf_logger() -> PerformanceLogger:
    """Get performance logger instance"""
    global _perf_logger
    if _perf_logger is None:
        _perf_logger = PerformanceLogger(get_logger('performance'))
    return _perf_logger
