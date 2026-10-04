import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { describe, expect, it } from 'vitest';

import { AppLayout } from '@app/layouts/AppLayout';
import en from '@app/i18n/languages/en';
import es from '@app/i18n/languages/es';

const renderLayout = (overrides = {}) =>
  render(
    <AppLayout translations={es} language="ES" {...overrides}>
      <p>page content</p>
    </AppLayout>,
  );

describe('AppLayout', () => {
  it('renders the brand header and the page content', () => {
    renderLayout();

    expect(screen.getByRole('heading', { name: 'PAUHelper' })).toBeInTheDocument();
    expect(screen.getByText(es.appTagline)).toBeInTheDocument();
    expect(screen.getByText('page content')).toBeInTheDocument();
  });

  it('keeps the How It Works dialog closed by default', () => {
    renderLayout();

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('opens the dialog with the localized Spanish PDF', async () => {
    renderLayout();

    await userEvent.click(screen.getByRole('button', { name: es.howItWorks }));

    expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
    expect(screen.getByTitle(es.pdfTitle)).toHaveAttribute(
      'src',
      '/api/docs/how-it-works?language=ES',
    );
  });

  it('requests the English PDF when the app is in English', async () => {
    renderLayout({ translations: en, language: 'EN' });

    await userEvent.click(screen.getByRole('button', { name: en.howItWorks }));

    expect(screen.getByTitle(en.pdfTitle)).toHaveAttribute(
      'src',
      '/api/docs/how-it-works?language=EN',
    );
  });

  it('falls back to Spanish for an unexpected language value', async () => {
    renderLayout({ language: 'FR' });

    await userEvent.click(screen.getByRole('button', { name: es.howItWorks }));

    expect(screen.getByTitle(es.pdfTitle)).toHaveAttribute(
      'src',
      '/api/docs/how-it-works?language=ES',
    );
  });

  it('closes the dialog from the close button', async () => {
    renderLayout();
    await userEvent.click(screen.getByRole('button', { name: es.howItWorks }));

    await userEvent.click(screen.getByRole('button', { name: es.close }));

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('closes the dialog when the backdrop is clicked', async () => {
    renderLayout();
    await userEvent.click(screen.getByRole('button', { name: es.howItWorks }));

    await userEvent.click(screen.getByRole('dialog'));

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('keeps the dialog open when its content is clicked', async () => {
    renderLayout();
    await userEvent.click(screen.getByRole('button', { name: es.howItWorks }));

    await userEvent.click(screen.getByRole('heading', { name: es.howItWorks }));

    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });
});
