import os
import glob
from datetime import datetime
import requests
import csv
import time
import logging
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import random

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
DOWNLOAD_DIR = f"{os.getcwd()}/downloads/"
AUTH_URL = 'https://idm.asiakas.elenia.fi/'
USERNAME = os.getenv('ELENIA_USERNAME')
PASSWORD = os.getenv('ELENIA_PASSWORD')
CURRENT_YEAR = datetime.now().year
CONSUMPTION_FILE = f"{DOWNLOAD_DIR}consumption_{CURRENT_YEAR}0101_{CURRENT_YEAR}1231.csv"
PRICE_FILE = f"{DOWNLOAD_DIR}spot_prices.csv"

# Ensure download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def fetch_consumption_data():
    preferences = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--window-size=1480x560")
    chrome_options.add_experimental_option("prefs", preferences)
    
    service = Service(ChromeDriverManager().install())

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logging.info(f"Chrome version: {driver.capabilities['browserVersion']}")
        logging.info(f"ChromeDriver version: {driver.capabilities['chrome']['chromedriverVersion'].split(' ')[0]}")

        logging.info("Navigating to login page")
        driver.get(AUTH_URL)
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'signin-email')))
        logging.info("Page is ready!")

        # Wait for the cookie button to be clickable and click it
        cookie_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]'))
        )
        cookie_button.click()
        logging.info("Cookie button clicked")

        # Wait for the username field to be visible and interactable
        username_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@id='signin-email']"))
        )
        logging.info(f"Username element found: {username_element.is_displayed()}")

        actions = ActionChains(driver)

        # Login process
        logging.info("Clicking on username field")
        actions.move_to_element(username_element).click().perform()
        time.sleep(random.uniform(0.5, 1.0))

        logging.info("Filling in the username")
        actions.send_keys(USERNAME).perform()
        time.sleep(random.uniform(0.5, 1.0))

        logging.info("Pressing TAB to move to password field")
        actions.send_keys(Keys.TAB).perform()
        time.sleep(random.uniform(0.5, 1.0))

        active_element = driver.switch_to.active_element
        if active_element.get_attribute('id') == 'password':
            logging.info("Successfully moved to password field")
            logging.info("Filling in the password")
            for char in PASSWORD:
                actions.send_keys(char).perform()
                time.sleep(random.uniform(0.05, 0.2))
        else:
            logging.error("Failed to move to password field")
            return

        actions.send_keys(Keys.TAB).perform()
        time.sleep(random.uniform(0.5, 1.0))

        active_element = driver.switch_to.active_element
        if active_element.get_attribute('type') == 'submit':
            logging.info("Successfully moved to login button")
            actions.send_keys(Keys.ENTER).perform()
        else:
            logging.error("Failed to move to login button")
            return

        time.sleep(5)

        # Navigate to Elenia Aina
        ainalab_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Elenia Aina"]'))
        )
        ainalab_button.click()
        logging.info("Navigated to Elenia Aina")

        time.sleep(3)

        # Navigate to Kulutustiedot
        protected_resource_url = 'https://asiakas.elenia.fi/kulutus'
        max_attempts = 10
        attempt = 0
        expected_title = "Elenia Aina - Kulutustiedot"
        
        while attempt < max_attempts:
            driver.get(protected_resource_url)
            time.sleep(2)  # Wait for page to start loading
            
            if driver.title == expected_title:
                logging.info(f"Opened kulutus. Page title: {driver.title}")
                break
            else:
                attempt += 1
                logging.info(f"Waiting for correct page title. Attempt {attempt}/{max_attempts}")
        
        if attempt == max_attempts:
            logging.error(f"Failed to load the correct page. Current title: {driver.title}")
            raise Exception("Failed to load the Kulutustiedot page")

        time.sleep(5)
        logging.info("Opened kulutus")
        logging.info(f"Page title: {driver.title}")

        def navigate_to_download_button():
            # Tab navigation to find the download button with specific text
            target_text = "Lataa kulutus tuntitasolla"
            for _ in range(10):
                actions.send_keys(Keys.TAB).perform()
                time.sleep(random.uniform(0.1, 0.3))
                active_element = driver.switch_to.active_element
                if active_element.text.strip() == target_text:
                    print(active_element)
                    # press enter
                    actions.send_keys(Keys.ENTER).perform()
                    break
            else:
                print(f'Element with text "{target_text}" not found after 10 TAB presses.')

        navigate_to_download_button()

        # Wait for download to start
        download_started = False
        for _ in range(30):  # Wait up to 30 seconds for download to start
            time.sleep(1)
            files = glob.glob(os.path.join(DOWNLOAD_DIR, "consumption_*.csv"))
            if files:
                download_started = True
                logging.info(f"Download started: {files[0]}")
                break

        if not download_started:
            logging.error("Download did not start within the expected time")
            raise Exception("Download did not start")

        # Wait for download to complete
        download_completed = False
        for _ in range(60):  # Wait up to 60 seconds for download to complete
            time.sleep(1)
            files = glob.glob(os.path.join(DOWNLOAD_DIR, "consumption_*.csv"))
            if files and not any(file.endswith('.crdownload') for file in files):
                download_completed = True
                logging.info(f"Download completed: {files[0]}")
                break

        if not download_completed:
            logging.error("Download did not complete within the expected time")
            raise Exception("Download did not complete")

        logging.info("Consumption data download process completed successfully")

    except Exception as e:
        logging.error(f"Error during navigation or download: {e}")
        if driver:
            logging.info(f"Current URL: {driver.current_url}")
            logging.info(f"Page source: {driver.page_source}")
        raise  # Re-raise the exception to stop the script

    finally:
        if driver:
            driver.quit()

def fetch_price_data():
    current_year = datetime.now().year
    start_date = f"{current_year}-01-01"
    end_date = f"{current_year}-12-31"
    url = f"https://www.vattenfall.fi/api/price/spot/{start_date}/{end_date}?lang=fi"
    
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        with open(PRICE_FILE, mode='w', newline='') as csv_file:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=';', quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            for row in data:
                row_with_comma_decimal = {key: str(value).replace('.', ',') if isinstance(value, float) else value for key, value in row.items()}
                writer.writerow(row_with_comma_decimal)
        
        logging.info(f"Price data saved to {PRICE_FILE}")
    except Exception as e:
        logging.error(f"Error fetching price data: {e}")

if __name__ == "__main__":
    fetch_consumption_data()
    time.sleep(2)  # Small delay between requests
    fetch_price_data()
