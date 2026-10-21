import React from 'react';

/**
 * Renders controls for the learner's region, subject, and language.
 *
 * @param {{ config: object, onConfigChange: Function, communities: Array<string>, subjects: Array<string>, translations: Record<string, string> }} props
 * @returns {React.ReactElement}
 */
export const StudyConfig = ({ config, onConfigChange, communities, subjects, translations }) => {
  return (
    <section className="study-panel flex flex-col gap-5 p-4 sm:p-6">
      <div>
        <h2 className="display-heading text-xl font-bold text-slate-900">{translations.studyConfig}</h2>
        <p className="mt-1.5 text-sm leading-relaxed text-slate-600">{translations.studyConfigHint}</p>
      </div>
      
      <div className="flex flex-col gap-2">
        <label htmlFor="region" className="text-sm font-semibold text-slate-700">{translations.regionLabel}</label>
        <select 
          id="region"
          value={config.region}
          onChange={(e) => onConfigChange('region', e.target.value)}
          className="study-select rounded-xl border px-3 py-2 text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-700/20"
        >
          {communities.map((community) => (
            <option key={community} value={community}>{community}</option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-2">
        <label htmlFor="subject" className="text-sm font-semibold text-slate-700">{translations.subjectLabel}</label>
        <select 
          id="subject"
          value={config.subject}
          onChange={(e) => onConfigChange('subject', e.target.value)}
          className="study-select rounded-xl border px-3 py-2 text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-700/20"
        >
          {subjects.map((subject) => (
            <option key={subject} value={subject}>{subject}</option>
          ))}
        </select>
      </div>

      <fieldset className="mt-1 flex flex-col gap-2">
        <legend className="text-sm font-semibold text-slate-700">{translations.languageLabel}</legend>
        <div className="language-switch flex overflow-hidden rounded-xl border p-1" role="group">
          <button 
            type="button"
            onClick={() => onConfigChange('language', 'ES')}
            aria-pressed={config.language === 'ES'}
            className="language-option flex-1 rounded-lg px-3 py-2 text-sm font-semibold focus:z-10 focus:outline-none focus:ring-2 focus:ring-emerald-700/30"
          >
            {translations.spanish}
          </button>
          <button 
            type="button"
            onClick={() => onConfigChange('language', 'EN')}
            aria-pressed={config.language === 'EN'}
            className="language-option flex-1 rounded-lg px-3 py-2 text-sm font-semibold focus:z-10 focus:outline-none focus:ring-2 focus:ring-emerald-700/30"
          >
            {translations.english}
          </button>
        </div>
      </fieldset>
    </section>
  );
};
