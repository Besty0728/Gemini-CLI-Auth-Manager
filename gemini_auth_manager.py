import json
import os
import shutil
import sys
from pathlib import Path

# Configuration Paths
GEMINI_DIR = Path(os.path.expanduser("~/.gemini"))
PROFILES_DIR = GEMINI_DIR / "auth_profiles"
ACCOUNTS_JSON = GEMINI_DIR / "google_accounts.json"
CREDS_FILE = GEMINI_DIR / "oauth_creds.json"
ID_FILE = GEMINI_DIR / "google_account_id"

def ensure_dirs():
    if not PROFILES_DIR.exists():
        PROFILES_DIR.mkdir(parents=True)

def get_accounts_config():
    """Reads the full configuration from google_accounts.json"""
    if not ACCOUNTS_JSON.exists():
        return {"active": None, "old": []}
    try:
        with open(ACCOUNTS_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except Exception as e:
        print(f"Error reading accounts config: {e}")
        return {"active": None, "old": []}

def save_current_profile():
    """Backs up the current credential files to the profile directory."""
    config = get_accounts_config()
    email = config.get('active')
    
    if not email:
        # print("No active account found in google_accounts.json. Skipping backup.")
        return

    user_profile_dir = PROFILES_DIR / email
    if not user_profile_dir.exists():
        user_profile_dir.mkdir(parents=True)

    # Save oauth_creds.json
    if CREDS_FILE.exists():
        shutil.copy2(CREDS_FILE, user_profile_dir / "oauth_creds.json")
    
    # Save google_account_id
    if ID_FILE.exists():
        shutil.copy2(ID_FILE, user_profile_dir / "google_account_id")

    return email

def load_profile(target_email):
    """Restores credential files from the profile directory."""
    user_profile_dir = PROFILES_DIR / target_email
    
    if not (user_profile_dir / "oauth_creds.json").exists():
        print(f"Error: No saved credentials found for {target_email}")
        print("Please log in manually to restore this account.")
        return False

    # Restore files
    shutil.copy2(user_profile_dir / "oauth_creds.json", CREDS_FILE)
    
    if (user_profile_dir / "google_account_id").exists():
        shutil.copy2(user_profile_dir / "google_account_id", ID_FILE)
    
    # Update google_accounts.json
    update_active_account_config(target_email)
    print(f"\nSUCCESS: Switched to {target_email}")
    return True

def update_active_account_config(new_email):
    """Updates the 'active' field in google_accounts.json"""
    if not ACCOUNTS_JSON.exists():
        return
    
    try:
        with open(ACCOUNTS_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Update active
        current_active = data.get('active')
        if current_active and current_active != new_email:
            # Move current active to 'old' list if not already there
            if 'old' not in data:
                data['old'] = []
            if current_active not in data['old']:
                data['old'].append(current_active)
        
        data['active'] = new_email
        
        # Ensure new active is not in 'old' list
        if 'old' in data and new_email in data['old']:
            data['old'].remove(new_email)

        with open(ACCOUNTS_JSON, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
    except Exception as e:
        print(f"Error updating config: {e}")

def get_profiles_status():
    """Returns a tuple: (active_email, local_profiles, history_only)"""
    ensure_dirs()
    # Sync current state first
    save_current_profile()
    
    config = get_accounts_config()
    active = config.get('active')
    old_list = config.get('old', [])

    # Local profiles (directories)
    local_profiles = [d.name for d in PROFILES_DIR.iterdir() if d.is_dir()]
    
    # Determine history accounts (in 'old' but no local directory)
    history_only = [email for email in old_list if email not in local_profiles]

    return active, local_profiles, history_only

def delete_profile(email):
    """Removes a profile from storage."""
    user_profile_dir = PROFILES_DIR / email
    if user_profile_dir.exists():
        shutil.rmtree(user_profile_dir)
        print(f"Deleted profile files: {email}")
    else:
        print(f"No local files found for {email}")

    # Clean up from google_accounts.json
    try:
        with open(ACCOUNTS_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        changed = False
        if 'old' in data and email in data['old']:
            data['old'].remove(email)
            changed = True
        
        if data.get('active') == email:
            print("Warning: You deleted the currently active account config.")
            # We don't remove 'active' key, just leave it or set to None?
            # Usually better to leave it until switched, or set to None.
            # For now, just removing from 'old' is sufficient for history.
            
        if changed:
            with open(ACCOUNTS_JSON, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print("Removed from history records.")
            
    except Exception as e:
        print(f"Error cleaning config: {e}")

def main():
    ensure_dirs()
    
    # Always try to back up current state on launch
    save_current_profile()
    
    active, local_profiles, history_only = get_profiles_status()

    # --- CLI Argument Handling (Switch Mode) ---
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        target_profile = None

        if arg.isdigit():
            idx = int(arg) - 1
            if 0 <= idx < len(local_profiles):
                target_profile = local_profiles[idx]
            else:
                print(f"Error: Index {arg} out of range. Available profiles: 1-{len(local_profiles)}")
                return
        else:
            # Try to match by name (email)
            if arg in local_profiles:
                target_profile = arg
            else:
                print(f"Error: Profile '{arg}' not found locally.")
                return

        if target_profile:
            if target_profile == active:
                print(f"Already on profile: {target_profile}")
            else:
                load_profile(target_profile)
        return
    # -----------------------------

    # --- Interactive Mode (Gemini Auth Mode) ---
    while True:
        # Refresh status in loop
        active, local_profiles, history_only = get_profiles_status()
        
        print("\n========================================")
        print("       Gemini Account Manager")
        print("========================================")
        print(f"Active Account : {active if active else 'None'}")
        print("----------------------------------------")
        
        if not local_profiles and not history_only:
            print("No profiles found. Please login using Gemini CLI.")
            return

        print("Saved Profiles (Ready to Switch):")
        if local_profiles:
            for idx, p in enumerate(local_profiles):
                marker = "->" if p == active else "  "
                print(f" {idx + 1}. {marker} {p}")
        else:
            print("  (None)")

        if history_only:
            print("\nHistory Records (Login Required):")
            for h in history_only:
                print(f"  - {h}")
        
        print("----------------------------------------")
        print("A. Add New Account (Help)")
        print("D. Delete Account")
        print("Q. Quit")
        
        choice = input("\nCommand > ").strip().lower()
        
        if choice == 'q':
            break
        elif choice == 'a':
            print("\n--- How to Add a New Account ---")
            print("1. Quit this tool (Press Q).")
            print("2. Run 'gemini login' or your standard auth command.")
            print("3. Follow the browser flow.")
            print("4. Run 'gemini_auth' again. The new account will be auto-saved.")
            input("\nPress Enter to continue...")
        elif choice == 'd':
            target_to_delete = input("Enter email or number to delete: ").strip()
            
            # Handle number input for local profiles
            if target_to_delete.isdigit():
                idx = int(target_to_delete) - 1
                if 0 <= idx < len(local_profiles):
                    target_to_delete = local_profiles[idx]
            
            if not target_to_delete:
                continue

            if target_to_delete == active:
                print("Cannot delete the currently active account. Switch first.")
            else:
                # Check if it exists in either list
                if target_to_delete in local_profiles or target_to_delete in history_only:
                    confirm = input(f"Are you sure you want to delete {target_to_delete}? (y/n): ")
                    if confirm.lower() == 'y':
                        delete_profile(target_to_delete)
                else:
                    print("Account not found.")
        
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(local_profiles):
                target = local_profiles[idx]
                if target == active:
                    print("Already on this account.")
                else:
                    load_profile(target)
            else:
                print("Invalid selection.")
        else:
            # Try to match email directly for switch
            if choice in local_profiles:
                if choice == active:
                    print("Already on this account.")
                else:
                    load_profile(choice)
            else:
                print("Invalid command.")

if __name__ == "__main__":
    main()
