#!/bin/bash
set -e

echo "Initializing Docker entrypoint..."

# Create directories if not exist
mkdir -p /app/data/artifacts /app/data/logs /app/data/logs/console /app/data/logs/celery

# Load environment variables from .env if present
if [ -f ".env" ]; then
  echo "Loading environment variables from .env"
  export $(grep -v '^#' .env | xargs)
fi

# -----------------------------------
# Download models if they don’t exist
# -----------------------------------
echo "Downloading Embedding model..."
hf download "sentence-transformers/$EMBEDDING_MODEL" --local-dir /app/data/artifacts/$EMBEDDING_MODEL
echo "Download complete."

echo "Downloading Reranker model..."
hf download "cross-encoder/$RERANKER_MODEL" --local-dir /app/data/artifacts/$RERANKER_MODEL
echo "Download complete."

echo "Downloading Chunker model..."
hf download "sentence-transformers/$CHUNKER_MODEL" --local-dir /app/data/artifacts/$CHUNKER_MODEL
echo "Download complete."

echo "Downloading Docling models..."
docling-tools models download -o /app/data/artifacts
echo "Download complete."

echo "Starting supervisord..."
/usr/bin/supervisord -c /app/supervisord.conf
