import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  checkHealth,
  createSystem,
  fileToDataUrl,
  getConfig,
  sendChatMessage,
} from '@app/lib/api';
import { getCorrelationId, setCorrelationId } from '@app/utils/logger';

const CORRELATION_ID_HEADER = 'X-Request-ID';

/** Minimal stand-in for the parts of `Response` that api.js touches. */
const fakeResponse = ({ status = 200, body = {}, correlationId = 'server-id', json } = {}) => ({
  ok: status >= 200 && status < 300,
  status,
  headers: { get: (name) => (name === CORRELATION_ID_HEADER ? correlationId : null) },
  json: json ?? (async () => body),
});

const mockFetch = (result) => {
  const fetchMock = vi.fn(() =>
    result instanceof Error ? Promise.reject(result) : Promise.resolve(result),
  );
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
};

const lastCall = (fetchMock) => fetchMock.mock.calls[0];

describe('api client', () => {
  beforeEach(() => {
    vi.spyOn(console, 'debug').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});
    setCorrelationId(null);
  });

  describe('request plumbing', () => {
    it('prefixes paths with the API base url', async () => {
      const fetchMock = mockFetch(fakeResponse({ body: { ok: true } }));

      await checkHealth();

      expect(lastCall(fetchMock)[0]).toBe('/api/');
    });

    it('sends JSON content type and a generated correlation id', async () => {
      const fetchMock = mockFetch(fakeResponse());

      await checkHealth();

      const { headers } = lastCall(fetchMock)[1];
      expect(headers['Content-Type']).toBe('application/json');
      expect(headers[CORRELATION_ID_HEADER]).toEqual(expect.any(String));
      expect(headers[CORRELATION_ID_HEADER]).not.toHaveLength(0);
    });

    it('uses a distinct correlation id per request', async () => {
      const fetchMock = mockFetch(fakeResponse());

      await checkHealth();
      await checkHealth();

      const [first, second] = fetchMock.mock.calls.map(
        (call) => call[1].headers[CORRELATION_ID_HEADER],
      );
      expect(first).not.toBe(second);
    });

    it('adopts the correlation id echoed by the backend', async () => {
      mockFetch(fakeResponse({ correlationId: 'from-backend' }));

      await checkHealth();

      expect(getCorrelationId()).toBe('from-backend');
    });

    it('keeps the outgoing id when the backend does not echo one', async () => {
      const fetchMock = mockFetch(fakeResponse({ correlationId: null }));

      await checkHealth();

      expect(getCorrelationId()).toBe(lastCall(fetchMock)[1].headers[CORRELATION_ID_HEADER]);
    });

    it('returns the parsed JSON body', async () => {
      mockFetch(fakeResponse({ body: { message: 'PAUHelper is running' } }));

      await expect(checkHealth()).resolves.toEqual({ message: 'PAUHelper is running' });
    });

    it('aborts the request when the timeout elapses', async () => {
      vi.useFakeTimers();
      let capturedSignal;
      vi.stubGlobal(
        'fetch',
        vi.fn((url, options) => {
          capturedSignal = options.signal;
          return new Promise(() => {});
        }),
      );

      checkHealth();
      await Promise.resolve();
      vi.advanceTimersByTime(5000);

      expect(capturedSignal.aborted).toBe(true);
    });
  });

  describe('error handling', () => {
    it('surfaces the backend detail message', async () => {
      mockFetch(fakeResponse({ status: 400, body: { detail: 'Call /create_system first.' } }));

      await expect(checkHealth()).rejects.toThrow('Call /create_system first.');
    });

    it('falls back to a status message when the body is not JSON', async () => {
      mockFetch(
        fakeResponse({
          status: 500,
          json: async () => {
            throw new SyntaxError('Unexpected token');
          },
        }),
      );

      await expect(checkHealth()).rejects.toThrow('Request failed (500)');
    });

    it('falls back to a status message when the body has no detail', async () => {
      mockFetch(fakeResponse({ status: 502, body: {} }));

      await expect(checkHealth()).rejects.toThrow('Request failed (502)');
    });

    it('reports network failures', async () => {
      mockFetch(new TypeError('Failed to fetch'));

      await expect(checkHealth()).rejects.toThrow('Failed to fetch');
    });

    it('reports timeouts distinctly from other network failures', async () => {
      const abortError = new Error('The operation was aborted');
      abortError.name = 'AbortError';
      mockFetch(abortError);

      await expect(checkHealth()).rejects.toThrow('Request timed out');
    });
  });

  describe('endpoints', () => {
    it('checkHealth issues a GET to the service root', async () => {
      const fetchMock = mockFetch(fakeResponse());

      await checkHealth();

      expect(lastCall(fetchMock)).toEqual(['/api/', expect.objectContaining({ method: 'GET' })]);
    });

    it('getConfig defaults to Spanish', async () => {
      const fetchMock = mockFetch(fakeResponse());

      await getConfig();

      expect(lastCall(fetchMock)[0]).toBe('/api/config?language=ES');
    });

    it('getConfig forwards the requested language', async () => {
      const fetchMock = mockFetch(fakeResponse());

      await getConfig('EN');

      expect(lastCall(fetchMock)[0]).toBe('/api/config?language=EN');
    });

    it('createSystem posts the session payload as JSON', async () => {
      const fetchMock = mockFetch(fakeResponse());
      const payload = { session_id: 's1', category: 'Andalucía', subject: 'Biología' };

      await createSystem(payload);

      const [url, options] = lastCall(fetchMock);
      expect(url).toBe('/api/create_system');
      expect(options.method).toBe('POST');
      expect(JSON.parse(options.body)).toEqual(payload);
    });

    it('sendChatMessage posts the chat payload as JSON', async () => {
      const fetchMock = mockFetch(fakeResponse());
      const payload = { session_id: 's1', query: '¿Qué es la mitosis?' };

      await sendChatMessage(payload);

      const [url, options] = lastCall(fetchMock);
      expect(url).toBe('/api/chat');
      expect(options.method).toBe('POST');
      expect(JSON.parse(options.body)).toEqual(payload);
    });
  });

  describe('fileToDataUrl', () => {
    it('resolves with the data url of the selected file', async () => {
      const file = new File(['hello'], 'note.txt', { type: 'text/plain' });

      await expect(fileToDataUrl(file)).resolves.toBe('data:text/plain;base64,aGVsbG8=');
    });

    it('rejects with a readable message when the file cannot be read', async () => {
      vi.stubGlobal(
        'FileReader',
        class {
          readAsDataURL() {
            setTimeout(() => this.onerror(new Error('boom')), 0);
          }
        },
      );

      await expect(fileToDataUrl({})).rejects.toThrow('Unable to read the selected image');
    });
  });
});
