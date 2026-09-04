import React, { useState, useRef } from 'react';

export const ChatInterface = ({ messages, onSendMessage, translations, isLoading, error }) => {
  const [input, setInput] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);
  const fileInputRef = useRef(null);

  const handleSend = () => {
    if (!input.trim() && !selectedImage) return;
    onSendMessage(input, selectedImage);
    setInput('');
    setSelectedImage(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleImageChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedImage(e.target.files[0]);
    }
  };

  const canSend = Boolean(input.trim() || selectedImage) && !isLoading;

  return (
    <section className="flex h-[min(42rem,calc(100dvh-9rem))] min-h-[30rem] min-h-0 flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm sm:h-[min(44rem,calc(100dvh-10rem))] lg:h-full">
      <div className="border-b border-slate-200 px-4 py-4 sm:px-5">
        <h2 className="text-lg font-bold tracking-tight text-slate-900">{translations.chatTitle}</h2>
      </div>
      
      {/* Messages */}
      <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-4 sm:p-5" aria-live="polite" aria-label={translations.messagesLabel}>
        {messages.length === 0 && !isLoading && !error && (
          <p className="m-auto max-w-sm text-center text-sm leading-relaxed text-slate-500">{translations.emptyChat}</p>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[88%] break-words rounded-2xl p-3.5 text-sm leading-relaxed whitespace-pre-wrap sm:max-w-[80%] ${
              msg.role === 'user' 
                ? 'bg-blue-100 text-blue-900 rounded-br-none' 
                : 'bg-gray-100 text-gray-800 rounded-bl-none'
            }`}>
              {msg.image && (
                <img src={msg.image} alt={translations.uploadPreview} className="mb-2 max-h-64 max-w-full rounded-lg border border-slate-200 object-contain" />
              )}
              {msg.content}
            </div>
          </div>
        ))}
        {isLoading && <div className="flex items-center gap-2 text-sm text-slate-500" role="status"><span className="h-2 w-2 animate-pulse rounded-full bg-[#4F7396]" aria-hidden="true" />{translations.loading}</div>}
        {error && <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800" role="alert">{error}</div>}
      </div>

      {/* Input container */}
      <form className="flex flex-col gap-3 border-t border-slate-200 p-4 sm:p-5" onSubmit={(event) => { event.preventDefault(); handleSend(); }}>
        {selectedImage && (
          <div className="flex max-w-full items-center gap-2 self-start rounded-md bg-blue-50 px-3 py-1.5 text-xs text-blue-800">
            <span className="min-w-0 truncate">{selectedImage.name}</span>
            <button 
              type="button" 
              onClick={() => setSelectedImage(null)} 
              className="ml-1 shrink-0 rounded px-1 font-bold text-red-700 transition-colors hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-600/40"
              aria-label={translations.removeImage}
            >
              ×
            </button>
          </div>
        )}

        <div className="flex items-center gap-2 rounded-lg border border-slate-300 bg-white p-2 transition-shadow focus-within:border-blue-700 focus-within:ring-4 focus-within:ring-blue-700/20">
          <input
            id="chat-message"
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={translations.inputPlaceholder}
            aria-label={translations.inputLabel}
            className="min-w-0 flex-1 bg-transparent px-2 text-sm text-slate-800 outline-none placeholder:text-slate-500"
          />
        </div>

        <div className="flex items-center justify-between gap-3 px-1">
          {/* Hidden file input triggered by image icon button */}
          <input 
            type="file" 
            ref={fileInputRef} 
            accept="image/*" 
            onChange={handleImageChange} 
            className="hidden" 
          />
          <button 
            type="button"
            onClick={() => fileInputRef.current && fileInputRef.current.click()}
            className="rounded-md p-2 text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900 focus:outline-none focus:ring-4 focus:ring-blue-700/20"
            aria-label={translations.attachImage}
            title={translations.attachImage}
          >
            {/* Image icon matching the mockup */}
            <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <circle cx="8.5" cy="8.5" r="1.5"></circle>
              <polyline points="21 15 16 10 5 21"></polyline>
            </svg>
          </button>
          
          <button 
            type="button"
            onClick={handleSend}
            className="min-h-11 rounded-lg bg-[#4F7396] px-5 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-[#3D5B78] focus:outline-none focus:ring-4 focus:ring-blue-700/30 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={!canSend}
          >
            {translations.send} →
          </button>
        </div>
      </form>
    </section>
  );
};
