# 🧪 How-to: Run Tests and Check Quality

This guide explains how to run the test suite and linting tools.

## Running Tests

We use `pytest` for running tests.

### Run all tests

```bash
pytest
```

### Run with coverage

```bash
pytest --cov=migasfree
```

### Run specific test

```bash
pytest tests/test_core_project_views.py
```

## Code Quality

We use **Ruff** for linting and formatting. Please run these before committing.

```bash
# Check for errors
ruff check .

# Fix auto-fixable errors
ruff check --fix .

# Format code
ruff format .
```
