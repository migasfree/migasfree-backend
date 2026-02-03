# 🔌 API Documentation

Migasfree Backend provides a comprehensive REST API for automation and integration.

## 📖 Interactive Documentation

When the server is running, you can access interactive documentation generated from the OpenAPI 3.0 schema:

- **Swagger UI**: `/docs/`
  - Visual interface to explore and test endpoints.

## 🔐 Authentication

The API supports multiple authentication methods tailored to different clients:

### 1. Token Authentication (Frontend)

Used by the **Migasfree Frontend** (`migasfree-frontend`). This is a standard Django REST Framework Token authentication.

**Get Token:**

```bash
POST /token-auth/
Content-Type: application/json

{
    "username": "your_user",
    "password": "your_password"
}
```

**Response:**

```json
{
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

**Use Token:**

Include the token in the `Authorization` header with the `Token` prefix:

```text
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

### 2. JWT Authentication (Client)

Used by the **Migasfree Client** (`migasfree-client`) and external integrations.

**Get Token:**

```bash
POST /token-auth-jwt/
Content-Type: application/json

{
    "username": "your_user",
    "password": "your_password"
}
```

**Response:**

```json
{
    "access": "eyJ0eX...",
    "refresh": "eyJ0eX..."
}
```

**Use Token:**

Include the token in the `Authorization` header with the `Bearer` prefix:

```text
Authorization: Bearer <access_token>
```

> [!NOTE]
> The Client also uses **JWE/JWS (JSON Web Encryption/Signature)** for securing payloads (Inventory, Sync) ensuring end-to-end integrity and confidentiality.

### 3. Mutual TLS (mTLS)

Used for device identity verification during the synchronization cycle.

## 🛠️ Common Endpoints

Most management endpoints are available under the `/api/v1/token/` prefix (requiring authentication).

### Computers

List and manage computers.

```url
GET /api/v1/token/computers/
GET /api/v1/token/computers/{id}/
```

### Projects

Manage software projects (Operating System scopes).

```url
GET /api/v1/token/projects/
POST /api/v1/token/projects/
```

### Deployments

Manage repository deployments.

```url
GET /api/v1/token/deployments/
```

## 📦 Client API

### Modern Client (v5+)

The **Migasfree Client v5.0+** uses a RESTful API with mTLS and JWT/JWE security.

- **Base URL**: `/api/v1/`
- **Authentication**: mTLS (Certificate) + JWT (Token)
- **Endpoints**:
  - **Availability**: `/manager/v1/public/synchronizations/availability/`
  - **Registration**: `/api/v1/public/keys/project/` (Project keys)
  - **Inventory (Safe)**:
    - Hardware: `/api/v1/safe/computers/hardware/`
    - Software: `/api/v1/safe/computers/software/`
    - Attributes: `/api/v1/safe/computers/attributes/`
  - **Configuration**:
    - Repositories: `/api/v1/safe/computers/repositories/`
    - Faults: `/api/v1/safe/computers/faults/`

### Legacy Client (v4)

The `api_v4` application provides backward compatibility for **Migasfree Client v4**. This is a monolithic, file-based API.

- **Endpoint**: `/api/`
- **Mechanism**: POST request with a signed `message` file.
- **Authentication**: Custom signature verification.
