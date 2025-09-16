#!/usr/bin/env python3
"""Setup script for initializing the Merchant Center Monitor."""

import os
import sys
import json
from pathlib import Path

def create_env_file():
    """Create .env file from template."""
    env_example = Path("env.example")
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return
    
    if not env_example.exists():
        print("❌ env.example file not found")
        return
    
    # Copy template
    with open(env_example, 'r') as f:
        content = f.read()
    
    with open(env_file, 'w') as f:
        f.write(content)
    
    print("✅ Created .env file from template")
    print("📝 Please edit .env file with your configuration")

def create_firestore_collections():
    """Create initial Firestore collections structure."""
    print("📊 Firestore collections will be created automatically on first run")
    print("   Collections: checks, email_alerts, settings")

def validate_requirements():
    """Validate that all requirements are met."""
    print("🔍 Validating requirements...")
    
    # Check Python version
    if sys.version_info < (3, 12):
        print("❌ Python 3.12+ is required")
        return False
    
    print("✅ Python version OK")
    
    # Check if requirements.txt exists
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found")
        return False
    
    print("✅ requirements.txt found")
    
    # Check if .env exists
    if not Path(".env").exists():
        print("⚠️  .env file not found - run setup first")
        return False
    
    print("✅ .env file found")
    
    return True

def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing dependencies...")
    os.system("pip install -r requirements.txt")
    print("✅ Dependencies installed")

def run_tests():
    """Run tests to verify installation."""
    print("🧪 Running tests...")
    result = os.system("pytest tests/ -v")
    if result == 0:
        print("✅ All tests passed")
    else:
        print("❌ Some tests failed")
    return result == 0

def main():
    """Main setup function."""
    print("🚀 Merchant Center Monitor Setup")
    print("=" * 40)
    
    # Create .env file
    create_env_file()
    
    # Create Firestore collections info
    create_firestore_collections()
    
    # Validate requirements
    if not validate_requirements():
        print("\n❌ Setup validation failed")
        print("Please fix the issues above and run setup again")
        return
    
    # Install dependencies
    install_dependencies()
    
    # Run tests
    if run_tests():
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file with your configuration")
        print("2. Set up Google Service Account and Merchant Center access")
        print("3. Configure SendGrid API key")
        print("4. Run: python run.py")
    else:
        print("\n⚠️  Setup completed with test failures")
        print("Please check the test output above")

if __name__ == "__main__":
    main()
