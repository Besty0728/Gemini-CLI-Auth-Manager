#!/usr/bin/env python3
"""
Gemini CLI 配额查询 API 客户端
直接调用 Google Code Assist API 获取配额信息
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime
import requests

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# API Endpoints (from Gemini CLI source code)
CODE_ASSIST_ENDPOINT = "https://cloudcode-pa.googleapis.com"
CODE_ASSIST_API_VERSION = "v1internal"

GEMINI_DIR = Path(os.path.expanduser("~/.gemini"))
OAUTH_CREDS_FILE = GEMINI_DIR / "oauth_creds.json"


def load_oauth_token():
    """Load OAuth access token from credentials file."""
    if not OAUTH_CREDS_FILE.exists():
        raise FileNotFoundError(f"OAuth credentials not found: {OAUTH_CREDS_FILE}")
    
    with open(OAUTH_CREDS_FILE, 'r', encoding='utf-8') as f:
        creds = json.load(f)
    
    access_token = creds.get("access_token")
    expiry_date = creds.get("expiry_date", 0)
    
    # Check if token is expired
    if expiry_date and datetime.now().timestamp() * 1000 > expiry_date:
        print("⚠️  Warning: OAuth token may be expired")
    
    return access_token


def call_load_code_assist(access_token):
    """
    Call loadCodeAssist API to get cloudaicompanionProject.
    This is how Gemini CLI gets the project ID on auth.
    """
    url = f"{CODE_ASSIST_ENDPOINT}/{CODE_ASSIST_API_VERSION}:loadCodeAssist"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "metadata": {
            "ideType": "GEMINI_CLI",
            "platform": "WINDOWS_AMD64",
            "pluginType": "GEMINI",
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        # Debugging: Print status code
        # print(f"DEBUG: HTTPError caught, status: {e.response.status_code}", file=sys.stderr)
        
        if e.response.status_code == 401:
            print(f"⚠️  Token expired (401). Attempting to refresh via Gemini CLI...")
            try:
                # Run a cheap command to force CLI to refresh token
                # On Windows, shell=True is needed to resolve npm scripts (.cmd)
                import subprocess
                is_windows = sys.platform == 'win32'
                
                subprocess.run(
                    ["gemini", "models", "list", "--limit", "1"], 
                    check=True, 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL,
                    shell=is_windows
                )
                
                # Reload token
                new_token = load_oauth_token()
                if new_token != access_token:
                    print("✅ Token refreshed. Retrying...")
                    headers["Authorization"] = f"Bearer {new_token}"
                    response = requests.post(url, headers=headers, json=payload, timeout=30)
                    response.raise_for_status()
                    return response.json()
                else:
                    print("❌ Token refresh failed (file not updated).")
            except Exception as refresh_err:
                print(f"❌ Failed to auto-refresh token: {refresh_err}")

        print(f"❌ Error calling loadCodeAssist: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling loadCodeAssist: {e}")
        return None


def call_retrieve_user_quota(access_token, project_id):
    """
    Call retrieveUserQuota API to get quota information.
    This is the API that powers /stats.
    """
    url = f"{CODE_ASSIST_ENDPOINT}/{CODE_ASSIST_API_VERSION}:retrieveUserQuota"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "project": project_id
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling retrieveUserQuota: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None


def format_reset_time(reset_time_str):
    """Format reset time as relative duration."""
    if not reset_time_str:
        return ""
    
    try:
        reset_time = datetime.fromisoformat(reset_time_str.replace("Z", "+00:00"))
        now = datetime.now(reset_time.tzinfo)
        diff = reset_time - now
        
        if diff.total_seconds() <= 0:
            return "(已重置)"
        
        hours = int(diff.total_seconds() // 3600)
        minutes = int((diff.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"(重置于 {hours}h {minutes}m 后)"
        return f"(重置于 {minutes}m 后)"
    except:
        return ""


def display_quota_info(quota_response):
    """Display quota information in a formatted table."""
    buckets = quota_response.get("buckets", [])
    
    if not buckets:
        print("❌ No quota information available")
        return
    
    print("\n" + "=" * 70)
    print("📊 Gemini CLI 配额状态")
    print("=" * 70)
    print(f"{'模型':<30} {'剩余配额':<15} {'重置时间'}")
    print("-" * 70)
    
    for bucket in buckets:
        model_id = bucket.get("modelId", "unknown")
        remaining_fraction = bucket.get("remainingFraction")
        reset_time = bucket.get("resetTime", "")
        
        if remaining_fraction is not None:
            percentage = remaining_fraction * 100
            # Color indicator
            if percentage < 10:
                status = "🔴"
            elif percentage < 30:
                status = "🟡"
            else:
                status = "🟢"
            
            remaining_str = f"{status} {percentage:.1f}%"
        else:
            remaining_str = "N/A"
        
        reset_str = format_reset_time(reset_time)
        
        print(f"{model_id:<30} {remaining_str:<15} {reset_str}")
    
    print("=" * 70)
    
    # Check if any model is low
    low_quota_models = [
        b for b in buckets 
        if b.get("remainingFraction") is not None and b["remainingFraction"] < 0.3
    ]
    
    if low_quota_models:
        print("\n⚠️  以下模型配额较低，建议切换账号：")
        for b in low_quota_models:
            print(f"   - {b.get('modelId')}: {b.get('remainingFraction', 0) * 100:.1f}%")
    
    return buckets


def main():
    print("🔍 Gemini CLI 配额查询工具\n")
    
    # Step 1: Load OAuth token
    print("1. 加载 OAuth 凭证...")
    try:
        access_token = load_oauth_token()
        print("   ✅ 凭证已加载")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return None
    
    # Step 2: Get project ID via loadCodeAssist
    print("\n2. 获取 cloudaicompanionProject ID...")
    load_result = call_load_code_assist(access_token)
    
    if not load_result:
        print("   ❌ 无法获取项目信息")
        return None
    
    project_id = load_result.get("cloudaicompanionProject")
    current_tier = load_result.get("currentTier", {})
    tier_name = current_tier.get("name", "unknown")
    tier_id = current_tier.get("id", "unknown")
    
    if not project_id:
        print("   ❌ 未找到 cloudaicompanionProject")
        print(f"   可能原因: 账户未正确 onboard 或使用的是 API Key 认证")
        print(f"   Load result: {json.dumps(load_result, indent=2)}")
        return None
    
    print(f"   ✅ Project ID: {project_id}")
    print(f"   ✅ Tier: {tier_name} ({tier_id})")
    
    # Step 3: Get quota information
    print("\n3. 查询配额状态...")
    quota_result = call_retrieve_user_quota(access_token, project_id)
    
    if not quota_result:
        print("   ❌ 无法获取配额信息")
        return None
    
    # Display results
    buckets = display_quota_info(quota_result)
    
    return buckets


if __name__ == "__main__":
    result = main()
    
    if result:
        # Save to JSON for debugging
        output_file = Path(__file__).parent / "quota_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n📁 详细结果已保存到: {output_file}")
