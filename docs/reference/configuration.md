# ⚙️ Configuration Guide

This guide details all available configuration options for **migasfree-backend**.

Configuration is managed via **Environment Variables**. These can be set in your shell profile, systemd unit files, or a `.env` file loaded by your process manager.

## 🌍 Environment Variables

### Core Django Settings

| Variable | Description | Default | Required |
| :--- | :--- | :--- | :--- |
| `DJANGO_SETTINGS_MODULE` | Python path to settings module. Use `migasfree.settings.production` for deployment. | `migasfree.settings.development` | Yes (for prod) |
| `MIGASFREE_SECRET_KEY` | Secret key for cryptographic signing. **Keep this secret!** | (Insecure default) | **Yes** |
| `DEBUG` | Enable debug mode. **Must be False in production.** | `False` (in prod) | No |
| `ALLOWED_HOSTS` | Comma-separated list of valid hostnames. | `*` (development) | **Yes** |
| `FQDN` | Fully Qualified Domain Name of the server. Used for `ALLOWED_HOSTS` default logic. | `localhost` | Yes |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated trusted origins for CSRF protection. | `https://{FQDN}` | No |

### Database (PostgreSQL)

| Variable | Description | Default |
| :--- | :--- | :--- |
| `MIGASFREE_DB_NAME` | Database name | `migasfree` |
| `MIGASFREE_DB_USER` | Database user | `migasfree` |
| `MIGASFREE_DB_PASSWORD` | Database password | `migasfree` |
| `MIGASFREE_DB_HOST` | Database host | `localhost` |
| `MIGASFREE_DB_PORT` | Database port | `5432` |

### Redis (Broker & Cache)

| Variable | Description | Default |
| :--- | :--- | :--- |
| `MIGASFREE_REDIS_HOST` | Redis host | `localhost` |
| `MIGASFREE_REDIS_PORT` | Redis port | `6379` |
| `MIGASFREE_REDIS_DB` | Redis DB index | `0` |

### Migasfree Specific

| Variable | Description | Default |
| :--- | :--- | :--- |
| `MIGASFREE_SECRET_DIR` | Directory for storing secrets (deprecated). | `/etc/migasfree-server/` |
| `MIGASFREE_KEYS_DIR` | Directory where RSA and JWK keys are stored. | `/var/lib/migasfree-server/keys/` |
| `MIGASFREE_TMP_DIR` | Directory for temporary files. | `/tmp/migasfree-server/` |
| `MIGASFREE_BYPASS_PMS` | If `True`, mocks package management commands (simulated sync). | `False` |

## 🔐 Security Configuration

### 1. Allowed Hosts

To prevent Host Header Injection attacks, you must configure `ALLOWED_HOSTS`.

If you set the `FQDN` environment variable (e.g., `migasfree.example.com`), the system will automatically allow:

- `migasfree.example.com`
- `*.migasfree.example.com`
- `localhost`

Alternatively, you can manually set `ALLOWED_HOSTS`:

```bash
export ALLOWED_HOSTS='migasfree.example.com,internal.migasfree.local'
```

### 2. HTTPS & SSL

In production, you should always run behind a reverse proxy (Nginx/Apache) that handles SSL termination.

Ensure your proxy sets the following headers:

- `X-Forwarded-Proto: https`

And set `SECURE_PROXY_SSL_HEADER` in Django (already set in `production.py`):

```python
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

### 3. Key Management

Migasfree uses cryptographic keys for client communication.

- **RSA Keys**: Used for legacy client authentication.
- **JWK (JSON Web Keys)**: Used for modern token signing.

Ensure `MIGASFREE_KEYS_DIR` is writable **only** by the `migasfree` user.

## 🧩 Advanced Settings

### CORS (Cross-Origin Resource Sharing)

If your frontend is on a different domain, configure CORS:

```bash
export CORS_ALLOWED_ORIGINS='https://dashboard.example.com,https://other.example.com'
```
