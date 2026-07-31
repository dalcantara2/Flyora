"""
config.py
---------
Central configuration for the Flyora application.
All environment-specific settings live here so they are easy to find and change.
"""

import os

# ---------------------------------------------------------------------------
# Base directory — the folder this file lives in.
# All other paths are built relative to this so the app works on any machine.
# ---------------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
# The 'database/' subfolder keeps the .db file away from the source code.
DATABASE_DIR  = os.path.join(BASE_DIR, "database")
DATABASE_PATH = os.path.join(DATABASE_DIR, "skyroute.db")

# ---------------------------------------------------------------------------
# Flask
# ---------------------------------------------------------------------------
# SECRET_KEY is used to sign session cookies.
# In production this should be set via an environment variable, not hardcoded.
SECRET_KEY = os.environ.get("SECRET_KEY", "flyora-dev-secret-key-change-in-prod")

# DEBUG should be True locally and False in production.
DEBUG = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
