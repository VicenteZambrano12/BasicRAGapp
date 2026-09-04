import React from 'react';
import { AppLayout } from '../layouts/AppLayout';
import { StudyConfig, ChatInterface, useChatStore } from '../features/ai-chat';
import { getTranslations } from '../i18n';

export const ChatPage = () => {
  const { config, updateConfig, messages, sendMessage } = useChatStore();
  const translations = getTranslations(config.language);

  return (
    <AppLayout translations={translations}>
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-full items-start">
        <div className="lg:col-span-4">
          <StudyConfig config={config} onConfigChange={updateConfig} translations={translations} />
        </div>
        <div className="lg:col-span-8">
          <ChatInterface messages={messages} onSendMessage={sendMessage} translations={translations} />
        </div>
      </div>
    </AppLayout>
  );
};
