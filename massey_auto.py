import os
import json
import time
import tempfile
from datetime import datetime, date, timezone

import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

import gspread
from google.oauth2.service_account import Credentials

# ===============================
# CONSTANTS
# ===============================
DOWNLOAD_DIR = "downloads"
CSV_FILE = os.path.join(DOWNLOAD_DIR, "export.csv")

SHEET_ID = "1LiE7lf1FNK91ieiszgtzloZfQxMWa8pRSa9f-2JIEIc"   # keep yours
SHEET_NAME = "Massey_Ratings"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

RUN_LOG_FILE = "last_run_date.txt"

# ===============================
# TIME (UTC SAFE)
# ===============================
def utc_today():
    return datetime.now(timezone.utc).date()

# ===============================
# GOOGLE CREDENTIALS
# ===============================
def get_google_credentials():
    secret_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not secret_json:
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS secret not found")

    data = json.loads(secret_json)

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    with open(temp.name, "w") as f:
        json.dump(data, f)

    return temp.name

# ===============================
# SEASON CHECK (Nov 1 – Apr 10)
# ===============================
def in_season(today: date) -> bool:
    if today.month >= 11:
        start = date(today.year, 11, 1)
        end = date(today.year + 1, 4, 10)
    else:
        start = date(today.year - 1, 11, 1)
        end = date(today.year, 4, 10)

    return start <= today <= end

# ===============================
# RUN-ONCE-PER-DAY CHECK
# ===============================
def already_ran_today(today: date) -> bool:
    if not os.path.exists(RUN_LOG_FILE):
        return False

    with open(RUN_LOG_FILE, "r") as f:
        last = f.read().strip()

    return last == today.isoformat()

def mark_ran(today: date):
    with open(RUN_LOG_FILE, "w") as f:
        f.write(today.isoformat())

# ===============================
# DOWNLOAD MASSEY CSV
# ===============================
def download_massey():
    print("Downloading Massey Ratings...")

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get("https://masseyratings.com/cb/")
        time.sleep(5)

        timeout = time.time() + 90
        while time.time() < timeout:
            files = os.listdir(DOWNLOAD_DIR)
            if any(f.endswith(".csv") for f in files):
                print("CSV downloaded.")
                return
            time.sleep(1)

        raise RuntimeError("CSV download timed out")

    finally:
        driver.quit()

# ===============================
# UPLOAD TO GOOGLE SHEETS
# ===============================
def upload_to_sheets(today: date):
    print("Uploading to Google Sheets...")

    df = pd.read_csv(CSV_FILE, dtype=str).fillna("")
    df.insert(0, "Last Updated (UTC)", today.isoformat())

    cred_file = get_google_credentials()
    creds = Credentials.from_service_account_file(cred_file, scopes=SCOPES)

    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())

# ===============================
# MAIN
# ===============================
def main():
    today = utc_today()

    print(f"RUN DATE (UTC): {datetime.datetime.utcnow().isoformat()}")

    if not in_season(today):
        print("Out of season — exiting.")
        return

    today = datetime.date.today()

if already_ran_today(today) and os.path.exists(CSV_FILE):
    print("Already ran today and CSV exists — exiting.")
    return

    download_massey()
    upload_to_sheets(today)

    mark_ran(today)
    print("Update complete.")

if __name__ == "__main__":
    main()
