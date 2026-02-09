import os
import requests
import hashlib
import time
import json
import tempfile
import datetime
import pandas as pd

import gspread
from google.oauth2.service_account import Credentials

# ===============================
# CONSTANTS
# ===============================
DOWNLOAD_DIR = "downloads"
CSV_FILE = os.path.join(DOWNLOAD_DIR, "export.csv")
LAST_RUN_FILE = "last_run_date.txt"
CHECKSUM_FILE = "last_checksum.txt"

SHEET_ID = "1LiE7lf1FNK91ieiszgtzloZfQxMWa8pRSa9f-2JIEIc"
WORKSHEET_NAME = "Massey_Ratings"          # ← your exact tab name
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

print(f"RUN DATE (UTC): {datetime.datetime.utcnow().isoformat()}")

# ===============================
# GOOGLE CREDENTIALS
# ===============================
def get_google_credentials():
    secret_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not secret_json:
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS secret not found in environment")

    print(f"Credentials secret loaded (length: {len(secret_json)} chars)")

    try:
        data = json.loads(secret_json)
        print(f"Service account email: {data.get('client_email', 'missing')}")
    except json.JSONDecodeError:
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS is not valid JSON")

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    with open(temp.name, "w") as f:
        json.dump(data, f)

    return temp.name

# ===============================
# CHECKSUM HELPERS
# ===============================
def file_checksum(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()

# ===============================
# RUN GUARD (optional - skip if you want to force run every time)
# ===============================
def already_ran_today(today):
    if not os.path.exists(LAST_RUN_FILE):
        return False
    with open(LAST_RUN_FILE, "r") as f:
        last = f.read().strip()
    return last == today.isoformat()

def write_last_run(today):
    with open(LAST_RUN_FILE, "w") as f:
        f.write(today.isoformat())

# ===============================
# DOWNLOAD
# ===============================
def download_massey():
    print("Downloading Massey Ratings...")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    url = "https://masseyratings.com/cb/exportCSV.php"
    response = requests.get(url, timeout=60)
    response.raise_for_status()  # fail fast on bad status

    with open(CSV_FILE, "wb") as f:
        f.write(response.content)

    size = os.path.getsize(CSV_FILE)
    if size < 1000:
        raise RuntimeError(f"Downloaded CSV is too small ({size} bytes)")

    print(f"CSV downloaded successfully ({size} bytes)")

# ===============================
# UPLOAD TO SHEETS
# ===============================
def upload_to_sheets():
    print("Starting upload to Google Sheets...")

    if not os.path.exists(CSV_FILE):
        raise FileNotFoundError(f"CSV file not found: {CSV_FILE}")

    df = pd.read_csv(CSV_FILE, dtype=str).fillna("")
    print(f"DataFrame loaded with {len(df)} rows and {len(df.columns)} columns")

    # Checksum to skip if unchanged
    current_checksum = file_checksum(CSV_FILE)
    if os.path.exists(CHECKSUM_FILE):
        with open(CHECKSUM_FILE, "r") as f:
            last_checksum = f.read().strip()
        if current_checksum == last_checksum:
            print("CSV content unchanged — skipping Sheets upload.")
            return

    cred_file = get_google_credentials()
    creds = Credentials.from_service_account_file(cred_file, scopes=SCOPES)
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key(SHEET_ID)
    print(f"Opened spreadsheet: {spreadsheet.title}")

    worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    print(f"Target worksheet: {worksheet.title}")

    print("Clearing worksheet...")
    worksheet.clear()

    print("Updating worksheet with new data...")
    worksheet.update(
        [df.columns.tolist()] + df.values.tolist(),
        value_input_option="RAW"
    )

    print("Upload complete — data written to sheet")

    # Save new checksum
    with open(CHECKSUM_FILE, "w") as f:
        f.write(current_checksum)
    print("Checksum updated")

# ===============================
# MAIN
# ===============================
def main():
    today = datetime.date.today()

    # Optional: uncomment if you want to skip same-day runs
    # if already_ran_today(today):
    #     print("Already ran today — exiting.")
    #     return

    try:
        download_massey()
        upload_to_sheets()
        write_last_run(today)
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {str(e)}")
        raise

if __name__ == "__main__":
    main()
