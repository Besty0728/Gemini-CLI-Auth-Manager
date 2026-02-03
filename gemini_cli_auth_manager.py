#!/usr/bin/env python3
"""
Gemini CLI Auth Manager v2.0
Fast account switching with auto-rotation support for Gemini CLI.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

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
    "auto_switch": {
        "enabled": True,
        "strategy": "gemini3-first",
        "model_pattern": "gemini-3.*",
        "threshold": 5,
        "max_retries": 3,
        "notify_on_switch": True,
        "auto_restart": False,
        "cache_minutes": 3
    }
}

# --- Language Dictionary ---
LANG = {
    "en": {
        "title": "GEMINI-CLI-AUTH-MANAGER v2.0",
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
        "view_quota": "View Current Quota",
        "config_auto": "Configure Auto-Switch",
        "toggle_auto": "Toggle Auto-Switch (Enable/Disable)",
        "toggle_restart": "Toggle Auto-Restart",
        "manage_pool": "Manage Account Pool",
        "available_accounts": "Available Accounts",
        "enter_account_num": "Enter account number",
        "select_strategy": "Select Strategy",
        "conservative_desc": "Switch when ALL models exhausted",
        "gemini3_desc": "Switch when Gemini 3.x exhausted",
        "auto_config": "Auto-Switch Configuration",
        "set_threshold": "Set Threshold",
        "set_retries": "Set Max Retries",
        "set_pattern": "Set Model Pattern",
        "toggle_restart_sub": "Toggle Auto-Restart",
        "toggle_notify": "Toggle Notifications",
        "pool_mgmt": "Account Pool Management",
        "total": "Total",
        "options": "Options",
        "add_account": "Add new account",
        "remove_account": "Remove account",
        "import_creds": "Import credentials",
        "back": "Back to main menu",
        "invalid_choice": "Invalid choice. Please try again.",
        "press_enter": "Press Enter to continue...",
        "pool_overview": "Account Pool Overview",
        "standby": "Standby",
        "error": "Error",
        "ok": "OK",
        "warning": "Warning",
        "info": "Info",
        "no_profiles": "No profiles found",
        "switched_to": "Switched to",
        "already_using": "Already using",
        "account_added": "Account added",
        "account_removed": "Removed",
        "cannot_remove_active": "Cannot remove active account",
        "switch_first": "Please switch to another account first",
        "confirm_remove": "Remove",
        "cancelled": "Cancelled",
        "enter_email": "Enter account email",
        "invalid_email": "Invalid email format",
        "account_exists": "Account already exists",
        "use_current_creds": "Use current credentials for",
        "dir_created": "Account directory created",
        "complete_setup": "To complete setup",
        "file_not_found": "File not found",
        "imported": "Imported",
        "enter_path": "Enter credentials file path",
        "enter_remove_num": "Enter account number to remove"
    },
    "cn": {
        "title": "GEMINI-CLI 账号管理器 v2.0",
        "subtitle": "快速切换 + 自动轮换 | By Besty",
        "status": "状态",
        "active": "活跃",
        "auto": "自动",
        "enabled": "已启用",
        "disabled": "已禁用",
        "accounts": "账号列表",
        "usage": "使用方法",
        "current_status": "当前状态",
        "active_account": "活跃账号",
        "auto_switch": "自动切换",
        "strategy": "策略",
        "threshold": "阈值",
        "menu": "菜单",
        "exit": "退出",
        "goodbye": "再见！",
        "enter_choice": "请输入选项",
        "switch_account": "切换账号",
        "switch_next": "切换到下一个账号",
        "change_strategy": "更改策略",
        "view_quota": "查看当前配额",
        "config_auto": "配置自动切换",
        "toggle_auto": "开关自动切换功能",
        "toggle_restart": "开关自动重启功能",
        "manage_pool": "管理账号池",
        "available_accounts": "可用账号",
        "enter_account_num": "请输入账号编号",
        "select_strategy": "选择策略",
        "conservative_desc": "所有模型耗尽时切换",
        "gemini3_desc": "Gemini 3.x 耗尽时切换",
        "auto_config": "自动切换配置",
        "set_threshold": "设置阈值",
        "set_retries": "设置最大重试次数",
        "set_pattern": "设置模型匹配规则",
        "toggle_restart_sub": "开关自动重启",
        "toggle_notify": "切换通知开关",
        "pool_mgmt": "账号池管理",
        "total": "共计",
        "options": "选项",
        "add_account": "添加新账号",
        "remove_account": "删除账号",
        "import_creds": "导入凭证",
        "back": "返回主菜单",
        "invalid_choice": "无效选项，请重试。",
        "press_enter": "按回车键继续...",
        "pool_overview": "账号池概览",
        "standby": "待机",
        "error": "错误",
        "ok": "成功",
        "warning": "警告",
        "info": "提示",
        "no_profiles": "未找到账号",
        "switched_to": "已切换到",
        "already_using": "当前已在使用",
        "account_added": "账号已添加",
        "account_removed": "已删除",
        "cannot_remove_active": "无法删除活跃账号",
        "switch_first": "请先切换到其他账号",
        "confirm_remove": "确认删除",
        "cancelled": "已取消",
        "enter_email": "请输入账号邮箱",
        "invalid_email": "邮箱格式无效",
        "account_exists": "账号已存在",
        "use_current_creds": "是否使用当前凭证",
        "dir_created": "账号目录已创建",
        "complete_setup": "完成设置步骤",
        "file_not_found": "文件未找到",
        "imported": "已导入",
        "enter_path": "请输入凭证文件路径",
        "enter_remove_num": "请输入要删除的账号编号"
    }
}

# --- UI Helpers ---
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
    
    if not args:
        # Show current strategy
        print(f"\n{UI.BOLD}Current Strategy:{UI.RESET} {auto_switch.get('strategy', 'gemini3-first')}")
        print(f"\n{UI.BOLD}Available Strategies:{UI.RESET}")
        print(f"  - {UI.CYAN}conservative{UI.RESET}    : Switch when ALL models exhausted")
        print(f"  - {UI.CYAN}gemini3-first{UI.RESET}   : Switch when Gemini 3.x models exhausted")
        print(f"\n{UI.BOLD}Usage:{UI.RESET} gchange strategy <conservative|gemini3-first>")
        return
    
    strategy = args[0].lower()
    valid_strategies = ["conservative", "gemini3-first"]
    
    if strategy not in valid_strategies:
        print(f"{UI.RED}[Error] Invalid strategy: {strategy}{UI.RESET}")
        print(f"Valid options: {', '.join(valid_strategies)}")
        return
    
    auto_switch["strategy"] = strategy
    config["auto_switch"] = auto_switch
    
    if save_config(config):
        print(f"{UI.GREEN}[OK] Strategy set to: {strategy}{UI.RESET}")


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
    valid_keys = ["enabled", "strategy", "model_pattern", "threshold", "max_retries", "notify_on_switch", "cache_minutes", "models_to_check"]
    
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
    if key in ["enabled", "notify_on_switch"]:
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
                print(f"  {idx + 1:02d}. {p:40s} {status}")
        
        print(f"{UI.line('-', 50)}")
        print(f"  {t('total')}: {UI.CYAN}{len(profiles)}{UI.RESET}")
        print(f"\n{UI.BOLD}Commands:{UI.RESET}")
        print(f"  gchange pool add              {t('add_account')}")
        print(f"  gchange pool add <email>      {t('add_account')}")
        print(f"  gchange pool remove <n>       {t('remove_account')}")
        print(f"  gchange pool import <path>    {t('import_creds')}")
        return
    
    subcmd = args[0].lower()
    subargs = args[1:]
    
    if subcmd == "add":
        add_account(subargs)
    elif subcmd in ["remove", "delete", "rm"]:
        remove_account(subargs)
    elif subcmd == "import":
        import_account(subargs)
    else:
        print(f"{UI.RED}[Error] Unknown pool command: {subcmd}{UI.RESET}")
        print("Valid commands: add, remove, import")


def add_account(args):
    """Add a new account to the pool."""
    if args:
        email = args[0]
    else:
        try:
            email = input(f"  Enter account email: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
    
    if not email or "@" not in email:
        print(f"{UI.RED}[Error] Invalid email format.{UI.RESET}")
        return
    
    # Create profile directory
    profile_dir = PROFILES_DIR / email
    
    if profile_dir.exists():
        print(f"{UI.YELLOW}[Warning] Account already exists: {email}{UI.RESET}")
        return
    
    profile_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if current credentials should be used
    if CREDS_FILE.exists():
        try:
            use_current = input(f"  Use current credentials for {email}? (y/N): ").strip().lower()
            if use_current in ["y", "yes"]:
                shutil.copy2(CREDS_FILE, profile_dir / "oauth_creds.json")
                if ID_FILE.exists():
                    shutil.copy2(ID_FILE, profile_dir / "google_account_id")
                print(f"{UI.GREEN}[OK] Account added: {email}{UI.RESET}")
                return
        except (EOFError, KeyboardInterrupt):
            print()
            return
    
    # Create placeholder
    print(f"{UI.YELLOW}[Info] Account directory created: {profile_dir}{UI.RESET}")
    print(f"  To complete setup:")
    print(f"  1. Login with Gemini CLI using this account")
    print(f"  2. Run: gchange pool import <path_to_oauth_creds.json>")
    print(f"  Or manually copy oauth_creds.json to: {profile_dir}")


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


def interactive_menu():
    """Interactive configuration menu."""
    while True:
        UI.header()
        config = load_config()
        auto_switch = config.get("auto_switch", DEFAULT_CONFIG["auto_switch"])
        active = get_active_account()
        profiles = get_profiles()
        
        # Current Status
        print(f"\n  {UI.BOLD}{t('current_status')}:{UI.RESET}")
        print(f"  {t('active_account')} : {UI.GREEN}{active or 'None'}{UI.RESET}")
        enabled_text = t('enabled') if auto_switch.get('enabled') else t('disabled')
        print(f"  {t('auto_switch')}    : {UI.GREEN if auto_switch.get('enabled') else UI.RED}{enabled_text}{UI.RESET}")
        print(f"  {t('strategy')}       : {UI.CYAN}{auto_switch.get('strategy', 'gemini3-first')}{UI.RESET}")
        print(f"  {t('threshold')}      : {auto_switch.get('threshold', 5)}%")
        restart_text = t('enabled') if auto_switch.get('auto_restart') else t('disabled')
        print(f"  Only Restart      : {UI.GREEN if auto_switch.get('auto_restart') else UI.RED}{restart_text}{UI.RESET}")
        
        print(f"\n  {UI.BOLD}{t('menu')}:{UI.RESET}")
        print(f"  {UI.line('-', 40)}")
        print(f"  {UI.CYAN}1{UI.RESET}. {t('switch_account')}")
        print(f"  {UI.CYAN}2{UI.RESET}. {t('switch_next')}")
        print(f"  {UI.CYAN}3{UI.RESET}. {t('change_strategy')}")
        print(f"  {UI.CYAN}4{UI.RESET}. {t('view_quota')}")
        print(f"  {UI.CYAN}5{UI.RESET}. {t('config_auto')}")
        print(f"  {UI.CYAN}6{UI.RESET}. {t('toggle_auto')}")
        print(f"  {UI.CYAN}7{UI.RESET}. {t('toggle_restart')}")
        print(f"  {UI.CYAN}8{UI.RESET}. {t('manage_pool')}")
        print(f"  {UI.CYAN}0{UI.RESET}. {t('exit')}")
        print(f"  {UI.line('-', 40)}")
        
        try:
            choice = input(f"\n  {t('enter_choice')} (0-8): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        
        if choice == "0" or choice.lower() == "q":
            print(f"\n  {UI.GREEN}{t('goodbye')}{UI.RESET}\n")
            break
        
        elif choice == "1":
            # Switch Account
            print(f"\n  {UI.BOLD}{t('available_accounts')}:{UI.RESET}")
            for idx, p in enumerate(profiles):
                marker = f"{UI.GREEN}[*]{UI.RESET}" if p == active else "[ ]"
                print(f"  {idx + 1}. {marker} {p}")
            try:
                acc_choice = input(f"\n  {t('enter_account_num')} (1-{len(profiles)}): ").strip()
                if acc_choice.isdigit() and 1 <= int(acc_choice) <= len(profiles):
                    fast_switch(acc_choice)
                    input(f"\n  {t('press_enter')}")
            except (EOFError, KeyboardInterrupt):
                pass
        
        elif choice == "2":
            # Switch to Next
            switch_next()
            input(f"\n  {t('press_enter')}")
        
        elif choice == "3":
            # Change Strategy
            print(f"\n  {UI.BOLD}{t('select_strategy')}:{UI.RESET}")
            print(f"  1. {UI.CYAN}conservative{UI.RESET}  - {t('conservative_desc')}")
            print(f"  2. {UI.CYAN}gemini3-first{UI.RESET} - {t('gemini3_desc')}")
            try:
                strat_choice = input(f"\n  {t('enter_choice')} (1-2): ").strip()
                if strat_choice == "1":
                    handle_strategy(["conservative"])
                elif strat_choice == "2":
                    handle_strategy(["gemini3-first"])
                input(f"\n  {t('press_enter')}")
            except (EOFError, KeyboardInterrupt):
                pass
        
        elif choice == "4":
            # View current quota
            try:
                # Use subprocess to run independent script to avoid scope pollution
                subprocess.run(
                    ["python", str(GEMINI_DIR / "quota_api_client.py")], 
                    check=False
                )
            except Exception as e:
                print(f"{UI.RED}[Error] Failed to run quota check: {e}{UI.RESET}")
            input(f"\n  {t('press_enter')}")

        elif choice == "5":
            # Configure Auto-Switch
            print(f"\n  {UI.BOLD}{t('auto_config')}:{UI.RESET}")
            print(f"  1. {t('set_threshold')} ({auto_switch.get('threshold', 5)}%)")
            print(f"  2. {t('set_retries')} ({auto_switch.get('max_retries', 3)})")
            print(f"  3. {t('set_pattern')} ({auto_switch.get('model_pattern', 'gemini-3.*')})")
            print(f"  4. {t('toggle_notify')} ({auto_switch.get('notify_on_switch', True)})")
            print(f"  5. {t('toggle_restart_sub')} ({auto_switch.get('auto_restart', False)})")
            try:
                cfg_choice = input(f"\n  {t('enter_choice')} (1-5): ").strip()
                if cfg_choice == "1":
                    val = input(f"  {t('threshold')} (0-100): ").strip()
                    handle_config(["threshold", val])
                elif cfg_choice == "2":
                    val = input(f"  Max retries: ").strip()
                    handle_config(["max_retries", val])
                elif cfg_choice == "3":
                    val = input(f"  Model pattern: ").strip()
                    handle_config(["model_pattern", val])
                elif cfg_choice == "4":
                    current = auto_switch.get('notify_on_switch', True)
                    handle_config(["notify_on_switch", "false" if current else "true"])
                elif cfg_choice == "5":
                    current = auto_switch.get('auto_restart', False)
                    handle_config(["auto_restart", "false" if current else "true"])
                input(f"\n  {t('press_enter')}")
            except (EOFError, KeyboardInterrupt):
                pass
        
        elif choice == "6":
            # Toggle Auto-Switch
            current = auto_switch.get('enabled', True)
            handle_config(["enabled", "false" if current else "true"])
            input(f"\n  {t('press_enter')}")
        
        elif choice == "7":
            # Toggle Auto-Restart
            curr = auto_switch.get("auto_restart", False)
            auto_switch["auto_restart"] = not curr
            config["auto_switch"] = auto_switch
            save_config(config)
            print(f"{UI.GREEN}[OK] Auto-Restart {'Enabled' if not curr else 'Disabled'}{UI.RESET}")
            time.sleep(1)

        elif choice == "8":
            # Manage Account Pool
            print(f"\n  {UI.BOLD}{t('pool_mgmt')}:{UI.RESET}")
            print(f"  {UI.line('-', 40)}")
            for idx, p in enumerate(profiles):
                if p == active:
                    status = f"{UI.GREEN}● {t('active')}{UI.RESET}"
                else:
                    status = f"{UI.DIM}○ {t('standby')}{UI.RESET}"
                print(f"  {idx + 1:02d}. {p:35s} {status}")
            print(f"  {UI.line('-', 40)}")
            print(f"  {t('total')}: {UI.CYAN}{len(profiles)}{UI.RESET}")
            print(f"\n  {t('options')}:")
            print(f"  a. {t('add_account')}")
            print(f"  r. {t('remove_account')}")
            print(f"  i. {t('import_creds')}")
            print(f"  b. {t('back')}")
            try:
                pool_choice = input(f"\n  {t('enter_choice')}: ").strip().lower()
                if pool_choice == "a":
                    add_account([])
                elif pool_choice == "r":
                    acc = input(f"  {t('enter_remove_num')}: ").strip()
                    remove_account([acc])
                elif pool_choice == "i":
                    path = input(f"  {t('enter_path')}: ").strip()
                    import_account([path])
                input(f"\n  {t('press_enter')}")
            except (EOFError, KeyboardInterrupt):
                pass
        
        else:
            print(f"\n  {UI.YELLOW}{t('invalid_choice')}{UI.RESET}")
            input(f"\n  {t('press_enter')}")


def main():
    """Main entry point."""
    # Enable ANSI colors on Windows
    if os.name == 'nt':
        os.system('')
    
    if len(sys.argv) < 2:
        list_status()
        return
    
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
