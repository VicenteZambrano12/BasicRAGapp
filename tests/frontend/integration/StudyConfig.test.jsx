import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { describe, expect, it, vi } from 'vitest';

import { StudyConfig } from '@app/features/ai-chat/components/StudyConfig';
import es from '@app/i18n/languages/es';

const COMMUNITIES = ['Andalucía', 'Cataluña', 'Comunidad de Madrid'];
const SUBJECTS = ['Biología', 'Física', 'Historia'];

const renderConfig = (overrides = {}) => {
  const onConfigChange = vi.fn();
  const utils = render(
    <StudyConfig
      config={{ region: 'Andalucía', subject: 'Biología', language: 'ES' }}
      onConfigChange={onConfigChange}
      communities={COMMUNITIES}
      subjects={SUBJECTS}
      translations={es}
      {...overrides}
    />,
  );
  return { ...utils, onConfigChange };
};

describe('StudyConfig', () => {
  it('renders every community and subject option', () => {
    renderConfig();

    const region = screen.getByLabelText(es.regionLabel);
    const subject = screen.getByLabelText(es.subjectLabel);

    expect([...region.options].map((o) => o.value)).toEqual(COMMUNITIES);
    expect([...subject.options].map((o) => o.value)).toEqual(SUBJECTS);
  });

  it('reflects the active configuration', () => {
    renderConfig({ config: { region: 'Cataluña', subject: 'Física', language: 'EN' } });

    expect(screen.getByLabelText(es.regionLabel)).toHaveValue('Cataluña');
    expect(screen.getByLabelText(es.subjectLabel)).toHaveValue('Física');
    expect(screen.getByRole('button', { name: es.english })).toHaveAttribute(
      'aria-pressed',
      'true',
    );
  });

  it('reports region changes', async () => {
    const { onConfigChange } = renderConfig();

    await userEvent.selectOptions(screen.getByLabelText(es.regionLabel), 'Cataluña');

    expect(onConfigChange).toHaveBeenCalledWith('region', 'Cataluña');
  });

  it('reports subject changes', async () => {
    const { onConfigChange } = renderConfig();

    await userEvent.selectOptions(screen.getByLabelText(es.subjectLabel), 'Historia');

    expect(onConfigChange).toHaveBeenCalledWith('subject', 'Historia');
  });

  it.each([
    [es.spanish, 'ES'],
    [es.english, 'EN'],
  ])('reports the %s language selection', async (label, expected) => {
    const { onConfigChange } = renderConfig();

    await userEvent.click(screen.getByRole('button', { name: label }));

    expect(onConfigChange).toHaveBeenCalledWith('language', expected);
  });

  it('marks only the active language as pressed', () => {
    renderConfig();

    expect(screen.getByRole('button', { name: es.spanish })).toHaveAttribute(
      'aria-pressed',
      'true',
    );
    expect(screen.getByRole('button', { name: es.english })).toHaveAttribute(
      'aria-pressed',
      'false',
    );
  });

  it('renders without options before the backend config arrives', () => {
    renderConfig({
      communities: [],
      subjects: [],
      config: { region: '', subject: '', language: 'ES' },
    });

    expect(screen.getByLabelText(es.regionLabel).options).toHaveLength(0);
    expect(screen.getByText(es.studyConfig)).toBeInTheDocument();
  });
});
