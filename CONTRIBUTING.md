# Contributing to migasfree-backend

Thank you for your interest in contributing to migasfree-backend! This document provides guidelines and instructions for contributing.

## 📋 Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- PostgreSQL 12+
- Redis 6+
- Git

### Development Setup

1. **Fork the repository** on GitHub

2. **Clone your fork**:

   ```bash
   git clone https://github.com/YOUR_USERNAME/migasfree-backend.git
   cd migasfree-backend
   ```

3. **Install development dependencies**:

   ```bash
   pip3 install -e .[dev]
   ```

4. **Run tests** to verify your setup:
   ```bash
   python3 -m pytest
   ```

## 🔄 Development Workflow

### Creating a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Use prefixes:

- `feature/` for new features
- `fix/` for bug fixes
- `docs/` for documentation changes
- `refactor/` for code refactoring

### Making Changes

1. Write your code following our style guide
2. Add or update tests as needed
3. Update documentation if applicable
4. Run the test suite before committing

### Commit Messages

Use clear, descriptive commit messages:

```
type: short description

Longer description if needed.
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:

```
feat: add APK package management support

Implements PMS backend for Alpine Linux APK packages.
```

## 🧪 Testing

### Running Tests

```bash
# All tests
python3 -m pytest

# With coverage
python3 -m pytest --cov=migasfree

# Specific test file
python3 -m pytest tests/test_utils.py -v
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files as `test_*.py`
- Use descriptive test method names
- Include both positive and negative test cases

## 📝 Code Style

We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.

### Style Guidelines

- Line length: 120 characters max
- Use single quotes for strings
- Follow PEP 8 naming conventions
- Add type hints where practical

### Running Linter

```bash
ruff check .
ruff format .
```

## 📤 Submitting Changes

### Pull Request Process

1. **Update your branch** with the latest main:

   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Push your changes**:

   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request** on GitHub with:
   - Clear title describing the change
   - Description of what and why
   - Reference to related issues (if any)

### PR Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated (if needed)
- [ ] Commit messages are clear
- [ ] PR description explains the changes

## 🐛 Reporting Bugs

Open an issue with:

- Clear, descriptive title
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)

## 💡 Suggesting Features

Open an issue with:

- Feature description
- Use case and motivation
- Possible implementation approach (optional)

## 📖 Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions and classes
- Keep comments concise and meaningful

## ❓ Questions?

- Open a GitHub issue for general questions
- Check existing issues before creating new ones

## 📄 License

By contributing, you agree that your contributions will be licensed under the GPLv3 License.

---

Thank you for contributing! 🎉
