#!/usr/bin/env python3
"""
Gemini CLI Auth Manager v2.0 - Installer
Installs account manager with optional auto-switch hook.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# --- Configuration Dictionary ---
CONFIG = {
    'en': {
        'desc': 'Switch Gemini accounts. Usage: /change <index_or_email|next|strategy|config>',
        'success': 'Installation Complete!',
        'msg_cli': '1. CLI Command:  Type "gchange" in your terminal.',
        'msg_slash': '2. Slash Command: Type "/change" in Gemini CLI.',
        'msg_auto': '3. Auto-Switch:  Enabled (configurable via "gchange config")',
        'ask_auto': 'Enable auto-switch when quota exhausted? (Y/n): ',
        'hook_ok': '[OK] Auto-switch hook installed.',
        'hook_skip': '[Skip] Auto-switch disabled by user.'
    },
    'cn': {
        'desc': '切换 Gemini 账户。用法: /change <序号或邮箱|next|strategy|config>',
        'success': '安装完成！',
        'msg_cli': '1. 终端命令: 在终端直接输入 "gchange"',
        'msg_slash': '2. 斜杠命令: 在 Gemini CLI 中输入 "/change"',
        'msg_auto': '3. 自动切换: 已启用（可通过 "gchange config" 配置）',
        'ask_auto': '是否启用配额耗尽自动切换功能？(Y/n): ',
        'hook_ok': '[OK] 自动切换钩子已安装。',
        'hook_skip': '[Skip] 用户已禁用自动切换。'
    }
}


def get_user_language():
    """Prompt user to select language."""
    print("\nSelect Language / 请选择语言")
    print("1. English")
    print("2. 中文 (Chinese)")
    
    while True:
        choice = input("Enter number (1/2): ").strip()
        if choice == '1':
            return 'en'
        elif choice == '2':
            return 'cn'
        else:
            print("Invalid selection. Please enter 1 or 2.")


def add_to_path(target_dir):
    """Adds the target directory to the user PATH if not already present (Windows only)."""
    if sys.platform != "win32":
        return

    target_str = str(target_dir)
    if target_str in os.environ.get("PATH", ""):
        print(f"[Skip] Directory already in PATH: {target_str}")
        return

    print(f"Adding to user PATH: {target_str}")
    try:
        ps_command = (
            f'$key = "HKCU:\\Environment"; '
            f'$oldPath = (Get-ItemProperty -Path $key -Name Path -ErrorAction SilentlyContinue).Path; '
            f'if ($oldPath -notlike "*{target_str}*") {{ '
            f'  $newPath = $oldPath + ";{target_str}"; '
            f'  Set-ItemProperty -Path $key -Name Path -Value $newPath; '
            f'  Write-Output "Updated"; '
            f'}}'
        )
        
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_command],
            capture_output=True, text=True
        )
        
        if result.returncode == 0 and "Updated" in result.stdout:
            print("[OK] PATH updated successfully. (Restart terminal to take effect)")
        else:
            print("[Info] PATH might already be set or update requires manual check.")
            
    except Exception as e:
        print(f"[Warning] Failed to update PATH automatically: {e}")
        print(f"Please manually add this folder to your PATH: {target_str}")


def update_settings_json(gemini_dir, hook_script_path):
    """Update or create settings.json with hook configuration (official format)."""
    settings_file = gemini_dir / "settings.json"
    settings = {}
    
    # Load existing settings
    if settings_file.exists():
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except:
            pass
    
    # Prepare hook entry using OFFICIAL nested format:
    # { "matcher": "*", "hooks": [ { hook definitions } ] }
    hook_command = f'python {hook_script_path.as_posix()}'
    hook_definition = {
        "name": "quota-auto-switch",
        "type": "command",
        "command": hook_command,
        "timeout": 10000,
        "description": "Auto-switch account when quota exhausted"
    }
    
    matcher_entry = {
        "matcher": "*",
        "hooks": [hook_definition]
    }
    
    # Update hooks section
    if "hooks" not in settings:
        settings["hooks"] = {}
    
    if "AfterAgent" not in settings["hooks"]:
        settings["hooks"]["AfterAgent"] = []
    
    # Check if our hook already exists (search in nested structure)
    existing_entries = settings["hooks"]["AfterAgent"]
    hook_exists = False
    for entry in existing_entries:
        if "hooks" in entry:
            for h in entry["hooks"]:
                if "quota_auto_switch" in h.get("command", "") or h.get("name") == "quota-auto-switch":
                    hook_exists = True
                    break
    
    if not hook_exists:
        existing_entries.append(matcher_entry)
    
    # Save settings
    try:
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[Error] Failed to update settings.json: {e}")
        return False


def install():
    print("=" * 50)
    print("   Gemini-CLI-Auth-Manager v2.0 Installer")
    print("   Fast Switching + Auto Rotation Support")
    print("=" * 50)

    # 1. Get Language
    lang_key = get_user_language()
    texts = CONFIG[lang_key]

    # 2. Determine Paths
    source_dir = Path(__file__).parent.resolve()
    user_home = Path.home()
    gemini_dir = user_home / ".gemini"
    commands_dir = gemini_dir / "commands"
    hooks_dir = gemini_dir / "hooks"
    
    # Source files
    core_script = source_dir / "gemini_cli_auth_manager.py"
    hook_script = source_dir / "quota_auto_switch.py"
    config_file = source_dir / "auth_config.json"
    
    # Target files
    target_script = gemini_dir / "gemini_cli_auth_manager.py"
    target_hook = hooks_dir / "quota_auto_switch.py"
    target_config = gemini_dir / "auth_config.json"
    target_bat = gemini_dir / "gchange.bat"
    target_toml = commands_dir / "change.toml"

    print(f"\nTarget Directory: {gemini_dir}")

    # 3. Create Directories
    gemini_dir.mkdir(parents=True, exist_ok=True)
    commands_dir.mkdir(parents=True, exist_ok=True)
    hooks_dir.mkdir(parents=True, exist_ok=True)

    # 4. Copy Core Script
    if core_script.exists():
        shutil.copy2(core_script, target_script)
        print(f"[OK] Core script installed: {target_script.name}")
    else:
        print(f"[Error] Source file not found: {core_script}")
        return

    # 5. Create Batch Launcher
    bat_content = '@echo off\r\npython "%USERPROFILE%\\.gemini\\gemini_cli_auth_manager.py" %*'
    try:
        with open(target_bat, 'w', encoding='utf-8') as f:
            f.write(bat_content)
        print(f"[OK] Batch launcher created: {target_bat.name}")
    except Exception as e:
        print(f"[Error] Creating batch file: {e}")

    # 6. Create TOML Command
    toml_content = (
        f'description = "{texts["desc"]}"\n'
        f'prompt = "!{{python \\"{target_script.as_posix()}\\" {{{{args}}}}}}"\n'
    )
    try:
        with open(target_toml, 'w', encoding='utf-8') as f:
            f.write(toml_content)
        print(f"[OK] Slash command configured: /change")
    except Exception as e:
        print(f"[Error] Creating TOML file: {e}")

    # 7. Ask about Auto-Switch
    print()
    enable_auto = input(texts['ask_auto']).strip().lower()
    enable_auto = enable_auto in ['', 'y', 'yes', '是']
    
    # Create or update config with language setting
    config_data = {}
    if target_config.exists():
        try:
            with open(target_config, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except:
            pass
    
    # Set language based on user selection
    config_data["language"] = lang_key
    
    if enable_auto:
        # Copy hook script
        if hook_script.exists():
            shutil.copy2(hook_script, target_hook)
        else:
            print(f"[Warning] Hook script not found: {hook_script}")
        
        # Update auto_switch config
        if "auto_switch" not in config_data:
            config_data["auto_switch"] = {
                "enabled": True,
                "strategy": "gemini3-first",
                "model_pattern": "gemini-3.*",
                "threshold": 5,
                "max_retries": 3,
                "notify_on_switch": True
            }
        
        # Update settings.json
        if update_settings_json(gemini_dir, target_hook):
            print(texts['hook_ok'])
    else:
        print(texts['hook_skip'])
    
    # Save config (always, to preserve language setting)
    with open(target_config, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Language set to: {lang_key.upper()}")

    # 8. Update PATH
    add_to_path(gemini_dir)

    # 9. Success Message
    print("\n" + "=" * 50)
    print(f"✅ {texts['success']}")
    print("-" * 50)
    print(texts['msg_cli'])
    print(texts['msg_slash'])
    if enable_auto:
        print(texts['msg_auto'])
    print("=" * 50)
    
    print("\n📋 Quick Reference:")
    print("  gchange              - List all accounts")
    print("  gchange <n>          - Switch to account #n")
    print("  gchange next         - Switch to next account")
    print("  gchange strategy     - View/change rotation strategy")
    print("  gchange config       - View/change auto-switch config")


if __name__ == "__main__":
    install()