import path from 'node:path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  // Backend .env lives at the repo root, one level up from frontend/.
  const rootEnv = loadEnv(mode, path.resolve(__dirname, '..'), '');
  const isLocal = (rootEnv.MODE || 'LOCAL').toUpperCase() === 'LOCAL';

  return {
    plugins: [react()],
    server: {
      port: 3000,
      // Only needed for LOCAL dev, where the frontend (vite) and backend
      // (uvicorn) run as separate servers; in GCP they share one container.
      proxy: isLocal
        ? {
            '/api': {
              target: 'http://localhost:8000',
              changeOrigin: true,
            },
          }
        : undefined,
    },
  };
});

