import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { describe, expect, it, vi } from 'vitest';

import { ChatInterface } from '@app/features/ai-chat/components/ChatInterface';
import es from '@app/i18n/languages/es';

const renderChat = (props = {}) => {
  const onSendMessage = vi.fn();
  const utils = render(
    <ChatInterface
      messages={[]}
      onSendMessage={onSendMessage}
      translations={es}
      isLoading={false}
      error=""
      {...props}
    />,
  );
  return { ...utils, onSendMessage };
};

describe('ChatInterface', () => {
  describe('conversation rendering', () => {
    it('shows the empty state before the first message', () => {
      renderChat();

      expect(screen.getByText(es.emptyChat)).toBeInTheDocument();
    });

    it('hides the empty state while a response is loading', () => {
      renderChat({ isLoading: true });

      expect(screen.queryByText(es.emptyChat)).not.toBeInTheDocument();
      expect(screen.getByRole('status')).toHaveTextContent(es.loading);
    });

    it('renders user messages as plain text', () => {
      renderChat({ messages: [{ id: '1', role: 'user', content: '**not markdown**' }] });

      expect(screen.getByText('**not markdown**')).toBeInTheDocument();
    });

    it('renders assistant messages as markdown', () => {
      renderChat({ messages: [{ id: '1', role: 'assistant', content: '**bold**' }] });

      expect(screen.getByText('bold').tagName).toBe('STRONG');
    });

    it('renders an attached image preview inside the message', () => {
      renderChat({
        messages: [{ id: '1', role: 'user', content: 'look', image: 'blob:preview' }],
      });

      expect(screen.getByAltText(es.uploadPreview)).toHaveAttribute('src', 'blob:preview');
    });

    it('shows the error banner when a turn fails', () => {
      renderChat({ error: 'Request timed out' });

      expect(screen.getByRole('alert')).toHaveTextContent('Request timed out');
    });
  });

  describe('source citations', () => {
    const messageWithSources = {
      id: '1',
      role: 'assistant',
      content: 'answer',
      sources: [
        { doc_id: 'biology/cells.pdf', file_name: 'cells.pdf', page: 4, url: 'https://signed/a' },
        { doc_id: 'biology/genes.pdf', file_name: 'genes.pdf', page: null, url: 'https://signed/b' },
      ],
    };

    it('lists one button per source, with the page when known', () => {
      renderChat({ messages: [messageWithSources] });

      expect(screen.getByText(es.sourcesLabel)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /cells\.pdf · p\.4/ })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /genes\.pdf/ })).toBeInTheDocument();
    });

    it('opens the signed url anchored at the cited page', async () => {
      const open = vi.fn();
      vi.stubGlobal('open', open);
      renderChat({ messages: [messageWithSources] });

      await userEvent.click(screen.getByRole('button', { name: /cells\.pdf/ }));

      expect(open).toHaveBeenCalledWith('https://signed/a#page=4', '_blank', 'noopener');
    });

    it('defaults to page 1 when the source has no page', async () => {
      const open = vi.fn();
      vi.stubGlobal('open', open);
      renderChat({ messages: [messageWithSources] });

      await userEvent.click(screen.getByRole('button', { name: /genes\.pdf/ }));

      expect(open).toHaveBeenCalledWith('https://signed/b#page=1', '_blank', 'noopener');
    });

    it('does not render a sources section for user messages', () => {
      renderChat({ messages: [{ ...messageWithSources, role: 'user' }] });

      expect(screen.queryByText(es.sourcesLabel)).not.toBeInTheDocument();
    });
  });

  describe('composer', () => {
    it('disables sending until there is something to send', async () => {
      renderChat();
      const sendButton = screen.getByRole('button', { name: new RegExp(es.send) });

      expect(sendButton).toBeDisabled();

      await userEvent.type(screen.getByLabelText(es.inputLabel), 'hola');

      expect(sendButton).toBeEnabled();
    });

    it('stays disabled while a response is in flight', async () => {
      renderChat({ isLoading: true });

      await userEvent.type(screen.getByLabelText(es.inputLabel), 'hola');

      expect(screen.getByRole('button', { name: new RegExp(es.send) })).toBeDisabled();
    });

    it('sends the typed message and clears the input', async () => {
      const { onSendMessage } = renderChat();
      const input = screen.getByLabelText(es.inputLabel);

      await userEvent.type(input, '¿Qué es la mitosis?');
      await userEvent.click(screen.getByRole('button', { name: new RegExp(es.send) }));

      expect(onSendMessage).toHaveBeenCalledWith('¿Qué es la mitosis?', null);
      expect(input).toHaveValue('');
    });

    it('sends on Enter', async () => {
      const { onSendMessage } = renderChat();

      await userEvent.type(screen.getByLabelText(es.inputLabel), 'hola{Enter}');

      expect(onSendMessage).toHaveBeenCalledWith('hola', null);
    });

    it('ignores whitespace-only input', async () => {
      const { onSendMessage } = renderChat();

      await userEvent.type(screen.getByLabelText(es.inputLabel), '   {Enter}');

      expect(onSendMessage).not.toHaveBeenCalled();
    });
  });

  describe('image attachment', () => {
    const attach = async (container, file) => {
      const fileInput = container.querySelector('input[type="file"]');
      await userEvent.upload(fileInput, file);
      return fileInput;
    };

    it('shows the chosen file name and sends it alongside the text', async () => {
      const { container, onSendMessage } = renderChat();
      const file = new File(['x'], 'exercise.png', { type: 'image/png' });

      await attach(container, file);
      expect(screen.getByText('exercise.png')).toBeInTheDocument();

      await userEvent.type(screen.getByLabelText(es.inputLabel), 'resuélvelo');
      await userEvent.click(screen.getByRole('button', { name: new RegExp(es.send) }));

      expect(onSendMessage).toHaveBeenCalledWith('resuélvelo', file);
    });

    it('allows sending an image with no text', async () => {
      const { container, onSendMessage } = renderChat();
      const file = new File(['x'], 'exercise.png', { type: 'image/png' });

      await attach(container, file);
      await userEvent.click(screen.getByRole('button', { name: new RegExp(es.send) }));

      expect(onSendMessage).toHaveBeenCalledWith('', file);
    });

    it('removes the attachment when the remove button is used', async () => {
      const { container } = renderChat();

      await attach(container, new File(['x'], 'exercise.png', { type: 'image/png' }));
      await userEvent.click(screen.getByRole('button', { name: es.removeImage }));

      expect(screen.queryByText('exercise.png')).not.toBeInTheDocument();
    });

    it('clears the attachment after sending', async () => {
      const { container } = renderChat();

      await attach(container, new File(['x'], 'exercise.png', { type: 'image/png' }));
      await userEvent.click(screen.getByRole('button', { name: new RegExp(es.send) }));

      expect(screen.queryByText('exercise.png')).not.toBeInTheDocument();
    });

    it('opens the file picker from the attach button', async () => {
      const { container } = renderChat();
      const fileInput = container.querySelector('input[type="file"]');
      const click = vi.spyOn(fileInput, 'click').mockImplementation(() => {});

      await userEvent.click(screen.getByRole('button', { name: es.attachImage }));

      expect(click).toHaveBeenCalled();
    });
  });

  it('exposes the message log to assistive technology', () => {
    renderChat({ messages: [{ id: '1', role: 'assistant', content: 'answer' }] });

    const log = screen.getByLabelText(es.messagesLabel);
    expect(log).toHaveAttribute('aria-live', 'polite');
    expect(within(log).getByText('answer')).toBeInTheDocument();
  });
});
