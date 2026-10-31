import React, { useEffect, useRef, useState } from 'react';

const API_URL = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '');

/** Builds the API URL for the localized How It Works PDF, served from the GCS "documents" bucket. */
const getHowItWorksPdfUrl = (language) => `${API_URL}/docs/how-it-works?language=${language === 'EN' ? 'EN' : 'ES'}`;

/**
 * Renders the application shell and the How It Works PDF dialog.
 *
 * @param {{ children: React.ReactNode, translations: Record<string, string>, language: string }} props
 * @returns {React.ReactElement}
 */
export const AppLayout = ({ children, translations, language }) => {
  const [isPdfOpen, setIsPdfOpen] = useState(false);
  const openButtonRef = useRef(null);
  const closeButtonRef = useRef(null);
  const dialogRef = useRef(null);

  const pdfUrl = getHowItWorksPdfUrl(language);
  const closePdf = () => setIsPdfOpen(false);

  useEffect(() => {
    if (!isPdfOpen) return undefined;

    closeButtonRef.current?.focus();
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        closePdf();
        return;
      }

      if (event.key === 'Tab') {
        const focusableItems = dialogRef.current?.querySelectorAll(
          'button:not([disabled]), iframe, [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
        );
        const firstItem = focusableItems?.[0];
        const lastItem = focusableItems?.[focusableItems.length - 1];

        if (event.shiftKey && document.activeElement === firstItem) {
          event.preventDefault();
          lastItem?.focus();
        } else if (!event.shiftKey && document.activeElement === lastItem) {
          event.preventDefault();
          firstItem?.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      openButtonRef.current?.focus();
    };
  }, [isPdfOpen]);

  return (
    <div className="app-shell flex min-h-[100dvh] flex-col items-center px-3 py-4 sm:px-6 sm:py-6 lg:h-[100dvh] lg:overflow-hidden lg:px-8">
      <div className="app-frame flex h-full min-h-0 flex-col gap-5 sm:gap-6">
        <header className="app-header flex shrink-0 items-center gap-3 rounded-2xl px-3 py-3 sm:px-5">
          <div className="brand-mark" aria-hidden="true">P</div>
          <div className="min-w-0">
            <h1 className="brand-name text-xl font-bold text-[#173f34] sm:text-2xl">PAUHelper</h1>
            <span className="mt-0.5 hidden text-sm text-slate-600 sm:block">
              {translations.appTagline}
            </span>
          </div>
          <button
            type="button"
            onClick={() => setIsPdfOpen(true)}
            ref={openButtonRef}
            className="help-button ml-auto inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-emerald-700/30 sm:px-4"
            title={translations.howItWorks}
          >
            <svg aria-hidden="true" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="9" />
              <path d="M9.8 9a2.3 2.3 0 1 1 3.7 1.8c-.9.7-1.5 1-1.5 2.2" />
              <path d="M12 16.5h.01" />
            </svg>
            {translations.howItWorks}
          </button>
        </header>
        
        <main className="min-h-0 flex-1">
          {children}
        </main>
      </div>

      {isPdfOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-[#10231c]/70 p-3 backdrop-blur-sm sm:p-6"
          role="dialog"
          aria-modal="true"
          aria-labelledby="how-it-works-title"
          onClick={closePdf}
        >
          <section
            ref={dialogRef}
            className="modal-panel flex h-[min(760px,calc(100dvh-1.5rem))] w-full max-w-5xl flex-col overflow-hidden bg-white sm:h-[min(760px,calc(100dvh-3rem))]"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
              <h2 id="how-it-works-title" className="display-heading text-lg font-bold text-[#173f34]">
                {translations.howItWorks}
              </h2>
              <button
                type="button"
                onClick={closePdf}
                ref={closeButtonRef}
                className="flex h-9 w-9 items-center justify-center rounded-full text-2xl leading-none text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-300"
                aria-label={translations.close}
                title={translations.close}
              >
                ×
              </button>
            </div>
            <iframe
              src={pdfUrl}
              title={translations.pdfTitle}
              className="min-h-0 flex-1 bg-slate-100"
            />
          </section>
        </div>
      )}
    </div>
  );
};
