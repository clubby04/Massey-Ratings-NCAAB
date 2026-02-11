import os
import time
import json
import hashlib
import tempfile
import datetime
import pandas as pd

import gspread
from google.oauth2.service_account import Credentials

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service


# ===============================
# CONSTANTS
# ===============================
DOWNLOAD_DIR = "downloads"
CSV_FILE = os.path.join(DOWNLOAD_DIR, "export.csv")
CHECKSUM_FILE = "last_checksum.txt"

SHEET_ID = "1LiE7lf1FNK91ieiszgtzloZfQxMWa8pRSa9f-2JIEIc"
WORKSHEET_NAME = "Massey_Ratings"
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
# CHECKSUM
# ===============================
def file_checksum(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()


# ===============================
# DOWNLOAD VIA SELENIUM
# ===============================
def download_massey():
    print("Downloading Massey Ratings...")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)

    chrome_options = webdriver.ChromeOptions()

    # Headless but stealth
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    prefs = {
        "download.default_directory": os.path.abspath(DOWNLOAD_DIR),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Remove webdriver flag
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        },
    )

    try:
        print("Opening Massey page...")
        driver.get("https://masseyratings.com/cb/ncaa-d1/ratings")

        wait = WebDriverWait(driver, 45)

        print("Waiting for dropdown...")
        dropdown = wait.until(
            EC.presence_of_element_located((By.ID, "pulldownlinks"))
        )

        print("Dropdown found. Clicking export...")

        for option in dropdown.find_elements(By.TAG_NAME, "option"):
            if option.get_attribute("value") == "exportCSV":
                option.click()
                break

        print("Waiting for CSV download...")

        timeout = time.time() + 90
        while time.time() < timeout:
            if os.path.exists(CSV_FILE):
                break
            time.sleep(1)
        else:
            raise RuntimeError("CSV download timed out")

        size = os.path.getsize(CSV_FILE)
        if size < 1000:
            raise RuntimeError(f"Downloaded CSV too small ({size} bytes)")

        print(f"CSV downloaded successfully ({size} bytes)")

    finally:
        driver.quit()


# ===============================
# UPLOAD TO GOOGLE SHEETS
# ===============================
def upload_to_sheets():
    print("Uploading to Google Sheets...")

    if not os.path.exists(CSV_FILE):
        raise FileNotFoundError(f"CSV file not found: {CSV_FILE}")

    df = pd.read_csv(CSV_FILE, dtype=str).fillna("")

    current_checksum = file_checksum(CSV_FILE)

    if os.path.exists(CHECKSUM_FILE):
        with open(CHECKSUM_FILE, "r") as f:
            last_checksum = f.read().strip()

        if current_checksum == last_checksum:
            print("CSV unchanged — skipping Sheets upload.")
            return

    cred_file = get_google_credentials()
    creds = Credentials.from_service_account_file(cred_file, scopes=SCOPES)
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key(SHEET_ID)
    worksheet = spreadsheet.worksheet(WORKSHEET_NAME)

    worksheet.clear()
    worksheet.update(
        [df.columns.tolist()] + df.values.tolist(),
        value_input_option="RAW"
    )

    print("Sheet updated successfully.")

    with open(CHECKSUM_FILE, "w") as f:
        f.write(current_checksum)

    print("Checksum saved.")


# ===============================
# MAIN
# ===============================
def main():
    try:
        download_massey()
        upload_to_sheets()
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        raise


if __name__ == "__main__":
    main()
