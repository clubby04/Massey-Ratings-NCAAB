# =========================
# Google Sheets Upload
# =========================

import json
import tempfile
import hashlib
import os
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials


def file_checksum(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def get_google_credentials():
    secret_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

    if not secret_json:
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS secret not found")

    data = json.loads(secret_json)

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    with open(temp.name, "w") as f:
        json.dump(data, f)

    return temp.name


def upload_to_sheets():
    print("Uploading to Google Sheets...")

    checksum_file = "last_checksum.txt"
    current_checksum = file_checksum(CSV_FILE)

    # Skip upload if CSV unchanged
    if os.path.exists(checksum_file):
        with open(checksum_file, "r") as f:
            last_checksum = f.read().strip()

        if current_checksum == last_checksum:
            print("CSV unchanged — skipping Sheets upload.")
            return

    # Load CSV
    df = pd.read_csv(CSV_FILE, dtype=str).fillna("")

    cred_file = get_google_credentials()

    creds = Credentials.from_service_account_file(
        cred_file,
        scopes=SCOPES
    )

    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.worksheet(TAB_NAME)

    # Overwrite sheet
    worksheet.clear()
    worksheet.update(
        [df.columns.tolist()] + df.values.tolist(),
        value_input_option="RAW"
    )

    # Save checksum AFTER successful upload
    with open(checksum_file, "w") as f:
        f.write(current_checksum)

    print("Google Sheets updated.")
