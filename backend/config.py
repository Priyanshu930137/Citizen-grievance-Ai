# ==========================================
# CITIZEN CONNECT - CONFIGURATION
# ==========================================

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


# ==========================================
# BASE DIRECTORY
# ==========================================

BASE_DIR = Path(__file__).resolve().parent


# ==========================================
# DATABASE
# ==========================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{BASE_DIR / 'citizen_connect.db'}"
)


# ==========================================
# PROJECT SETTINGS
# ==========================================

PROJECT_NAME = "Citizen Connect"

PROJECT_VERSION = "1.0.0"
