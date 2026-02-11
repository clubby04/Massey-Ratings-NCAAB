import requests
import json
import os
import tempfile
import datetime
import gspread
from google.oauth2.service_account import Credentials

# ===============================
# CONSTANTS
# ===============================
SHEET_ID = "1LiE7lf1FNK91ieiszgtzloZfQxMWa8pRSa9f-2JIEIc"
WORKSHEET_NAME = "Massey_Ratings"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

MASSEY_URL = "https://masseyratings.com/json/rate.php?argv=slxlZrMjujc7FOv1L0Uz63eIfW0G5Xxyawl2HTSr7Vks72nWxxwgp35IAExoj-Cv39AN9n6oCP6-MoaTOAPIJchbHTuLa7KpHCbHhWc4sGw.&task=json"

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
# DOWNLOAD + UPLOAD
# ===============================
def fetch_massey_json():
    print("Fetching Massey JSON...")

    url = "https://masseyratings.com/json/rate.php?argv=slxlZrMjujc7FOv1L0Uz63eIfW0G5Xxyawl2HTSr7Vks72nWxxwgp35IAExoj-Cv39AN9n6oCP6-MoaTOAPIJchbHTuLa7KpHCbHhWc4sGw.&task=json"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://masseyratings.com/cb/ncaa-d1/ratings",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Connection": "keep-alive"
    }

    session = requests.Session()
    response = session.get(url, headers=headers, timeout=60)

    response.raise_for_status()

    return response.json()

    if not rows:
        raise Exception("No data returned from Massey")

    print(f"Retrieved {len(rows)} rows")

    # Convert JSON rows into 2D list for Sheets
    headers_row = list(rows[0].keys())
    values = [headers_row]

    for row in rows:
        values.append([row.get(col, "") for col in headers_row])

    print("Connecting to Google Sheets...")

    cred_file = get_google_credentials()
    creds = Credentials.from_service_account_file(cred_file, scopes=SCOPES)
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key(SHEET_ID)
    worksheet = spreadsheet.worksheet(WORKSHEET_NAME)

    print("Clearing worksheet...")
    worksheet.clear()

    print("Uploading data...")
    worksheet.update(values, value_input_option="RAW")

    print("Upload complete.")

# ===============================
# MAIN
# ===============================
def main():
    try:
        update_massey_sheet()
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {str(e)}")
        raise

if __name__ == "__main__":
    main()
