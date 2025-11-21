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
        
    def unpack(self, as_string=True):
        """
        Unpacks saved cookies.

        Args:
            as_string: If True, returns formatted Cookie header string.
                      If False, returns list of cookie dictionaries.
        """
        try:
            with open(COOKIES_PATH, "rb") as f:
                cookies = pickle.load(f)
                if cookies:
                    logger.info("Saved cookies found")
                    if as_string:
                        # Format all cookies as "name=value; name2=value2"
                        cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
                        return cookie_string
                    else:
                        return cookies
                else:
                    logger.info(f"No cookies found in the {DOWNLOADS}")
                    return None

        except Exception as e:
            logger.error(f"Error: {e}")
            return None



if __name__ == "__main__":
    cc = Cookies(URL)
    max_attempts = 1
    retries = 0

    while retries <= max_attempts:
        # Get raw cookies for validation
        cookies_list = cc.unpack(as_string=False)
        try:
            if cookies_list:
                # Check if all cookies are valid
                all_valid = all(cc.is_valid(cookie) for cookie in cookies_list if "expiry" in cookie)
                if all_valid or not any("expiry" in cookie for cookie in cookies_list):
                    logger.info(f"Valid cookies found. Total: {len(cookies_list)}")
                    break
                else:
                    logger.info("Cookies expired, re-authenticating...")
                    cc.scrape_and_save(URL)
            else:
                logger.info("No cookies found, authenticating...")
                cc.scrape_and_save(URL)
        except Exception as e:
            logging.error(f"Issues loading cookies: {e}")
            cc.scrape_and_save(URL)
            retries += 1 


    