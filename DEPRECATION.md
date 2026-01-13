# Deprecation Timeline

This document tracks deprecated APIs and their planned removal dates.

## api_v4 Module

> [!WARNING]
> The entire `api_v4` module is deprecated and will be removed in **migasfree-backend 6.0**.

### Timeline

| Version | Status        | Action                          |
| ------- | ------------- | ------------------------------- |
| 5.x     | ⚠️ Deprecated | Module available but deprecated |
| 6.0     | 🔴 Removed    | Module will be deleted          |

### Affected Endpoints

All endpoints under `/api/v4/` including:

| Endpoint                             | Function              | Status                        |
| ------------------------------------ | --------------------- | ----------------------------- |
| `get_properties`                     | First sync call       | ⚠️ Deprecated                 |
| `upload_computer_info`               | Main sync endpoint    | ⚠️ Deprecated                 |
| `register_computer`                  | Computer registration | ⚠️ Deprecated                 |
| `upload_computer_hardware`           | Hardware capture      | ⚠️ Deprecated                 |
| `upload_computer_software_base_diff` | Software inventory    | ⚠️ Deprecated                 |
| `upload_computer_software_base`      | Software base         | ❌ Already deprecated (4.14+) |
| `get_computer_software`              | Get software          | ❌ Already deprecated (4.14+) |
| `upload_computer_software_history`   | Software history      | ⚠️ Deprecated                 |
| `upload_computer_errors`             | Error reporting       | ⚠️ Deprecated                 |
| `upload_computer_message`            | Status messages       | ⚠️ Deprecated                 |
| `upload_computer_faults`             | Fault reporting       | ⚠️ Deprecated                 |
| `upload_devices_changes`             | Device changes        | ❌ Already deprecated (4.13+) |
| `get_computer_tags`                  | Get tags              | ⚠️ Deprecated                 |
| `set_computer_tags`                  | Set tags              | ⚠️ Deprecated                 |
| `get_key_packager`                   | Packager keys         | ⚠️ Deprecated                 |
| `upload_server_package`              | Package upload        | ⚠️ Deprecated                 |
| `upload_server_set`                  | Package set upload    | ⚠️ Deprecated                 |
| `create_repositories_of_packageset`  | Create repos          | ⚠️ Deprecated                 |

### Migration Path

Clients should migrate to the `/api/v5/` endpoints (JWT-based REST API).

**Required client versions:**

- migasfree-client >= 5.0 (uses v5 API)

### Legacy Files to Remove in 6.0

```
migasfree/api_v4/
├── __init__.py
├── api.py
├── apps.py
├── errmfs.py
├── secure.py
├── urls.py
└── views/
    └── ...
```

### Contact

Questions about deprecation: [migasfree-backend issues](https://github.com/migasfree/migasfree-backend/issues)
