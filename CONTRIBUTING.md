# Contributing to migasfree-backend

Thank you for your interest in contributing to migasfree-backend! This document provides guidelines and instructions for contributing.

## 📋 Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## 🚀 Getting Started

Please refer to the **[Getting Started Tutorial](docs/tutorials/getting-started.md)** for instructions on:

- Prerequisites
- Installation & Setup
- Running Tests
- Code Style & Linting

## 🔄 Development Workflow

### Managing Dependencies

This project uses `pyproject.toml` as the source of truth for dependencies and `pip-tools` (`pip-compile`) to generate pinned `requirements.txt` files to ensure reproducible builds.

When you need to add or update a dependency:

1. Update the relevant section (`dependencies` or `project.optional-dependencies.dev`) in `pyproject.toml`.
2. Re-generate the requirements files by running:

   ```bash
   # Update production dependencies
   pip-compile --output-file=requirements.txt pyproject.toml

   # Update development dependencies
   pip-compile --extra dev --output-file=requirements-dev.txt pyproject.toml
   ```

3. Commit both `pyproject.toml` and the updated `requirements*.txt` files.

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
