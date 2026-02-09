import requests

def download_massey():
    print("Downloading Massey Ratings...")

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    url = "https://masseyratings.com/cb/exportCSV.php"
    response = requests.get(url, timeout=60)

    if response.status_code != 200 or "text" not in response.headers.get("Content-Type", ""):
        raise RuntimeError("Failed to download Massey CSV")

    with open(CSV_FILE, "wb") as f:
        f.write(response.content)

    if os.path.getsize(CSV_FILE) < 1000:
        raise RuntimeError("Downloaded CSV is unexpectedly small")

    print("CSV downloaded.")
