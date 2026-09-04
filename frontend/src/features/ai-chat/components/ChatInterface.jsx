import React, { useState, useRef } from 'react';

export const ChatInterface = ({ messages, onSendMessage, translations }) => {
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

  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm flex flex-col h-[700px]">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-bold text-gray-800">{translations.chatTitle}</h2>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] p-3.5 rounded-2xl whitespace-pre-wrap text-sm leading-relaxed ${
              msg.role === 'user' 
                ? 'bg-blue-100 text-blue-900 rounded-br-none' 
                : 'bg-gray-100 text-gray-800 rounded-bl-none'
            }`}>
              {msg.image && (
                <img src={msg.image} alt="Upload preview" className="max-w-xs rounded mb-2 border" />
              )}
              {msg.content}
            </div>
          </div>
        ))}
      </div>

      {/* Input container */}
      <div className="p-4 border-t border-gray-200 flex flex-col gap-3">
        {selectedImage && (
          <div className="flex items-center gap-2 text-xs bg-blue-50 text-blue-700 px-3 py-1.5 rounded-md w-fit">
            <span>📷 {selectedImage.name}</span>
            <button 
              type="button" 
              onClick={() => setSelectedImage(null)} 
              className="text-red-500 font-bold ml-1 hover:text-red-700"
            >
              ×
            </button>
          </div>
        )}

        <div className="flex items-center gap-2 border border-gray-300 rounded-lg p-2 bg-white focus-within:ring-2 focus-within:ring-blue-500">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={translations.inputPlaceholder}
            className="flex-1 outline-none text-gray-700 bg-transparent px-2 text-sm"
          />
        </div>

        <div className="flex justify-between items-center px-1">
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
            className="text-gray-500 hover:text-gray-700 p-1.5 rounded hover:bg-gray-100 transition-colors"
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
            className="bg-[#4F7396] hover:bg-[#3D5B78] text-white px-5 py-2 rounded-md font-medium transition-colors text-sm flex items-center gap-2 shadow-sm"
          >
            {translations.send} →
          </button>
        </div>
      </div>
    </div>
  );
};
