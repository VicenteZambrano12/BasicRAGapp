import React from 'react';
import { AppLayout } from '../layouts/AppLayout';
import { StudyConfig, ChatInterface, useChatStore } from '../features/ai-chat';
import { getTranslations } from '../i18n';

/** Renders the study configuration and AI chat workspace. */
export const ChatPage = () => {
  const { config, updateConfig, communities, subjects, messages, sendMessage, isLoading, error, isBackendAvailable } = useChatStore();
  const translations = getTranslations(config.language);

  return (
    <AppLayout translations={translations} language={config.language}>
      {!isBackendAvailable && (
        <div role="alert" className="mb-4 rounded-lg border border-red-300 bg-red-50 px-4 py-2 text-sm font-semibold text-red-700">
          {translations.backendUnavailable}
        </div>
      )}
      <div className="grid h-full min-h-0 grid-cols-1 items-start gap-4 sm:gap-6 lg:grid-cols-12 lg:items-stretch">
        <aside className="min-h-0 lg:col-span-4" aria-label={translations.studyConfig}>
          <StudyConfig config={config} onConfigChange={updateConfig} communities={communities} subjects={subjects} translations={translations} />
        </aside>
        <section className="min-h-0 lg:col-span-8 lg:h-full" aria-label={translations.chatTitle}>
          <ChatInterface messages={messages} onSendMessage={sendMessage} translations={translations} isLoading={isLoading} error={error} />
        </section>
      </div>
    </AppLayout>
  );
};
