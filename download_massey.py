def download_massey():
    print("Downloading Massey Ratings...")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    prefs = {
        "download.default_directory": os.path.abspath(DOWNLOAD_DIR),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Remove old CSV so we don't get false positives
        if os.path.exists(CSV_FILE):
            os.remove(CSV_FILE)

        # Direct export endpoint (bypasses dropdown JS)
        driver.get("https://masseyratings.com/cb/exportCSV.php")

        timeout = 120
        start = time.time()
        while time.time() - start < timeout:
            if os.path.exists(CSV_FILE) and not any(
                f.endswith(".crdownload") for f in os.listdir(DOWNLOAD_DIR)
            ):
                print("CSV downloaded.")
                return
            time.sleep(1)

        raise RuntimeError("CSV download timed out")

    finally:
        driver.quit()
