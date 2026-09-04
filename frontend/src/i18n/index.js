import en from './languages/en';
import es from './languages/es';

const dictionaries = { ES: es, EN: en };

export const getTranslations = (language = 'ES') =>
  dictionaries[language] || dictionaries.ES;
