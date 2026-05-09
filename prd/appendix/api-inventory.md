# API Inventory

This document lists all the key REST and GraphQL endpoints exposed by `migasfree-backend` to handle client synchronization and administrative management.

---

## 1. REST API: Public Endpoints (`/api/v1/public/` & `/api/v1/`)

Public endpoints require no authentication. They handle initial handshake, public key delivery, and availability queries.

| Path | Method | Module | Description |
| :--- | :--- | :--- | :--- |
| `/api/v1/public/server/info/` | `GET` | `core` | Retrieves backend version, system capabilities, and active public CA details. |
| `/api/v1/public/keys/project/` | `POST` | `core` | Generates asymmetric public keys (`server.pub`) for new client enrollments. |
| `/api/v1/public/keys/repositories/` | `GET` | `core` | Delivers GPG repository signing keys. |
| `/api/v1/public/keys/packager/` | `GET` | `core` | Delivers authorized package signing public keys. |
| `/manager/v1/public/synchronizations/availability/` | `GET` | `client` | Evaluates server and database saturation states to rate-limit client synchronizations. |

---

## 2. REST API: Secure Client Endpoints (`/api/v1/safe/`)

Secure endpoints are restricted to registered computers. They require mutual TLS (**mTLS**) authentication and signature verification of payload data.

| Path | Method | Module | Description |
| :--- | :--- | :--- | :--- |
| `/api/v1/safe/computers/id/` | `POST` | `client` | Resolves a computer ID matching the client's UUID and Name. |
| `/api/v1/safe/computers/` | `POST` | `client` | Enrolls a new machine into a project and issues its client certificate. |
| `/api/v1/safe/computers/properties/` | `GET` | `core` | Delivers python-based dynamic evaluation rules for attributes. |
| `/api/v1/safe/computers/faults/definitions/` | `GET` | `client` | Returns list of standard system faults. |
| `/api/v1/safe/computers/repositories/` | `GET` | `core` | Delivers repository configurations allocated for the computer. |
| `/api/v1/safe/computers/packages/mandatory/` | `GET` | `core` | Delivers the mandatory package update list for the machine profile. |
| `/api/v1/safe/computers/devices/` | `GET` | `device` | Returns physical and logical printer setups assigned to the computer. |
| `/api/v1/safe/computers/hardware/required/` | `GET` | `hardware` | Evaluates if a hardware inventory update is required. |
| `/api/v1/safe/computers/traits/` | `GET` | `client` | Generates and sends configuration traits and groups. |
| `/api/v1/safe/computers/errors/` | `POST` | `client` | Logs execution stderr and stack traces from the client. |
| `/api/v1/safe/computers/hardware/` | `POST` | `hardware` | Parses and registers detailed computer hardware profile. |
| `/api/v1/safe/computers/attributes/` | `POST` | `core` | Stores evaluated key-value system attributes. |
| `/api/v1/safe/computers/faults/` | `POST` | `client` | Stores system failure evaluations. |
| `/api/v1/safe/computers/software/` | `POST` | `core` | Records the list of all installed packages on the machine. |
| `/api/v1/safe/computers/devices/changes/` | `POST` | `device` | Processes printer installation logs and driver failures. |
| `/api/v1/safe/synchronizations/` | `POST` | `client` | Registers synchronization sessions (start/end times, success status). |
| `/api/v1/safe/eot/` | `POST` | `client` | Ends the synchronization session, releasing any locks. |

---

## 3. REST API: Authenticated Administrative Endpoints (`/api/v1/token/`)

Administrative endpoints require standard DRF Token authentication or JWT authorization headers (`Authorization: Bearer <token>`).

| Path | Method | Module | Description |
| :--- | :--- | :--- | :--- |
| `/api/v1/token/core/` | `GET` / `POST` | `core` | CRUD operations for projects, deployments, repositories, and packages. |
| `/api/v1/token/client/` | `GET` / `POST` | `client` | View registered computers, active synchronizations, and execution logs. |
| `/api/v1/token/devices/` | `GET` / `POST` | `device` | Manage global system printers, driver listings, and assignments. |
| `/api/v1/token/catalog/` | `GET` / `POST` | `app_catalog` | Manage self-service application catalog metadata. |
| `/api/v1/token/stats/` | `GET` | `stats` | Aggregated dashboard telemetry, computer distributions, and errors. |

---

## 4. GraphQL Administrative API (`/graphql`)

Designed for the modern Quasar frontend (`migasfree-frontend`), the GraphQL endpoint accepts complex schema queries.

| API Operation | Resolver / Target | Description |
| :--- | :--- | :--- |
| `Query` | `computers` | Paginated search of system fleets with granular filters. |
| `Query` | `synchronizations` | Search synchronization histories with N+1 prevention (DataLoaders). |
| `Query` | `hardwareStats` | Aggregates CPU and RAM distributions across the fleet. |
| `Mutation` | `registerComputer` | Enrolls computers or overrides statuses programmatically. |
| `Mutation` | `assignPrinter` | Links logical printers to computer groups or attributes. |
