# Tests

```
tests/
├── backend/          # pytest, FastAPI TestClient
│   ├── conftest.py   # env isolation (forces fakeredis), cache reset, TestClient fixtures
│   ├── factories.py  # fake LangChain/LangGraph objects
│   ├── unit/
│   └── integration/
└── frontend/         # Vitest + Testing Library, jsdom
    ├── setup.js
    ├── unit/
    └── integration/
```

## Backend

```powershell
uv pip install -r tests/requirements.txt   # once, on top of src/requirements.txt
.\.venv\Scripts\python.exe -m pytest                     # whole suite
.\.venv\Scripts\python.exe -m pytest -m integration      # HTTP + orchestration only
.\.venv\Scripts\python.exe -m pytest --cov=src --cov=vector_db
```

Configuration lives in [pytest.ini](../pytest.ini). No external service is required:
`conftest.py` blanks `REDIS_URL`/`REDIS_HOST` so the cache layer falls back to
fakeredis, the `TestClient` fixtures skip the startup lifespan (no Qdrant or Vertex
connection), and every test that would reach Qdrant, Gemini or GCS stubs that
boundary out.

## Frontend

```powershell
cd frontend
npm install
npm test                # whole suite
npm run test:watch
npm run test:coverage
```

Configuration lives in [frontend/vitest.config.js](../frontend/vitest.config.js).
Source files are imported through the `@app` alias (`frontend/src`). The network is
never touched: `fetch` is stubbed in the api-client tests and `@app/lib/api` is mocked
in the hook/page tests.

## Pre-push hook

Both suites run automatically on `git push`. Enable the hook once per clone:

```powershell
.\scripts\setup-hooks.ps1     # or: sh scripts/setup-hooks.sh
```

This sets `core.hooksPath` to [.githooks](../.githooks), where
[pre-push](../.githooks/pre-push) lives. It only runs the suite whose sources changed in
the commits being pushed (`src/`, `vector_db/`, `tests/backend/`, `pytest.ini` or a
`requirements.txt` for pytest; `frontend/` or `tests/frontend/` for Vitest), and falls
back to running everything when the pushed range cannot be resolved.

To bypass it: `SKIP_TESTS=1 git push` or `git push --no-verify`. The same commands run
in CI via [.github/workflows/tests.yml](../.github/workflows/tests.yml), which cannot be
bypassed.
