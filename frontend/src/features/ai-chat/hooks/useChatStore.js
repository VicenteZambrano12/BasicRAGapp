import { useEffect, useRef, useState } from 'react';
import { checkHealth, createSystem, fileToDataUrl, getConfig, sendChatMessage } from '../../../lib/api';

/**
 * Manages the active study configuration, chat messages, and API request state.
 *
 * @returns {{ config: object, updateConfig: Function, communities: Array<string>, subjects: Array<string>, messages: Array<object>, sendMessage: Function, isLoading: boolean, error: string, isBackendAvailable: boolean }}
 */
export const useChatStore = () => {
  const sessionId = useRef(crypto.randomUUID()).current;
  const [config, setConfig] = useState({
    region: '',
    subject: '',
    language: 'ES',
  });
  const [communities, setCommunities] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isBackendAvailable, setIsBackendAvailable] = useState(true);

  // Verifies the backend is reachable whenever the app loads or reloads.
  useEffect(() => {
    checkHealth()
      .then(() => setIsBackendAvailable(true))
      .catch(() => setIsBackendAvailable(false));
  }, []);

  useEffect(() => {
    let cancelled = false;

    const loadConfig = async () => {
      try {
        const result = await getConfig(config.language);
        if (cancelled) return;
        setCommunities(result.communities || []);
        setSubjects(result.subjects || []);
        setConfig((prev) => ({
          ...prev,
          region: prev.region || result.communities?.[0] || '',
          subject: prev.subject || result.subjects?.[0] || '',
        }));
      } catch (configError) {
        if (!cancelled) setError(configError.message);
      }
    };

    loadConfig();
    return () => { cancelled = true; };
  }, [config.language]);

  useEffect(() => {
    if (!config.region || !config.subject) return;

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
      setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'assistant', content: result.response || '', sources: result.sources || [] }]);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsLoading(false);
    }
  };

  return { config, updateConfig, communities, subjects, messages, sendMessage, isLoading, error, isBackendAvailable };
};
