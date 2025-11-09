# ============================
# Stage 1 — Builder
# ============================
FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install minimal build and runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libspatialindex-dev \
    libxml2-dev \
    libxslt-dev \
    libffi-dev \
    libssl-dev \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# ============================
# Stage 2 — Runtime
# ============================
FROM python:3.11-slim AS runtime

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Only runtime libs (no compilers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libspatialindex-dev \
    libxml2 \
    libxslt1.1 \
    libffi8 \
    libssl3 \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy Python env from builder
COPY --from=builder /usr/local /usr/local

# Copy project files
COPY . /app/

COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]
