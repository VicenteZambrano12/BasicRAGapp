import React, { useEffect, useState } from 'react';
import { createHowItWorksPdfUrl } from '../utils/howItWorksPdf';

export const AppLayout = ({ children, translations }) => {
  const [pdfUrl, setPdfUrl] = useState(null);

  useEffect(() => () => {
    if (pdfUrl) URL.revokeObjectURL(pdfUrl);
  }, [pdfUrl]);

  const closePdf = () => setPdfUrl(null);

  return (
    <div className="min-h-screen lg:h-screen lg:overflow-hidden bg-[#F0F2F5] flex flex-col items-center p-4 md:p-8">
      <div className="w-full max-w-6xl h-full min-h-0 flex flex-col gap-6">
        <header className="flex items-center gap-3 bg-white p-4 rounded-xl shadow-sm border border-gray-200">
          <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center text-xl">
             🎓
          </div>
          <h1 className="text-2xl font-bold text-[#1E3A8A]">PAUHelper</h1>
          <span className="text-gray-500 ml-2 border-l pl-4 border-gray-300 text-sm hidden sm:inline">
            {translations.appTagline}
          </span>
          <button
            type="button"
            onClick={() => setPdfUrl(createHowItWorksPdfUrl(translations))}
            className="ml-auto inline-flex items-center gap-2 rounded-lg border border-[#1E3A8A] px-3 py-2 text-sm font-semibold text-[#1E3A8A] transition-colors hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-300"
            title={translations.howItWorks}
          >
            <span aria-hidden="true">↗</span>
            {translations.howItWorks}
          </button>
        </header>
        
        <main className="flex-1 min-h-0">
          {children}
        </main>
      </div>

      {pdfUrl && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="how-it-works-title"
          onClick={closePdf}
        >
          <section
            className="flex h-[min(760px,calc(100vh-2rem))] w-full max-w-4xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
              <h2 id="how-it-works-title" className="text-lg font-bold text-[#1E3A8A]">
                {translations.howItWorks}
              </h2>
              <button
                type="button"
                onClick={closePdf}
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
