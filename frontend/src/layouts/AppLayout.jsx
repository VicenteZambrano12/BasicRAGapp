import React from 'react';

export const AppLayout = ({ children, translations }) => {
  return (
    <div className="min-h-screen bg-[#F0F2F5] flex flex-col items-center p-4 md:p-8">
      <div className="w-full max-w-6xl flex flex-col gap-6">
        <header className="flex items-center gap-3 bg-white p-4 rounded-xl shadow-sm border border-gray-200">
          <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center text-xl">
             🎓
          </div>
          <h1 className="text-2xl font-bold text-[#1E3A8A]">PAUHelper</h1>
          <span className="text-gray-500 ml-2 border-l pl-4 border-gray-300 text-sm hidden sm:inline">
            {translations.appTagline}
          </span>
        </header>
        
        <main className="flex-1">
          {children}
        </main>
      </div>
    </div>
  );
};
