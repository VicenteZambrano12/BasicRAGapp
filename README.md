# PAUHelper

PAUHelper is a retrieval-augmented study assistant for Spain's university entrance exam (PAU). Students select an autonomous community, subject, and language, then ask curriculum-grounded questions in a chat interface. The app supports English and Spanish, including image-assisted questions.

## Project structure

- `frontend/`: React and Vite user interface, localization, chat, and static assets.
- `src/`: FastAPI backend, API routes, retrieval workflow, and application services.
- `vector_db/`: Qdrant client and curriculum ingestion utilities.
- `content/`: Source curriculum material organized by subject.
- `config/`: Localized study configuration.
- `infra/`: Terraform infrastructure configuration.
- `tests/`: Backend pytest and frontend Vitest suites.

## Requirements

- Python 3.12 or later
- [uv](https://docs.astral.sh/uv/)
- Node.js 24 and npm
- Google AI / Google Cloud credentials for the configured language model and embeddings
- A Qdrant instance containing the curriculum data

Redis is optional for local development. Without a reachable Redis configured through `REDIS_URL` or `REDIS_HOST`, the backend uses an in-memory cache. That cache is not shared between processes or retained across restarts; configure Redis when running multiple backend workers.

## Configuration

Create a root `.env` from the sample file:

```powershell
Copy-Item .env.sample .env
```

Set the values appropriate for your environment. The sample lists the supported settings, including:

- Model access: `GEMINI_API_KEY`, `GCP_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS`, `GOOGLE_GENAI_USE_ENTERPRISE`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `LLM_MODEL`, and `EMBEDDING_MODEL`.
- Vector database: `QDRANT_URL` and `QDRANT_API_KEY` for Qdrant Cloud, or `QDRANT_HOST` and `QDRANT_PORT` for a self-hosted instance.
- Documents and ingestion: `GCS_BUCKET_NAME` and `CONTENT_DIRECTORY`.
- Runtime mode: `MODE` (`LOCAL` for local development).

Only configure the credentials and service settings needed by your selected integrations. Keep `.env` and service-account credentials out of version control.

## Run locally

### Backend

From the repository root, create a virtual environment and install the backend requirements:

```powershell
uv venv
uv pip install --python .venv\Scripts\python.exe -r src\requirements.txt
```

On macOS or Linux, use `.venv/bin/python` in place of `.venv\Scripts\python.exe` in the commands below.

Start the API from the repository root:

```powershell
.venv\Scripts\python.exe -m uvicorn src.app:app --reload --host 0.0.0.0 --port 8000
```

The API is available at `http://localhost:8000`; interactive API documentation is at `http://localhost:8000/docs`. The backend attempts to initialize its embedding model and connect to Qdrant on startup, so configure valid credentials and a reachable vector database for full functionality.

### Frontend

In a separate terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open `http://localhost:3000`. In local mode, Vite proxies `/api` requests to the backend at `http://localhost:8000`. The frontend's API base defaults to `/api`; set `VITE_API_URL` if the API is hosted at a different base URL.

To build the production frontend bundle:

```powershell
npm run build
```

## API

API routes are prefixed with `/api`:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/` | Health and cache diagnostics |
| `GET` | `/api/config?language=ES` | Localized communities and subjects (`ES` or `EN`) |
| `POST` | `/api/create_system` | Initialize a study system for the selected session context |
| `POST` | `/api/chat` | Send a text or image-assisted chat request |
| `GET` | `/api/docs/how-it-works?language=ES` | Redirect to the localized How It Works PDF in Google Cloud Storage |

See `/docs` on a running backend for request and response schemas.

## Ingest curriculum content

Run the ingestion utility from the repository root. By default it reads `./content`; set `CONTENT_DIRECTORY` to use another source directory. Configure Google credentials and Qdrant before running:

```powershell
.venv\Scripts\python.exe vector_db\ingest.py
```

## Tests

Install the backend and test requirements, then run pytest from the repository root:

```powershell
uv pip install --python .venv\Scripts\python.exe -r src\requirements.txt -r tests\requirements.txt
.venv\Scripts\python.exe -m pytest
```

Run the frontend tests from `frontend/`:

```powershell
npm test
```

The frontend production build can also be checked with `npm run build`. Test setup stubs external service boundaries, so the suites do not require live Qdrant, Google AI, or Google Cloud Storage services. See [tests/README.md](tests/README.md) for test organization, coverage commands, and details.

Both suites run in GitHub Actions and can run before `git push` when the repository hook is enabled:

```powershell
.\scripts\setup-hooks.ps1
```

On macOS or Linux, run `sh scripts/setup-hooks.sh`.

## Container

The root `Dockerfile` builds the Vite frontend and packages it with the FastAPI backend in a single image. Build it from the repository root:

```powershell
docker build -t pauhelper .
```

The container listens on port `8080` by default (or the `PORT` value supplied by the runtime). Provide the required model, Qdrant, and Google Cloud settings to the container environment. For local Docker runs, make Application Default Credentials or the credentials file available inside the container as well. Terraform configuration for infrastructure is in `infra/`.
