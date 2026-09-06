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
- uv
- Node.js and npm
- Google Cloud credentials for Vertex AI or Gemini integrations
- Qdrant and Redis services

## Local Python Setup with uv

Install `uv` if it is not already available:

Windows PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

macOS or Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

From the repository root, remove an existing virtual environment, create a new one, and install the backend dependencies:

Windows PowerShell:

```powershell
Remove-Item -Recurse -Force venv, .venv, env -ErrorAction SilentlyContinue
uv venv
uv pip install --python .venv\Scripts\python.exe -r src\requirements.txt
```

macOS or Linux:

```bash
rm -rf venv .venv env
uv venv
uv pip install --python .venv/bin/python -r src/requirements.txt
```

To record the installed, resolved versions back into the dependency file:

Windows PowerShell:

```powershell
uv pip freeze --python .venv\Scripts\python.exe | Set-Content src\requirements.txt
```

macOS or Linux:

```bash
uv pip freeze --python .venv/bin/python > src/requirements.txt
```

The commands below use `uv run`, so manually activating the virtual environment is optional.

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

## Run the Backend Locally

Start the API with:

```bash
uv run uvicorn src.app:app --reload --host 0.0.0.0 --port 8000
```

The backend is available at `http://localhost:8000`. Ensure that Qdrant and Redis are running through your preferred local or hosted service.

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
uv run python ingest.py
```

## Testing

Backend API tests can be run with:

```bash
uv run --with pytest pytest
```

The frontend production build can be validated with:

```bash
cd frontend
npm run build
```
