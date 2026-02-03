# 🎓 Tutorial: Getting Started with Migasfree

In this tutorial, you will learn how to set up a local development environment and run the Migasfree backend server. By the end, you'll have a running API that you can interact with.

## Prerequisites

- Basic command line knowledge.
- Python 3.10+ installed.
- Docker (optional, for dependencies) or local PostgreSQL/Redis.

## Step 1: Clone the Repository

First, get the code on your machine.

```bash
git clone https://github.com/migasfree/migasfree-backend.git
cd migasfree-backend
```

## Step 2: Set Up Python Environment

We'll use a virtual environment to keep dependencies isolated.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .[dev]
```

## Step 3: Configure Environment

Migasfree needs to know which settings to load. For this tutorial, we'll use the development settings.

```bash
export DJANGO_SETTINGS_MODULE='migasfree.settings.development'
```

## Step 4: Prepare the Database

Run migrations to set up the database schema and create an admin user.

```bash
python3 manage.py migrate
python3 manage.py createsuperuser
```

## Step 5: Run the Server

Start the development server.

```bash
python3 manage.py runserver 0.0.0.0:8000
```

## Step 6: Run Celery (Tasks & Schedule)

Migasfree relies on Celery for background tasks (e.g., generating package repositories) and scheduled events. You will need two new terminal windows.

**Terminal 2 (Worker):**

```bash
# Activate virtualenv first
source venv/bin/activate
# Worker must listen to specific PMS queues for repository generation
celery --app=migasfree.celery.app worker --without-gossip --loglevel=DEBUG --queues=default,pms-apt,pms-dnf,pms-pacman,pms-wpt,pms-yum,pms-zypper
```

**Terminal 3 (Beat):**

```bash
# Activate virtualenv first
source venv/bin/activate
celery --app=migasfree.celery.app beat --loglevel=DEBUG
```

> [!NOTE]
> Ensure Redis is running (`sudo systemctl start redis-server` or via Docker) as it is the message broker.

## Step 6: Verify

Open your browser and navigate to `http://localhost:8000/admin`. Log in with the superuser you created.

**Congratulations!** You have a running Migasfree backend.
