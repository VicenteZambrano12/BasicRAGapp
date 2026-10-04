import { beforeEach, describe, expect, it, vi } from 'vitest';

import { getCorrelationId, logger, setCorrelationId } from '@app/utils/logger';

describe('logger', () => {
  beforeEach(() => {
    setCorrelationId(null);
    delete window.__errorTracker;
  });

  describe('correlation id', () => {
    it('stores and returns the last id seen', () => {
      setCorrelationId('abc-123');
      expect(getCorrelationId()).toBe('abc-123');
    });

    it('clears the id when given a falsy value', () => {
      setCorrelationId('abc-123');
      setCorrelationId(undefined);
      expect(getCorrelationId()).toBeNull();
    });
  });

  describe('console output', () => {
    it.each([
      ['debug', 'DEBUG'],
      ['info', 'INFO'],
      ['warn', 'WARN'],
      ['error', 'ERROR'],
    ])('routes %s to the matching console method', (level, label) => {
      const spy = vi.spyOn(console, level).mockImplementation(() => {});

      logger[level]('a message');

      expect(spy).toHaveBeenCalledTimes(1);
      expect(spy.mock.calls[0][0]).toContain(`[${label}] a message`);
    });

    it('prefixes every line with an ISO timestamp', () => {
      const spy = vi.spyOn(console, 'info').mockImplementation(() => {});

      logger.info('a message');

      expect(spy.mock.calls[0][0]).toMatch(/^\[\d{4}-\d{2}-\d{2}T[\d:.]+Z\] \[INFO\]/);
    });

    it('includes the active correlation id in the prefix', () => {
      const spy = vi.spyOn(console, 'info').mockImplementation(() => {});
      setCorrelationId('abc-123');

      logger.info('a message');

      expect(spy.mock.calls[0][0]).toContain('[cid:abc-123]');
    });

    it('omits the correlation id segment when none is set', () => {
      const spy = vi.spyOn(console, 'info').mockImplementation(() => {});

      logger.info('a message');

      expect(spy.mock.calls[0][0]).not.toContain('cid:');
    });

    it('passes the context object through as a second argument', () => {
      const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const context = { detail: 'boom' };

      logger.error('a message', context);

      expect(spy.mock.calls[0][1]).toBe(context);
    });

    it('logs without a second argument when no context is given', () => {
      const spy = vi.spyOn(console, 'info').mockImplementation(() => {});

      logger.info('a message');

      expect(spy.mock.calls[0]).toHaveLength(1);
    });
  });

  describe('external error tracker', () => {
    it.each(['warn', 'error'])('forwards %s events to the sink', (level) => {
      vi.spyOn(console, level).mockImplementation(() => {});
      const sink = vi.fn();
      window.__errorTracker = sink;
      setCorrelationId('abc-123');

      logger[level]('a message', { detail: 'boom' });

      expect(sink).toHaveBeenCalledWith({
        level: level.toUpperCase(),
        message: 'a message',
        context: { detail: 'boom' },
        correlationId: 'abc-123',
        timestamp: expect.any(String),
      });
    });

    it.each(['debug', 'info'])('does not forward %s events', (level) => {
      vi.spyOn(console, level).mockImplementation(() => {});
      const sink = vi.fn();
      window.__errorTracker = sink;

      logger[level]('a message');

      expect(sink).not.toHaveBeenCalled();
    });

    it('is a no-op when no sink is registered', () => {
      vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => logger.error('a message')).not.toThrow();
    });
  });
});
