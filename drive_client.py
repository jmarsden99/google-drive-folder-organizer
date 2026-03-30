"""Google Drive API connection and file operations."""

import logging
import time

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import CREDENTIALS_FILE, TOKEN_FILE, SCOPES

log = logging.getLogger(__name__)


def get_drive_service():
    """Authenticate and return a Google Drive API service instance.

    Uses OAuth2 with credentials.json. Saves/reuses token.json for
    subsequent runs so you only need to log in once.
    """
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0, prompt="select_account")
        TOKEN_FILE.write_text(creds.to_json())

    return build("drive", "v3", credentials=creds)


def _execute_with_retry(request, retries=5):
    """Execute a Google API request with exponential backoff on 500 errors."""
    for attempt in range(retries):
        try:
            return request.execute()
        except HttpError as e:
            if e.resp.status in (500, 503) and attempt < retries - 1:
                wait = 2 ** attempt
                log.warning("Google API %d error, retrying in %ds...", e.resp.status, wait)
                time.sleep(wait)
            else:
                raise


def list_files_in_folder(service, folder_id: str) -> list[dict]:
    """List all files (not folders) in a single Drive folder."""
    results = []
    page_token = None
    query = f"'{folder_id}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false"

    while True:
        response = _execute_with_retry(
            service.files()
            .list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType, createdTime, modifiedTime, size)",
                pageSize=100,
                pageToken=page_token,
            )
        )
        results.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return results


def list_subfolders(service, folder_id: str) -> list[dict]:
    """List all subfolders in a Drive folder."""
    results = []
    page_token = None
    query = f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"

    while True:
        response = _execute_with_retry(
            service.files()
            .list(
                q=query,
                fields="nextPageToken, files(id, name)",
                pageSize=100,
                pageToken=page_token,
            )
        )
        results.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return results


def scan_folder_recursive(service, folder_id: str, path: str = "") -> list[dict]:
    """Recursively scan a folder and all subfolders, returning all files."""
    all_files = []

    files = list_files_in_folder(service, folder_id)
    for f in files:
        f["path"] = path
    all_files.extend(files)

    subfolders = list_subfolders(service, folder_id)
    for folder in subfolders:
        sub_path = f"{path}/{folder['name']}" if path else folder["name"]
        all_files.extend(scan_folder_recursive(service, folder["id"], sub_path))

    return all_files


def find_or_create_folder(service, name: str, parent_id: str) -> str:
    """Find a subfolder by name under parent_id, or create it. Returns folder ID."""
    query = (
        f"'{parent_id}' in parents "
        f"and mimeType = 'application/vnd.google-apps.folder' "
        f"and name = '{name}' "
        f"and trashed = false"
    )
    response = service.files().list(q=query, fields="files(id)").execute()
    existing = response.get("files", [])

    if existing:
        return existing[0]["id"]

    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(body=metadata, fields="id").execute()
    return folder["id"]


def move_file(service, file_id: str, current_parents: str, new_folder_id: str):
    """Move a file to a new folder in Google Drive."""
    service.files().update(
        fileId=file_id,
        addParents=new_folder_id,
        removeParents=current_parents,
        fields="id, parents",
    ).execute()
