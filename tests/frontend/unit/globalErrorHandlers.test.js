import { beforeEach, describe, expect, it, vi } from 'vitest';

import { initGlobalErrorHandlers } from '@app/utils/globalErrorHandlers';
import { logger } from '@app/utils/logger';

describe('initGlobalErrorHandlers', () => {
  let errorSpy;

  beforeEach(() => {
    errorSpy = vi.spyOn(logger, 'error').mockImplementation(() => {});
  });

  it('registers listeners for both uncaught error types', () => {
    const addEventListener = vi.spyOn(window, 'addEventListener');

    initGlobalErrorHandlers();

    expect(addEventListener).toHaveBeenCalledWith('error', expect.any(Function));
    expect(addEventListener).toHaveBeenCalledWith('unhandledrejection', expect.any(Function));
  });

  it('logs uncaught errors with their source location', () => {
    const handlers = {};
    vi.spyOn(window, 'addEventListener').mockImplementation((type, handler) => {
      handlers[type] = handler;
    });
    initGlobalErrorHandlers();

    handlers.error({
      message: 'boom',
      filename: 'app.js',
      lineno: 12,
      colno: 4,
      error: { stack: 'stack-trace' },
    });

    expect(errorSpy).toHaveBeenCalledWith('Uncaught error: boom', {
      source: 'app.js',
      line: 12,
      column: 4,
      stack: 'stack-trace',
    });
  });

  it('logs unhandled promise rejections carrying an Error', () => {
    const handlers = {};
    vi.spyOn(window, 'addEventListener').mockImplementation((type, handler) => {
      handlers[type] = handler;
    });
    initGlobalErrorHandlers();

    const reason = new Error('network down');
    handlers.unhandledrejection({ reason });

    expect(errorSpy).toHaveBeenCalledWith('Unhandled promise rejection: network down', {
      stack: reason.stack,
    });
  });

  it('logs unhandled rejections with a non-Error reason', () => {
    const handlers = {};
    vi.spyOn(window, 'addEventListener').mockImplementation((type, handler) => {
      handlers[type] = handler;
    });
    initGlobalErrorHandlers();

    handlers.unhandledrejection({ reason: 'plain string' });

    expect(errorSpy).toHaveBeenCalledWith('Unhandled promise rejection: plain string', {
      stack: undefined,
    });
  });
});
