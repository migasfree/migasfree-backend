# Dockerfile
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MIGASFREE_PROJECT_DIR=/app \
    DJANGO_SETTINGS_MODULE=migasfree.settings.development

WORKDIR /app

# Install system dependencies
# Aligned with migasfree-swarm build/core/Dockerfile
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    libpq-dev \
    libcairo2-dev \
    libjpeg62-turbo-dev \
    libxml2-dev \
    libxslt1-dev \
    libmagic1 \
    swig \
    postgresql-client \
    netcat-traditional \
    procps \
    curl \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies from pyproject.toml
COPY pyproject.toml .
# No requirements.txt available, so we install the package in editable mode or build strictly from pyproject
# Using pip install . to install dependencies defined in pyproject.toml
RUN pip install --no-cache-dir .[dev]

# Copy project files
COPY . .

# Create necessary directories for local dev (if they match settings)
RUN mkdir -p /var/lib/migasfree-backend/public /var/lib/migasfree-backend/keys /var/lib/migasfree-backend/static

# Expose port
EXPOSE 8000

# Default command (can be overridden by compose)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "migasfree.asgi:application"]
