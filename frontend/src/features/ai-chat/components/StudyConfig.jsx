import React from 'react';

export const StudyConfig = ({ config, onConfigChange, translations }) => {
  return (
    <section className="flex flex-col gap-5 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900">{translations.studyConfig}</h2>
        <p className="mt-1 text-sm text-slate-600">{translations.studyConfigHint}</p>
      </div>
      
      {/* Comunidad Autónoma */}
      <div className="flex flex-col gap-2">
        <label htmlFor="region" className="text-sm font-semibold text-slate-700">{translations.regionLabel}</label>
        <select 
          id="region"
          value={config.region}
          onChange={(e) => onConfigChange('region', e.target.value)}
          className="min-h-11 rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-700 transition-shadow focus:border-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-700/20"
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
        <label htmlFor="subject" className="text-sm font-semibold text-slate-700">{translations.subjectLabel}</label>
        <select 
          id="subject"
          value={config.subject}
          onChange={(e) => onConfigChange('subject', e.target.value)}
          className="min-h-11 rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-700 transition-shadow focus:border-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-700/20"
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
      <fieldset className="mt-1 flex flex-col gap-2">
        <legend className="text-sm font-semibold text-slate-700">{translations.languageLabel}</legend>
        <div className="flex overflow-hidden rounded-lg border border-slate-300" role="group">
          <button 
            type="button"
            onClick={() => onConfigChange('language', 'ES')}
            aria-pressed={config.language === 'ES'}
            className={`min-h-11 flex-1 px-3 py-2 text-sm font-semibold transition-colors focus:z-10 focus:outline-none focus:ring-4 focus:ring-blue-700/20 ${config.language === 'ES' ? 'bg-[#4F7396] text-white' : 'bg-slate-50 text-slate-700 hover:bg-slate-100'}`}
          >
            {translations.spanish}
          </button>
          <button 
            type="button"
            onClick={() => onConfigChange('language', 'EN')}
            aria-pressed={config.language === 'EN'}
            className={`min-h-11 flex-1 border-l border-slate-300 px-3 py-2 text-sm font-semibold transition-colors focus:z-10 focus:outline-none focus:ring-4 focus:ring-blue-700/20 ${config.language === 'EN' ? 'bg-[#4F7396] text-white' : 'bg-slate-50 text-slate-700 hover:bg-slate-100'}`}
          >
            {translations.english}
          </button>
        </div>
      </fieldset>
    </section>
  );
};
