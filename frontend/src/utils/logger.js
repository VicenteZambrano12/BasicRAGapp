/**
 * Centralized client-side logger.
 *
 * Wraps `console` with leveled, timestamped, structured output. DEBUG/INFO are
 * suppressed in production builds; WARN/ERROR always emit and are also routed
 * to an external tracking sink (if configured) via `reportError`.
 */

const LEVELS = { DEBUG: 10, INFO: 20, WARN: 30, ERROR: 40 };

const isProd = Boolean(import.meta.env?.PROD);
const minLevel = isProd ? LEVELS.WARN : LEVELS.DEBUG;

/** Last correlation id observed from a backend response, attached to subsequent logs. */
let currentCorrelationId = null;

export const setCorrelationId = (id) => {
  currentCorrelationId = id || null;
};

export const getCorrelationId = () => currentCorrelationId;

const CONSOLE_METHOD = {
  DEBUG: 'debug',
  INFO: 'info',
  WARN: 'warn',
  ERROR: 'error',
};

/** Sends WARN/ERROR events to an external tracking service (e.g. Sentry), if configured. */
const reportToExternalService = (level, message, context) => {
  const sink = window.__errorTracker;
  if (typeof sink === 'function') {
    sink({ level, message, context, correlationId: currentCorrelationId, timestamp: new Date().toISOString() });
  }
};

const log = (level, message, context) => {
  if (LEVELS[level] < minLevel) return;

  const timestamp = new Date().toISOString();
  const correlationSuffix = currentCorrelationId ? ` [cid:${currentCorrelationId}]` : '';
  const prefix = `[${timestamp}] [${level}]${correlationSuffix}`;
  const consoleMethod = CONSOLE_METHOD[level];

  if (context !== undefined) {
    // eslint-disable-next-line no-console
    console[consoleMethod](`${prefix} ${message}`, context);
  } else {
    // eslint-disable-next-line no-console
    console[consoleMethod](`${prefix} ${message}`);
  }

  if (LEVELS[level] >= LEVELS.WARN) {
    reportToExternalService(level, message, context);
  }
};

export const logger = {
  debug: (message, context) => log('DEBUG', message, context),
  info: (message, context) => log('INFO', message, context),
  warn: (message, context) => log('WARN', message, context),
  error: (message, context) => log('ERROR', message, context),
};

export default logger;
