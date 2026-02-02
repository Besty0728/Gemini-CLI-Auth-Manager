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

# Quota error patterns
QUOTA_ERROR_PATTERNS = [
    r"429",
    r"Resource exhausted",
    r"Quota exceeded",
    r"rate limit",
    r"Usage limit reached",
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
        # No error, reset retry count and continue
        reset_retry_count()
        print("{}")
        sys.exit(0)
    
    # Quota error detected
    max_retries = auto_switch.get("max_retries", 3)
    current_retry = get_retry_count()
    
    if current_retry >= max_retries:
        log(f"⚠️ [Auth Manager] Max retries ({max_retries}) reached. All accounts may be exhausted.")
        reset_retry_count()
        print("{}")
        sys.exit(0)
    
    # Check if we should switch based on strategy
    # Note: We don't have direct access to /stats output in hook context,
    # so we rely on error detection. Future improvement could invoke /stats.
    if should_switch_by_strategy(config):
        new_account = switch_to_next()
        
        if new_account:
            set_retry_count(current_retry + 1)
            
            if auto_switch.get("notify_on_switch", True):
                log(f"⚠️ [Auth Manager] Quota exhausted. Switched to {new_account}. Retrying... ({current_retry + 1}/{max_retries})")
            
            # Exit 2 triggers automatic retry in Gemini CLI
            sys.exit(2)
        else:
            log("⚠️ [Auth Manager] Failed to switch account.")
            print("{}")
            sys.exit(0)
    else:
        print("{}")
        sys.exit(0)


if __name__ == "__main__":
    main()
