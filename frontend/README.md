# BasicRAGapp Frontend

This directory contains the React and Vite frontend for BasicRAGapp. It provides the PAUHelper study interface for configuring a study context, chatting with the AI assistant, attaching exercise images, switching languages, and viewing the How It Works document.

## Structure

- `src/` contains the application entry point, layouts, pages, feature components, chat state, API helpers, localization, and utilities.
- `src/features/ai-chat/` contains the study configuration, chat interface, and `useChatStore` hook.
- `src/lib/` contains backend API integrations.
- `src/i18n/` contains the supported English and Spanish translations.
- `public/` contains static frontend assets.

## Requirements

- Node.js and npm
- React `18.3.x`
- Vite `5.x`
- Tailwind CSS `3.x`
- A running BasicRAGapp backend, available at `http://localhost:8000` by default

## Configuration

Set `VITE_API_URL` when the backend is hosted at a non-default URL:

```powershell
$env:VITE_API_URL = "http://localhost:8000"
```

The frontend sends chat and study-context requests to the backend API. The chat state is managed locally by `useChatStore`.

## Development

```powershell
npm install
npm run dev
```

The Vite development server runs on port `3000` by default.

## Production Build

```powershell
npm run build
npm run preview
```

`npm run build` creates the production bundle in `dist/`. `npm run preview` serves the generated bundle locally.

## Available Scripts

- `npm run dev` starts the Vite development server.
- `npm run build` creates the production bundle.
- `npm run preview` previews the production bundle locally.

This file is the single frontend-level guide; application behavior is documented through the source module structure and component contracts.
