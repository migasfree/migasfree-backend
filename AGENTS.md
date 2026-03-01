# AGENTS.md

> **Context for AI Agents working on `migasfree-backend`**
> This file provides the essential context, commands, and conventions for AI agents to work effectively on this project.

## 1. Project Overview

**migasfree-backend** is the server-side component of the Migasfree Systems Management System. It provides a RESTful API for centralized software configuration and fleet management.

- **Framework**: Django 5.x + Django REST Framework (DRF)
- **Database**: PostgreSQL
- **Task Queue**: Celery + Redis
- **Language**: Python 3.10+
- **API Standards**: REST (Token & JWT Auth), OpenAPI 3.0 (Swagger)
- **Legacy Support**: `api_v4` module for backward compatibility with v4 clients.

## 2. Setup & Commands

Always use the virtual environment `migasfree-backend`.

- **Environment Variable**: `export DJANGO_SETTINGS_MODULE='migasfree.settings.development'`
- **Install Dependencies**: `pip install -e .[dev]`
- **Run Server**: `python manage.py runserver 0.0.0.0:8000`
- **Run Migrations**: `python manage.py migrate`
- **Run Tests**: `pytest` or `python manage.py test`
- **Lint Code**: `ruff check .`
- **Format Code**: `ruff format .`
- **Celery Worker**: `celery -A migasfree worker -l info`
- **Celery Beat**: `celery -A migasfree beat -l info`

## 3. Code Style & Conventions

- **Linter/Formatter**: Ruff is authoritative for both linting and formatting.
- **Coding Standards**: Follow PEP 8 and Django best practices.
- **Docstrings**: Use Google-style or standard Sphinx docstrings for complex logic.
- **ORM Efficiency**: Always check for N+1 queries. Use `select_related` and `prefetch_related` liberally in QuerySets and Serializers.
- **Type Hinting**: Use Python type hints where appropriate to improve readability and tool support.

## 4. Architecture Standards

The project is organized into functional modules:

- **`migasfree.core`**: The backbone (projects, deployments, package sets).
- **`migasfree.client`**: Computer management, synchronization logic, and reports.
- **`migasfree.device`**: Peripheral hardware, drivers, and logical devices.
- **`migasfree.hardware`**: Detailed hardware inventory (CPU, RAM, Disks).
- **`migasfree.stats`**: Historical data aggregation and dashboard live stats.
- **`migasfree.api_v4`**: Legacy monolithic API for v4 clients.

## 5. Available Skills & Specialized Constraints

This project is supported by specialized AI Skills in `.agent/skills`. **ALWAYS** check and use these skills:

- **Django & DRF**: `django-expert` (ORM efficiency, API design)
- **Celery & Async**: `celery-expert` (Task queues, synchronization)
- **PostgreSQL**: `postgresql-expert` (Native SQL optimization)
- **Redis**: `redis-expert` (Caching, WebSocket layers)
- **Python Language**: `python-expert` (Pythonic patterns, quality)
- **GraphQL**: `graphql-expert` (If working on Graphene integrations)
- **Bash & Scripting**: `bash-expert` (DevOps and automation scripts)
- **Security**: `security-expert` (API security, mTLS)
- **Documentation**: `docs-expert` (Diátaxis, REST docs)

## 6. Critical Rules

1. **Environment**: ALWAYS use `DJANGO_SETTINGS_MODULE='migasfree.settings.development'` for local commands unless specified otherwise.
2. **Database Integrity**: Be extremely careful with data migrations. Ensure they are reversible.
3. **Registry/Sync Logic**: The synchronization process is performance-critical. Avoid heavy logic inside the sync loop.
4. **User Rules**: Follow specific environment rules in `memory` regarding tool usage (e.g., `npx -y`, `yarnpkg`).
