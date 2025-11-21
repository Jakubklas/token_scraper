import requests
from config import *
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import pickle
import time

# Configure logging to emit to terminal
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

class Cookies:
    def __init__(self, url=URL):
        self.url = url

    def scrape_and_save(self, url):
        """Prompts authentication and saves session cookies."""
        
        driver = webdriver.Chrome()

        try:
            logger.info(f"Opening {self.url}...")
            driver.get(self.url)

            # Wait for user to manually log in
            logger.info("\nPlease log in manually in the browser window.")
            logger.info("Once you're successfully logged in and can see the scheduling page,")
            logger.info("press Enter here to save the cookies...")
            input()

            # Get all cookies
            cookies = driver.get_cookies()

            # Save cookies to file
            with open(COOKIES_PATH, 'wb') as f:
                pickle.dump(cookies, f)

            logger.info(f"\nCookies saved successfully to: {DOWNLOADS}")
            logger.info(f"Total cookies saved: {len(cookies)}")

        except Exception as e:
            logger.error(f"Error: {e}")

        finally:
            # Close the browser
            logger.info("\nClosing browser...")
            time.sleep(1)
            driver.quit()

    def is_valid(self, cookie):
        """Checks whether cookie is valid or expired."""
        if "expiry" in cookie.keys():
            expiry = cookie["expiry"]  # Already a Unix timestamp
            current_timestamp = datetime.now().timestamp()
            if expiry >= current_timestamp:
                return True
            return False
        else:
            logging.info("No expiry information found in the cookie.")
            return False
        
    def unpack(self):
        """
        Unpacks & returns still valid saved cookies if
        available & not expired.
        """
        try:
            with open(COOKIES_PATH, "rb") as f:
                cookies = pickle.load(f)
                for idx, cookie in enumerate(cookies):
                    if "session-token" not in cookie.values():
                        continue
                    logger.info("Saved cookies found")
                    return cookie
            logger.info(f"No cookies found in the {DOWNLOADS}")       
        
        except Exception as e:
            logger.error(f"Error: {e}")



if __name__ == "__main__":
    cc = Cookies(URL)
    max_attempts = 1
    retries = 0

    while retries <= max_attempts:
        cookie = cc.unpack()
        try:
            if cc.is_valid(cookie):
                logger.info(f"Valid cookies found for domain '{cookie["domain"]}'.")
                break
            else:
                cc.scrape_and_save(URL)
        except Exception as e:
            logging.error(f"Issues loading cookies: {e}")
            cc.scrape_and_save(URL)
            retries += 1 


    