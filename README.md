# migasfree-backend

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.x](https://img.shields.io/badge/django-5.x-green.svg)](https://www.djangoproject.com/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**migasfree-backend** is the server component of the **Migasfree Server Suite 5**. It provides a complete REST API for centralized software configuration management across large computer fleets.

## 📚 Documentation

We have comprehensive documentation available in the `docs/` directory:

- **[Getting Started](docs/tutorials/getting-started.md)**: Start here!
- **[Installation](docs/how-to/install-production.md)**: Production setup.
- **[Configuration](docs/reference/configuration.md)**: Settings reference.
- **[Core Concepts](docs/explanation/core-concepts.md)**: How Migasfree works.
- **[API](docs/reference/api.md)**: REST API details.

## ✨ Key Features

- 🔐 **Authentication**: Supports JWT, Session, and Mutual TLS (mTLS) for ultra-secure client communication.
- 📊 **Real-time Dashboard**: Live statistics powered by Redis and WebSockets.
- 🔄 **Scalable Processing**: Asynchronous architecture using Celery to handle thousands of concurrent client syncs.
- 📦 **Extensible PMS**: Modular support for APK, APT, DNF, Pacman, YUM, Zypper, and WPT.
- 🔍 **API Documentation**: Automatic OpenAPI 3.0 schema generation with Swagger UI.
- 🌍 **Internationalization**: Fully translatable (Spanish, English, French, and more).

## 🚀 Getting Started

For a quick local setup, check the **[Getting Started Tutorial](docs/tutorials/getting-started.md)**.

### Quick Install (Users)

```bash
pip3 install migasfree-backend
```

## 🏗️ Architecture Modules

For a detailed deep-dive, read our **[Architecture Explanation](docs/explanation/architecture.md)**.

| Module         | Purpose                                                                                 |
| -------------- | --------------------------------------------------------------------------------------- |
| **`client`**   | Manages computers (`Computer`), synchronizations (v5), and incident reports.            |
| **`core`**     | The backbone: projects, deployments, package sets, and properties.                      |
| **`device`**   | Management of peripheral hardware such as drivers and network printers.                 |
| **`hardware`** | Highly detailed hardware inventory (CPUs, RAM, Disks, Motherboards).                    |
| **`stats`**    | Logic for aggregating and serving historical data for the dashboard.                    |
| **`api_v4`**   | Legacy API layer for backward compatibility with Migasfree Client v4.                   |

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
