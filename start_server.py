#!/usr/bin/env python3
"""
Unified startup script for VisionVault with Engines integration
Starts both the engines API (background) and VisionVault UI (foreground)
"""
import subprocess
import time
import sys
import os
import signal

engines_process = None

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n🛑 Shutting down servers...")
    if engines_process:
        engines_process.terminate()
        engines_process.wait()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    print("="*80)
    print("🚀 Starting VisionVault with Engines Integration")
    print("="*80)
    
    # Start engines API in background (inherit stdout/stderr to avoid pipe blocking)
    print("\n📡 Starting Engines API on internal port...")
    engines_process = subprocess.Popen(
        [sys.executable, "engines/main.py"]
    )
    
    # Give engines a moment to start
    time.sleep(2)
    
    # Check if engines started successfully
    if engines_process.poll() is not None:
        print("❌ Engines API failed to start")
        sys.exit(1)
    
    print("✅ Engines API started successfully")
    
    # Start VisionVault UI in foreground
    print("\n🌐 Starting VisionVault UI on port 5000...")
    print("="*80)
    print("\n")
    
    try:
        # Run VisionVault - this blocks until it exits
        subprocess.run(
            [sys.executable, "full_vision_vault/run_server.py"],
            check=True
        )
    except KeyboardInterrupt:
        pass
    finally:
        # Clean up engines process
        if engines_process:
            engines_process.terminate()
            engines_process.wait()
