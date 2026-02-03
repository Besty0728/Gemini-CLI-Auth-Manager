#!/usr/bin/env python3
"""
Gemini CLI Quota Auto-Switch Hook
AfterAgent hook script for automatic account switching when quota is exhausted.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# --- Configuration ---
GEMINI_DIR = Path(os.path.expanduser("~/.gemini"))
CONFIG_FILE = GEMINI_DIR / "auth_config.json"
RETRY_FILE = GEMINI_DIR / ".auto_switch_retry_count"
ERROR_STATE_FILE = GEMINI_DIR / ".last_quota_error"  # For BeforeAgent pre-check

DEFAULT_CONFIG = {
    "auto_switch": {
        "enabled": True,
        "strategy": "gemini3-first",
        "model_pattern": "gemini-3.*",
        "threshold": 5,
        "max_retries": 3,
        "notify_on_switch": True
    }
}

# Quota error patterns (case-insensitive matching)
QUOTA_ERROR_PATTERNS = [
    # HTTP status codes
    r"429",
    r"403.*quota",
    
    # API error messages
    r"Resource exhausted",
    r"Quota exceeded",
    r"rate limit",
    r"RESOURCE_EXHAUSTED",
    
    # Gemini CLI UI messages
    r"Usage limit reached",
    r"limit reached for all.*models",
    r"Access resets at",
    r"Keep trying.*Stop",  # 检测 "1. Keep trying  2. Stop" 选项
    
    # Validation errors (403)
    r"PERMISSION_DENIED.*VALIDATION_REQUIRED",
    r"Please verify your account",
]


def log(message):
    """Log message to stderr (visible to user but not parsed by CLI)."""
    print(message, file=sys.stderr)


def load_config():
    """Load configuration from file."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_CONFIG.copy()


def get_retry_count():
    """Get current retry count for this session."""
    if RETRY_FILE.exists():
        try:
            with open(RETRY_FILE, 'r') as f:
                return int(f.read().strip())
        except:
            pass
    return 0


def set_retry_count(count):
    """Set retry count."""
    try:
        with open(RETRY_FILE, 'w') as f:
            f.write(str(count))
    except:
        pass


def reset_retry_count():
    """Reset retry count after successful response."""
    if RETRY_FILE.exists():
        try:
            RETRY_FILE.unlink()
        except:
            pass


