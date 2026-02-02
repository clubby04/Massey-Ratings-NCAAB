import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os

print("Running gspread uploader...")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CSV_FILE = os.path.join(BASE_DIR, "downloads", "export.csv")
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "service_account.json")

SHEET_ID = "1LiE7lf1FNK91ieiszgtzloZfQxMWa8pRSa9f-2JIEIc"
TAB_NAME = "Massey_Ratings"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def main():
    print("Reading CSV...")
    df = pd.read_csv(CSV_FILE, dtype=str).fillna("")

    print("Authorizing...")
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )

    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.worksheet(TAB_NAME)

    print("Clearing worksheet...")
    worksheet.clear()

    print("Uploading data...")
    worksheet.update(
        [df.columns.tolist()] + df.values.tolist(),
        value_input_option="RAW"
    )

    print("✅ Upload complete!")

if __name__ == "__main__":
    main()
