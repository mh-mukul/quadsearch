#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

echo "Initializing Docker entrypoint..."

echo "Starting supervisord..."

mkdir -p /app/logs /app/logs/console /app/logs/celery

/usr/bin/supervisord -c /app/supervisord.conf
