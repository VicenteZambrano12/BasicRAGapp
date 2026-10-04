import { describe, expect, it } from 'vitest';

import { getTranslations } from '@app/i18n';
import en from '@app/i18n/languages/en';
import es from '@app/i18n/languages/es';

describe('getTranslations', () => {
  it('defaults to Spanish', () => {
    expect(getTranslations()).toBe(es);
  });

  it('returns the English dictionary', () => {
    expect(getTranslations('EN')).toBe(en);
  });

  it.each(['FR', 'es', '', null, undefined])(
    'falls back to Spanish for the unsupported value %s',
    (language) => {
      expect(getTranslations(language)).toBe(es);
    },
  );
});

describe('dictionaries', () => {
  it('expose exactly the same keys, so no label can go untranslated', () => {
    expect(Object.keys(en).sort()).toEqual(Object.keys(es).sort());
  });

  it('have no empty values', () => {
    for (const dictionary of [es, en]) {
      for (const [key, value] of Object.entries(dictionary)) {
        expect(value, `empty translation for "${key}"`).toBeTruthy();
      }
    }
  });
});
