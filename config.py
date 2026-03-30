import os
from pathlib import Path

# Project paths
PROJECT_DIR = Path(__file__).parent
CREDENTIALS_FILE = PROJECT_DIR / "credentials.json"
TOKEN_FILE = PROJECT_DIR / "token.json"
LOG_FILE = PROJECT_DIR / "organizer.log"

# Google Drive folder ID to organize (set via env var or change here)
# Find this in the folder's URL: https://drive.google.com/drive/folders/<FOLDER_ID>
ROOT_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID", "")

# Anthropic
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Categories — files get sorted into subfolders with these names
CATEGORIES = ["Finance", "HR", "Projects", "Legal", "Personal", "Other"]

# Google Drive API scopes
SCOPES = ["https://www.googleapis.com/auth/drive"]
