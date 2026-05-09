# Service: GraphQL API Engine

> **Endpoint Scope:** `/graphql`
> **Access Privilege:** **Administrators & Dashboard Frontend**
> **Module:** `migasfree` (GraphQL layer)

---

## 1. Overview

The GraphQL engine in `migasfree-backend` serves as the primary high-performance data access layer for modern administrative frontends (such as `migasfree-frontend`). It provides a highly flexible alternative to traditional REST endpoints, allowing dashboards to query complex data trees in a single round-trip.

---

## 2. Graphene Integration & N+1 Prevention

The GraphQL layer is built using **Graphene-Django**. To prevent the common **N+1 query problem** (where querying a list of computers executes a separate database query for each computer's attributes or synchronization history), the backend employs **DataLoaders**.

```txt
Query: Get Computers & Synchronizations

  Without DataLoaders (N+1 Problem):
  Query 1: Select * from Computer; -> Returns 100 computers
  Queries 2-101: Select * from Synchronization where computer_id = X; -> 100 extra queries!

  With DataLoaders (Batching):
  Query 1: Select * from Computer; -> Returns 100 computers
  Query 2: Select * from Synchronization where computer_id IN (1, 2, ..., 100); -> 1 query!
```

---

## 3. Core Schema Capabilities

The GraphQL schema exposes a wide range of types, queries, and mutations:

### Queries

- `computers`: Granular search supporting filters (by project, tag, status, hardware component).
- `synchronizations`: View sync history, filtered by duration, status (Success/Failed), or execution errors.
- `hardwareTelemetry`: Aggregates processor core distributions, total system memory layouts, and disk capacity metrics for analytics dashboards.

### Mutations

- `createComputer`: Programs computer creation or overrides registration data.
- `updatePrinterAssignment`: Programmatically maps logical printers to target client groups or tags.
- `triggerRepoRebuild`: Forces background repository reindexing.
