# 📀 Explanation: Migasfree Golden Images (MGI)

This document explains the concept of **Migasfree Golden Images (MGI)**, their build pipeline, their security registration model, and planned architecture changes.

---

## 1. Overview

**Migasfree Golden Image (MGI)** is a core feature in Migasfree 5 designed to generate minimal, standardized operating system root filesystems (Golden Images) for massive fleet deployments (similar to thin clients, kiosk machines, and cloud environments).

An MGI consists of:
- **Base OS**: The minimal operating system (e.g. Debian 13 "Trixie", Ubuntu 24.04).
- **Core Packages**: The default packages and configurations defined for a specific platform.
- **Migasfree Client & Agent**: Pre-installed and pre-configured tools linking the image back to the central Migasfree Server.
- **Partition Layout**: Defining target filesystems and RAW partitions (e.g., `SYSTEM.raw`, `boot.raw`) for raw sector-level imaging.

---

## 2. The MGI Build Pipeline

MGI generation is orchestrated via an asynchronous background engine leveraging Docker containers:

```mermaid
sequenceDiagram
    participant API as Django Backend
    participant Manager as Manager FastAPI
    participant Engine as Docker Engine
    participant Registry as Migasfree Registry

    API->>Manager: 1. Trigger build request
    Manager->>Engine: 2. Spin up build container and render Dockerfile
    Engine->>Registry: 3. Resolve repos and download client packages
    Engine->>Engine: 4. Execute registration and sync
    Engine-->>Manager: 5. Export root filesystem and pack partitions
    Manager-->>API: 6. Update build status
```

1. **Triggering**: A superadmin issues a POST request to `/api/v1/token/mgi/releases/{id}/build/`. The request is proxied internally to the `inv_manager` microservice inside the Swarm cluster.
2. **Jinja2 Rendering**: The manager loads the target MGI template (`mgi_config`) and renders a Dockerfile using project-specific properties.
3. **Docker Build**: The image is compiled in a sandbox. The container automatically adds host routes to resolve internal services (`inv.org`) via `--add-host`.
4. **Client Sync**: During the compilation phase, the container runs:
   ```bash
   migasfree conf --server inv.org --project Debian-13
   migasfree register
   migasfree sync
   ```
5. **Sectorization**: The resulting container root filesystem is extracted, packaged, and formatted as ext4 partitions (`SYSTEM.raw`) with correct filesystems and UUID metadata.
6. **Catalog Update**: The generated assets are moved to `/pool/mgi/` and indexed in `catalog.json` for clients to download.

---

## 3. Current Registration Security Model

To synchronize and populate its initial cache during the build phase, the client inside the build container MUST register itself against the Migasfree database.

Currently, this registration relies on the target **Project's** configuration:
- **`auto_register_computers = True`**:
  * **How it works**: The registration API allows the new client to automatically register itself and sign its client certificate without needing password/token authorization credentials.
  * **Limitation**: While it makes the unattended build pipeline completely hands-off, keeping `auto_register_computers` enabled in production projects presents a **security risk**, as any unauthenticated machine knowing the project key could register itself.
- **`auto_register_computers = False`**:
  * **How it works**: New client registrations are blocked unless explicitly authorized via administrator/registration tokens.
  * **Limitation**: During the unattended MGI build, the `migasfree register` command encounters an authorization prompt, blocking the build or throwing an `EOFError`.

---

## 4. 🚀 Pending Architectural Changes (Roadmap)

To eliminate the security trade-offs of the `auto_register_computers` setting, the following architecture optimizations are planned for implementation:

### Task A: Pre-registered Builder UUID Architecture (Alternative B)

Instead of generating a brand new registration and client certificate interactively at build time, the build engine will transition to a **static pre-authorized compiler** model:

1. **Pre-registered Identity**:
   A specific computer identity with UUID `71656d75-a1b2-c3d4-e5f6-7890abcdef02` (representing the `mci-builder` / `mgi-builder`) is pre-created in the PostgreSQL database.
2. **Certificate Injection**:
   The `inv_manager` container will hold a secure set of pre-signed client certificates associated with this builder UUID.
3. **Dockerfile Injection**:
   During the Dockerfile template compilation, rather than invoking `migasfree register` (which prompts for credentials), the builder will **inject the pre-generated certificate and private key** directly into `/etc/migasfree/keys/` inside the build environment.
4. **Secure Sync**:
   The client inside the container will authenticate immediately using these pre-existing certificates, successfully syncing and obtaining packages even when `auto_register_computers` is securely set to `False`.

### Task B: Standardization of project-templates repository

Align and lock the versioned templates in `mgi_config` to strictly match the base image versions (e.g. Debian 13 "Trixie" or Ubuntu 24.04 LTS), removing legacy compatibility blocks from older environments.
