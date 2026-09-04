import React from 'react';

export const StudyConfig = ({ config, onConfigChange, translations }) => {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm flex flex-col gap-5">
      <h2 className="text-xl font-bold text-gray-800">{translations.studyConfig}</h2>
      
      {/* Comunidad Autónoma */}
      <div className="flex flex-col gap-2">
        <label className="text-sm font-medium text-gray-700">{translations.regionLabel}</label>
        <select 
          value={config.region}
          onChange={(e) => onConfigChange('region', e.target.value)}
          className="border border-gray-300 rounded-md p-2 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="Madrid">Madrid</option>
          <option value="Cataluña">Cataluña</option>
          <option value="Andalucía">Andalucía</option>
          <option value="Comunidad Valenciana">Comunidad Valenciana</option>
          <option value="Galicia">Galicia</option>
          <option value="Castilla y León">Castilla y León</option>
          <option value="País Vasco">País Vasco</option>
        </select>
      </div>

      {/* Asignatura */}
      <div className="flex flex-col gap-2">
        <label className="text-sm font-medium text-gray-700">{translations.subjectLabel}</label>
        <select 
          value={config.subject}
          onChange={(e) => onConfigChange('subject', e.target.value)}
          className="border border-gray-300 rounded-md p-2 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="Historia de España">Historia de España</option>
          <option value="Matemáticas II">Matemáticas II</option>
          <option value="Lengua Castellana y Literatura">Lengua Castellana</option>
          <option value="Biología">Biología</option>
          <option value="Física">Física</option>
          <option value="Química">Química</option>
        </select>
      </div>

      {/* Language Toggle */}
      <div className="flex flex-col gap-2 mt-2">
        <label className="text-sm font-medium text-gray-700">{translations.languageLabel}</label>
        <div className="flex rounded-md border border-gray-300 overflow-hidden">
          <button 
            type="button"
            onClick={() => onConfigChange('language', 'ES')}
            className={`flex-1 py-2 text-sm font-medium transition-colors ${config.language === 'ES' ? 'bg-[#4F7396] text-white' : 'bg-gray-50 text-gray-600 hover:bg-gray-100'}`}
          >
            {translations.spanish}
          </button>
          <button 
            type="button"
            onClick={() => onConfigChange('language', 'EN')}
            className={`flex-1 py-2 text-sm font-medium transition-colors border-l border-gray-300 ${config.language === 'EN' ? 'bg-[#4F7396] text-white' : 'bg-gray-50 text-gray-600 hover:bg-gray-100'}`}
          >
            {translations.english}
          </button>
        </div>
      </div>
    </div>
  );
};
