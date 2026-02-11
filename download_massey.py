import requests
import os
import csv

DOWNLOAD_DIR = "downloads"
MASSEY_URL = "https://masseyratings.com/json/rate.php?argv=slxlZrMjujc7FOv1L0Uz63eIfW0G5Xxyawl2HTSr7Vks72nWxxwgp35IAExoj-Cv39AN9n6oCP6-MoaTOAPIJchbHTuLa7KpHCbHhWc4sGw.&task=json"

def download_massey():
    print("Downloading Massey Ratings (JSON endpoint)...")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://masseyratings.com/cb/ncaa-d1/ratings"
    }

    response = requests.get(MASSEY_URL, headers=headers, timeout=60)
    response.raise_for_status()

    data = response.json()

    output_file = os.path.join(DOWNLOAD_DIR, "massey_ratings.csv")

    # The JSON structure usually contains a 'data' key
    rows = data.get("data", [])

    if not rows:
        raise Exception("No data found in JSON response.")

    # Write CSV
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(rows[0].keys())  # headers
        for row in rows:
            writer.writerow(row.values())

    print("Massey CSV saved successfully.")
