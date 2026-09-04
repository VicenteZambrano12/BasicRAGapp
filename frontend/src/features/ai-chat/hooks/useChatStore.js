import { useEffect, useRef, useState } from 'react';
import { createSystem, fileToDataUrl, sendChatMessage } from '../../../lib/api';

export const useChatStore = () => {
  const sessionId = useRef(crypto.randomUUID()).current;
  const [config, setConfig] = useState({
    region: 'Madrid',
    subject: 'Historia de España',
    language: 'ES',
  });
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;

    const initialize = async () => {
      setError('');
      try {
        const result = await createSystem({ session_id: sessionId, category: config.region, subject: config.subject, language: config.language });
        if (!cancelled && result.response) {
          setMessages([{ id: crypto.randomUUID(), role: 'assistant', content: result.response }]);
        }
      } catch (initializationError) {
        if (!cancelled) setError(initializationError.message);
      }
    };

    initialize();
    return () => { cancelled = true; };
  }, [config.region, config.subject, config.language, sessionId]);

  const updateConfig = (key, value) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  };

  const sendMessage = async (content, imageFile = null) => {
    if (!content.trim() && !imageFile) return;

    const newMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      image: imageFile ? URL.createObjectURL(imageFile) : null
    };

    setMessages((prev) => [...prev, newMessage]);
    setIsLoading(true);
    setError('');

    try {
      const image = imageFile ? await fileToDataUrl(imageFile) : null;
      const result = await sendChatMessage({
        session_id: sessionId,
        query: content,
        image,
        image_type: image ? 'base64' : 'url',
        category: config.region,
        subject: config.subject,
        language: config.language,
      });
      setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'assistant', content: result.response || '' }]);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsLoading(false);
    }
  };

  return { config, updateConfig, messages, sendMessage, isLoading, error };
};
