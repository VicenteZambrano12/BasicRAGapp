import { logger, setCorrelationId } from '../utils/logger';

const API_URL = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '');

// Matches the backend's RequestLoggingMiddleware header (src/api/middleware/logging_middleware.py).
const CORRELATION_ID_HEADER = 'X-Request-ID';

async function request(path, options = {}) {
  const method = options.method || 'GET';
  const outgoingCorrelationId = crypto.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`;

  logger.debug(`API request: ${method} ${path}`, { correlationId: outgoingCorrelationId });

  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      headers: {
        'Content-Type': 'application/json',
        [CORRELATION_ID_HEADER]: outgoingCorrelationId,
      },
      ...options,
    });
  } catch (networkError) {
    logger.error(`API network error: ${method} ${path}`, {
      correlationId: outgoingCorrelationId,
      message: networkError.message,
    });
    throw networkError;
  }

  // The backend echoes back its own correlation id (generated if none was sent).
  const serverCorrelationId = response.headers.get(CORRELATION_ID_HEADER) || outgoingCorrelationId;
  setCorrelationId(serverCorrelationId);

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {}
    logger.error(`API response error: ${method} ${path} -> ${response.status}`, {
      correlationId: serverCorrelationId,
      detail,
    });
    throw new Error(detail);
  }

  logger.debug(`API response: ${method} ${path} -> ${response.status}`, { correlationId: serverCorrelationId });
  return response.json();
}

/** Checks backend availability, called on app load/reload. */
export const checkHealth = () => request('/', { method: 'GET' });

/** Fetches the localized autonomous communities and subjects. */
export const getConfig = (language = 'ES') => request(`/config?language=${language}`, { method: 'GET' });

/** Creates or updates the backend study context for a chat session. */
export const createSystem = (payload) => request('/create_system', {
  method: 'POST',
  body: JSON.stringify(payload),
});

/** Sends a chat message and returns the backend response. */
export const sendChatMessage = (payload) => request('/chat', {
  method: 'POST',
  body: JSON.stringify(payload),
});

/** Converts a browser-selected file to a data URL. */
export const fileToDataUrl = (file) => new Promise((resolve, reject) => {
  const reader = new FileReader();
  reader.onload = () => resolve(reader.result);
  reader.onerror = () => reject(new Error('Unable to read the selected image'));
  reader.readAsDataURL(file);
});