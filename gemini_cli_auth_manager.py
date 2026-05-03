#!/usr/bin/env python3
"""
Gemini CLI Auth Manager v2.4
Fast account switching with auto-rotation support for Gemini CLI.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import webbrowser
import requests
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# --- Configuration Paths ---
GEMINI_DIR = Path(os.path.expanduser("~/.gemini"))
PROFILES_DIR = GEMINI_DIR / "auth_profiles"
ACCOUNTS_JSON = GEMINI_DIR / "google_accounts.json"
CREDS_FILE = GEMINI_DIR / "oauth_creds.json"
ID_FILE = GEMINI_DIR / "google_account_id"
CONFIG_FILE = GEMINI_DIR / "auth_config.json"

# --- Default Configuration ---
DEFAULT_CONFIG = {
    "language": "en",
    "oauth_client": {
        "client_id": "681255809395-" + "oo8ft2oprdrnp9e3aqf6av3hmdib135j.apps.googleusercontent.com",
        "client_secret": "GOCSPX" + "-4uHgMPm-1o7Sk-geV6Cu5clXFsxl"
    },
    "auto_switch": {
        "enabled": True,
        "strategy": "gemini3.1-series-only",
        "model_pattern": "gemini-3.1.*",
        "custom_model_pattern": "",
        "threshold": 10,
        "max_retries": 3,
        "notify_on_switch": True,
        "auto_restart": False,
        "cache_minutes": 3
    }
}

def _init_oauth_credentials():
    """Load OAuth client credentials from ~/.gemini/auth_config.json at startup."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            oauth = cfg.get("oauth_client", {})
            cid = oauth.get("client_id", "")
            cs = oauth.get("client_secret", "")
            if cid and cs:
                return cid, cs
        except Exception:
            pass
    return DEFAULT_CONFIG["oauth_client"]["client_id"], DEFAULT_CONFIG["oauth_client"]["client_secret"]

GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET = _init_oauth_credentials()
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]

