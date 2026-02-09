import json
import tempfile

checksum_file = "last_checksum.txt"
current_checksum = file_checksum(CSV_FILE)

if os.path.exists(checksum_file):
    with open(checksum_file, "r") as f:
        last_checksum = f.read().strip()
    if current_checksum == last_checksum:
        print("CSV unchanged — skipping Sheets upload.")
        return

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

    df = pd.read_csv(CSV_FILE, dtype=str).fillna("")

    cred_file = get_google_credentials()

    creds = Credentials.from_service_account_file(
        cred_file,
        scopes=SCOPES
    )

    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.worksheet(Massey_Ratings)

    worksheet.clear()
    worksheet.update(
        [df.columns.tolist()] + df.values.tolist(),
        value_input_option="RAW"
    )

with open(checksum_file, "w") as f:
    f.write(current_checksum)
