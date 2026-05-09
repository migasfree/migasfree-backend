# Service: Legacy Compatibility Engine (v4 Client Support)

> **Endpoint Scope:** `/api/v1/` (Legacy endpoints)
> **Access Privilege:** **v4 Registered Clients**
> **Module:** `migasfree.api_v4`

---

## 1. Overview

To support legacy client versions running on older enterprise OS deployments, `migasfree-backend` includes the **`api_v4`** compatibility engine. It acts as a translation layer, mapping legacy REST endpoint queries into modern Django v5 core models.

---

## 2. Legacy Endpoint Translation

Because v4 clients expect monolithic, non-paginated, flat JSON response formats, the compatibility layer translates modern structured relational data on the fly:

```txt
                  ┌──────────────────────────────────────────────┐
                  │          GET /api/v1/computers/              │
                  │          (v4 flat monolithic request)        │
                  └──────────────────────┬───────────────────────┘
                                         │ Intercepted by api_v4 views
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │      Django v5 Core Database Query           │
                  │      (Resolves Computer, Traits, Attributes) │
                  └──────────────────────┬───────────────────────┘
                                         │ Flattens & translates fields
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │      Flat v4 JSON Response Delivery          │
                  └──────────────────────────────────────────────┘
```

### Key Differences Handled

1. **Response Unwrapping**: v4 clients cannot parse pagination metadata (`count`, `next`, `previous`). The compatibility layer completely unwraps Django QuerySets and returns raw array lists.
2. **Key mapping stability**: Resolves legacy field names. For example, modern `attributes` are flattened and delivered under the old `properties` JSON namespace.
3. **No mTLS requirement**: Unlike modern secure routes (`/api/v1/safe/`), some legacy endpoints communicate over HTTP with simpler signature verification. This keeps communications open for old agents without updating their certificates.
