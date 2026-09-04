const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // Keep the HTTP error when the server did not return JSON.
    }
    throw new Error(detail);
  }

  return response.json();
}

export const createSystem = (payload) => request('/create_system', {
  method: 'POST',
  body: JSON.stringify(payload),
});

export const sendChatMessage = (payload) => request('/chat', {
  method: 'POST',
  body: JSON.stringify(payload),
});

export const fileToDataUrl = (file) => new Promise((resolve, reject) => {
  const reader = new FileReader();
  reader.onload = () => resolve(reader.result);
  reader.onerror = () => reject(new Error('Unable to read the selected image'));
  reader.readAsDataURL(file);
});