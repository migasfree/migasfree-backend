# 🏗️ Explanation: Project Structure

This document details the internal organization of the `migasfree-backend` codebase.

## Django Apps

The project is modularized into several Django applications, each handling a specific domain:

- **`migasfree.core`**: The backbone. Manages Projects, Packages, and the general data model.
- **`migasfree.client`**: Handles Computer logic, authentication, and the synchronization API.
- **`migasfree.device`**: Manages peripheral devices (Printers, etc.) and Drivers.
- **`migasfree.hardware`**: Dedicated to storing and querying hardware inventory (CPU, RAM, Disks).
- **`migasfree.stats`**: Dashboard statistics and real-time monitoring.

## Design Patterns

### Models

- **One file per model**: Unlike standard Django, we split `models.py` into a `models/` package with one file per class.
- **MigasLink**: A custom mixin that standardizes how models link to each other in the Admin interface.

### API (DRF)

- **ViewSets**: We use ViewSets almost exclusively to provide standard CRUD operations.
- **Serializers**: Separate Read and Write serializers are often used to enforce read-only fields.

### Async Tasks

- **Celery**: All heavy lifting (repo generation, big database updates) is offloaded to Celery workers.
- **Redis**: Acts as the message broker for Celery and the channel layer for WebSockets.
