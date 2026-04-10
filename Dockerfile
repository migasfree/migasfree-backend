# Dockerfile
# Pinned version for determinism across environments
FROM python:3.11-slim-bookworm

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

# Install python dependencies from lockfile for determinism
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Install the migasfree-backend package itself
RUN pip install --no-cache-dir --no-deps .

# Create necessary directories for local dev (if they match settings)
RUN mkdir -p /var/lib/migasfree-backend/public /var/lib/migasfree-backend/keys /var/lib/migasfree-backend/static

# Create a non-root user and set directory permissions
RUN groupadd -r migasfree && useradd -r -g migasfree migasfree \
    && chown -R migasfree:migasfree /app /var/lib/migasfree-backend

# Switch to the non-root user for security
USER migasfree

# Expose port
EXPOSE 8000

# Default command (can be overridden by compose)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "migasfree.asgi:application"]