# --- Language Dictionary ---
LANG = {
    "en": {
        "title": "GEMINI-CLI-AUTH-MANAGER v2.4",
        "subtitle": "Fast Switcher + Auto Rotation | By Besty",
        "status": "STATUS",
        "active": "ACTIVE",
        "auto": "AUTO",
        "enabled": "Enabled",
        "disabled": "Disabled",
        "accounts": "ACCOUNTS",
        "usage": "USAGE",
        "current_status": "Current Status",
        "active_account": "Active Account",
        "auto_switch": "Auto-Switch",
        "strategy": "Strategy",
        "threshold": "Threshold",
        "menu": "Menu",
        "exit": "Exit",
        "goodbye": "Goodbye!",
        "enter_choice": "Enter choice",
        "switch_account": "Switch Account",
        "switch_next": "Switch to Next Account",
        "change_strategy": "Change Strategy",
        "select_strategy": "Select Strategy",
        "strategy_desc": {
            "conservative": "Monitor ALL models (Switch if ANY runs out)",
            "gemini3-first": "Monitor Gemini 3.0+ series (gemini-3.*)",
            "gemini3.1-pro-only": "Monitor Gemini 3.1 Pro Only (gemini-3.1-pro.*)",
            "gemini3.1-series-only": "Monitor Gemini 3.1 Series (gemini-3.1.*)",
            "custom": "Custom regex pattern"
        },
        "enter_custom_pattern": "Enter custom regex pattern (e.g. gemini-2.5.*): ",
        "invalid_regex": "Invalid regex pattern. Please try again.",
        "strategy_updated": "Strategy set to",
        "strategy_invalid": "Invalid strategy",
        "manage_pool": "Manage Account Pool",
        "toggle_auto": "Toggle Auto-Switch",
        "toggle_restart": "Toggle Auto-Restart",
        "config_details": "View Detailed Config",
        "current_val": "Current value",
        "new_val": "Enter new value (empty to cancel)",
        "updated": "Updated",
        "invalid_val": "Invalid value",
        "error": "Error",
        "success": "Success",
        "account_pool": "Account Pool Management",
        "pool_list": "List Accounts",
        "pool_login": "Add Account (OAuth Login)",
        "pool_remove": "Remove Account",
        "pool_import": "Import Credentials",
        "pool_back": "Back to Main Menu",
        "enter_idx_email": "Enter account index or email",
        "confirm_remove": "Are you sure you want to remove account",
        "login_browser": "Opening browser for OAuth login...",
        "login_success": "Successfully added account",
        "login_failed": "Login failed",
        "file_not_found": "File not found",
        "import_success": "Imported credentials from",
        "restarting": "Restarting Gemini CLI...",
        "pool_overview": "Account Pool Overview",
        "no_profiles": "No accounts found in pool",
        "total": "Total",
        "options": "Options",
        "pool_mgmt": "Account Pool Management",
        "remove_account": "Remove Account",
        "import_creds": "Import Credentials",
        "enter_remove_num": "Enter account index to remove",
        "enter_path": "Enter path to credentials file",
        "back": "Back",
        "active": "Active",
        "standby": "Standby"
    },
    "cn": {
        "title": "GEMINI CLI 账号管理器 v2.4",
        "subtitle": "极速切换 + 自动轮换 | By Besty",
        "status": "状态",
        "active": "正在使用",
        "auto": "自动切换",
        "enabled": "已启用",
        "disabled": "已禁用",
        "accounts": "号池",
        "usage": "用法",
        "current_status": "当前状态",
        "active_account": "当前账号",
        "auto_switch": "配额自动切换",
        "strategy": "切换策略",
        "threshold": "切换阈值",
        "menu": "主菜单",
        "exit": "退出",
        "goodbye": "再见！",
        "enter_choice": "请输入选项",
        "switch_account": "切换账号",
        "switch_next": "切换到下一个账号",
        "change_strategy": "更改轮换策略",
        "select_strategy": "选择轮换策略",
        "strategy_desc": {
            "conservative": "保守模式：监控所有模型（任一耗尽即切）",
            "gemini3-first": "Gemini 3.0+ 优先 (匹配 gemini-3.*)",
            "gemini3.1-pro-only": "仅监控 Gemini 3.1 Pro (匹配 gemini-3.1-pro.*)",
            "gemini3.1-series-only": "监控 Gemini 3.1 全系列 (匹配 gemini-3.1.*)",
            "custom": "自定义正则表达式模式"
        },
        "enter_custom_pattern": "请输入自定义正则表达式 (例如 gemini-2.5.*): ",
        "invalid_regex": "无效的正则表达式，请重试。",
        "strategy_updated": "策略已设置为",
        "strategy_invalid": "无效的策略名称",
        "manage_pool": "管理账号池",
        "toggle_auto": "开启/关闭自动切换",
        "toggle_restart": "开启/关闭自动重启",
        "config_details": "查看详细配置",
        "current_val": "当前值",
        "new_val": "请输入新值 (留空取消)",
        "updated": "已更新",
        "invalid_val": "无效的值",
        "error": "错误",
        "success": "成功",
        "account_pool": "账号池管理",
        "pool_list": "查看账号列表",
        "pool_login": "添加账号 (OAuth 登录)",
        "pool_remove": "删除账号",
        "pool_import": "导入凭据文件",
        "pool_back": "返回主菜单",
        "enter_idx_email": "请输入账号序号或邮箱",
        "confirm_remove": "确定要删除账号吗",
        "login_browser": "正在打开浏览器进行登录...",
        "login_success": "成功添加账号",
        "login_failed": "登录失败",
        "file_not_found": "找不到文件",
        "import_success": "成功导入凭据",
        "restarting": "正在重启 Gemini CLI...",
        "pool_overview": "账号池概览",
        "no_profiles": "号池中没有账号",
        "total": "总计",
        "options": "选项",
        "pool_mgmt": "号池管理",
        "remove_account": "删除账号",
        "import_creds": "导入凭据",
        "enter_remove_num": "请输入要删除的账号序号",
        "enter_path": "请输入凭据文件路径",
        "back": "返回",
        "active": "正在使用",
        "standby": "待命"
    }
}
class UI:
    RESET = "\033[0m"
    BOLD  = "\033[1m"
    CYAN  = "\033[36m"
    GREEN = "\033[32m"
    YELLOW= "\033[33m"
    RED   = "\033[31m"
    DIM   = "\033[2m"

    @staticmethod
    def line(char="=", width=60):
        return char * width

    @staticmethod
    def header():
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{UI.CYAN}{UI.line('=')}{UI.RESET}")
        print(f"{UI.BOLD}  {t('title')}{UI.RESET}")
        print(f"{UI.DIM}  {t('subtitle')}{UI.RESET}")
        print(f"{UI.CYAN}{UI.line('=')}{UI.RESET}")


