# Single-image build: React/Vite frontend + FastAPI backend, served from one container.

# ---- Stage 1: build the frontend static assets ----
FROM node:24-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: backend runtime, serving the built frontend as static files ----
FROM python:3.12-slim AS backend
WORKDIR /app

# System deps kept minimal; gunicorn/uvicorn come from requirements.txt.
COPY src/requirements.txt ./src/requirements.txt
RUN pip install --no-cache-dir -r src/requirements.txt

COPY src/ ./src/
COPY vector_db/ ./vector_db/
COPY prompts/ ./prompts/
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x entrypoint.sh

# Built frontend is served by FastAPI's StaticFiles mount (see src/api/app.py).
COPY --from=frontend-build /app/frontend/dist ./frontend_dist

ENV PORT=8080
EXPOSE 8080

ENTRYPOINT ["./entrypoint.sh"]
