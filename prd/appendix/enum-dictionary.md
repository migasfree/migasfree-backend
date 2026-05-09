# Enum & Constant Dictionary

This document details database status codes, model enums, and system-wide constants defined within the `migasfree-backend` system.

---

## 1. Synchronization Status Enums (`Synchronization` Model)

Found in `migasfree/client/models/synchronization.py`.

| Status Code | Label | Meaning | Description |
| :--- | :--- | :--- | :--- |
| `SUCCESS` | `Success` | Success | The entire client synchronization cycle completed with no errors. |
| `FAILED` | `Failed` | Failure | The synchronization process failed (e.g. PMS transaction error, script failure). |
| `IN_PROGRESS` | `In Progress` | In Progress | The synchronization session is currently active. |
| `INTERRUPTED` | `Interrupted` | Interrupted | Session was aborted due to network loss or system signal interruption. |

---

## 2. Package Source Types (`Package` Model)

Found in `migasfree/core/models/package.py`.

| Source Type | Label | Description |
| :--- | :--- | :--- |
| `MANUAL` | `Manual Upload` | Package was uploaded manually via CLI or administration portal. |
| `SYNCED` | `External Sync` | Package was synchronized automatically from an upstream repository. |
| `VIRTUAL` | `Virtual Package` | Logical package placeholder used for dependency mapping. |

---

## 3. Printer Connection Protocols (`Printer` Model)

Found in `migasfree/device/models/printer.py`.

| Protocol Code | Connection Protocol | Description |
| :--- | :--- | :--- |
| `IPP` | `ipp://` | Internet Printing Protocol (Standard for modern network printers). |
| `IPPS` | `ipps://` | IPP over secure HTTPS. |
| `LPD` | `lpd://` | Line Printer Daemon protocol (Legacy network printers). |
| `SOCKET` | `socket://` | Direct TCP socket connection (port 9100). |
| `USB` | `usb://` | Local physical USB connection. |
| `SMB` | `smb://` | Windows Samba shared printer protocol. |

---

## 4. Hardware Component Classes (`Hardware` Model)

Found in `migasfree/hardware/models/component.py`.

| Class Code | Component Name | Description |
| :--- | :--- | :--- |
| `cpu` | Processor | Processor architecture, cores, and clock speed specs. |
| `ram` | Physical Memory | Total capacity and layout of system memory modules. |
| `disk` | Hard Drive | Storage capacity, interface (SATA, NVMe), and partition maps. |
| `pci` | PCI Card | Dynamic PCI bridges, graphic cards, and sound controllers. |
| `net` | Network Card | Network interfaces, physical MAC addresses, and connection links. |
| `usb` | USB Device | Controllers and connected USB peripheral devices. |
