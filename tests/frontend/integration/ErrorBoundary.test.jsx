import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ErrorBoundary } from '@app/components/ErrorBoundary';
import { logger } from '@app/utils/logger';

const Boom = () => {
  throw new Error('render exploded');
};

describe('ErrorBoundary', () => {
  beforeEach(() => {
    // React logs the caught error itself; silence it to keep the output readable.
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  it('renders its children when nothing throws', () => {
    render(
      <ErrorBoundary>
        <p>all good</p>
      </ErrorBoundary>,
    );

    expect(screen.getByText('all good')).toBeInTheDocument();
  });

  it('shows the fallback instead of unmounting the app', () => {
    render(
      <ErrorBoundary>
        <Boom />
      </ErrorBoundary>,
    );

    expect(screen.getByRole('heading', { name: 'Something went wrong' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Reload' })).toBeInTheDocument();
  });

  it('reports the crash through the logger', () => {
    const errorSpy = vi.spyOn(logger, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <Boom />
      </ErrorBoundary>,
    );

    expect(errorSpy).toHaveBeenCalledWith(
      'Unhandled render error: render exploded',
      expect.objectContaining({ componentStack: expect.any(String) }),
    );
  });

  it('reloads the page from the fallback button', async () => {
    const reload = vi.fn();
    Object.defineProperty(window, 'location', {
      value: { ...window.location, reload },
      configurable: true,
      writable: true,
    });
    vi.spyOn(logger, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <Boom />
      </ErrorBoundary>,
    );
    await userEvent.click(screen.getByRole('button', { name: 'Reload' }));

    expect(reload).toHaveBeenCalled();
  });
});
