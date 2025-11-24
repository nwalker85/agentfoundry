/**
 * Structured Logging Utility for Agent Foundry Frontend
 * =====================================================
 *
 * Provides structured logging with consistent formatting and log levels.
 * In development, outputs colored console logs. In production, outputs JSON
 * for log aggregation services.
 *
 * Features:
 * - Log levels (debug, info, warn, error)
 * - Structured context fields
 * - Environment-aware formatting
 * - Session/request correlation
 *
 * @example
 * ```typescript
 * import { logger, createLogger } from '@/lib/logger';
 *
 * // Use default logger
 * logger.info('User logged in', { userId: '123', method: 'oauth' });
 *
 * // Create scoped logger
 * const agentLogger = createLogger('agent');
 * agentLogger.debug('Processing request', { agentId: 'cibc-activation' });
 * ```
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogContext {
  [key: string]: unknown;
}

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  scope: string;
  message: string;
  context?: LogContext;
}

/**
 * Log level priority for filtering
 */
const LOG_LEVEL_PRIORITY: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

/**
 * Get minimum log level from environment
 */
function getMinLogLevel(): LogLevel {
  const envLevel = process.env.NEXT_PUBLIC_LOG_LEVEL?.toLowerCase();
  if (envLevel && envLevel in LOG_LEVEL_PRIORITY) {
    return envLevel as LogLevel;
  }
  // Default: debug in development, info in production
  return process.env.NODE_ENV === 'development' ? 'debug' : 'info';
}

/**
 * Check if we should output JSON format
 */
function isJsonOutput(): boolean {
  return process.env.NODE_ENV === 'production' || process.env.NEXT_PUBLIC_LOG_FORMAT === 'json';
}

/**
 * Format log entry for console output (development)
 */
function formatConsoleLog(entry: LogEntry): string {
  const timestamp = new Date(entry.timestamp).toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    fractionalSecondDigits: 3,
  });

  let contextStr = '';
  if (entry.context && Object.keys(entry.context).length > 0) {
    const pairs = Object.entries(entry.context)
      .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
      .join(' ');
    contextStr = ` {${pairs}}`;
  }

  return `[${timestamp}] ${entry.level.toUpperCase().padEnd(5)} [${entry.scope}] ${entry.message}${contextStr}`;
}

/**
 * Get console style for log level (for browser console)
 */
function getConsoleStyle(level: LogLevel): string {
  const styles: Record<LogLevel, string> = {
    debug: 'color: #6B7280', // gray
    info: 'color: #10B981', // green
    warn: 'color: #F59E0B', // yellow
    error: 'color: #EF4444', // red
  };
  return styles[level];
}

/**
 * Logger class for structured logging
 */
class Logger {
  private scope: string;
  private minLevel: LogLevel;

  /**
   * Create a new logger instance
   * @param scope - Logger scope/namespace (e.g., 'agent', 'api', 'chat')
   */
  constructor(scope: string = 'app') {
    this.scope = scope;
    this.minLevel = getMinLogLevel();
  }

  /**
   * Check if log level should be output
   */
  private shouldLog(level: LogLevel): boolean {
    return LOG_LEVEL_PRIORITY[level] >= LOG_LEVEL_PRIORITY[this.minLevel];
  }

  /**
   * Create log entry
   */
  private createEntry(level: LogLevel, message: string, context?: LogContext): LogEntry {
    return {
      timestamp: new Date().toISOString(),
      level,
      scope: this.scope,
      message,
      context,
    };
  }

  /**
   * Output log entry
   */
  private output(entry: LogEntry): void {
    if (!this.shouldLog(entry.level)) return;

    // Skip logging in server-side rendering
    if (typeof window === 'undefined') return;

    const consoleMethod =
      entry.level === 'error' ? console.error : entry.level === 'warn' ? console.warn : console.log;

    if (isJsonOutput()) {
      // JSON output for production
      consoleMethod(JSON.stringify(entry));
    } else {
      // Pretty console output for development
      const formatted = formatConsoleLog(entry);
      const style = getConsoleStyle(entry.level);
      consoleMethod(`%c${formatted}`, style);

      // Log context object separately for expandability
      if (entry.context && Object.keys(entry.context).length > 0) {
        console.groupCollapsed('%c  └─ Context', 'color: #9CA3AF; font-size: 10px');
        console.table(entry.context);
        console.groupEnd();
      }
    }
  }

  /**
   * Log at debug level
   * @param message - Log message
   * @param context - Additional context fields
   */
  debug(message: string, context?: LogContext): void {
    this.output(this.createEntry('debug', message, context));
  }

  /**
   * Log at info level
   * @param message - Log message
   * @param context - Additional context fields
   */
  info(message: string, context?: LogContext): void {
    this.output(this.createEntry('info', message, context));
  }

  /**
   * Log at warn level
   * @param message - Log message
   * @param context - Additional context fields
   */
  warn(message: string, context?: LogContext): void {
    this.output(this.createEntry('warn', message, context));
  }

  /**
   * Log at error level
   * @param message - Log message
   * @param context - Additional context fields
   */
  error(message: string, context?: LogContext): void {
    this.output(this.createEntry('error', message, context));
  }

  /**
   * Log an error with stack trace
   * @param message - Log message
   * @param error - Error object
   * @param context - Additional context fields
   */
  exception(message: string, error: Error, context?: LogContext): void {
    this.output(
      this.createEntry('error', message, {
        ...context,
        error: {
          name: error.name,
          message: error.message,
          stack: error.stack,
        },
      })
    );
  }

  /**
   * Create a child logger with additional scope
   * @param childScope - Child scope to append
   * @returns New logger instance with combined scope
   */
  child(childScope: string): Logger {
    return new Logger(`${this.scope}.${childScope}`);
  }
}

/**
 * Create a scoped logger instance
 * @param scope - Logger scope/namespace
 * @returns Logger instance
 *
 * @example
 * ```typescript
 * const chatLogger = createLogger('chat');
 * chatLogger.info('Message sent', { messageId: '123' });
 * ```
 */
export function createLogger(scope: string): Logger {
  return new Logger(scope);
}

/**
 * Default application logger
 *
 * @example
 * ```typescript
 * import { logger } from '@/lib/logger';
 *
 * logger.info('Application started');
 * logger.error('Failed to load data', { endpoint: '/api/agents' });
 * ```
 */
export const logger = new Logger('app');

/**
 * Pre-configured loggers for common use cases
 */
export const loggers = {
  /** Logger for API calls */
  api: createLogger('api'),
  /** Logger for agent execution */
  agent: createLogger('agent'),
  /** Logger for chat functionality */
  chat: createLogger('chat'),
  /** Logger for authentication */
  auth: createLogger('auth'),
  /** Logger for WebSocket connections */
  ws: createLogger('ws'),
};

/**
 * Performance timing utility
 * @param label - Label for the timing
 * @returns Object with end() method to log duration
 *
 * @example
 * ```typescript
 * const timer = timing('fetchAgents');
 * const data = await fetchAgents();
 * timer.end(); // Logs: "fetchAgents completed in 123ms"
 * ```
 */
export function timing(label: string): { end: () => void } {
  const start = performance.now();
  return {
    end: () => {
      const duration = performance.now() - start;
      logger.debug(`${label} completed`, { durationMs: Math.round(duration) });
    },
  };
}

export type { LogLevel, LogContext, LogEntry, Logger };
