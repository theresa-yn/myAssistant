#!/usr/bin/env python3
"""
Startup script for Railway deployment
"""
import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from myassistant.web_gui import main

if __name__ == "__main__":
    main()
