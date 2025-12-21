import json
import os
import shutil
import sys
from pathlib import Path

# --- Configuration Paths ---
GEMINI_DIR = Path(os.path.expanduser("~/.gemini"))
PROFILES_DIR = GEMINI_DIR / "auth_profiles"
ACCOUNTS_JSON = GEMINI_DIR / "google_accounts.json"
CREDS_FILE = GEMINI_DIR / "oauth_creds.json"
ID_FILE = GEMINI_DIR / "google_account_id"

# --- UI Helpers (Pure ASCII for Compatibility) ---
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
        # Simple, robust ASCII header
        print(f"{UI.CYAN}{UI.line('=')}{UI.RESET}")
        print(f"{UI.BOLD}  GEMINI-CLI-AUTH-MANAGER v1.3{UI.RESET}")
        print(f"{UI.DIM}  Fast Switcher | By Besty{UI.RESET}")
        print(f"{UI.CYAN}{UI.line('=')}{UI.RESET}")

def fast_switch(target_arg):
    # (Keep existing fast_switch logic, but use simpler color prints)
    target_dir = PROFILES_DIR / target_arg
    target_email = target_arg

    if not target_dir.exists():
        if target_arg.isdigit():
            try:
                profiles = sorted([d.name for d in PROFILES_DIR.iterdir() if d.is_dir()])
                idx = int(target_arg) - 1
                if 0 <= idx < len(profiles):
                    target_email = profiles[idx]
                    target_dir = PROFILES_DIR / target_email
                else:
                    print(f"{UI.RED}[Error] Index {target_arg} out of range.{UI.RESET}")
                    return
            except OSError:
                print(f"{UI.RED}[Error] Could not read profiles directory.{UI.RESET}")
                return
        else:
            print(f"{UI.RED}[Error] Account not found: {target_arg}{UI.RESET}")
            return

    target_creds = target_dir / "oauth_creds.json"
    if not target_creds.exists():
        print(f"{UI.RED}[Error] Missing credentials for: {target_email}{UI.RESET}")
        return

    current_active = None
    data = {"active": None, "old": []}
    if ACCOUNTS_JSON.exists():
        try:
            with open(ACCOUNTS_JSON, 'r', encoding='utf-8') as f:
                data = json.load(f)
                current_active = data.get('active')
        except: pass

    if current_active == target_email:
        print(f"{UI.GREEN}[OK] Already using {target_email}{UI.RESET}")
        return

    # Backup current
    if current_active:
        curr_dir = PROFILES_DIR / current_active
        if not curr_dir.exists(): curr_dir.mkdir(parents=True, exist_ok=True)
        if CREDS_FILE.exists(): shutil.copy2(CREDS_FILE, curr_dir / "oauth_creds.json")
        if ID_FILE.exists(): shutil.copy2(ID_FILE, curr_dir / "google_account_id")

    # Perform switch
    try:
        shutil.copy2(target_creds, CREDS_FILE)
        t_id = target_dir / "google_account_id"
        if t_id.exists(): shutil.copy2(t_id, ID_FILE)
        elif ID_FILE.exists(): ID_FILE.unlink(missing_ok=True)
    except OSError as e:
        print(f"{UI.RED}[Error] Switch failed: {e}{UI.RESET}")
        return

    # Update state
    if current_active and current_active != target_email:
        if 'old' not in data: data['old'] = []
        if current_active not in data['old']: data['old'].append(current_active)
    data['active'] = target_email
    if 'old' in data and target_email in data['old']: data['old'].remove(target_email)

    try:
        with open(ACCOUNTS_JSON, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except: pass

    print(f"{UI.GREEN}[OK] Switched to {target_email}{UI.RESET}")

def list_status():
    UI.header()
    
    active = None
    if ACCOUNTS_JSON.exists():
        try:
            with open(ACCOUNTS_JSON, 'r', encoding='utf-8') as f:
                active = json.load(f).get('active')
        except: pass

    # Active Section
    print(f"\n  {UI.BOLD}STATUS:{UI.RESET}")
    if active:
        print(f"  [ ACTIVE ] {UI.GREEN}{active}{UI.RESET}")
    else:
        print(f"  [ ACTIVE ] {UI.YELLOW}None{UI.RESET}")
    
    print(f"\n  {UI.BOLD}ACCOUNTS:{UI.RESET}")
    print(f"  {UI.line('-', 40)}")

    if PROFILES_DIR.exists():
        profiles = sorted([d.name for d in PROFILES_DIR.iterdir() if d.is_dir()])
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
    else:
        print("  (Auth profiles directory missing)")

    print(f"  {UI.line('-', 40)}")
    
    # Usage
    print(f"\n  {UI.BOLD}USAGE:{UI.RESET}")
    print(f"  gchange <number|email>")
    print(f"\n{UI.CYAN}{UI.line('=')}{UI.RESET}\n")

def main():
    # Attempt to enable ANSI on Windows
    if os.name == 'nt':
        os.system('') 
        
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg not in ['menu', 'interactive', '-i', 'list']:
            fast_switch(arg)
            return
            
    list_status()

if __name__ == "__main__":
    main()


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        # Fast path for switching
        if arg not in ['menu', 'interactive', '-i', 'list']:
            fast_switch(arg)
            return
            
    # Fallback to status list
    list_status()

if __name__ == "__main__":
    main()
