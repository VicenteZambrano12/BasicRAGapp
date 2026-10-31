import React from 'react';
import { logger } from '../utils/logger';

/**
 * Catches React rendering crashes in its subtree, logs them, and shows a
 * fallback UI instead of unmounting the whole app.
 */
export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    logger.error(`Unhandled render error: ${error.message}`, {
      stack: error.stack,
      componentStack: errorInfo.componentStack,
    });
  }

  handleReload = () => {
    this.setState({ hasError: false });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="app-shell flex min-h-screen items-center justify-center p-6">
          <div className="study-panel w-full max-w-md p-7 text-center sm:p-9">
            <div className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-2xl border border-red-200 bg-red-50 text-red-700" aria-hidden="true">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 3 2.8 19a1.4 1.4 0 0 0 1.2 2.1h16a1.4 1.4 0 0 0 1.2-2.1z" />
                <path d="M12 9v4M12 17h.01" />
              </svg>
            </div>
            <h1 className="display-heading mb-2 text-xl font-bold text-[#173f34]">Something went wrong</h1>
            <p className="mb-5 text-sm leading-relaxed text-slate-600">
              An unexpected error occurred. Please try reloading the page.
            </p>
            <button
              type="button"
              onClick={this.handleReload}
              className="send-button inline-flex min-h-11 items-center justify-center gap-2 rounded-xl px-5 py-2 text-sm font-semibold text-white transition-colors hover:bg-[#104d3d] focus:outline-none focus:ring-2 focus:ring-emerald-700/40"
            >
              Reload
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
