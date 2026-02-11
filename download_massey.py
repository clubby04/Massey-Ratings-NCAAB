def download_massey():
    print("Downloading Massey Ratings...")

    import shutil
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    import time

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Clear old export file if exists
    for f in os.listdir(DOWNLOAD_DIR):
        if f.startswith("export") and f.endswith(".csv"):
            os.remove(os.path.join(DOWNLOAD_DIR, f))

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    prefs = {
        "download.default_directory": os.path.abspath(DOWNLOAD_DIR),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get("https://masseyratings.com/cb/ncaa-d1/ratings")

        wait = WebDriverWait(driver, 30)
        dropdown = wait.until(
            EC.presence_of_element_located((By.ID, "pulldownlinks"))
        )

        for option in dropdown.find_elements(By.TAG_NAME, "option"):
            if option.get_attribute("value") == "exportCSV":
                option.click()
                break

        # Wait for download
        timeout = 60
        start = time.time()

        while True:
            files = os.listdir(DOWNLOAD_DIR)
            if any(f.endswith(".csv") for f in files):
                break
            if time.time() - start > timeout:
                raise RuntimeError("CSV download timed out")
            time.sleep(1)

        print("CSV downloaded.")

    finally:
        driver.quit()
