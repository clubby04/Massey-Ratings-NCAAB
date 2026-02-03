from datetime import date
import os
import time
import datetime
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

import gspread
from google.oauth2.service_account import Credentials


# ===============================
# SEASON CHECK (Nov 1 – Apr 10)
# ===============================
today = date.today()

season_start = date(today.year, 11, 1)
season_end = date(today.year + 1, 4, 10)

if today.month <= 4:
    season_start = date(today.year - 1, 11, 1)
    season_end = date(today.year, 4, 10)

if not (season_start <= today <= season_end):
    print("Outside NCAA basketball season. Exiting.")
    exit(0)


# ===============================
# PATHS & CONSTANTS
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
LAST_RUN_FILE = os.path.join(BASE_DIR, "last_run.txt")

CSV_FILE = os.path.join(DOWNLOAD_DIR, "export.csv")
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "service_account.json")

SHEET_ID = "1LiE7lf1FNK91ieiszgtzloZfQxMWa8pRSa9f-2JIEIc"
TAB_NAME = "Massey_Ratings"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


# ===============================
# HELPER FUNCTIONS
# ===============================
def in_season(today):
    if today.month >= 11:
        season_start = datetime.date(today.year, 11, 1)
        season_end = datetime.date(today.year + 1, 4, 10)
    else:
        season_start = datetime.date(today.year - 1, 11, 1)
        season_end = datetime.date(today.year, 4, 10)

    return season_start <= today <= season_end


def already_ran_today(today):
    if not os.path.exists(LAST_RUN_FILE):
        return False
    with open(LAST_RUN_FILE, "r") as f:
        return f.read().strip() == today.isoformat()


def mark_ran(today):
    with open(LAST_RUN_FILE, "w") as f:
        f.write(today.isoformat())


# ===============================
# DOWNLOAD MASSEY RATINGS
# ===============================
def download_massey():
    print("Downloading Massey Ratings...")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # 🔧 STEP 1 — CI-SAFE HEADLESS CHROME SETUP
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    service = Service("/usr/bin/chromedriver")

    attempts = 0
    while attempts < 3:
        attempts += 1
        print(f"Attempt {attempts}...")

        driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            driver.set_page_load_timeout(180)
            driver.get("https://masseyratings.com/cb/ncaa-d1/ratings")

            wait = WebDriverWait(driver, 40)
            dropdown = wait.until(
                EC.presence_of_element_located((By.ID, "pulldownlinks"))
            )

            for option in dropdown.find_elements(By.TAG_NAME, "option"):
                if option.text.strip() == "Export":
                    option.click()
                    break

            time.sleep(2)

            timeout = 90
            start = time.time()
            while True:
                files = os.listdir(DOWNLOAD_DIR)
                if any("export" in f and f.endswith(".csv") for f in files):
                    break
                if time.time() - start > timeout:
                    raise Exception("Download did not start within 90 seconds.")
                time.sleep(1)

            while any(f.endswith(".crdownload") for f in os.listdir(DOWNLOAD_DIR)):
                time.sleep(1)

            print("Download complete!")
            driver.quit()
            return

        except Exception as e:
            print("Error:", e)
            driver.save_screenshot("error.png")
            driver.quit()
            if attempts == 3:
                raise
            print("Retrying in 5 seconds...")
            time.sleep(5)


# ===============================
# UPLOAD TO GOOGLE SHEETS
# ===============================
def upload_to_sheets():
    print("Uploading to Google Sheets...")

    df = pd.read_csv(CSV_FILE, dtype=str).fillna("")

    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )

    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.worksheet(TAB_NAME)

    worksheet.clear()
    worksheet.update(
        [df.columns.tolist()] + df.values.tolist(),
        value_input_option="RAW"
    )


# ===============================
# MAIN
# ===============================
def main():
    today = datetime.date.today()

    print("🟢 massey_auto.py started")
    print("Today is:", today)

    if not in_season(today):
        print("Out of season — exiting.")
        return

    if already_ran_today(today):
        print("Already ran today — exiting.")
        return

    download_massey()
    upload_to_sheets()
    mark_ran(today)

    print("✅ Massey update complete.")


if __name__ == "__main__":
    main()
