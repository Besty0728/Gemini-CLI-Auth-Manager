# Gemini CLI Auth Manager

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Version](https://img.shields.io/badge/version-2.0-brightgreen.svg)

**Gemini CLI Auth Manager** is a lightweight, powerful utility for managing multiple accounts in the Google Gemini CLI environment. Features instant account switching, **automatic rotation when quota is exhausted**, and **unified account pool management**!

> 📖 [中文版本 (Chinese Version)](./README-CN.md)

---

## ✨ Features

- **One-Command Switch**: Toggle between accounts instantly
- **Auto Backup**: Automatically saves your credentials when switching
- **🆕 Auto-Rotation**: Automatically switch to next account when quota exhausted
- **🆕 Account Pool**: Unified view, add, and remove accounts
- **🆕 Interactive Menu**: Visual configuration interface for easy management
- **Slash Command**: Fully integrated with Gemini CLI as `/change`

---

## 🚀 Installation

```bash
git clone https://github.com/Besty0728/Gemini-CLI-Auth-Manager.git
cd gemini-auth-manager
python install.py
```

### How to Update

If you have an older version installed, follow these steps to update:

1. Run `git pull` in the project directory to sync the latest code.
2. Re-run `python install.py` to upgrade (Recommended, to sync the latest Hook logic).
3. Or manually copy `quota_auto_switch.py` to the `~/.gemini/` directory.

---

## 🛠 Usage

### Quick Reference

```bash
# List all accounts
gchange

# Switch accounts
gchange 1                    # Switch to account #1
gchange user@gmail.com       # Switch by email
gchange next                 # Switch to next account

# Interactive menu (recommended)
gchange menu

# Account pool management
gchange pool                 # View pool
gchange pool add             # Add account (interactive)
gchange pool add user@gmail.com    # Add specific account
gchange pool remove 2        # Remove account #2
gchange pool import ~/creds.json   # Import credentials file

# Strategy management
gchange strategy             # View current strategy
gchange strategy conservative       # Set to conservative mode
gchange strategy gemini3-first      # Set to Gemini3-first mode

# Configuration
gchange config               # View all config
gchange config enabled true  # Enable auto-switch
gchange config threshold 10  # Set threshold to 10%
```

### Slash Commands (Inside Gemini CLI)

```text
/change           # List all accounts
/change 1         # Switch to account #1
/change next      # Switch to next account
```

---

## 🎯 Interactive Menu

Run `gchange menu` to open the interactive configuration interface:

```
  Menu:
  ----------------------------------------
  1. Switch Account
  2. Switch to Next Account
  3. Change Strategy
  4. Configure Auto-Switch
  5. Toggle Auto-Switch (Enable/Disable)
  6. Manage Account Pool
  0. Exit
```

---

## 📦 Account Pool Management

### View Pool

```bash
gchange pool
```

Output example:
```
Account Pool Overview:
--------------------------------------------------
  01. user1@gmail.com                    ● Active
  02. user2@gmail.com                    ○ Standby
  03. user3@gmail.com                    ○ Standby
--------------------------------------------------
  Total: 3 accounts
```

### Add Account

```bash
# Interactive add
gchange pool add

# Direct add
gchange pool add newuser@gmail.com
```

### Remove Account

```bash
# Remove by index
gchange pool remove 2

# Remove by email
gchange pool remove user2@gmail.com
```

### Import Credentials

```bash
gchange pool import /path/to/oauth_creds.json
```

---

## 🔄 Auto-Switch Feature

When API returns quota error (429), the system will automatically:
1. Switch to the next account
2. Retry the current request
3. Notify you of the switch

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `enabled` | Enable auto-switch | `true` |
| `strategy` | Rotation strategy | `gemini3-first` |
| `threshold` | Quota threshold (%) | `5` |
| `max_retries` | Max retry attempts | `3` |

### Strategy Comparison

| Strategy | Trigger Condition | Use Case |
|----------|-------------------|----------|
| `conservative` | All models ≤ threshold | Maximize each account |
| `gemini3-first` | Any Gemini 3.x ≤ threshold | Prefer latest models |

---

## ❓ FAQ

### Q: Which errors does auto-switch support detecting?

The Hook automatically detects the following scenarios to trigger an account switch:

| Error Type | Example Message |
|------------|-----------------|
| HTTP 429 | `429 Too Many Requests` |
| Quota Exhausted | `Resource exhausted`, `Quota exceeded` |
| CLI Tip | `Usage limit reached for all Pro models` |
| Wait for Reset | `Access resets at 11:55 PM GMT+8` |
| Selection UI | `1. Keep trying  2. Stop` |

### Q: What should I do if a 403 VALIDATION_REQUIRED error occurs?

This is a Google Account verification issue, not an issue with the switching tool.

**Steps to solve**:
1. Visit the validation link in the error message.
2. Log in to the corresponding Google account and complete the verification.
3. Or delete credentials and log in again: `rm ~/.gemini/oauth_creds.json && gemini`

### Q: How to switch languages manually?

```bash
# Edit config file
# Add "language": "cn" or "en" to ~/.gemini/auth_config.json
```

---

## ❤️ Contributing

Feel free to submit issues or pull requests if you have ideas for improvements!
