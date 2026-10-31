import React, { useLayoutEffect, useState, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

/**
 * Renders the conversation history and message composer.
 *
 * @param {{ messages: Array<object>, onSendMessage: Function, translations: Record<string, string>, isLoading: boolean, error: string }} props
 * @returns {React.ReactElement}
 */
export const ChatInterface = ({ messages, onSendMessage, translations, isLoading, error }) => {
  const [input, setInput] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);
  const fileInputRef = useRef(null);
  const logRef = useRef(null);
  const latestMessageRef = useRef(null);
  const latestMessage = messages[messages.length - 1];

  useLayoutEffect(() => {
    const log = logRef.current;
    const message = latestMessageRef.current;
    if (!log || !message) return;

    if (latestMessage?.role === 'assistant') {
      log.scrollTop += message.getBoundingClientRect().top - log.getBoundingClientRect().top;
    } else {
      log.scrollTop = log.scrollHeight;
    }
  }, [latestMessage?.id]);

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
    <section className="chat-panel flex h-[min(42rem,calc(100dvh-9rem))] min-h-0 flex-col overflow-hidden sm:h-[min(44rem,calc(100dvh-10rem))] lg:h-full">
      <div className="chat-header flex shrink-0 items-center border-b border-slate-200 px-4 py-4 sm:px-5">
        <h2 className="display-heading text-lg font-bold text-slate-900">{translations.chatTitle}</h2>
      </div>
      
      <div ref={logRef} className="chat-log flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-4 sm:p-5" role="log" aria-live="polite" aria-relevant="additions text" aria-label={translations.messagesLabel}>
        {messages.length === 0 && !isLoading && !error && (
          <div className="empty-state m-auto flex flex-col items-center gap-3 px-6 py-8 text-center sm:px-8">
            <span className="empty-mark" aria-hidden="true">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5z" />
                <path d="M4 5.5v16M8 7h8M8 11h7" />
              </svg>
            </span>
            <p className="max-w-sm text-sm leading-relaxed text-slate-600">{translations.emptyChat}</p>
          </div>
        )}
        {messages.map((msg) => (
          <div key={msg.id} ref={msg.id === latestMessage?.id ? latestMessageRef : null} className={`flex min-w-0 shrink-0 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`message-bubble max-w-[88%] break-words rounded-2xl p-3.5 text-sm leading-relaxed sm:max-w-[80%] ${
              msg.role === 'user'
                ? 'message-user rounded-br-md whitespace-pre-wrap'
                : 'message-assistant rounded-bl-md'
            }`}>
              {msg.image && (
                <img src={msg.image} alt={translations.uploadPreview} className="mb-2 max-h-64 max-w-full rounded-lg border border-slate-200 object-contain" />
              )}
              {msg.role === 'user' ? (
                msg.content
              ) : (
                <div className="prose prose-sm max-w-none prose-p:my-1 prose-pre:my-2 prose-headings:my-2 prose-ul:my-1 prose-ol:my-1">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                </div>
              )}
              {msg.role === 'assistant' && msg.sources?.length > 0 && (
                <div className="mt-3 border-t border-slate-200 pt-2.5">
                  <p className="mb-2 text-[11px] font-bold uppercase tracking-[0.1em] text-slate-500">{translations.sourcesLabel}</p>
                  <div className="flex flex-wrap gap-2">
                    {msg.sources.map((source) => (
                      <button
                        key={source.doc_id}
                        type="button"
                        onClick={() => window.open(`${source.url}#page=${source.page ?? 1}`, '_blank', 'noopener')}
                        className="citation-button inline-flex max-w-full items-center gap-1.5 rounded-lg border px-3 py-1.5 text-left text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-700/30"
                        title={source.file_name}
                      >
                        <svg aria-hidden="true" className="shrink-0" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                          <path d="M14 2v6h6M8 13h8M8 17h8" />
                        </svg>
                        <span className="truncate">{source.file_name}{source.page ? ` · p.${source.page}` : ''}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        {isLoading && <div className="flex items-center gap-2 text-sm text-slate-500" role="status"><span className="h-2 w-2 animate-pulse rounded-full bg-[#4F7396]" aria-hidden="true" />{translations.loading}</div>}
        {error && <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800" role="alert">{error}</div>}
      </div>

      <form className="chat-composer flex shrink-0 flex-col gap-3 border-t border-slate-200 p-3 sm:p-4" onSubmit={(event) => { event.preventDefault(); handleSend(); }}>
        {selectedImage && (
          <div className="flex max-w-full items-center gap-2 self-start rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs text-emerald-900">
            <span className="min-w-0 truncate">{selectedImage.name}</span>
            <button 
              type="button" 
              onClick={() => setSelectedImage(null)} 
              className="ml-1 grid h-8 w-8 shrink-0 place-items-center rounded-md text-lg font-medium text-red-700 transition-colors hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-600/40"
              aria-label={translations.removeImage}
            >
              ×
            </button>
          </div>
        )}

        <div className="composer-field flex items-center gap-2 rounded-xl border p-1.5 transition-shadow">
          <input
            id="chat-message"
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={translations.inputPlaceholder}
            aria-label={translations.inputLabel}
            className="min-w-0 flex-1 bg-transparent px-2 text-sm text-slate-800 outline-none placeholder:text-slate-500"
          />
        </div>

        <div className="flex items-center justify-between gap-3 px-1">
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
            className="composer-button grid w-11 shrink-0 place-items-center rounded-xl text-slate-600 transition-colors hover:bg-emerald-50 hover:text-emerald-900 focus:outline-none focus:ring-2 focus:ring-emerald-700/30"
            aria-label={translations.attachImage}
            title={translations.attachImage}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <circle cx="8.5" cy="8.5" r="1.5"></circle>
              <polyline points="21 15 16 10 5 21"></polyline>
            </svg>
          </button>
          
          <button 
            type="submit"
            className="composer-button send-button rounded-xl px-5 py-2 text-sm font-semibold text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-700/40 disabled:cursor-not-allowed disabled:opacity-45"
            disabled={!canSend}
          >
            {translations.send} →
          </button>
        </div>
      </form>
    </section>
  );
};
