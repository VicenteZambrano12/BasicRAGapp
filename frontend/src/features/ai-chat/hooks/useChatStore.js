import { useState } from 'react';

export const useChatStore = () => {
  const [config, setConfig] = useState({
    region: 'Madrid',
    subject: 'Historia de España',
    language: 'ES',
  });

  const [messages, setMessages] = useState([
    {
      id: '1',
      role: 'assistant',
      content: '¡Hola! He cargado el temario de Historia de España para Madrid. ¿En qué puedo ayudarte hoy?'
    },
    {
      id: '2',
      role: 'user',
      content: 'Resume la crisis de la Restauración (1902-1923).'
    },
    {
      id: '3',
      role: 'assistant',
      content: 'Resumen: Crisis de la Restauración (1902-1923)\n\n• El periodo se caracterizó por la inestabilidad política, el caciquismo, la fragmentación de los partidos dinásticos y el auge de la oposición...'
    }
  ]);

  const updateConfig = (key, value) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  };

  const sendMessage = (content, imageFile = null) => {
    if (!content.trim() && !imageFile) return;

    const newMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      image: imageFile ? URL.createObjectURL(imageFile) : null
    };

    setMessages((prev) => [...prev, newMessage]);
    
    // Connect your backend API call here
  };

  return { config, updateConfig, messages, sendMessage };
};
