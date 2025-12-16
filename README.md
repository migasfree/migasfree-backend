# migasfree-backend

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.x](https://img.shields.io/badge/django-5.x-green.svg)](https://www.djangoproject.com/)

**migasfree-backend** is the server component of the [Migasfree](https://migasfree.org/) systems management platform. It provides a complete REST API for centralized software configuration management across computer fleets.

## 📋 Description

Migasfree is a systems management tool that enables:

- **Centralized package management**: Software distribution and updates across multiple computers
- **Hardware and software inventory**: Detailed tracking of your computer fleet
- **Scheduled deployments**: Update planning with date and attribute controls
- **Error and fault management**: Incident monitoring and resolution
- **Multi-platform support**: Compatible with different package systems (APT, DNF, Pacman, Zypper, etc.)

## ✨ Key Features

- 🔐 **Secure REST API** with JWT authentication
- 📊 **Real-time statistics dashboard** with Redis
- 🔄 **Asynchronous processing** with Celery
- 📦 **Multiple PMS support**: APK, APT, DNF, Pacman, YUM, Zypper, WPT
- 🌐 **WebSockets** for real-time updates
- 📈 **GraphQL** for flexible queries (experimental)
- 📁 **Data Export** (CSV)
- 🔍 **OpenAPI documentation** (Swagger/ReDoc)

## 🛠️ Technology Stack

| Component    | Technology            |
| ------------ | --------------------- |
| Framework    | Django 5.x            |
| REST API     | Django REST Framework |
| Auth         | JWT (SimpleJWT)       |
| Database     | PostgreSQL            |
| Cache/Broker | Redis                 |
| Async Tasks  | Celery                |
| WebSockets   | Django Channels       |
| ASGI Server  | Daphne                |

## 📦 Requirements

- Python 3.10 or higher
- PostgreSQL 12+
- Redis 6+

## 🚀 Installation

### Development Installation

```bash
# Clone the repository
git clone https://github.com/migasfree/migasfree-backend.git
cd migasfree-backend

# Install with development dependencies
pip3 install -e .[dev]
```

### Production Installation

```bash
pip3 install migasfree-backend
```

## ⚙️ Configuration

### Main Environment Variables

| Variable                 | Description            |
| ------------------------ | ---------------------- |
| `DJANGO_SETTINGS_MODULE` | Django settings module |
| `MIGASFREE_SECRET_DIR`   | Secrets directory      |
| `MIGASFREE_TMP_DIR`      | Temporary directory    |
| `MIGASFREE_INVALID_UUID` | List of invalid UUIDs  |

## 🔧 Running in Development Mode

### 1. Django Server

```bash
python3 manage.py runserver 0.0.0.0:2345 --settings=migasfree.settings.development
```

### 2. Celery Beat (Task Scheduler)

```bash
DJANGO_SETTINGS_MODULE='migasfree.settings.development' \
celery --app=migasfree.celery.app beat --loglevel=DEBUG
```

### 3. Celery Worker (Task Processor)

```bash
DJANGO_SETTINGS_MODULE='migasfree.settings.development' \
celery --app=migasfree.celery.app worker \
    --without-gossip \
    --concurrency=10 \
    --queues=default,pms-apt,pms-dnf,pms-pacman,pms-wpt,pms-yum,pms-zypper \
    --loglevel=DEBUG
```

## 📡 REST API

### View Available Endpoints

```bash
python3 manage.py show_urls --settings=migasfree.settings.development
```

### Interactive Documentation

Once the server is running, access:

- **Swagger UI**: `http://localhost:2345/api/v4/swagger/`
- **ReDoc**: `http://localhost:2345/api/v4/redoc/`
- **OpenAPI Schema**: `http://localhost:2345/api/v4/schema/`

## 📊 Redis Statistics

### Key Structure

```text
migasfree:watch:stats:years:YYYY
migasfree:watch:stats:<project_id>:years:YYYY
migasfree:stats:years:YYYY
migasfree:stats:<project_id>:years:YYYY

migasfree:watch:stats:months:YYYYMM
migasfree:watch:stats:<project_id>:months:YYYYMM
migasfree:stats:months:YYYYMM
migasfree:stats:<project_id>:months:YYYYMM

migasfree:watch:stats:days:YYYYMMDD
migasfree:watch:stats:<project_id>:days:YYYYMMDD
migasfree:stats:days:YYYYMMDD
migasfree:stats:<project_id>:days:YYYYMMDD

migasfree:watch:stats:hours:YYYYMMDDHH
migasfree:watch:stats:<project_id>:hours:YYYYMMDDHH
migasfree:stats:hours:YYYYMMDDHH
migasfree:stats:<project_id>:hours:YYYYMMDDHH
```

### Update Statistics

```bash
python3 manage.py refresh_redis_syncs \
    --settings=migasfree.settings.development \
    --since 2020 \
    --until=2021
```

## 🧪 Testing

### Run Tests

```bash
python3 -m pytest
```

### With Code Coverage

```bash
python3 -m pytest --cov=migasfree
```

### Specific Tests

```bash
# API v4 tests
python3 -m pytest tests/test_api_v4.py -v

# Utility tests
python3 -m pytest tests/test_utils.py -v
```

## 📁 Project Structure

```text
migasfree-backend/
├── migasfree/
│   ├── api_v4/          # REST API v4
│   ├── app_catalog/     # Application catalog
│   ├── client/          # Client computer management
│   ├── core/            # Core models and logic
│   ├── device/          # Device management
│   ├── hardware/        # Hardware inventory
│   ├── settings/        # Django configurations
│   └── stats/           # Statistics and metrics
├── tests/               # Unit and integration tests
├── pyproject.toml       # Project configuration
└── manage.py            # Django CLI
```

## 🏗️ Main Modules

| Module        | Description                                              |
| ------------- | -------------------------------------------------------- |
| `core`        | Base models: projects, platforms, properties, attributes |
| `client`      | Computer management: syncs, errors, faults               |
| `device`      | Device and printer management                            |
| `hardware`    | Hardware inventory and specifications                    |
| `app_catalog` | Installable applications catalog                         |
| `stats`       | Statistics and dashboards                                |
| `api_v4`      | REST endpoints for migasfree clients                     |

## 📄 License

This project is licensed under the [GNU General Public License v3.0](LICENSE).

## 👥 Authors

- **Alberto Gacías** - [@albertogacias](https://github.com/albertogacias)
- **Jose Antonio Chavarría** - [@jact_abcweb](https://github.com/jact)

## 🤝 Contributing

Contributions are welcome! Please read the [contribution guidelines](CONTRIBUTING.md) before submitting a pull request.

## 🔗 Links

- **Official Website**: [https://migasfree.org/](https://migasfree.org/)
- **Repository**: [https://github.com/migasfree/migasfree-backend/](https://github.com/migasfree/migasfree-backend/)
- **Documentation**: [https://github.com/migasfree/fun-with-migasfree](https://github.com/migasfree/fun-with-migasfree)
- **Issues**: [https://github.com/migasfree/migasfree-backend/issues](https://github.com/migasfree/migasfree-backend/issues)
