#!/usr/bin/env python3
"""
BeforeAgent Hook: 配额预检测
在每次请求前检查配额状态，如果低于阈值则自动切换账号

优化特性：
1. 缓存机制：避免每次请求都调用 API（默认 5 分钟缓存）
2. 会话级检测：检测到新会话时强制刷新缓存
3. 策略支持：支持 "conservative" (耗尽所有) 和 "gemini3-first" (耗尽指定系列)
4. 清晰的切换提示：通过 systemMessage 通知用户

API 说明:
- loadCodeAssist: 获取 cloudaicompanionProject ID
- retrieveUserQuota: 获取各模型配额剩余百分比
"""
import json
import os
import sys
import subprocess
import re
from pathlib import Path
from datetime import datetime, timedelta

# API Endpoints (from Gemini CLI source code)
CODE_ASSIST_ENDPOINT = "https://cloudcode-pa.googleapis.com"
CODE_ASSIST_API_VERSION = "v1internal"

GEMINI_DIR = Path(os.path.expanduser("~/.gemini"))
OAUTH_CREDS_FILE = GEMINI_DIR / "oauth_creds.json"
AUTH_CONFIG_FILE = GEMINI_DIR / "auth_config.json"
QUOTA_CACHE_FILE = GEMINI_DIR / "quota_cache.json"

# Default configuration
DEFAULT_THRESHOLD = 0.10  # 10% remaining triggers switch
DEFAULT_MODELS_TO_CHECK = ["gemini-3-pro-preview", "gemini-2.5-pro"]
DEFAULT_CACHE_MINUTES = 5  # Cache quota check for 5 minutes
DEFAULT_STRATEGY = "gemini3-first"
DEFAULT_PATTERN = "gemini-3.*"


