#!/usr/bin/env python3
"""
Google Sheets database helper.
Sheet columns: chat_id | student_id | phone | active | registered_at
"""

import os, json, logging
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

log = logging.getLogger(__name__)

SCOPES           = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID   = os.environ.get("GOOGLE_SHEET_ID", "")
SHEET_NAME       = "users"
CREDS_JSON       = os.environ.get("GOOGLE_CREDS_JSON", "")   # full JSON as string

HEADERS = ["chat_id", "student_id", "phone", "active", "registered_at"]


def _get_service():
    creds_dict = json.loads(CREDS_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds).spreadsheets()


def _get_all_rows():
    svc = _get_service()
    result = svc.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A:E"
    ).execute()
    return result.get("values", [])


def _ensure_headers():
    rows = _get_all_rows()
    if not rows:
        svc = _get_service()
        svc.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A1",
            valueInputOption="RAW",
            body={"values": [HEADERS]}
        ).execute()


def get_all_users() -> list:
    rows = _get_all_rows()
    if len(rows) <= 1:
        return []
    users = []
    for row in rows[1:]:   # skip header
        if len(row) >= 4:
            users.append({
                "chat_id":    row[0],
                "student_id": row[1],
                "phone":      row[2],
                "active":     row[3],
            })
    return users


def get_user(chat_id: str):
    users = get_all_users()
    for u in users:
        if u["chat_id"] == chat_id:
            return u
    return None


def _find_row_index(chat_id: str):
    """Returns 1-based row index in sheet, or None if not found."""
    rows = _get_all_rows()
    for i, row in enumerate(rows):
        if row and row[0] == chat_id:
            return i + 1   # sheets are 1-indexed
    return None


def register_user(chat_id: str, student_id: str, phone: str):
    _ensure_headers()
    existing_row = _find_row_index(chat_id)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    svc = _get_service()

    if existing_row:
        svc.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A{existing_row}:E{existing_row}",
            valueInputOption="RAW",
            body={"values": [[chat_id, student_id, phone, "TRUE", now]]}
        ).execute()
    else:
        svc.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:E",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [[chat_id, student_id, phone, "TRUE", now]]}
        ).execute()
    log.info(f"Registered/updated user {chat_id} — student {student_id}")


def set_user_active(chat_id: str, active: bool):
    row_idx = _find_row_index(chat_id)
    if not row_idx:
        log.warning(f"User {chat_id} not found in sheet")
        return
    svc = _get_service()
    svc.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!D{row_idx}",
        valueInputOption="RAW",
        body={"values": [["TRUE" if active else "FALSE"]]}
    ).execute()
    log.info(f"Set user {chat_id} active={active}")
