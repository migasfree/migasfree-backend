# Service: Synchronization Handler Flow

> **Endpoint Scope:** `/api/v1/safe/`
> **Access Privilege:** **mTLS Enrolled Clients**
> **Module:** `migasfree.client`

---

## 1. Overview

The Synchronization Handler is the core transactional service of `migasfree-backend`. It handles state, inventory uploads, dynamic policy calculations, and peripheral allocation requests from millions of active client agents.

---

## 2. API Endpoint Handshakes

The synchronization handler coordinates the following secure endpoints to update machine profiles:

```txt
                  ┌──────────────────────────────────────────────┐
                  │          GET /safe/computers/properties/     │
                  └──────────────────────┬───────────────────────┘
                                         │ Evaluates dynamic attributes
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │          POST /safe/computers/attributes/    │
                  └──────────────────────┬───────────────────────┘
                                         │ Saves attributes to DB
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │      GET /safe/computers/packages/mandatory/ │
                  └──────────────────────┬───────────────────────┘
                                         │ Computes update list
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │          POST /safe/computers/software/      │
                  └──────────────────────────────────────────────┘
                                         Saves current packages
```

---

## 3. Real-Time Policy Calculation & Attribute Evaluation

One of the most powerful features of `migasfree-backend` is resolving client profiles using **python-based evaluation rules**.

1. When the client calls `GET /safe/computers/properties/`, the backend queries the `DynamicProperty` database table.
2. It returns a JSON object containing Python scripts as strings.
3. The client executes these scripts locally to resolve its key-value dynamic attributes (e.g., matching subnet IPs to resolve "System Department = Human Resources").
4. The client submits evaluated values back to `POST /safe/computers/attributes/`.
5. The backend parses this payload, updates the `Attribute` table, and evaluates which `Deployment` and `Repository` sets match the client's new profile in real-time.

---

## 4. Software Inventory Processing

To keep package records accurate, `POST /safe/computers/software/` accepts a full list of installed packages on the client.

- **Bulk Insertion Optimization**: Because package lists can exceed thousands of lines per machine, the view parses the JSON in bulk and updates the computer's software mapping.
- **Package History logs**: If packages are newly added or removed since the last sync session, the backend logs these entries into the `PackageHistory` table to provide administrative audit logs.

---

## 5. Hardware Profile Capture

When `GET /safe/computers/hardware/required/` is queried, the backend evaluates if a new scan is required based on expiration timers (default: 30 days) or force flags.

- If required, `POST /safe/computers/hardware/` accepts the detailed hardware JSON.
- The backend parses the hardware profile and updates the system tables `cpu`, `ram`, `disk`, `pci`, `net`, and `usb`, indexing each component for fleet searching.

---

## 6. Security & Transaction Integrity

- **Session Locking**: Releasing session resources is triggered by calling `POST /safe/eot/`. This ensures the synchronization is closed cleanly, logging final durations in the `Synchronization` table.
- **Fault capture**: Any local script or package installation failures are caught and posted to `/api/v1/safe/computers/faults/`. The backend logs them into `Fault` with a reference to the active `Synchronization` session, triggering admin alerts on the dashboard.
