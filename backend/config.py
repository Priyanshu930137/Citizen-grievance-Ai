# ==========================================
# CITIZEN CONNECT - CONFIGURATION
# ==========================================

from pathlib import Path


# ==========================================
# BASE DIRECTORY
# ==========================================

BASE_DIR = Path(__file__).resolve().parent


# ==========================================
# DATABASE
# ==========================================

DATABASE_URL = (
    f"sqlite:///{BASE_DIR / 'citizen_connect.db'}"
)


# ==========================================
# PROJECT SETTINGS
# ==========================================

PROJECT_NAME = "Citizen Connect"

PROJECT_VERSION = "1.0.0"