# --- Configuration Management ---
def load_config():
    """Load configuration from file, return defaults if not exists."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_CONFIG.copy()


def get_lang():
    """Get current language from config."""
    config = load_config()
    return config.get("language", "en")


def t(key):
    """Get translated text for key."""
    lang = get_lang()
    return LANG.get(lang, LANG["en"]).get(key, key)


def save_config(config):
    """Save configuration to file."""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"{UI.RED}[Error] Failed to save config: {e}{UI.RESET}")
        return False


def get_profiles():
    """Get sorted list of profile names."""
    if not PROFILES_DIR.exists():
        return []
    return sorted([d.name for d in PROFILES_DIR.iterdir() if d.is_dir()])


def get_active_account():
    """Get currently active account email."""
    if ACCOUNTS_JSON.exists():
        try:
            with open(ACCOUNTS_JSON, 'r', encoding='utf-8') as f:
                return json.load(f).get('active')
        except:
            pass
    return None


def get_account_data():
    """Get full account data."""
    if ACCOUNTS_JSON.exists():
        try:
            with open(ACCOUNTS_JSON, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"active": None, "old": []}


# --- Core Functions ---
def fast_switch(target_arg, silent=False):
    """Switch to specified account by index or email."""
    profiles = get_profiles()
    if not profiles:
        if not silent:
            print(f"{UI.RED}[Error] No profiles found.{UI.RESET}")
        return None

    target_dir = PROFILES_DIR / target_arg
    target_email = target_arg

    # Handle numeric index
    if not target_dir.exists():
        if target_arg.isdigit():
            idx = int(target_arg) - 1
            if 0 <= idx < len(profiles):
                target_email = profiles[idx]
                target_dir = PROFILES_DIR / target_email
            else:
                if not silent:
                    print(f"{UI.RED}[Error] Index {target_arg} out of range (1-{len(profiles)}).{UI.RESET}")
                return None
        else:
            if not silent:
                print(f"{UI.RED}[Error] Account not found: {target_arg}{UI.RESET}")
            return None

    target_creds = target_dir / "oauth_creds.json"
    if not target_creds.exists():
        if not silent:
            print(f"{UI.RED}[Error] Missing credentials for: {target_email}{UI.RESET}")
        return None

    data = get_account_data()
    current_active = data.get('active')

    if current_active == target_email:
        if not silent:
            print(f"{UI.GREEN}[OK] Already using {target_email}{UI.RESET}")
        return target_email

    # Backup current credentials
    if current_active:
        curr_dir = PROFILES_DIR / current_active
        curr_dir.mkdir(parents=True, exist_ok=True)
        if CREDS_FILE.exists():
            shutil.copy2(CREDS_FILE, curr_dir / "oauth_creds.json")
        if ID_FILE.exists():
            shutil.copy2(ID_FILE, curr_dir / "google_account_id")

    # Perform switch
    try:
        shutil.copy2(target_creds, CREDS_FILE)
        t_id = target_dir / "google_account_id"
        if t_id.exists():
            shutil.copy2(t_id, ID_FILE)
        elif ID_FILE.exists():
            ID_FILE.unlink(missing_ok=True)
            
        # --- NEW: Clear Token Cache ---
        # Gemini CLI caches tokens. We must delete this cache to force it to use our new oauth_creds.json
        cache_file = GEMINI_DIR / "mcp-oauth-tokens-v2.json"
        if cache_file.exists():
            try:
                cache_file.unlink()
                if not silent:
                    print(f"{UI.DIM}  [Cache] Cleared token cache to force reload.{UI.RESET}")
            except OSError as e:
                if not silent:
                    print(f"{UI.YELLOW}[Warning] Failed to clear token cache: {e}{UI.RESET}")
        # ------------------------------
    except OSError as e:
        if not silent:
            print(f"{UI.RED}[Error] Switch failed: {e}{UI.RESET}")
        return None

    # Update state
    if current_active and current_active != target_email:
        if 'old' not in data:
            data['old'] = []
        if current_active not in data['old']:
            data['old'].append(current_active)
    data['active'] = target_email
    if 'old' in data and target_email in data['old']:
        data['old'].remove(target_email)

    try:
        with open(ACCOUNTS_JSON, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except:
        pass

    if not silent:
        print(f"{UI.GREEN}[OK] Switched to {target_email}{UI.RESET}")
    return target_email


def switch_next(silent=False):
    """Switch to the next account in rotation."""
    profiles = get_profiles()
    if not profiles:
        if not silent:
            print(f"{UI.RED}[Error] No profiles found.{UI.RESET}")
        return None

    current = get_active_account()
    if current and current in profiles:
        current_idx = profiles.index(current)
        next_idx = (current_idx + 1) % len(profiles)
    else:
        next_idx = 0

    next_account = profiles[next_idx]
    
    # Check if we've cycled through all accounts
    if next_account == current:
        if not silent:
            print(f"{UI.YELLOW}[Warning] Only one account available.{UI.RESET}")
        return None

    return fast_switch(next_account, silent=silent)


def list_status():
    """Display current status and all accounts."""
    UI.header()
    
    active = get_active_account()
    config = load_config()
    auto_switch = config.get("auto_switch", {})

    # Status Section
    print(f"\n  {UI.BOLD}STATUS:{UI.RESET}")
    if active:
        print(f"  [ ACTIVE ] {UI.GREEN}{active}{UI.RESET}")
    else:
        print(f"  [ ACTIVE ] {UI.YELLOW}None{UI.RESET}")
    
    # Auto-switch status
    if auto_switch.get("enabled", False):
        strategy = auto_switch.get("strategy", "gemini3-first")
        threshold = auto_switch.get("threshold", 5)
        print(f"  [ AUTO   ] {UI.CYAN}Enabled{UI.RESET} | Strategy: {strategy} | Threshold: {threshold}%")
    else:
        print(f"  [ AUTO   ] {UI.DIM}Disabled{UI.RESET}")
    
    # Accounts Section
    print(f"\n  {UI.BOLD}ACCOUNTS:{UI.RESET}")
    print(f"  {UI.line('-', 40)}")

    profiles = get_profiles()
    if profiles:
        for idx, p in enumerate(profiles):
            if p == active:
                marker = f"{UI.GREEN}[*]{UI.RESET}"
                label = f"{UI.GREEN}{p} (Active){UI.RESET}"
            else:
                marker = "[ ]"
                label = p
            print(f"  {idx + 1:02d}. {marker} {label}")
    else:
        print("  (No profiles found)")

    print(f"  {UI.line('-', 40)}")
    
    # Usage
    print(f"\n  {UI.BOLD}USAGE:{UI.RESET}")
    print(f"  gchange                    List accounts")
    print(f"  gchange <number|email>     Switch account")
    print(f"  gchange next               Switch to next account")
    print(f"  gchange menu               Interactive menu")
    print(f"  gchange pool               Manage account pool")
    print(f"  gchange strategy [name]    View/set strategy")
    print(f"  gchange config [key] [val] View/set config")
    print(f"\n{UI.CYAN}{UI.line('=')}{UI.RESET}\n")


def handle_strategy(args):
    """Handle strategy command."""
    config = load_config()
    auto_switch = config.get("auto_switch", DEFAULT_CONFIG["auto_switch"])

    valid_strategies = ["conservative", "gemini3-first", "gemini3.1-pro-only", "gemini3.1-series-only", "custom"]

    if not args:
        # Show current strategy
        current = auto_switch.get("strategy", "gemini3.1-series-only")
        print(f"\n{UI.BOLD}{t('strategy')}:{UI.RESET} {current}")
        if current == 'custom':
            print(f"  {UI.DIM}Custom Pattern: {auto_switch.get('custom_model_pattern', 'Not set')}{UI.RESET}")

        print(f"\n{UI.BOLD}{t('select_strategy')}:{UI.RESET}")
        for s in valid_strategies:
            desc = t("strategy_desc").get(s, "")
            print(f"  - {UI.CYAN}{s.ljust(22)}{UI.RESET} : {desc}")

        print(f"\n{UI.BOLD}{t('usage')}:{UI.RESET} gchange strategy <{'|'.join(valid_strategies)}>")
        return

    strategy = args[0].lower()

    # Alias support
    if strategy == "pro": strategy = "gemini3.1-pro-only"
    if strategy == "series": strategy = "gemini3.1-series-only"

    if strategy not in valid_strategies:
        print(f"{UI.RED}[{t('error')}] {t('strategy_invalid')}: {strategy}{UI.RESET}")
        print(f"Valid options: {', '.join(valid_strategies)}")
        return

    if strategy == "custom":
        # Read the remaining args as pattern or prompt
        if len(args) > 1:
            pattern = args[1]
        else:
            try:
                pattern = input(f"\n  {t('enter_custom_pattern')}").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return

        if pattern:
            try:
                re.compile(pattern)
                auto_switch["custom_model_pattern"] = pattern
            except re.error:
                print(f"{UI.RED}[{t('error')}] {t('invalid_regex')}{UI.RESET}")
                return
        else:
            print(f"{UI.YELLOW}[Warning] Custom pattern not set. Strategy change aborted.{UI.RESET}")
            return

    # Update model_pattern for presets
    if strategy == "gemini3.1-pro-only":
        auto_switch["model_pattern"] = "gemini-3.1-pro.*"
    elif strategy == "gemini3.1-series-only":
        auto_switch["model_pattern"] = "gemini-3.1.*"
    elif strategy == "gemini3-first":
        auto_switch["model_pattern"] = "gemini-3.*"

    auto_switch["strategy"] = strategy
    config["auto_switch"] = auto_switch

    if save_config(config):
        print(f"{UI.GREEN}[OK] {t('strategy_updated')}: {UI.BOLD}{strategy}{UI.RESET}")
        if strategy == "custom":
            print(f"  Pattern: {auto_switch['custom_model_pattern']}")
    else:
        print(f"{UI.RED}[{t('error')}] Failed to save config.{UI.RESET}")


def handle_config(args):
    """Handle config command."""
    config = load_config()
    auto_switch = config.get("auto_switch", DEFAULT_CONFIG["auto_switch"])
    
    if not args:
        # Show full config
        print(f"\n{UI.BOLD}Auto-Switch Configuration:{UI.RESET}")
        print(f"  enabled        : {UI.GREEN if auto_switch.get('enabled') else UI.RED}{auto_switch.get('enabled', True)}{UI.RESET}")
        print(f"  strategy       : {UI.CYAN}{auto_switch.get('strategy', 'gemini3-first')}{UI.RESET}")
        print(f"  model_pattern  : {auto_switch.get('model_pattern', 'gemini-3.*')}")
        print(f"  threshold      : {auto_switch.get('threshold', 5)}%")
        print(f"  cache_minutes  : {auto_switch.get('cache_minutes', 5)}")
        print(f"  models_to_check: {auto_switch.get('models_to_check', [])}")
        print(f"\n{UI.BOLD}Usage:{UI.RESET} gchange config <key> <value>")
        return
    
    key = args[0].lower()
    valid_keys = ["enabled", "strategy", "model_pattern", "threshold", "max_retries", "notify_on_switch", "auto_restart", "cache_minutes", "models_to_check"]
    
    if key not in valid_keys:
        print(f"{UI.RED}[Error] Invalid config key: {key}{UI.RESET}")
        print(f"Valid keys: {', '.join(valid_keys)}")
        return
    
    if len(args) < 2:
        # Show specific key value
        print(f"{key} = {auto_switch.get(key, 'not set')}")
        return
    
    value = args[1]
    
    # Type conversion
    if key in ["enabled", "notify_on_switch", "auto_restart"]:
        value = value.lower() in ["true", "1", "yes", "on"]
    elif key in ["threshold", "max_retries", "cache_minutes"]:
        try:
            value = int(value)
        except ValueError:
            print(f"{UI.RED}[Error] {key} must be a number.{UI.RESET}")
            return
    elif key == "models_to_check":
        # Parse comma-separated list
        value = [x.strip() for x in value.split(",") if x.strip()]
    
    auto_switch[key] = value
    config["auto_switch"] = auto_switch
    
    if save_config(config):
        print(f"{UI.GREEN}[OK] {key} = {value}{UI.RESET}")


def handle_pool(args):
    """Handle pool command - manage account pool."""
    profiles = get_profiles()
    active = get_active_account()
    
    if not args:
        # Show pool overview
        print(f"\n{UI.BOLD}{t('pool_overview')}:{UI.RESET}")
        print(f"{UI.line('-', 50)}")
        
        if not profiles:
            print(f"  {UI.YELLOW}({t('no_profiles')}){UI.RESET}")
        else:
            for idx, p in enumerate(profiles):
                if p == active:
                    status = f"{UI.GREEN}● {t('active')}{UI.RESET}"
                else:
                    status = f"{UI.DIM}○ {t('standby')}{UI.RESET}"
                print(f"  {idx + 1:02d}. {p:35s} {status}")
        
        print(f"{UI.line('-', 50)}")
        print(f"  {t('total')}: {UI.CYAN}{len(profiles)}{UI.RESET}")
        print(f"\n{UI.BOLD}{t('usage')}:{UI.RESET}")
        print(f"  gchange pool login            {t('pool_login')}")
        print(f"  gchange pool login <email>    {t('pool_login')}")
        print(f"  gchange pool remove <n>       {t('remove_account')}")
        print(f"  gchange pool import <path>    {t('import_creds')}")
        return
    
    subcmd = args[0].lower()
    subargs = args[1:]
    
    if subcmd == "login":
        login_account(subargs)
    elif subcmd in ["remove", "delete", "rm"]:
        remove_account(subargs)
    elif subcmd == "import":
        import_account(subargs)
    else:
        print(f"{UI.RED}[Error] Unknown pool command: {subcmd}{UI.RESET}")
        print("Valid commands: add, remove, import")


def remove_account(args):
    """Remove an account from the pool."""
    profiles = get_profiles()
    active = get_active_account()
    
    if not args:
        print(f"{UI.RED}[Error] Please specify account number or email.{UI.RESET}")
        print(f"Usage: gchange pool remove <number|email>")
        return
    
    target = args[0]
    target_email = None
    
    # Find target
    if target.isdigit():
        idx = int(target) - 1
        if 0 <= idx < len(profiles):
            target_email = profiles[idx]
        else:
            print(f"{UI.RED}[Error] Invalid index: {target}{UI.RESET}")
            return
    else:
        if target in profiles:
            target_email = target
        else:
            print(f"{UI.RED}[Error] Account not found: {target}{UI.RESET}")
            return
    
    # Confirm deletion
    if target_email == active:
        print(f"{UI.YELLOW}[Warning] Cannot remove active account.{UI.RESET}")
        print(f"  Please switch to another account first.")
        return
    
    try:
        confirm = input(f"  Remove {target_email}? (y/N): ").strip().lower()
        if confirm not in ["y", "yes"]:
            print(f"{UI.DIM}Cancelled.{UI.RESET}")
            return
    except (EOFError, KeyboardInterrupt):
        print()
        return
    
    # Remove profile directory
    profile_dir = PROFILES_DIR / target_email
    try:
        shutil.rmtree(profile_dir)
        print(f"{UI.GREEN}[OK] Removed: {target_email}{UI.RESET}")
        
        # Update accounts.json
        data = get_account_data()
        if target_email in data.get("old", []):
            data["old"].remove(target_email)
            with open(ACCOUNTS_JSON, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
    except Exception as e:
        print(f"{UI.RED}[Error] Failed to remove: {e}{UI.RESET}")


def import_account(args):
    """Import account credentials from file."""
    if not args:
        print(f"{UI.RED}[Error] Please specify credentials file path.{UI.RESET}")
        print(f"Usage: gchange pool import <path_to_oauth_creds.json>")
        return
    
    creds_path = Path(args[0])
    
    if not creds_path.exists():
        print(f"{UI.RED}[Error] File not found: {creds_path}{UI.RESET}")
        return
    
    # Read credentials to extract email
    try:
        with open(creds_path, 'r', encoding='utf-8') as f:
            creds = json.load(f)
    except Exception as e:
        print(f"{UI.RED}[Error] Failed to read credentials: {e}{UI.RESET}")
        return
    
    # Try to get email
    if len(args) > 1:
        email = args[1]
    else:
        try:
            email = input(f"  Enter account email: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
    
    if not email or "@" not in email:
        print(f"{UI.RED}[Error] Invalid email format.{UI.RESET}")
        return
    
    # Create profile
    profile_dir = PROFILES_DIR / email
    profile_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy credentials
    shutil.copy2(creds_path, profile_dir / "oauth_creds.json")
    
    # Also look for google_account_id
    id_path = creds_path.parent / "google_account_id"
    if id_path.exists():
        shutil.copy2(id_path, profile_dir / "google_account_id")
    
    print(f"{UI.GREEN}[OK] Imported: {email}{UI.RESET}")


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handles Google OAuth callback on localhost."""
    def log_message(self, format, *args):
        pass # Silent logging

    def do_GET(self):
        query = urlparse(self.path).query
        params = parse_qs(query)
        self.server.auth_code = params.get('code', [None])[0]
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        success_msg = """
        <html>
        <body style='font-family: sans-serif; text-align: center; padding: 50px;'>
            <h1 style='color: #4CAF50;'>Authentication Successful!</h1>
            <p>You can close this window and return to the application.</p>
            <script>setTimeout(function() { window.close(); }, 2000);</script>
        </body>
        </html>
        """
        self.wfile.write(success_msg.encode('utf-8'))


