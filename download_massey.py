def download_massey():
    print("Downloading Massey Ratings...")

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    chrome_options = webdriver.ChromeOptions()

    # Headless but more stealth
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    attempts = 0
    while attempts < 3:
        attempts += 1
        print(f"Attempt {attempts}...")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

        try:
            # Increase page load timeout
            driver.set_page_load_timeout(180)

            # Reduce detectability
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined})
                """
            })

            print("Loading Massey Ratings page...")
            driver.get("https://masseyratings.com/cb/ncaa-d1/ratings")

            print("Waiting for dropdown...")
            wait = WebDriverWait(driver, 40)
            dropdown = wait.until(
                EC.presence_of_element_located((By.ID, "pulldownlinks"))
            )

            print("Dropdown found. Clicking Export...")
            for option in dropdown.find_elements(By.TAG_NAME, "option"):
                if option.text.strip() == "Export":
                    option.click()
                    break

            print("Clicked Export. Waiting for download to start...")
            time.sleep(2)

            timeout = 90
            start = time.time()
            while True:
                files = os.listdir(DOWNLOAD_DIR)
                if any("export" in f and f.endswith(".csv") for f in files):
                    print("CSV file detected!")
                    break
                if time.time() - start > timeout:
                    raise Exception("Download did not start within 90 seconds.")
                time.sleep(1)

            print("Waiting for download to finish...")
            while any(f.endswith(".crdownload") for f in os.listdir(DOWNLOAD_DIR)):
                time.sleep(1)

            print("Download complete!")
            driver.quit()
            return

        except Exception as e:
            print("Error:", e)
            driver.quit()
            if attempts == 3:
                raise
            print("Retrying in 5 seconds...")
            time.sleep(5)
