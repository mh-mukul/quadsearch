#!/bin/bash
set -e

echo "Initializing Docker entrypoint..."

# Create directories if not exist
mkdir -p /app/data/artifacts /app/data/logs /app/data/logs/console /app/data/logs/celery

# -----------------------------------
# Download models if they don’t exist
# -----------------------------------
if [ ! -d "/app/data/artifacts/all-MiniLM-L6-v2" ]; then
  echo "Downloading SentenceTransformer model..."
  huggingface-cli download sentence-transformers/all-MiniLM-L6-v2 --local-dir /app/data/artifacts/all-MiniLM-L6-v2
else
  echo "SentenceTransformer model already exists. Skipping download."
fi

if [ ! -d "/app/data/artifacts/ms-marco-MiniLM-L-6-v2" ]; then
  echo "Downloading CrossEncoder model..."
  huggingface-cli download cross-encoder/ms-marco-MiniLM-L-6-v2 --local-dir /app/data/artifacts/ms-marco-MiniLM-L-6-v2
else
  echo "CrossEncoder model already exists. Skipping download."
fi

if [ ! -d "/app/data/artifacts/docling" ]; then
  echo "Downloading Docling models..."
  docling-tools models download -o /app/data/artifacts
else
  echo "Docling models already exist. Skipping download."
fi

echo "Starting supervisord..."
/usr/bin/supervisord -c /app/supervisord.conf
