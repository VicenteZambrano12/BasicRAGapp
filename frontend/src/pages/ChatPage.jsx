import React from 'react';
import { AppLayout } from '../layouts/AppLayout';
import { StudyConfig, ChatInterface, useChatStore } from '../features/ai-chat';
import { getTranslations } from '../i18n';

/** Renders the study configuration and AI chat workspace. */
export const ChatPage = () => {
  const mockMode = new URLSearchParams(window.location.search).get('mock') === '1';
  const { config, updateConfig, communities, subjects, messages, sendMessage, isLoading, error, isBackendAvailable, isBackendStarting } = useChatStore({ mockMode });
  const translations = getTranslations(config.language);

  if (isBackendStarting) {
    return (
      <AppLayout translations={translations} language={config.language}>
        <div role="status" className="flex h-full min-h-[50vh] flex-col items-center justify-center gap-5 px-6 text-center">
          <div className="relative grid h-16 w-16 place-items-center rounded-2xl border border-emerald-900/10 bg-white shadow-sm">
            <span className="absolute inset-1 animate-spin rounded-xl border-2 border-emerald-100 border-t-emerald-700" aria-hidden="true" />
            <span className="brand-mark relative h-10 w-10 rounded-xl text-base" aria-hidden="true">P</span>
          </div>
          <p className="max-w-md text-sm font-semibold leading-relaxed text-slate-700">{translations.backendStarting}</p>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout translations={translations} language={config.language}>
      <div className="flex min-h-0 flex-col lg:h-full">
      {mockMode && (
        <div role="status" className="preview-notice mb-4 shrink-0 rounded-xl border px-4 py-3 text-sm font-medium leading-relaxed">
          {translations.previewMode}
        </div>
      )}
      {!isBackendAvailable && (
        <div role="alert" className="backend-notice mb-4 flex shrink-0 items-start gap-3 rounded-xl border px-4 py-3 text-sm font-semibold leading-relaxed">
          <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full border border-current text-xs" aria-hidden="true">!</span>
          {translations.backendUnavailable}
        </div>
      )}
      <div className="grid min-h-0 flex-1 grid-cols-1 items-start gap-4 sm:gap-6 lg:grid-cols-12 lg:grid-rows-[minmax(0,1fr)] lg:items-stretch">
        <aside className="min-h-0 min-w-0 lg:col-span-4 lg:overflow-y-auto" aria-label={translations.studyConfig}>
          <StudyConfig config={config} onConfigChange={updateConfig} communities={communities} subjects={subjects} translations={translations} />
        </aside>
        <section className="min-h-0 min-w-0 lg:col-span-8 lg:h-full" aria-label={translations.chatTitle}>
          <ChatInterface messages={messages} onSendMessage={sendMessage} translations={translations} isLoading={isLoading} error={error} />
        </section>
      </div>
      </div>
    </AppLayout>
  );
};
