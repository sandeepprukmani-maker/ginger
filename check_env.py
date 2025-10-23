"""
Environment Check Script
Run this script to verify your .env file is set up correctly
"""
import os
from dotenv import load_dotenv, dotenv_values

print("=" * 60)
print("Environment Configuration Check")
print("=" * 60)

# Check if .env file exists
if os.path.exists('.env'):
    print("✅ .env file found")
else:
    print("❌ .env file NOT found")
    print("   Please create a .env file in the project root directory")
    print("   You can copy .env.example and rename it to .env")
    exit(1)

# Check what's in the .env file (before loading into environment)
print("\n📄 Checking .env file contents...")
env_values = dotenv_values('.env')
if 'OPENAI_API_KEY' in env_values:
    env_key = env_values['OPENAI_API_KEY']
    masked_env = env_key[:10] + "..." + env_key[-4:] if len(env_key) > 14 else "***"
    print(f"   .env file contains OPENAI_API_KEY: {masked_env}")
else:
    print("   ⚠️  .env file does NOT contain OPENAI_API_KEY")

# Check if there's a system environment variable (before loading .env)
print("\n🔍 Checking system environment variables...")
system_key = os.environ.get('OPENAI_API_KEY')
if system_key:
    masked_sys = system_key[:10] + "..." + system_key[-4:] if len(system_key) > 14 else "***"
    print(f"   ⚠️  WARNING: System has OPENAI_API_KEY set: {masked_sys}")
    print("   This might conflict with your .env file!")
    print("\n   To remove the system environment variable:")
    print("   - Close all Command Prompt/PowerShell windows")
    print("   - Open a fresh terminal and run this script again")
    print("   - Or in current session, run: set OPENAI_API_KEY=")
else:
    print("   ✅ No system OPENAI_API_KEY found (good!)")

# Load .env file with override
print("\n🔄 Loading .env file...")
load_dotenv(override=True)

# Check for OPENAI_API_KEY after loading
print("\n✅ Final environment check:")
api_key = os.environ.get('OPENAI_API_KEY')
if api_key:
    # Mask the key for security
    masked_key = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "***"
    print(f"   OPENAI_API_KEY is set: {masked_key}")
    
    # Check if it matches the .env file
    if 'OPENAI_API_KEY' in env_values and api_key == env_values['OPENAI_API_KEY']:
        print("   ✅ Matches .env file - Perfect!")
    elif system_key and api_key == env_values['OPENAI_API_KEY']:
        print("   ✅ Using .env file (system variable was overridden)")
    else:
        print("   ⚠️  Using system environment variable")
else:
    print("   ❌ OPENAI_API_KEY is NOT set")
    print("   Please add OPENAI_API_KEY=your-key-here to your .env file")
    exit(1)

# Check for SESSION_SECRET
session_secret = os.environ.get('SESSION_SECRET')
if session_secret:
    print(f"   ✅ SESSION_SECRET is set")
else:
    print("   ⚠️  SESSION_SECRET is not set (optional but recommended)")

print("=" * 60)
print("✅ All required environment variables are configured!")
print("You can now run: python main.py")
print("=" * 60)
