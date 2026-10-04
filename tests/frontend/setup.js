import * as jestDomMatchers from '@testing-library/jest-dom/matchers';
import { cleanup } from '@testing-library/react';
import { afterEach, expect, vi } from 'vitest';

// Registered by hand rather than via '@testing-library/jest-dom/vitest': the
// aliased package entry (see frontend/vitest.config.js) resolves to the CommonJS
// build, which cannot `require('vitest')`.
expect.extend(jestDomMatchers.default ?? jestDomMatchers);

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

// jsdom implements neither of these, and the chat feature relies on both.
if (!globalThis.crypto?.randomUUID) {
  let counter = 0;
  Object.defineProperty(globalThis, 'crypto', {
    value: { ...globalThis.crypto, randomUUID: () => `uuid-${(counter += 1)}` },
    configurable: true,
  });
}

if (!globalThis.URL.createObjectURL) {
  globalThis.URL.createObjectURL = () => 'blob:mock-object-url';
  globalThis.URL.revokeObjectURL = () => {};
}
