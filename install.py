import os
import shutil
import sys
from pathlib import Path

# --- Configuration Dictionary ---
CONFIG = {
    'en': {
        'desc': 'Switch Gemini accounts. Usage: /change <index_or_email>',
        'success': 'Installation Complete!',
        'msg_cli': '1. CLI Command:  Type "change" in your terminal.',
        'msg_slash': '2. Slash Command: Type "/change" in Gemini CLI.'
    },
    'cn': {
        'desc': '切换 Gemini 账户。用法: /change <序号或邮箱>',
        'success': '安装完成！',
        'msg_cli': '1. 终端命令: 在终端直接输入 "change"',
        'msg_slash': '2. 斜杠命令: 在 Gemini CLI 中输入 "/change"'
    }
}

def get_user_language():
    """Prompt user to select language"""
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

def install():
    print("========================================")
    print("   Gemini Auth Manager Installer")
    print("========================================")

    # 1. Get Language
    lang_key = get_user_language()
    texts = CONFIG[lang_key]

    # 2. Determine Paths
    source_dir = Path(__file__).parent.resolve()
    core_script_name = "gemini_auth_manager.py"
    
    # Target: User Home Directory
    user_home = Path.home() # e.g. C:\Users\Tom
    gemini_dir = user_home / ".gemini"
    commands_dir = gemini_dir / "commands"
    
    # Target File Paths
    target_script_path = gemini_dir / core_script_name
    target_bat_path = gemini_dir / "change.bat"
    target_toml_path = commands_dir / "change.toml"

    print(f"\nTarget Directory: {gemini_dir}")

    # 3. Create Directories
    if not gemini_dir.exists():
        gemini_dir.mkdir(parents=True)
    if not commands_dir.exists():
        commands_dir.mkdir(parents=True)

    # 4. Copy Core Script
    source_script = source_dir / core_script_name
    if source_script.exists():
        shutil.copy2(source_script, target_script_path)
        print(f"[OK] Core script copied to: {target_script_path}")
    else:
        print(f"[Error] Source file '{core_script_name}' not found in current directory!")
        print("Please ensure you downloaded the full project.")
        return

    # 5. Generate Batch Launcher (change.bat)
    # Using %USERPROFILE% for portability
    bat_content = r'@echo off\npython "%USERPROFILE%\.gemini\gemini_auth_manager.py" %*'
    try:
        with open(target_bat_path, 'w', encoding='utf-8') as f:
            f.write(bat_content)
        print(f"[OK] Batch launcher created: {target_bat_path.name}")
    except Exception as e:
        print(f"[Error] Creating batch file: {e}")

    # 6. Generate TOML Config (change.toml)
    # Using calculated ABSOLUTE path for robustness against shell environment issues
    clean_script_path = target_script_path.as_posix()
    
    toml_content = (
        f'description = "{texts["desc"]}"\n'
        f'prompt = "!{{python {clean_script_path} {{{{args}}}}}}"'
    )
    
    try:
        with open(target_toml_path, 'w', encoding='utf-8') as f:
            f.write(toml_content)
        print(f"[OK] Custom command configured: {target_toml_path.name}")
        print(f"     Language set to: {lang_key.upper()}")
    except Exception as e:
        print(f"[Error] Creating TOML file: {e}")

    # 7. Success Message
    print("\n" + "="*30)
    print(f"✅ {texts['success']}")
    print("-" * 30)
    print(texts['msg_cli'])
    print(texts['msg_slash'])
    print("="*30)

if __name__ == "__main__":
    install()