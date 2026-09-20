import { logger } from './logger';

/**
 * Registers window-level listeners for uncaught errors and unhandled promise
 * rejections that React's ErrorBoundary cannot catch (e.g. async callbacks,
 * event handlers, timers).
 */
export const initGlobalErrorHandlers = () => {
  window.addEventListener('error', (event) => {
    logger.error(`Uncaught error: ${event.message}`, {
      source: event.filename,
      line: event.lineno,
      column: event.colno,
      stack: event.error?.stack,
    });
  });

  window.addEventListener('unhandledrejection', (event) => {
    const reason = event.reason;
    logger.error(`Unhandled promise rejection: ${reason?.message || reason}`, {
      stack: reason?.stack,
    });
  });
};

export default initGlobalErrorHandlers;
