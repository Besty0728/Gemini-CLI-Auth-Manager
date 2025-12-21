# Gemini CLI Account Manager

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**Gemini CLI Account Manager** is a lightweight, powerful utility for managing multiple accounts in the Google Gemini CLI environment. Switch profiles instantly with a single command!

> 📖 [中文版本 (Chinese Version)](./README-CN.md)

---

## ✨ Features

- **One-Command Switch**: Toggle between accounts instantly.
- **Auto Backup**: Automatically saves your credentials when switching.
- **Interactive Menu**: View active account, saved profiles, and history.
- **Slash Command**: Fully integrated with Gemini CLI as `/change`.
- **Bilingual Installer**: Smart setup script with English & Chinese support.

---

## 🚀 Installation

### 1. Download
Download this repository or clone it:
```bash
git clone https://github.com/Besty0728/Gemini-CLI-Auth-Manager.git
cd gemini-auth-manager
```

### 2. Install
Run the installer script. It will automatically configure everything for you.
```bash
python install.py
```
> Follow the prompts to select your language (English or Chinese).

---

## 🛠 Usage

### Option 1: Gemini CLI (Slash Command)
Inside the Gemini chat interface:

```text
/change 1                # Switch to Profile #1
/change user@gmail.com   # Switch by email
```

### Option 2: Windows Terminal (CMD/PowerShell)
From your standard command line:

```bash
# Open Interactive Menu
change

# Quick Switch
change 2
```

---

## ❤️ Contributing
Feel free to submit issues or pull requests if you have ideas for improvements!
