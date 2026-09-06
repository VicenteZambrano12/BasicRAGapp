# PAUHelper

PAUHelper is a retrieval-augmented study assistant for Spain's university entrance exam (PAU). It provides localized AI chat support using curriculum context selected by autonomous community, subject, and language.

## Project Structure

- `frontend/`: React and Vite user interface for study configuration, chat, image attachments, localization, and the How It Works PDF.
- `src/`: FastAPI backend and application services.
- `vector_db/`: Vector database management and migration utilities.
- `content/`: Subject and regional curriculum source material.
- `prompts/`: Regional and subject-specific prompt content.
- `infra/`: Terraform infrastructure configuration.

## Frontend Module

The `frontend/src` module renders the PAUHelper application workspace. It manages study configuration, localized chat interactions, image attachments, loading and error states, backend communication, and the How It Works PDF experience.

The frontend relies on React, ReactDOM, Vite, and Tailwind CSS. Chat configuration, messages, request state, and errors are managed through the `useChatStore` hook. Backend requests use the `VITE_API_URL` environment variable and default to `http://localhost:8000`.

## Backend API Module

The `src/api` module exposes the FastAPI entry point for PAUHelper. It composes the application lifecycle, publishes localized study configuration, initializes session-specific retrieval systems, and handles text or image-assisted chat requests.

Key endpoints include `GET /` for health and cache diagnostics, `GET /config` for localized communities and subjects, `POST /create_system` for session system initialization, and `POST /chat` for assistant responses.

## Requirements

- Python 3.12 or later
- Node.js and npm
- Docker and Docker Compose for the containerized setup
- Google Cloud credentials for Vertex AI or Gemini integrations
- Qdrant and Redis, provided by Docker Compose or equivalent services

## Configuration

Copy `.env.sample` to `.env` and configure the required values, including:

- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_CLOUD_LOCATION`
- `GOOGLE_APPLICATION_CREDENTIALS`
- `LLM_MODEL`
- `EMBEDDING_MODEL`
- `VECTOR_DB_TYPE`
- Qdrant connection settings when using Qdrant Cloud

Keep service-account credentials outside version control.

## Run With Docker Compose

```bash
docker compose up --build
```

The backend is available at `http://localhost:8000`. Qdrant is exposed on ports `6333` and `6334`, and Redis is exposed on port `6379`.

## Run the Frontend Locally

```bash
cd frontend
npm install
npm run dev
```

The Vite development server runs on port `3000` by default. To point the frontend at a different backend, set `VITE_API_URL` before starting Vite.

To create a production frontend bundle:

```bash
cd frontend
npm run build
```

## Populate the Knowledge Base

The ingestion script processes the source material used by the retrieval system:

```bash
python ingest.py
```

## Testing

Backend API tests can be run with:

```bash
pytest
```

The frontend production build can be validated with:

```bash
cd frontend
npm run build
```
