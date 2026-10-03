<div align="center">

# ⚡ Roblox Cleaner

**A modern, high-performance, and safe Windows desktop application to clean Roblox cache, logs, and temporary files.**

[![GitHub Repo](https://img.shields.io/badge/GitHub-nikiGAMER5%2FRobloxCleaner-blue?logo=github)](https://github.com/nikiGAMER5/RobloxCleaner)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![UI Framework](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt6-success.svg)](https://www.qt.io/)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-0078D6.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Safety Verified](https://img.shields.io/badge/security-whitelisted%20targets-orange.svg)](#-security--privacy-guarantee)

[Features](#-features) • [Installation](#-installation--quick-start) • [Build EXE](#-build-standalone-windows-exe) • [Security](#-security--privacy-guarantee) • [FAQ](#-faq)

</div>

---

## 📌 Overview

While playing Roblox and building in Roblox Studio, Windows accumulates massive amounts of temporary asset caches, textures, 3D meshes, crash dumps, and diagnostic logs. Over time, these files can occupy several gigabytes of storage and lead to sluggish game loading times or cache corruption.

**Roblox Cleaner** scans and organizes these volatile files in fractions of a second, safely reclaims valuable disk space, and provides full transparency—all while strictly protecting your accounts, credentials, and game installations.


## ✨ Features

- **🚀 Ultra-Fast Scanning**:
  - Direct Windows NTFS filesystem traversal using low-overhead `os.scandir` enumerates over 30,000+ cache files in under 0.6 seconds.
- **🛡️ 100% Safe & Privacy-Focused**:
  - Never reads, stores, modifies, or deletes cookies, `.ROBLOSECURITY`, authentication tokens, passwords, or account settings.
  - Multi-layer security validator prevents accidental deletion of Windows system files or Roblox executables.
- **👁️ Transparent Category Preview & File Inspector**:
  - Clear breakdown: *Category | Files | Size*.
  - Inspect individual files, view exact paths and sizes, and jump directly to files in Windows Explorer.
- **⚡ Roblox Process Detection**:
  - Detects active instances of `RobloxPlayerBeta.exe`, `RobloxStudio.exe`, and installers.
  - Offers a one-click graceful termination before cleaning to prevent locked file errors.
- **📦 Optional Safety Backup**:
  - Optionally create a compressed, timestamped ZIP archive before removing files.
- **📁 One-Click Folder Access**:
  - Quick-access **`📁 Open App Folder`** button directly in the main header opens the application directory in Windows Explorer.
- **🎨 Modern Dark Mode Design**:
  - 3 customizable themes: *Dark Modern*, *OLED Midnight*, and *Cyber Blue*.
  - Bilingual support with full English and German translations.

---

## 📂 Cleanable Categories

| Category | Typical Locations | Description |
|---|---|---|
| **HTTP & Asset Cache** | `%LOCALAPPDATA%\Temp\Roblox\http`<br>`%LOCALAPPDATA%\Roblox\rbx-storage-sc` | Downloaded 3D meshes, model assets, textures, and sounds. |
| **Roblox Logs & Diagnostics** | `%LOCALAPPDATA%\Roblox\logs`<br>`%LOCALAPPDATA%\Temp\Roblox\raknet`<br>`%LOCALAPPDATA%\Bloxstrap\Logs` | Player, Studio, and network diagnostic log files. |
| **Temporary Files** | `%LOCALAPPDATA%\Temp\Roblox\cache`<br>`%TEMP%\RBX-*.tmp` | Volatile runtime data and temporary screenshot captures. |
| **Crash Dumps** | `%LOCALAPPDATA%\CrashDumps\Roblox*.dmp` | Windows crash dump logs from previous game crashes. |
| **Installer & Patch Leftovers** | `%LOCALAPPDATA%\Roblox\Downloads`<br>`%LOCALAPPDATA%\Roblox\OTAPatchBackups` | Outdated update installers and OTA patch backups. |

---

## 🔒 Security & Privacy Guarantee

Safety is built into every layer of the architecture:

1. **Dynamic Environment Path Resolution**:
   - **No hardcoded user paths** (e.g. `C:\Users\NAME`). All targets resolve dynamically via Windows environment variables (`%LOCALAPPDATA%`, `%TEMP%`).
2. **Strict Root Whitelisting**:
   - Files are only evaluated if they reside strictly within designated Roblox temporary subfolders.
3. **Blacklisted Protected Directories & Files**:
   - User settings (`GlobalBasicSettings_13.xml`, `ClientAppSettings.json`, etc.) are **never touched**.
   - Executable directories (`Versions/`) and credential stores (`LocalStorage/`) are strictly protected.
4. **Symlink / Junction Protection**:
   - The cleaner will not traverse symlinks pointing outside safe Roblox roots.
5. **No Blind Wildcards**:
   - Only files that were discovered and verified in the preceding scan can be deleted.
6. **Error Resilient**:
   - If a file is locked by Windows, the cleaner logs the event, skips it without crashing, and notifies the user at the end.

---

## 🛠️ Installation & Quick Start

### Prerequisites
- Windows 10 or Windows 11 (64-Bit)
- Python 3.10 or higher

### 1. Clone the Repository
```powershell
git clone https://github.com/nikiGAMER5/RobloxCleaner.git
cd RobloxCleaner
```

### 2. Set Up a Virtual Environment (Recommended)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Run the Application
```powershell
python main.py
```

---

## 🔨 Build Standalone Windows EXE

You can bundle the entire application into a single executable using **PyInstaller**:

### 1. Install PyInstaller
```powershell
pip install pyinstaller
```

### 2. Compile to Executable
Run the following command inside the project root:

```powershell
pyinstaller --noconsole --onefile `
  --name "RobloxCleaner" `
  --icon "assets/icon.ico" `
  --add-data "assets;assets" `
  main.py
```

Your standalone binary will be generated under:
```text
dist/RobloxCleaner.exe
```

---

## ❓ FAQ

### Will this delete my Roblox account or saved games?
**No.** All Roblox player data, game progress, and inventory items are stored in the Roblox cloud. Your login cookies and authentication tokens are kept in the protected `LocalStorage` directory, which Roblox Cleaner strictly ignores and never touches.

### Should I close Roblox before cleaning?
Yes. Active Roblox processes lock cache and log files, preventing Windows from deleting them. The application automatically detects running Roblox instances and provides a safe one-click termination button.

### Where are log files saved?
Application diagnostic logs are stored at:
`%LOCALAPPDATA%\RobloxCleaner\logs\roblox_cleaner.log`
You can also view the logs directly inside the application under **Settings -> Logs**.

### Where are backups located?
When *Safety Backup* is enabled in Settings, ZIP backups are created in:
`%LOCALAPPDATA%\RobloxCleaner\Backups\roblox_backup_YYYYMMDD_HHMMSS.zip`

---

## 🤝 Contributing

Contributions, bug reports, and suggestions are welcome!

1. Fork the repository: [nikiGAMER5/RobloxCleaner](https://github.com/nikiGAMER5/RobloxCleaner)
2. Create a feature branch: `git checkout -b feature/AmazingFeature`
3. Commit your changes: `git commit -m "Add AmazingFeature"`
4. Push to the branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request.

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.

*Disclaimer: Roblox is a registered trademark of Roblox Corporation. This project is an independent community utility and is not affiliated with, authorized, or endorsed by Roblox Corporation.*
