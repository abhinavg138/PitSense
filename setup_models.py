"""
PitSense Model Downloader (Root Entry Point)
============================================
Downloads and caches required Hugging Face AI models locally in backend/models/.
"""

import sys
from pathlib import Path

# Add backend directory to path and delegate to backend/setup_models.py
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from setup_models import main

if __name__ == "__main__":
    main()
