def download_massey():
    print("Downloading Massey Ratings...")

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    url = "https://masseyratings.com/cb/exportCSV.php"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://masseyratings.com/cb/ncaa-d1.php",
        "Accept": "text/csv,text/plain,*/*",
    }

    response = requests.get(url, headers=headers, timeout=60)

    if response.status_code != 200:
        raise RuntimeError(f"Failed to download CSV (status {response.status_code})")

    with open(CSV_FILE, "wb") as f:
        f.write(response.content)

    if os.path.getsize(CSV_FILE) < 1000:
        raise RuntimeError("Downloaded CSV is unexpectedly small")

    print("CSV downloaded.")