def set_error_state(retry_count):
    """Set error state for BeforeAgent pre-check (persists even if CLI crashes)."""
    try:
        with open(ERROR_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump({"quota_error": True, "retry_count": retry_count}, f)
    except:
        pass


def clear_error_state():
    """Clear the error state file after successful request."""
    if ERROR_STATE_FILE.exists():
        try:
            ERROR_STATE_FILE.unlink()
        except:
            pass


def is_quota_error(response):
    """Check if response contains quota-related error."""
    response_lower = response.lower()
    for pattern in QUOTA_ERROR_PATTERNS:
        if re.search(pattern, response_lower, re.IGNORECASE):
            return True
    return False


def parse_model_usage(stats_output):
    """
    Parse /stats output to extract model usage information.
    Returns dict: {model_name: usage_percent}
    """
    usage = {}
    # Match pattern like: gemini-3-pro-preview    1     99.5% (Resets in 23h 59m)
    pattern = r'(gemini-[\w\.-]+)\s+[\d-]+\s+([\d.]+)%'
    
    for match in re.finditer(pattern, stats_output, re.IGNORECASE):
        model_name = match.group(1)
        usage_left = float(match.group(2))
        usage[model_name] = usage_left
    
    return usage


def should_switch_by_strategy(config, model_usage=None):
    """
    Determine if we should switch based on strategy.
    Returns True if switch is needed.
    """
    auto_switch = config.get("auto_switch", {})
    strategy = auto_switch.get("strategy", "gemini3-first")
    threshold = auto_switch.get("threshold", 5)
    model_pattern = auto_switch.get("model_pattern", "gemini-3.*")
    
    # If no model usage data, rely on error detection alone
    if not model_usage:
        return True
    
    if strategy == "conservative":
        # Switch only when ALL models are below threshold
        all_exhausted = all(usage <= threshold for usage in model_usage.values())
        return all_exhausted
    
    elif strategy == "gemini3-first":
        # Switch when any Gemini 3.x model is below threshold
        pattern = re.compile(model_pattern, re.IGNORECASE)
        for model, usage in model_usage.items():
            if pattern.match(model) and usage <= threshold:
                return True
        return False
    
    # Default: switch on any error
    return True


def switch_to_next():
    """Call gchange next to switch account."""
    try:
        result = subprocess.run(
            ["python", str(GEMINI_DIR / "gemini_cli_auth_manager.py"), "next"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # Extract new account from output
        output = result.stdout + result.stderr
        match = re.search(r'Switched to (\S+)', output)
        if match:
            return match.group(1)
        return "next account"
    except Exception as e:
        log(f"[Auth Manager] Switch failed: {e}")
        return None


def main():
    """Main hook entry point."""
    try:
        # Read context from stdin
        try:
            context = json.load(sys.stdin)
        except:
            # No valid input, pass through
            print("{}")
            sys.exit(0)
        
        response = context.get("prompt_response", "")
        
        # Load config
        config = load_config()
        auto_switch = config.get("auto_switch", {})
        
        # Check if auto-switch is enabled
        if not auto_switch.get("enabled", True):
            print("{}")
            sys.exit(0)
        
        # Check for quota error
        if not is_quota_error(response):
            # No error, reset retry count and clear error state
            reset_retry_count()
            clear_error_state()  # Clear state for BeforeAgent
            print("{}")
            sys.exit(0)
        
        # Quota error detected - IMMEDIATELY write error state
        # This ensures BeforeAgent can pre-switch even if CLI crashes after this
        current_retry = get_retry_count()
        set_error_state(current_retry)  # Write state BEFORE any other processing
        
        max_retries = auto_switch.get("max_retries", 3)
        
        if current_retry >= max_retries:
            log(f"⚠️ [Auth Manager] Max retries ({max_retries}) reached. All accounts may be exhausted.")
            reset_retry_count()
            clear_error_state()  # Clear state since we've given up
            print("{}")
            sys.exit(0)
        
        # Check if we should switch based on strategy
        if should_switch_by_strategy(config):
            new_account = switch_to_next()
            
            if new_account:
                set_retry_count(current_retry + 1)
                
                # Build message based on language
                lang = config.get("language", "en")
                if lang == "cn":
                    msg = f"🔄 配额已耗尽，已自动切换到账号：{new_account}。正在重试请求... ({current_retry + 1}/{max_retries})"
                else:
                    msg = f"🔄 Quota exhausted. Switched to: {new_account}. Retrying... ({current_retry + 1}/{max_retries})"
                
                # Log to stderr (visible in debug console)
                log(f"⚠️ [Auth Manager] {msg}")
                
                # Delete token cache to force reload
                cache_file = GEMINI_DIR / "mcp-oauth-tokens-v2.json"
                if cache_file.exists():
                    try:
                        cache_file.unlink()
                        log("[Cache] Cleared token cache.")
                    except OSError as e:
                        log(f"[Cache] Warning: Failed to clear cache: {e}")

                # Output JSON with retry decision
                # For AfterAgent, use "decision": "retry" to trigger retry
                result = {
                    "decision": "retry",
                    "systemMessage": msg
                }
                print(json.dumps(result))
                
                # --- AUTO-RESTART LOGIC ---
                if auto_switch.get("auto_restart", False):
                    try:
                        # Determine current PID (likely python script itself)
                        target_pid = os.getppid()
                        
                        # Launch restart helper detached
                        restart_script = GEMINI_DIR / "restart_helper.py"
                        if not restart_script.exists():
                            # Maybe still in source dir?
                            script_dir = Path(__file__).parent
                            restart_script = script_dir / "restart_helper.py"
                            
                        if restart_script.exists():
                            log(f"[Auto-Restart] Triggering restart for PID {target_pid}...")
                            
                            cmd = [sys.executable, str(restart_script), "--pid", str(target_pid), "--delay", "3"]
                            
                            if sys.platform == "win32":
                                # Use os.system with 'start' command - most reliable way on Windows
                                # 'start /b' runs in background without new window for the helper
                                # The helper itself will use 'start gemini' to open new window
                                os.system(f'start /b "" "{sys.executable}" "{restart_script}" --pid {target_pid} --delay 3')
                            else:
                                subprocess.Popen(
                                    [sys.executable, str(restart_script), "--pid", str(target_pid), "--delay", "3"],
                                    start_new_session=True,
                                    close_fds=True
                                )
                        else:
                            log(f"[Auto-Restart] Helper script not found: {restart_script}")
                            
                    except Exception as restart_err:
                        log(f"[Auto-Restart] Failed to trigger: {restart_err}")
                # --------------------------

                sys.exit(0)  # Use exit(0) for successful hook execution
            else:
                log("⚠️ [Auth Manager] Failed to switch account.")
                print("{}")
                sys.exit(0)
        else:
            print("{}")
            sys.exit(0)
    
    except Exception as e:
        # Catch any unexpected errors to prevent hook failure
        log(f"⚠️ [Auth Manager] Error: {e}")
        print("{}")
        sys.exit(0)


if __name__ == "__main__":
    main()

