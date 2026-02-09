def download_massey():
    print("Downloading Massey Ratings...")

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    base_url = "https://masseyratings.com/cb/ncaa-d1.php"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": base_url,
    }

    session = requests.Session()
    session.headers.update(headers)

    # Step 1: load page (sets session cookie)
    r1 = session.get(base_url, timeout=60)
    if r1.status_code != 200:
        raise RuntimeError("Failed to load Massey NCAA page")

    # Step 2: POST export action (this matches the dropdown behavior)
    r2 = session.post(
        base_url,
        data={"pulldownlinks": "exportCSV"},
        timeout=60,
    )

    if r2.status_code != 200:
        raise RuntimeError(f"Failed to download CSV (status {r2.status_code})")

    with open(CSV_FILE, "wb") as f:
        f.write(r2.content)

    if os.path.getsize(CSV_FILE) < 1000:
        raise RuntimeError("Downloaded CSV is unexpectedly small")

    print("CSV downloaded.")
