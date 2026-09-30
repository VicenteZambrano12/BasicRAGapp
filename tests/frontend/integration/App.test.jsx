import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import App from '@app/App';
import * as api from '@app/lib/api';
import en from '@app/i18n/languages/en';
import es from '@app/i18n/languages/es';

vi.mock('@app/lib/api');

const CONFIG = {
  communities: ['Andalucía', 'Cataluña'],
  subjects: ['Biología', 'Física'],
};

describe('App (chat page)', () => {
  beforeEach(() => {
    vi.mocked(api.checkHealth).mockResolvedValue({ message: 'PAUHelper is running' });
    vi.mocked(api.getConfig).mockResolvedValue(CONFIG);
    vi.mocked(api.createSystem).mockResolvedValue({ response: '¡Hola!' });
    vi.mocked(api.sendChatMessage).mockResolvedValue({ response: 'respuesta', sources: [] });
  });

  it('shows the connecting state until the backend answers', async () => {
    vi.mocked(api.checkHealth).mockReturnValue(new Promise(() => {}));

    render(<App />);

    expect(screen.getByRole('status')).toHaveTextContent(es.backendStarting);
    expect(screen.queryByText(es.studyConfig)).not.toBeInTheDocument();
  });

  it('renders the configuration panel and the chat once ready', async () => {
    render(<App />);

    expect(await screen.findByText(es.studyConfig)).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: es.chatTitle })).toBeInTheDocument();
    expect(await screen.findByText('¡Hola!')).toBeInTheDocument();
  });

  it('drives a full question/answer round trip', async () => {
    render(<App />);
    await screen.findByText('¡Hola!');

    await userEvent.type(screen.getByLabelText(es.inputLabel), '¿Qué es la mitosis?');
    await userEvent.click(screen.getByRole('button', { name: new RegExp(es.send) }));

    expect(await screen.findByText('respuesta')).toBeInTheDocument();
    expect(api.sendChatMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        query: '¿Qué es la mitosis?',
        category: 'Andalucía',
        subject: 'Biología',
      }),
    );
  });

  it('switches the whole interface to English', async () => {
    render(<App />);
    await screen.findByText('¡Hola!');

    await userEvent.click(screen.getByRole('button', { name: es.english }));

    expect(await screen.findByText(en.studyConfig)).toBeInTheDocument();
    await waitFor(() => expect(api.getConfig).toHaveBeenCalledWith('EN'));
  });

  it('warns the user when the backend drops after a successful start', async () => {
    vi.mocked(api.checkHealth).mockRejectedValue(new Error('connection refused'));

    render(<App />);

    await waitFor(() => expect(api.checkHealth).toHaveBeenCalled());
    expect(screen.queryByText(es.backendUnavailable)).not.toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent(es.backendStarting);
  });

  it('shows the error banner when a chat turn fails', async () => {
    vi.mocked(api.sendChatMessage).mockRejectedValue(new Error('Request timed out'));
    render(<App />);
    await screen.findByText('¡Hola!');

    await userEvent.type(screen.getByLabelText(es.inputLabel), 'pregunta');
    await userEvent.click(screen.getByRole('button', { name: new RegExp(es.send) }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Request timed out');
  });

  it('re-initializes the system when the subject changes', async () => {
    render(<App />);
    await screen.findByText('¡Hola!');

    await userEvent.selectOptions(screen.getByLabelText(es.subjectLabel), 'Física');

    await waitFor(() =>
      expect(api.createSystem).toHaveBeenLastCalledWith(
        expect.objectContaining({ subject: 'Física' }),
      ),
    );
  });
});
