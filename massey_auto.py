import os
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

SHEET_ID = "1LiE7lf1FNK91ieiszgtzloZfQxMWa8pRSa9f-2JIEIc"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

print(f"RUN DATE (UTC): {datetime.datetime.utcnow().isoformat()}")

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
# RUN GUARD
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

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get("https://masseyratings.com/cb/ncaa-d1/ratings")
        time.sleep(5)

        # 🔧 Ensure previous CSV is removed so we always detect new download
        if os.path.exists(CSV_FILE):
            os.remove(CSV_FILE)

        # TODO: click export button here

        timeout = 90
        start = time.time()

        while time.time() - start < timeout:
            if os.path.exists(CSV_FILE):
                print("CSV downloaded.")
                return
            time.sleep(1)

        raise RuntimeError("CSV download timed out")

    finally:
        driver.quit()

# ===============================
# UPLOAD
# ===============================
def upload_to_sheets():
    print("Uploading to Google Sheets...")

    df = pd.read_csv(CSV_FILE, dtype=str).fillna("")

    cred_file = get_google_credentials()
    creds = Credentials.from_service_account_file(cred_file, scopes=SCOPES)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(SHEET_ID).sheet1
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())

# ===============================
# MAIN
# ===============================
def main():
    today = datetime.date.today()

    if already_ran_today(today):
        print("Already uploaded today — exiting.")
        return

    download_massey()
    upload_to_sheets()
    write_last_run(today)

if __name__ == "__main__":
    main()
