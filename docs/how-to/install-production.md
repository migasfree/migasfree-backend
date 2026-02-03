# 📦 How-to: Install in Production

The recommended way to deploy **migasfree-backend** in production is using **Docker Swarm** via the [migasfree-swarm](https://github.com/migasfree/migasfree-swarm) repository. This ensures a scalable, high-availability architecture with pre-configured services (HAProxy, Redis, PostgreSQL, Celery).

## Method 1: Docker Swarm (Recommended)

Please refer to the official [migasfree-swarm documentation](https://github.com/migasfree/migasfree-swarm) for detailed deployment instructions.

### Architecture Overview

- **Load Balancer**: HAProxy (ports 80/443).
- **Web Server**: Uvicorn (port 8080, behind HAProxy).
- **Task Queue**: Celery (Worker + Beat).
- **Databases**: PostgreSQL + Redis.

---

## Method 2: Manual Installation (Bare Metal)

If you cannot use Docker, follow these steps to replicate the production environment on a Debian/Ubuntu server.

### Prerequisites

- **OS**: Debian 12+ / Ubuntu 22.04+
- **Python**: 3.10+
- **Database**: PostgreSQL 12+
- **Broker/Cache**: Redis 6+

### 1. System Dependencies

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip python3-dev libpq-dev git postgresql redis-server uvicorn
```

### 2. Application Setup

Create a dedicated user and directory structure matching the standard layout.

```bash
sudo useradd -r -s /bin/false migasfree
sudo mkdir -p /var/lib/migasfree-backend/{conf,public,keys,tmp}
sudo chown -R migasfree:migasfree /var/lib/migasfree-backend
```

Clone and install:

```bash
cd /opt
sudo git clone https://github.com/migasfree/migasfree-backend.git
sudo chown -R migasfree:migasfree migasfree-backend
cd migasfree-backend

sudo -u migasfree python3 -m venv venv
sudo -u migasfree ./venv/bin/pip install .[production] uvicorn[standard]
```

### 3. Configuration

Create `/var/lib/migasfree-backend/conf/settings.py` or use environment variables.

```bash
export DJANGO_SETTINGS_MODULE='migasfree.settings.production'
export MIGASFREE_CONF_DIR='/var/lib/migasfree-backend/conf'
export MIGASFREE_PUBLIC_DIR='/var/lib/migasfree-backend/public'
export MIGASFREE_KEYS_DIR='/var/lib/migasfree-backend/keys'
```

### 4. Service Configuration (Systemd)

We use **Uvicorn** as the ASGI server (same as `migasfree-swarm`).

#### Web Server (Uvicorn)

`/etc/systemd/system/migasfree-web.service`

```ini
[Unit]
Description=Migasfree Web Server (Uvicorn)
After=network.target

[Service]
User=migasfree
Group=migasfree
WorkingDirectory=/opt/migasfree-backend
Environment="DJANGO_SETTINGS_MODULE=migasfree.settings.production"
EnvironmentFile=/etc/default/migasfree
ExecStart=/opt/migasfree-backend/venv/bin/uvicorn migasfree.asgi:application --lifespan off --host 127.0.0.1 --port 8080 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Celery Worker

`/etc/systemd/system/migasfree-worker.service`

```ini
[Unit]
Description=Migasfree Celery Worker
After=network.target redis-server.service

[Service]
User=migasfree
Group=migasfree
WorkingDirectory=/opt/migasfree-backend
Environment="DJANGO_SETTINGS_MODULE=migasfree.settings.production"
EnvironmentFile=/etc/default/migasfree
ExecStart=/opt/migasfree-backend/venv/bin/celery --app=migasfree.celery.app worker --loglevel=INFO --concurrency=4 --without-gossip
Restart=always

[Install]
WantedBy=multi-user.target
```

### 5. Reverse Proxy (Nginx)

Since Uvicorn runs on localhost:8080, configure Nginx to proxy traffic.

```nginx
server {
    listen 80;
    server_name migasfree.example.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/lib/migasfree-backend/public/static/;
    }
}
```
