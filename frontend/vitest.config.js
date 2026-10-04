import path from 'node:path';
import { createRequire } from 'node:module';
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

const repoRoot = path.resolve(__dirname, '..');

// The suites live in the repo-level tests/ folder so backend and frontend tests sit
// together. Node would resolve their bare imports by walking up from tests/, where
// there is no node_modules, so every package a test file imports directly is aliased
// to its resolved path inside frontend/node_modules.
const requireFromFrontend = createRequire(import.meta.url);
const externalTestDependencies = [
  'react',
  'react/jsx-runtime',
  'react/jsx-dev-runtime',
  'react-dom',
  'react-dom/client',
  '@testing-library/react',
  '@testing-library/user-event',
  '@testing-library/jest-dom/matchers',
];

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      { find: '@app', replacement: path.resolve(__dirname, 'src') },
      ...externalTestDependencies.map((id) => ({
        find: new RegExp(`^${id.replace(/[/\\^$*+?.()|[\]{}]/g, '\\$&')}$`),
        replacement: requireFromFrontend.resolve(id),
      })),
    ],
  },
  server: {
    fs: { allow: [repoRoot] },
  },
  test: {
    dir: path.resolve(repoRoot, 'tests/frontend'),
    include: ['**/*.test.{js,jsx}'],
    environment: 'jsdom',
    globals: true,
    setupFiles: [path.resolve(repoRoot, 'tests/frontend/setup.js')],
    restoreMocks: true,
    coverage: {
      provider: 'v8',
      include: ['src/**/*.{js,jsx}'],
      exclude: ['src/main.jsx'],
    },
  },
});
