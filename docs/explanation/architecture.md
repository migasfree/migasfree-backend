# Architecture

This document describes the architecture and organization of the **migasfree-backend** project.

## Overview

Migasfree-backend is a Django REST Framework application that provides the backend API for the migasfree computer management system. It manages software deployment, device configuration, and computer inventory across organizations.

## Technology Stack

- **Python**: 3.10+
- **Django**: 5.2+
- **Django REST Framework**: 3.16+
- **Database**: PostgreSQL (via psycopg2)
- **Cache / Message Broker**: Redis
- **Task Queue**: Celery
- **WebSockets**: Django Channels + Daphne
- **API Documentation**: drf-spectacular (OpenAPI 3.0)

## Project Structure

```text
migasfree-backend/
├── migasfree/              # Main Django application package
│   ├── api_v4/             # Legacy API v4 (compatibility layer)
│   ├── app_catalog/        # Application catalog management
│   ├── client/             # Computer/client management
│   ├── core/               # Core models and utilities
│   ├── device/             # Device and driver management
│   ├── hardware/           # Hardware inventory
│   ├── stats/              # Statistics and reporting
│   ├── settings/           # Django settings (base, dev, prod)
│   └── i18n/               # Internationalization
├── tests/                  # Test suite
├── manage.py               # Django management script
├── pyproject.toml          # Project configuration
└── pytest.ini              # Test configuration
```

## Django Apps

### Core (`migasfree/core/`)

The foundation of the system. Contains:

- **Models**: `Platform`, `Project`, `Deployment`, `Package`, `Store`, `Attribute`, `Property`, `Domain`, `Scope`, `UserProfile`
- **PMS Modules**: Package Management System handlers (apt, dnf, yum, pacman, zypper, winget)
- **Serializers**: REST API data serialization
- **Views**: API endpoints (ViewSets)

### Client (`migasfree/client/`)

Manages computer entities:

- **Models**: `Computer`, `Error`, `Fault`, `FaultDefinition`, `Message`, `Migration`, `Notification`, `StatusLog`, `Synchronization`, `User`
- **Tasks**: Celery async tasks for computer operations

### Device (`migasfree/device/`)

Device and printer management:

- **Models**: `Type`, `Manufacturer`, `Model`, `Connection`, `Capability`, `Driver`, `Device`, `Logical`
- **Features**: Logical device allocation, driver management

### Hardware (`migasfree/hardware/`)

Hardware inventory:

- **Models**: `Node`, `Capability`, `Configuration`, `LogicalName`
- **Features**: Hardware tree parsing (lshw format)

### App Catalog (`migasfree/app_catalog/`)

Application catalog for end users:

- **Models**: `Application`, `Category`, `PackagesByProject`, `Policy`, `PolicyGroup`

### Stats (`migasfree/stats/`)

Statistics and dashboard:

- **Views**: Dashboard data, charts, alerts
- **Consumers**: WebSocket consumers for real-time updates

### API v4 (`migasfree/api_v4/`)

Legacy compatibility layer for older migasfree-client versions.

## Django App Internal Structure

Each Django app follows a consistent structure:

```text
app_name/
├── __init__.py
├── admin.py               # Django admin configuration
├── apps.py                # App configuration
├── filters.py             # django-filter FilterSets
├── migrations/            # Database migrations
├── models/                # Model definitions (one file per model)
│   ├── __init__.py        # Exports all models
│   └── *.py               # Individual model files
├── permissions.py         # DRF permission classes
├── resources.py           # django-import-export resources
├── routers.py             # DRF router configuration
├── serializers.py         # DRF serializers
├── tasks.py               # Celery tasks
├── urls.py                # URL patterns
└── views/                 # ViewSets (one file per viewset or grouped)
    └── __init__.py
```

## Key Design Patterns

### Models

- **MigasLink mixin**: Provides common functionality (admin links, scoping)
- **Managers**: Custom querysets with `scope()` method for domain filtering
- **One model per file**: Models are organized in separate files within a `models/` directory

### Views

- **ViewSets**: REST API endpoints using DRF ModelViewSet
- **Mixins**: `DatabaseCheckMixin`, `ExportViewSet`, `MigasViewSet`
- **Pagination**: Cursor-based pagination by default
- **Filtering**: django-filter integration with FilterSets

### Serializers

- **Read/Write separation**: Separate serializers for read and write operations
- **Nested serializers**: Related objects are serialized with minimal data

### Security

- **JWT Authentication**: djangorestframework-simplejwt
- **Permission classes**: DRF permission classes per viewset
- **Scoping**: Domain-based data isolation

## Configuration

### Settings Files

```text
migasfree/settings/
├── __init__.py            # Settings selector
├── base.py                # Base settings (common)
├── development.py         # Development settings
├── production.py          # Production settings
├── celery.py              # Celery configuration
├── functions.py           # Helper functions
└── migasfree.py           # Migasfree-specific settings
```

Select environment via `DJANGO_SETTINGS_MODULE`:

- `migasfree.settings.development`
- `migasfree.settings.production`

## Testing

### Test Structure

```text
tests/
├── test_<app>_<model>_views.py     # API ViewSet tests
├── test_<app>_<feature>.py         # Feature tests
└── ...
```

### Conventions

- One test class per ViewSet
- One test file per test class
- Uses `pytest-django` and `APITestCase`

### Running Tests

```bash
# Activate virtualenv
source /home/tux/.virtualenvs/migasfree-backend/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=migasfree

# Run specific test file
pytest tests/test_device_type_views.py -v
```

## API Documentation

The API is documented using OpenAPI 3.0 (drf-spectacular):

- **Schema**: `/api/schema/`
- **Swagger UI**: `/api/schema/swagger-ui/`
- **Redoc**: `/api/schema/redoc/`

## Async Tasks (Celery)

Background tasks are handled by Celery:

- **Broker**: Redis
- **Tasks location**: `<app>/tasks.py`
- **Examples**: Repository generation, package synchronization, alerts

## WebSockets (Channels)

Real-time updates via Django Channels:

- **Consumers**: `migasfree/stats/consumers.py`
- **Routing**: `migasfree/stats/routing.py`
- **Server**: Daphne (ASGI)

## Database Schema

The main entities and their relationships:

```text
Platform → Project → Computer
                   ↓
              Deployment → Package
                   ↓
                Store

Property → Attribute → AttributeSet

Device → Model → Driver
   ↓
Logical → Capability
```

## Code Quality

- **Linter**: Ruff
- **Line length**: 120 characters
- **Style**: PEP 8 with single quotes

```bash
# Check linting
ruff check migasfree/

# Format code
ruff format migasfree/
```
