import { useEffect, useRef, useState } from 'react';
import { checkHealth, createSystem, fileToDataUrl, getConfig, sendChatMessage } from '../../../lib/api';

const HEALTH_POLL_INTERVAL_MS = 3000;
const MOCK_COMMUNITIES = ['Andalucía', 'Aragón', 'Cataluña', 'Galicia', 'Comunidad de Madrid'];
const MOCK_SUBJECTS = ['Biología', 'Física', 'Historia de España', 'Matemáticas'];

const createMockConversation = (language) => language === 'EN'
  ? [
      { id: 'mock-welcome', role: 'assistant', content: 'Welcome to the PAUHelper preview. Choose a subject and try the composer to see a sample response.' },
      { id: 'mock-question', role: 'user', content: 'What is the difference between mitosis and meiosis?' },
      { id: 'mock-answer', role: 'assistant', content: '**Mitosis** creates two genetically identical cells for growth and repair. **Meiosis** creates four genetically different cells with half the chromosome number for reproduction.\n\n- **Mitosis:** one division, two cells\n- **Meiosis:** two divisions, four cells' },
    ]
  : [
      { id: 'mock-welcome', role: 'assistant', content: 'Bienvenido a la vista previa de PAUHelper. Elige una asignatura y prueba el chat para ver una respuesta de ejemplo.' },
      { id: 'mock-question', role: 'user', content: '¿Qué diferencia hay entre mitosis y meiosis?' },
      { id: 'mock-answer', role: 'assistant', content: 'La **mitosis** produce dos células genéticamente idénticas para el crecimiento y la reparación. La **meiosis** produce cuatro células diferentes con la mitad de cromosomas, necesarias para la reproducción.\n\n- **Mitosis:** una división, dos células\n- **Meiosis:** dos divisiones, cuatro células' },
    ];

/**
 * Manages the active study configuration, chat messages, and API request state.
 *
 * @returns {{ config: object, updateConfig: Function, communities: Array<string>, subjects: Array<string>, messages: Array<object>, sendMessage: Function, isLoading: boolean, error: string, isBackendAvailable: boolean, isBackendStarting: boolean }}
 */
export const useChatStore = ({ mockMode = false } = {}) => {
  const sessionId = useRef(crypto.randomUUID()).current;
  const [config, setConfig] = useState({
    region: mockMode ? MOCK_COMMUNITIES[0] : '',
    subject: mockMode ? MOCK_SUBJECTS[0] : '',
    language: 'ES',
  });
  const [communities, setCommunities] = useState(mockMode ? MOCK_COMMUNITIES : []);
  const [subjects, setSubjects] = useState(mockMode ? MOCK_SUBJECTS : []);
  const [messages, setMessages] = useState(() => mockMode ? createMockConversation('ES') : []);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isBackendAvailable, setIsBackendAvailable] = useState(mockMode);
  const [isBackendStarting, setIsBackendStarting] = useState(!mockMode);

  // Polls until the backend responds. Frontend deploys can finish before the
  // backend container is ready, so a single check would show a false failure.
  useEffect(() => {
    if (mockMode) return undefined;
    let cancelled = false;
    let timeoutId;

    const poll = async () => {
      try {
        await checkHealth();
        if (cancelled) return;
        setIsBackendAvailable(true);
        setIsBackendStarting(false);
      } catch {
        if (cancelled) return;
        setIsBackendAvailable(false);
        timeoutId = setTimeout(poll, HEALTH_POLL_INTERVAL_MS);
      }
    };

    poll();
    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [mockMode]);

  useEffect(() => {
    if (mockMode) setMessages(createMockConversation(config.language));
  }, [config.language, mockMode]);

  useEffect(() => {
    if (mockMode || !isBackendAvailable) return;
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
  }, [isBackendAvailable, config.language, mockMode]);

  useEffect(() => {
    if (mockMode || !isBackendAvailable || !config.region || !config.subject) return;

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
  }, [isBackendAvailable, config.region, config.subject, config.language, sessionId, mockMode]);


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
      if (mockMode) {
        await new Promise((resolve) => window.setTimeout(resolve, 500));
        const response = config.language === 'EN'
          ? `This is a local preview response for **${config.subject}** in ${config.region}. In the connected app, an answer would be grounded in your exam curriculum${imageFile ? '. The attached image is shown here, but is not analyzed in preview mode.' : '.'}`
          : `Esta es una respuesta local de vista previa para **${config.subject}** en ${config.region}. En la versión conectada, la respuesta se basaría en el temario de la PAU${imageFile ? '. La imagen aparece adjunta, pero no se analiza en el modo de vista previa.' : '.'}`;
        setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'assistant', content: response }]);
        return;
      }

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

  return { config, updateConfig, communities, subjects, messages, sendMessage, isLoading, error, isBackendAvailable, isBackendStarting };
};
