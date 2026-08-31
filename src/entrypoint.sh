#!/bin/bash
set -e

cd /app/

# Calculate workers based on CPU and memory constraints
CPU_COUNT=$(nproc)
WORKERS=${WORKERS:-$((CPU_COUNT * 2 + 1))}

# Cloud Run memory-aware limits
# Adjust based on your container's memory allocation
MAX_WORKERS=${MAX_WORKERS:-8}
if [ "$WORKERS" -gt "$MAX_WORKERS" ]; then
  WORKERS=$MAX_WORKERS
fi

echo "Starting Gunicorn with $WORKERS workers on $CPU_COUNT CPUs"

exec /opt/venv/bin/gunicorn \
  -k uvicorn.workers.UvicornWorker \
  src.app:app \
  --bind "0.0.0.0:${PORT:-8080}" \
  --workers $WORKERS \
  --worker-connections 1000 \
  --timeout 600 \
  --graceful-timeout 120 \
  --keep-alive 75 \
  --max-requests 10000 \
  --max-requests-jitter 1000 \
  --worker-tmp-dir /dev/shm \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  --capture-output \
  --enable-stdio-inheritance