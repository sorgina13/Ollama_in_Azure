#!/bin/sh
set -eu

export OLLAMA_HOST="${OLLAMA_HOST:-0.0.0.0:11434}"

cleanup() {
  kill "$OLLAMA_PID"
  wait "$OLLAMA_PID"
}

ollama serve &
OLLAMA_PID=$!

trap cleanup INT TERM

echo "Waiting for Ollama to accept connections on ${OLLAMA_HOST}..."
attempt=0
until curl -fsS "http://127.0.0.1:11434/api/tags" >/dev/null; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 60 ]; then
    echo "Ollama did not become ready in time."
    exit 1
  fi
  sleep 2
done

if [ -n "${OLLAMA_MODEL:-}" ]; then
  echo "Pulling model ${OLLAMA_MODEL}..."
  ollama pull "${OLLAMA_MODEL}"
fi

if [ -n "${APP_SCRIPT:-}" ]; then
  echo "Running /app/${APP_SCRIPT}..."
  python3 "/app/${APP_SCRIPT}"
fi

wait "$OLLAMA_PID"