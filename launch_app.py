#!/usr/bin/env python3
"""
LangExtractor Application Launcher

Quick launcher for the main LangExtractor application.
This provides an easy way to launch the complete GUI application
from the project root directory.
"""

import sys
import os
from pathlib import Path

# Ensure we're running from the correct directory
project_root = Path(__file__).parent
os.chdir(project_root)

# Add project root to Python path
sys.path.insert(0, str(project_root))

# Import and run the main application
from demo_scripts.demo_complete_with_settings import main

if __name__ == "__main__":
    print("🚀 Launching LangExtractor Complete Application...")
    print("📁 Running from:", project_root)
    print("🎯 Loading GUI với Settings Dialog...")
    print()
    
    # Run the main application
    sys.exit(main()) 