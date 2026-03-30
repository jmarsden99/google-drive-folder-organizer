#!/usr/bin/env python3
"""Main entry point — scans Google Drive, categorizes files, and moves them."""

import argparse
import logging
import sys
from datetime import datetime

from config import ROOT_FOLDER_ID, LOG_FILE, CATEGORIES
from drive_client import (
    get_drive_service,
    list_files_in_folder,
    scan_folder_recursive,
    find_or_create_folder,
    move_file,
)
from categorizer import categorize_files

# Set up logging to both file and stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def run(limit: int = 0):
    log.info("=" * 60)
    log.info("Drive Organizer started at %s", datetime.now().isoformat())
    if limit:
        log.info("TEST MODE: processing only %d files", limit)

    if not ROOT_FOLDER_ID:
        log.error("DRIVE_FOLDER_ID is not set. Set it in config.py or as an env var.")
        sys.exit(1)

    # 1. Connect to Google Drive
    log.info("Connecting to Google Drive...")
    service = get_drive_service()

    # 2. Scan files
    if limit:
        log.info("Scanning top-level of folder %s...", ROOT_FOLDER_ID)
        files = list_files_in_folder(service, ROOT_FOLDER_ID)
    else:
        log.info("Scanning folder %s recursively...", ROOT_FOLDER_ID)
        files = scan_folder_recursive(service, ROOT_FOLDER_ID)
    log.info("Found %d files", len(files))

    if not files:
        log.info("No files found. Done.")
        return

    if limit:
        files = files[:limit]
        log.info("Limited to %d files for testing", len(files))

    # 3. Categorize files with Claude
    log.info("Categorizing files with Claude API...")
    categories = categorize_files(files)

    # 4. Create category folders and move files
    log.info("Organizing files into category folders...")
    folder_cache: dict[str, str] = {}
    moved = 0
    skipped = 0

    for f in files:
        category = categories.get(f["id"], "Other")

        # Get or create the category subfolder
        if category not in folder_cache:
            folder_cache[category] = find_or_create_folder(
                service, category, ROOT_FOLDER_ID
            )

        target_folder_id = folder_cache[category]

        # Skip if file is already in a category folder
        if f.get("path") in CATEGORIES:
            log.info("SKIP: '%s' already in '%s'", f["name"], f["path"])
            skipped += 1
            continue

        log.info("MOVE: '%s' → %s/", f["name"], category)
        move_file(service, f["id"], ROOT_FOLDER_ID, target_folder_id)
        moved += 1

    log.info("Done. Moved %d files, skipped %d.", moved, skipped)
    log.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Only process N files (for testing)")
    args = parser.parse_args()
    run(limit=args.limit)
