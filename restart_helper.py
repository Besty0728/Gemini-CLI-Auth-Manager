#!/usr/bin/env python3
"""
Gemini CLI Restart Helper
Terminates the parent Gemini CLI process and spawns a new instance in a new window.
"""
import os
import sys
import time
import subprocess
import argparse

def restart_gemini(pid, delay):
    """
    1. Wait for `delay` seconds.
    2. Kill process `pid`.
    3. Start new 'gemini' process in new window.
    """
    print(f"[Restart Helper] Waiting {delay}s before restart...", file=sys.stderr)
    time.sleep(delay)
    
    # 1. Kill the old process
    print(f"[Restart Helper] Terminating PID: {pid}...", file=sys.stderr)
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.kill(pid, 15) # SIGTERM
    except Exception as e:
        print(f"[Restart Helper] Failed to kill process {pid}: {e}", file=sys.stderr)
        # Continue anyway, eager to start new one
        
    # 2. Start new instance
    print(f"[Restart Helper] Starting new Gemini CLI...", file=sys.stderr)
    try:
        if sys.platform == "win32":
            # Start in new window
            # "start" is a shell command in cmd
            # We use Popen with shell=True to execute "start ..."
            # "gemini" command starts the CLI
            # FORCE FILE STORAGE to avoid keychain issues
            subprocess.Popen("set GEMINI_FORCE_FILE_STORAGE=true && start gemini", shell=True)
        else:
            # Linux/Mac (placeholder, mostly for Windows user)
            subprocess.Popen(["gemini"], start_new_session=True)
            
    except Exception as e:
        print(f"[Restart Helper] Failed to start new instance: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="Restart Gemini CLI helper")
    parser.add_argument("--pid", type=int, required=True, help="PID of the process to kill")
    parser.add_argument("--delay", type=float, default=3.0, help="Delay in seconds before killing")
    args = parser.parse_args()
    
    restart_gemini(args.pid, args.delay)

if __name__ == "__main__":
    # Detach from parent if possible (on Windows/Unix differently)
    # But this script is usually called as detached subprocess already.
    main()