def log(message, level="INFO"):
    """Write log message to stderr (visible in Gemini CLI debug)."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [quota-pre-check] [{level}] {message}", file=sys.stderr)


def load_config():
    """Load configuration from auth_config.json."""
    config = {
        "threshold": DEFAULT_THRESHOLD,
        "models_to_check": DEFAULT_MODELS_TO_CHECK,
        "enabled": True,
        "cache_minutes": DEFAULT_CACHE_MINUTES,
        "strategy": DEFAULT_STRATEGY,
        "model_pattern": DEFAULT_PATTERN,
    }
    
    if AUTH_CONFIG_FILE.exists():
        try:
            with open(AUTH_CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                auto_switch = data.get("auto_switch", {})
                config["threshold"] = auto_switch.get("threshold", DEFAULT_THRESHOLD * 100) / 100
                config["enabled"] = auto_switch.get("enabled", True)
                config["models_to_check"] = auto_switch.get("models_to_check", DEFAULT_MODELS_TO_CHECK)
                config["cache_minutes"] = auto_switch.get("cache_minutes", DEFAULT_CACHE_MINUTES)
                config["strategy"] = auto_switch.get("strategy", DEFAULT_STRATEGY)
                config["model_pattern"] = auto_switch.get("model_pattern", DEFAULT_PATTERN) # pattern for gemini3-first
        except:
            pass
    
    return config


def load_cache():
    """Load cached quota information."""
    if not QUOTA_CACHE_FILE.exists():
        return None
    
    try:
        with open(QUOTA_CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        
        # Check if cache is expired
        cache_time = datetime.fromisoformat(cache.get("timestamp", "2000-01-01T00:00:00"))
        cache_minutes = cache.get("cache_minutes", DEFAULT_CACHE_MINUTES)
        
        if datetime.now() - cache_time > timedelta(minutes=cache_minutes):
            log(f"Cache expired (>{cache_minutes}min old)", "DEBUG")
            return None
        
        return cache
    except Exception as e:
        log(f"Failed to load cache: {e}", "DEBUG")
        return None


def save_cache(buckets, session_id, cache_minutes):
    """Save quota information to cache."""
    try:
        cache = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "buckets": buckets,
            "cache_minutes": cache_minutes,
        }
        with open(QUOTA_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        log(f"Failed to save cache: {e}", "DEBUG")


def load_oauth_token():
    """Load OAuth access token from credentials file."""
    if not OAUTH_CREDS_FILE.exists():
        return None
    
    try:
        with open(OAUTH_CREDS_FILE, 'r', encoding='utf-8') as f:
            creds = json.load(f)
        return creds.get("access_token")
    except:
        return None


def call_api(endpoint, access_token, payload):
    """Make an API call using requests."""
    try:
        import requests
        
        url = f"{CODE_ASSIST_ENDPOINT}/{CODE_ASSIST_API_VERSION}:{endpoint}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log(f"API call failed: {e}", "ERROR")
        return None


def get_project_id(access_token):
    """Get cloudaicompanionProject ID via loadCodeAssist API."""
    payload = {
        "metadata": {
            "ideType": "GEMINI_CLI",
            "platform": "WINDOWS_AMD64",
            "pluginType": "GEMINI",
        }
    }
    
    result = call_api("loadCodeAssist", access_token, payload)
    if result:
        return result.get("cloudaicompanionProject")
    return None


def get_quota_info(access_token, project_id):
    """Get quota information via retrieveUserQuota API."""
    payload = {"project": project_id}
    return call_api("retrieveUserQuota", access_token, payload)


def check_quota(config, session_id):
    """
    Check quota status based on strategy.
    Returns (buckets, should_switch, reason)
    """
    cache_minutes = config["cache_minutes"]
    
    # Try loading from cache first
    cache = load_cache()
    if cache:
        # Check if session changed (new session = force refresh)
        if cache.get("session_id") == session_id:
            log(f"Using cached quota (expires in {cache_minutes}min)", "DEBUG")
            buckets = cache.get("buckets", [])
        else:
            log("New session detected, refreshing quota", "INFO")
            cache = None
    
    if not cache:
        # Need to fetch fresh data
        access_token = load_oauth_token()
        if not access_token:
            log("No OAuth token found", "WARN")
            return None, False, "No token"
        
        project_id = get_project_id(access_token)
        if not project_id:
            log("Could not get project ID", "WARN")
            return None, False, "No project ID"
        
        quota_result = get_quota_info(access_token, project_id)
        if not quota_result or "buckets" not in quota_result:
            log("Could not get quota info", "WARN")
            return None, False, "Api Failed"
        
        buckets = quota_result["buckets"]
        
        # Save to cache
        save_cache(buckets, session_id, cache_minutes)
    
    # --- Strategy Check ---
    threshold = config["threshold"]
    strategy = config["strategy"]
    
    target_buckets = []
    
    if strategy == "conservative":
        # Check ALL buckets with limits
        target_buckets = [b for b in buckets if b.get("remainingFraction") is not None]
        log("Strategy: conservative (checking ALL models)", "DEBUG")
    
    elif strategy == "gemini3-first":
        # Check buckets matching pattern
        pattern = config["model_pattern"]
        try:
            regex = re.compile(pattern)
            target_buckets = [
                b for b in buckets 
                if b.get("modelId") and regex.match(b["modelId"]) and b.get("remainingFraction") is not None
            ]
            log(f"Strategy: gemini3-first (pattern: {pattern})", "DEBUG")
        except:
            log(f"Invalid regex: {pattern}", "WARN")
            target_buckets = []
    
    # Fallback to models_to_check if no targets found (e.g. pattern mismatch)
    if not target_buckets and config["models_to_check"]:
        log("Strategy matched no models, fallback to models_to_check list", "DEBUG")
        target_buckets = [
            b for b in buckets
            if b.get("modelId") in config["models_to_check"] and b.get("remainingFraction") is not None
        ]
    
    if not target_buckets:
        log("No target models found to check", "WARN")
        return buckets, False, "No targets"
    
    # Check if ALL target buckets are below threshold
    all_low = True
    low_details = []
    
    for bucket in target_buckets:
        remaining = bucket.get("remainingFraction", 1.0)
        model_id = bucket.get("modelId", "unknown")
        
        if remaining > threshold:
            all_low = False
        else:
            low_details.append(f"{model_id}: {remaining * 100:.1f}%")
            
    if all_low:
        return buckets, True, ", ".join(low_details)
    else:
        return buckets, False, "Quota OK"


def switch_account():
    """Call gchange next to switch account."""
    try:
        result = subprocess.run(
            ["gchange", "next"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            log("Account switched successfully", "INFO")
            # Clear cache after switch to force fresh check
            if QUOTA_CACHE_FILE.exists():
                QUOTA_CACHE_FILE.unlink()
            return True
        else:
            log(f"Account switch failed: {result.stderr}", "ERROR")
            return False
    except Exception as e:
        log(f"Failed to call gchange: {e}", "ERROR")
        return False


def main():
    """Main entry point for BeforeAgent hook."""
    try:
        # Read context from stdin
        raw_input = sys.stdin.read()
        context = json.loads(raw_input) if raw_input.strip() else {}
    except:
        context = {}
    
    session_id = context.get("session_id", "unknown")
    
    # Load configuration
    config = load_config()
    
    if not config["enabled"]:
        log("Quota pre-check disabled", "INFO")
        print("{}")
        sys.exit(0)
    
    # Check quota
    buckets, should_switch, reason = check_quota(config, session_id)
    
    # Prepare output
    output = {}
    
    if not buckets:
        log(f"Quota check skipped: {reason}", "WARN")
        print(json.dumps(output, ensure_ascii=False))
        sys.exit(0)
    
    if not should_switch:
        threshold_pct = config["threshold"] * 100
        log(f"Quota OK (threshold: {threshold_pct:.0f}%). Strategy: {config['strategy']}", "INFO")
        print(json.dumps(output, ensure_ascii=False))
        sys.exit(0)
    
    # Low quota detected - switch account
    log(f"Low quota detected ({reason}). Switching...", "WARN")
    
    if switch_account():
        # Switch successful - notify user
        output["systemMessage"] = (
            f"⚡ **账号已自动切换** | Account Auto-Switched\n"
            f"   检测到配额耗尽: {reason}\n"
            f"   Detected exhausted quota, switched to next account.\n"
            f"   ⚠️ **请重启 CLI 生效** | Please restart CLI to apply changes."
        )
    else:
        # Switch failed - warn user
        output["systemMessage"] = (
            f"⚠️ **配额不足警告** | Low Quota Warning\n"
            f"   原因: {reason}\n"
            f"   自动切换失败，请手动运行: gchange next"
        )
    
    print(json.dumps(output, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
