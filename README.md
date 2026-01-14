# migasfree-backend

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.x](https://img.shields.io/badge/django-5.x-green.svg)](https://www.djangoproject.com/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**migasfree-backend** is the server component of the [Migasfree](https://migasfree.org/) systems management platform. It provides a complete REST API for centralized software configuration management across large computer fleets.

## 📋 Description

Migasfree is an Open Source systems management tool that enables:

- **Centralized package management**: Software distribution and updates across multiple computers.
- **Hardware and software inventory**: Detailed tracking and queryable database of your entire computer fleet.
- **Scheduled deployments**: Sophisticated update planning with execution windows, attribute control, and status tracking.
- **Error and fault management**: Automated monitoring of sync processes and system faults.
- **Multi-platform support**: Natively handles multiple package management systems (APT, DNF, Pacman, Zypper, etc.).
- **Attribute-based logic**: Target software or configurations based on custom computer attributes (department, hardware type, location).

## ✨ Key Features

- 🔐 **Authentication**: Supports JWT, Session, and Mutual TLS (mTLS) for ultra-secure client communication.
- 📊 **Real-time Dashboard**: Live statistics powered by Redis and WebSockets.
- 🔄 **Scalable Processing**: Asynchronous architecture using Celery to handle thousands of concurrent client syncs.
- 📦 **Extensible PMS**: Modular support for APK, APT, DNF, Pacman, YUM, Zypper, and WPT.
- 🔍 **API Documentation**: Automatic OpenAPI 3.0 schema generation with Swagger UI.
- 🌍 **Internationalization**: Fully translatable (Spanish, English, French, and more).

## 🚀 Getting Started

If you are a developer looking to set up the project locally, please read our **[Onboarding Guide](ONBOARDING.md)**.

### Quick Install

```bash
# For users
pip3 install migasfree-backend

# For developers
git clone https://github.com/migasfree/migasfree-backend.git
cd migasfree-backend
pip3 install -e .[dev]
```

## ⚙️ Configuration (Environment Variables)

The following environment variables can be used to customize the behavior of the server:

| Variable                 | Description                             | Default                           |
| ------------------------ | --------------------------------------- | --------------------------------- |
| `DJANGO_SETTINGS_MODULE` | Active Django settings module           | `migasfree.settings.development`  |
| `MIGASFREE_SECRET_DIR`   | Directory where secrets are stored      | `/etc/migasfree-server/`          |
| `MIGASFREE_KEYS_DIR`     | Directory for JWK and RSA keys          | `/var/lib/migasfree-server/keys/` |
| `MIGASFREE_TMP_DIR`      | Temporary files directory               | `/tmp/migasfree-server/`          |
| `MIGASFREE_INVALID_UUID` | Comma-separated list of UUIDs to ignore | (Default list)                    |

## 📊 Monitoring & Stats

Migasfree uses Redis to track synchronization metrics in real-time.

### Update Stats Manually

```bash
python3 manage.py refresh_redis_syncs --since 2024 --until 2025
```

## 🏗️ Architecture Modules

| Module         | Purpose                                                                                 |
| -------------- | --------------------------------------------------------------------------------------- |
| **`client`**   | Manages computers (`Computer`), synchronizations, and incident reports (errors/faults). |
| **`core`**     | The backbone: projects, deployments, package sets, and properties.                      |
| **`device`**   | Management of peripheral hardware such as drivers and network printers.                 |
| **`hardware`** | Highly detailed hardware inventory (CPUs, RAM, Disks, Motherboards).                    |
| **`stats`**    | Logic for aggregating and serving historical data for the dashboard.                    |
| **`api_v4`**   | The API layer optimized for communication with the Migasfree clients.                   |

## 📄 License

This project is licensed under the [GNU General Public License v3.0](LICENSE).

## 👥 Authors

- **Alberto Gacías** ([@albertogacias](https://github.com/albertogacias))
- **Jose Antonio Chavarría** ([@jact](https://github.com/jact))

## 🤝 Contributing

We value your help! Check our [Contribution Guidelines](CONTRIBUTING.md) and join our community at [migasfree.org](https://migasfree.org/).

---

- **Repository**: [github.com/migasfree/migasfree-backend](https://github.com/migasfree/migasfree-backend/)
- **Issues**: [Post a bug or feature request](https://github.com/migasfree/migasfree-backend/issues)
