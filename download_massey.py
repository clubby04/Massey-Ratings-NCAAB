from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def download_massey():
    print("Downloading Massey Ratings...")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # 🔑 ensure downloads go to /downloads
    prefs = {
        "download.default_directory": os.path.abspath(DOWNLOAD_DIR),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 30)

    try:
        driver.get("https://masseyratings.com/cb/ncaa-d1/ratings")

        # 🔴 Click the red "More" button
        more_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'More')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", more_button)
        more_button.click()

        # 📤 Click "Export"
        export_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Export')]"))
        )
        export_button.click()

        # 🧹 remove old CSV if present
        if os.path.exists(CSV_FILE):
            os.remove(CSV_FILE)

        # ⏳ wait for download
        timeout = 90
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
