# 🛠️ How-to: Set Up Development Environment

This guide explains how to configure your local machine for contributing to migasfree-backend.

## Prerequisites

- **Python**: 3.10+
- **Database**: PostgreSQL 12+
- **Cache**: Redis 6+
- **VCS**: Git

## Installation Steps

1. **Clone the repository**:

    ```bash
    git clone https://github.com/migasfree/migasfree-backend.git
    cd migasfree-backend
    ```

2. **Create virtual environment**:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install dependencies**:

    ```bash
    pip install -e .[dev]
    ```

4. **Configure environment variables**:

    ```bash
    export DJANGO_SETTINGS_MODULE='migasfree.settings.development'
    ```

5. **Initialize Database**:

    ```bash
    python3 manage.py migrate
    python3 manage.py createsuperuser
    ```

## Running the Server

```bash
python3 manage.py runserver 0.0.0.0:8000
```
