import React from 'react';
import { AppLayout } from '../layouts/AppLayout';
import { StudyConfig, ChatInterface, useChatStore } from '../features/ai-chat';
import { getTranslations } from '../i18n';

export const ChatPage = () => {
  const { config, updateConfig, messages, sendMessage, isLoading, error } = useChatStore();
  const translations = getTranslations(config.language);

  return (
    <AppLayout translations={translations}>
      <div className="grid h-full min-h-0 grid-cols-1 items-start gap-4 sm:gap-6 lg:grid-cols-12">
        <aside className="min-h-0 lg:col-span-4" aria-label={translations.studyConfig}>
          <StudyConfig config={config} onConfigChange={updateConfig} translations={translations} />
        </aside>
        <section className="min-h-0 lg:col-span-8" aria-label={translations.chatTitle}>
          <ChatInterface messages={messages} onSendMessage={sendMessage} translations={translations} isLoading={isLoading} error={error} />
        </section>
      </div>
    </AppLayout>
  );
};