def login_account(args):
    """Native Python OAuth flow to login and capture credentials to pool."""
    # Find a free port
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
    
    redirect_uri = f"http://localhost:{port}/oauth2callback"
    
    # Construct Auth URL (Match official parameter order and structure)
    from urllib.parse import urlencode
    auth_params = {
        "redirect_uri": redirect_uri,
        "access_type": "offline",
        "scope": " ".join(GOOGLE_SCOPES),
        "state": os.urandom(32).hex(), # Use a secure random state like official
        "response_type": "code",
        "client_id": GOOGLE_CLIENT_ID
    }
    # Using a simpler join to match the official look if needed, 
    # but urlencode is safer for special characters.
    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(auth_params)}"
    
    UI.header()
    print(f"\n{UI.CYAN}[OAuth] {t('starting_login')}{UI.RESET}")
    print(f"{UI.DIM}  Redirect URI: {redirect_uri}{UI.RESET}")
    print(f"\n  {UI.BOLD}Please open this URL if browser doesn't start:{UI.RESET}")
    print(f"  {UI.CYAN}{auth_url}{UI.RESET}\n")
    
    # Start local server
    server = HTTPServer(('127.0.0.1', port), OAuthCallbackHandler)
    server.auth_code = None
    
    # Open browser
    webbrowser.open(auth_url)
    
    # Wait for callback
    print(f"  {UI.YELLOW}Waiting for authentication...{UI.RESET}")
    try:
        server.handle_request()
    except KeyboardInterrupt:
        print(f"\n  {UI.RED}Login cancelled.{UI.RESET}")
        return

    if not server.auth_code:
        print(f"\n  {UI.RED}[Error] Failed to capture authorization code.{UI.RESET}")
        return

    print(f"  {UI.GREEN}Code captured. Exchanging for tokens...{UI.RESET}")
    
    # Exchange code for tokens
    try:
        # Use vs-code user agent as it might be required for this client_id
        headers = {"User-Agent": "vscode/1.92.2"}
        token_data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": server.auth_code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        
        resp = requests.post(GOOGLE_TOKEN_URL, data=token_data, headers=headers)
        resp.raise_for_status()
        tokens = resp.json()
        
        # Get User Info (Email)
        access_token = tokens.get("access_token")
        user_resp = requests.get(
            GOOGLE_USERINFO_URL, 
            headers={"Authorization": f"Bearer {access_token}", "User-Agent": "vscode/1.92.2"}
        )
        user_resp.raise_for_status()
        email = user_resp.json().get("email")
        
        if not email:
            print(f"\n  {UI.RED}[Error] Could not retrieve account email.{UI.RESET}")
            return

        # Prepare credentials object
        expiry_date = int((time.time() + tokens.get("expires_in", 3600)) * 1000)
        creds_obj = {
            "access_token": access_token,
            "refresh_token": tokens.get("refresh_token"),
            "scope": tokens.get("scope"),
            "token_type": "Bearer",
            "expiry_date": expiry_date
        }
        
        # Save to profile
        profile_dir = PROFILES_DIR / email
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        with open(profile_dir / "oauth_creds.json", "w", encoding="utf-8") as f:
            json.dump(creds_obj, f, indent=2)
            
        print(f"\n{UI.GREEN}[OK] {t('login_success')} {UI.BOLD}{email}{UI.RESET}")
        print(f"  Credentials saved to: {profile_dir}")
        
    except Exception as e:
        print(f"\n  {UI.RED}[Error] OAuth exchange failed: {e}{UI.RESET}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response: {e.response.text}")

    input(f"\n  {t('press_enter')}")


