#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

echo "Updating and installing packages..."

chmod 644 /etc/resolv.conf

# Update and install required system packages
apt-get update && apt-get install -y \
    nano \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

echo "Entrypoint script finished. Starting application..."

echo "Starting supervisord..."

mkdir -p /app/logs /app/logs/console /app/logs/celery

/usr/bin/supervisord -c /app/supervisord.conf
