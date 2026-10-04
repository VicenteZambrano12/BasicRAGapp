import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import * as api from '@app/lib/api';
import { useChatStore } from '@app/features/ai-chat/hooks/useChatStore';

vi.mock('@app/lib/api');

const CONFIG = {
  communities: ['Andalucía', 'Cataluña'],
  subjects: ['Biología', 'Física'],
};

/** Puts the hook in the "backend up, system initialized" state used by most tests. */
const renderReadyStore = async () => {
  const view = renderHook(() => useChatStore());
  await waitFor(() => expect(view.result.current.isBackendStarting).toBe(false));
  await waitFor(() => expect(api.createSystem).toHaveBeenCalled());
  return view;
};

describe('useChatStore', () => {
  beforeEach(() => {
    vi.mocked(api.checkHealth).mockResolvedValue({ message: 'PAUHelper is running' });
    vi.mocked(api.getConfig).mockResolvedValue(CONFIG);
    vi.mocked(api.createSystem).mockResolvedValue({ response: '¡Hola!' });
    vi.mocked(api.sendChatMessage).mockResolvedValue({ response: 'respuesta', sources: [] });
    vi.mocked(api.fileToDataUrl).mockResolvedValue('data:image/png;base64,AAA');
  });

  describe('startup', () => {
    it('starts in the "backend starting" state', () => {
      vi.mocked(api.checkHealth).mockReturnValue(new Promise(() => {}));

      const { result } = renderHook(() => useChatStore());

      expect(result.current.isBackendStarting).toBe(true);
      expect(result.current.isBackendAvailable).toBe(false);
    });

    it('marks the backend available once the health check succeeds', async () => {
      const { result } = renderHook(() => useChatStore());

      await waitFor(() => expect(result.current.isBackendAvailable).toBe(true));
      expect(result.current.isBackendStarting).toBe(false);
    });

    it('keeps polling until the backend answers', async () => {
      vi.useFakeTimers();
      vi.mocked(api.checkHealth)
        .mockRejectedValueOnce(new Error('connection refused'))
        .mockResolvedValue({});

      const { result } = renderHook(() => useChatStore());

      await vi.waitFor(() => expect(api.checkHealth).toHaveBeenCalledTimes(1));
      expect(result.current.isBackendStarting).toBe(true);

      await act(async () => {
        await vi.advanceTimersByTimeAsync(3000);
      });

      expect(api.checkHealth).toHaveBeenCalledTimes(2);
      expect(result.current.isBackendStarting).toBe(false);
    });
  });

  describe('study configuration', () => {
    it('loads the options and preselects the first of each', async () => {
      const { result } = await renderReadyStore();

      expect(result.current.communities).toEqual(CONFIG.communities);
      expect(result.current.subjects).toEqual(CONFIG.subjects);
      expect(result.current.config).toMatchObject({
        region: 'Andalucía',
        subject: 'Biología',
        language: 'ES',
      });
    });

    it('reloads the options when the language changes', async () => {
      const { result } = await renderReadyStore();

      act(() => result.current.updateConfig('language', 'EN'));

      await waitFor(() => expect(api.getConfig).toHaveBeenCalledWith('EN'));
    });

    it('keeps the chosen region and subject across a language switch', async () => {
      const { result } = await renderReadyStore();

      act(() => result.current.updateConfig('subject', 'Física'));
      act(() => result.current.updateConfig('language', 'EN'));

      await waitFor(() => expect(api.getConfig).toHaveBeenCalledWith('EN'));
      expect(result.current.config.subject).toBe('Física');
    });

    it('surfaces a config loading failure', async () => {
      vi.mocked(api.getConfig).mockRejectedValue(new Error('Request failed (500)'));
      const { result } = renderHook(() => useChatStore());

      await waitFor(() => expect(result.current.error).toBe('Request failed (500)'));
    });

    it('tolerates a config payload without options', async () => {
      vi.mocked(api.getConfig).mockResolvedValue({});
      const { result } = renderHook(() => useChatStore());

      await waitFor(() => expect(result.current.isBackendAvailable).toBe(true));
      expect(result.current.communities).toEqual([]);
      expect(result.current.config.region).toBe('');
      expect(api.createSystem).not.toHaveBeenCalled();
    });
  });

  describe('system initialization', () => {
    it('initializes the session and seeds the welcome message', async () => {
      const { result } = await renderReadyStore();

      expect(api.createSystem).toHaveBeenCalledWith({
        session_id: expect.any(String),
        category: 'Andalucía',
        subject: 'Biología',
        language: 'ES',
      });
      expect(result.current.messages).toEqual([
        { id: expect.any(String), role: 'assistant', content: '¡Hola!' },
      ]);
    });

    it('re-initializes and resets the transcript when the subject changes', async () => {
      const { result } = await renderReadyStore();

      vi.mocked(api.createSystem).mockResolvedValue({ response: '¡Hola de nuevo!' });
      act(() => result.current.updateConfig('subject', 'Física'));

      await waitFor(() =>
        expect(result.current.messages).toEqual([
          { id: expect.any(String), role: 'assistant', content: '¡Hola de nuevo!' },
        ]),
      );
      expect(api.createSystem).toHaveBeenLastCalledWith(
        expect.objectContaining({ subject: 'Física' }),
      );
    });

    it('surfaces an initialization failure', async () => {
      vi.mocked(api.createSystem).mockRejectedValue(new Error('Qdrant collection missing'));
      const { result } = renderHook(() => useChatStore());

      await waitFor(() => expect(result.current.error).toBe('Qdrant collection missing'));
    });
  });

  describe('sending messages', () => {
    it('appends the user turn and then the assistant answer', async () => {
      vi.mocked(api.sendChatMessage).mockResolvedValue({
        response: 'La mitosis es...',
        sources: [{ doc_id: 'a', file_name: 'a.pdf', page: 1, url: 'https://signed/a' }],
      });
      const { result } = await renderReadyStore();

      await act(() => result.current.sendMessage('¿Qué es la mitosis?'));

      expect(result.current.messages.slice(1)).toEqual([
        {
          id: expect.any(String),
          role: 'user',
          content: '¿Qué es la mitosis?',
          image: null,
        },
        {
          id: expect.any(String),
          role: 'assistant',
          content: 'La mitosis es...',
          sources: [{ doc_id: 'a', file_name: 'a.pdf', page: 1, url: 'https://signed/a' }],
        },
      ]);
    });

    it('sends the active study configuration with the message', async () => {
      const { result } = await renderReadyStore();

      await act(() => result.current.sendMessage('pregunta'));

      expect(api.sendChatMessage).toHaveBeenCalledWith({
        session_id: expect.any(String),
        query: 'pregunta',
        image: null,
        image_type: 'url',
        category: 'Andalucía',
        subject: 'Biología',
        language: 'ES',
      });
    });

    it('reuses the same session id across turns', async () => {
      const { result } = await renderReadyStore();

      await act(() => result.current.sendMessage('una'));
      await act(() => result.current.sendMessage('dos'));

      const [first, second] = vi.mocked(api.sendChatMessage).mock.calls;
      expect(first[0].session_id).toBe(second[0].session_id);
    });

    it('uploads an attached image as a base64 data url', async () => {
      const { result } = await renderReadyStore();
      const file = new File(['x'], 'exercise.png', { type: 'image/png' });

      await act(() => result.current.sendMessage('resuélvelo', file));

      expect(api.fileToDataUrl).toHaveBeenCalledWith(file);
      expect(api.sendChatMessage).toHaveBeenCalledWith(
        expect.objectContaining({
          image: 'data:image/png;base64,AAA',
          image_type: 'base64',
        }),
      );
      expect(result.current.messages[1].image).toBe('blob:mock-object-url');
    });

    it('ignores empty and whitespace-only messages', async () => {
      const { result } = await renderReadyStore();

      await act(() => result.current.sendMessage('   '));

      expect(api.sendChatMessage).not.toHaveBeenCalled();
      expect(result.current.messages).toHaveLength(1);
    });

    it('toggles the loading flag around the request', async () => {
      let resolveRequest;
      vi.mocked(api.sendChatMessage).mockReturnValue(
        new Promise((resolve) => {
          resolveRequest = resolve;
        }),
      );
      const { result } = await renderReadyStore();

      let pending;
      act(() => {
        pending = result.current.sendMessage('pregunta');
      });
      await waitFor(() => expect(result.current.isLoading).toBe(true));

      await act(async () => {
        resolveRequest({ response: 'respuesta', sources: [] });
        await pending;
      });

      expect(result.current.isLoading).toBe(false);
    });

    it('keeps the user turn and reports the error when the request fails', async () => {
      vi.mocked(api.sendChatMessage).mockRejectedValue(new Error('Request timed out'));
      const { result } = await renderReadyStore();

      await act(() => result.current.sendMessage('pregunta'));

      expect(result.current.error).toBe('Request timed out');
      expect(result.current.isLoading).toBe(false);
      expect(result.current.messages).toHaveLength(2);
    });

    it('defaults a missing response body to empty content and no sources', async () => {
      vi.mocked(api.sendChatMessage).mockResolvedValue({});
      const { result } = await renderReadyStore();

      await act(() => result.current.sendMessage('pregunta'));

      expect(result.current.messages.at(-1)).toMatchObject({ content: '', sources: [] });
    });
  });
});