def _clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def _print_banner():
    """Print the UI banner."""
    print(f"{UI.CYAN}{UI.line('=')}{UI.RESET}")
    print(f"{UI.BOLD}  {t('title')}{UI.RESET}")
    print(f"  {UI.DIM}{t('subtitle')}{UI.RESET}")
    print(f"{UI.CYAN}{UI.line('=')}{UI.RESET}")

def interactive_menu():
    """Interactive configuration menu."""
    while True:
        _clear_screen()
        _print_banner()
        
        config = load_config()
        auto_switch = config.get("auto_switch", DEFAULT_CONFIG["auto_switch"])
        active = get_active_account()
        profiles = get_profiles()

        # Current Status
        print(f"\n  {UI.BOLD}{t('current_status')}:{UI.RESET}")
        print(f"  {t('active_account')} : {UI.GREEN}{active or 'None'}{UI.RESET}")
        is_enabled = auto_switch.get('enabled', True)
        enabled_text = t('enabled') if is_enabled else t('disabled')
        print(f"  {t('auto_switch')}    : {UI.GREEN if is_enabled else UI.RED}{enabled_text}{UI.RESET}")
        print(f"  {t('strategy')}       : {UI.CYAN}{auto_switch.get('strategy', 'gemini3.1-series-only')}{UI.RESET}")
        print(f"  {t('threshold')}      : {UI.YELLOW}{auto_switch.get('threshold', 10)}%{UI.RESET}")
        
        is_restart = auto_switch.get('auto_restart', False)
        restart_text = t('enabled') if is_restart else t('disabled')
        print(f"  Auto-Restart      : {UI.GREEN if is_restart else UI.RED}{restart_text}{UI.RESET}")

        print(f"\n  {UI.BOLD}{t('menu')}:{UI.RESET}")
        print(f"  {UI.line('-', 40)}")
        print(f"  {UI.CYAN}1{UI.RESET}. {t('switch_account')}")
        print(f"  {UI.CYAN}2{UI.RESET}. {t('switch_next')}")
        print(f"  {UI.CYAN}3{UI.RESET}. {t('change_strategy')}")
        print(f"  {UI.CYAN}4{UI.RESET}. {t('manage_pool')}")
        print(f"  {UI.CYAN}5{UI.RESET}. {t('toggle_auto')}")
        print(f"  {UI.CYAN}6{UI.RESET}. {t('toggle_restart')}")
        print(f"  {UI.CYAN}0{UI.RESET}. {t('exit')}")
        print(f"  {UI.line('-', 40)}")

        try:
            choice = input(f"\n  {t('enter_choice')} (0-6): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if choice == "0" or choice.lower() == "q":
            print(f"\n  {UI.GREEN}{t('goodbye')}{UI.RESET}\n")
            break

        elif choice == "1":
            # Switch Account
            print(f"\n  {UI.BOLD}{t('accounts')}:{UI.RESET}")
            for idx, p in enumerate(profiles):
                marker = f"{UI.GREEN}[*]{UI.RESET}" if p == active else "[ ]"
                print(f"  {idx + 1:02d}. {marker} {p}")
            try:
                acc_choice = input(f"\n  {t('enter_idx_email')}: ").strip()
                if acc_choice:
                    fast_switch(acc_choice)
                    time.sleep(1)
            except:
                pass

        elif choice == "2":
            switch_next()
            time.sleep(1)

        elif choice == "3":
            # Change Strategy
            print(f"\n  {UI.BOLD}{t('select_strategy')}:{UI.RESET}")
            strategies = [
                ("1", "conservative"),
                ("2", "gemini3-first"),
                ("3", "gemini3.1-pro-only"),
                ("4", "gemini3.1-series-only"),
                ("5", "custom")
            ]
            for idx, name in strategies:
                desc = t("strategy_desc").get(name, "")
                print(f"    {UI.CYAN}{idx}{UI.RESET}. {name.ljust(22)} - {desc}")
            
            try:
                s_choice = input(f"\n    {t('enter_choice')} [1-5]: ").strip()
                if s_choice == '1': handle_strategy(["conservative"])
                elif s_choice == '2': handle_strategy(["gemini3-first"])
                elif s_choice == '3': handle_strategy(["gemini3.1-pro-only"])
                elif s_choice == '4': handle_strategy(["gemini3.1-series-only"])
                elif s_choice == '5': handle_strategy(["custom"])
                time.sleep(1)
            except:
                pass

        elif choice == "4":
            # Manage Pool
            handle_pool([])
            input(f"\n  {t('pool_back')} (Press Enter)...")

        elif choice == "5":
            # Toggle Auto-Switch
            handle_config(["enabled", "false" if is_enabled else "true"])
            time.sleep(1)

        elif choice == "6":
            # Toggle Auto-Restart
            handle_config(["auto_restart", "false" if is_restart else "true"])
            time.sleep(1)

        else:
            time.sleep(0.5)


def main():
    """Main entry point."""
    # Enable ANSI colors on Windows
    if os.name == 'nt':
        os.system('')
    
    if len(sys.argv) < 2:
        list_status()
        return
    
    # Handle combined command and sub-command if quoted
    if " " in sys.argv[1]:
        parts = sys.argv[1].split()
        command = parts[0].lower()
        args = parts[1:] + sys.argv[2:]
    else:
        command = sys.argv[1].lower()
        args = sys.argv[2:]
    
    # Command routing
    if command == "next":
        switch_next()
    elif command == "menu":
        interactive_menu()
    elif command == "pool":
        handle_pool(args)
    elif command == "strategy":
        handle_strategy(args)
    elif command == "config":
        handle_config(args)
    elif command in ["list", "-l"]:
        list_status()
    elif command in ["help", "-h", "--help"]:
        list_status()
    else:
        # Treat as account identifier
        fast_switch(command)


if __name__ == "__main__":
    main()
