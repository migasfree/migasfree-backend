# 📦 How-to: Add a New Package Management System

This guide explains how to extend Migasfree to support a new package manager (e.g., `pacman`, `zypper`).

## Context

Migasfree uses a modular system to handle multiple Package Management Systems (PMS). The logic resides in `migasfree/core/pms/`.

## Steps

1. **Create Module**: Create a new python file in `migasfree/core/pms/` (e.g., `pacman.py`).

2. **Inherit Base Class**:

    ```python
    from migasfree.core.pms.pms import Pms

    class PmsPacman(Pms):
        pass
    ```

3. **Implement Methods**: You must override the following methods to handle server-side repository management:

    - `create_repository(self, path, arch)`: Generates the repository metadata (e.g., `apt-ftparchive` or `createrepo`).
    - `package_info(self, package)`: Extracts detailed information (description, dependencies) from a package file.
    - `package_metadata(self, package)`: Returns basic metadata (name, version, architecture) as a dictionary.
    - `source_template(self, deploy)`: Returns the string template for the client's repository configuration (e.g., `sources.list` line).

4. **Register PMS**:
    - Import your class in `migasfree/core/pms/__init__.py`.
    - Add it to the `get_available_pms()` function:

        ```python
        def get_available_pms():
            ret = [
                # ...
                ('pacman', 'pacman'),
            ]
        ```
