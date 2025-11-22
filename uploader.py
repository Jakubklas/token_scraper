from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
import logging
import os

from config import *
from cookie_scrape import Cookies

logger = logging.getLogger(__name__)

class FileUploader:
    def __init__(self):
        self.driver = None
        self.url = CAPACITY_UPLOADER_URL

    def setup_driver(self, cookies_list):
        """Initialize Chrome driver and load cookies."""
        logger.info("Setting up Chrome driver...")
        self.driver = webdriver.Chrome()

        # First navigate to base domain to set cookies
        logger.info("Navigating to base domain...")
        self.driver.get("https://logistics.amazon.co.uk")

        # Load cookies
        logger.info("Loading cookies...")
        logger.info(f"Cookies list: {[c for c in cookies_list]}")

        if not cookies_list:
            logger.error("No valid cookies found!")
            return False

        for cookie in cookies_list:
            # Only add cookies that match the current domain
            cookie_domain = cookie.get('domain', '')
            current_domain = self.driver.current_url

            # Skip cookies from different domains
            if cookie_domain and not ('amazon.co.uk' in cookie_domain or 'logistics.amazon.co.uk' in cookie_domain):
                logger.debug(f"Skipping cookie {cookie.get('name')} from domain {cookie_domain}")
                continue

            try:
                # Remove keys that Selenium doesn't accept
                cookie_dict = {
                    'name': cookie.get('name', ''),
                    'value': cookie.get('value', ''),
                    'path': cookie.get('path', '/'),
                }

                # Only add domain if it matches current page
                if cookie_domain and 'amazon.co.uk' in cookie_domain:
                    cookie_dict['domain'] = cookie_domain

                if 'expiry' in cookie:
                    cookie_dict['expiry'] = cookie['expiry']

                logger.info(f"Adding cookie {cookie.get('name', 'unnamed')} for domain {cookie_domain}")
                self.driver.add_cookie(cookie_dict)

            except Exception as e:
                logger.warning(f"Failed to add cookie {cookie.get('name', 'unnamed')}: {e}")

        # Navigate to actual upload page with cookies applied
        logger.info("Navigating to upload page...")
        self.driver.get(self.url)
        logger.info("✓ Cookies loaded and authenticated")
        return True

    def upload_file(self, upload_type, file_path):
        """
        Upload a single file to the capacity uploader.

        Args:
            file_path: Absolute path to the CSV file
        """
        try:
            logger.info(f"Uploading file: {file_path}")

            # Wait for page to load
            wait = WebDriverWait(self.driver, 4)

            # Select file type dropdown (Amazon custom dropdown)
            logger.info(f"Selecting upload type: {upload_type}")

            # Click the dropdown to open it (adjust the ID/selector if needed)
            dropdown_trigger = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-action='a-dropdown-button']")))
            dropdown_trigger.click()

            # Wait for dropdown to open and click the option
            time.sleep(0.5)
            option = wait.until(EC.element_to_be_clickable((
                By.XPATH,
                f"//a[@class='a-dropdown-link' and contains(text(), '{upload_type}')]"
            )))
            option.click()
            logger.info(f"✓ Selected: {upload_type}")

            # Check if file exists first
            if not os.path.exists(file_path):
                logger.error(f"File does not exist: {file_path}")
                return False

            # Find the file input by ID
            logger.info("Locating file input element...")
            file_input = wait.until(EC.presence_of_element_located((By.ID, "flexuploadS3File")))

            # Send file path directly
            abs_path = os.path.abspath(file_path)
            logger.info(f"Selecting file: {abs_path}")
            logger.info(f"File exists: {os.path.exists(abs_path)}")

            file_input.send_keys(abs_path)

            # Check if value was set
            input_value = file_input.get_attribute('value')
            logger.info(f"Input value after send_keys: {input_value}")

            # Wait for file to be processed
            time.sleep(1)

            # Verify file name appears in display
            file_name_display = self.driver.find_element(By.ID, "gsfUploaderFileName")
            logger.info(f"File display shows: {file_name_display.text}")

            # Also check the input value again
            input_value_after = file_input.get_attribute('value')
            logger.info(f"Input value after wait: {input_value_after}")

            if "Choose a file" in file_name_display.text and not input_value_after:
                logger.error("File was not selected! Input value is empty.")
                logger.info("Browser will stay open for 30 seconds so you can inspect...")
                time.sleep(30)
                return False

            # Click "Upload File" button - click the button element, not the span
            logger.info("Clicking 'Upload File' button...")
            upload_button = wait.until(EC.element_to_be_clickable((By.ID, "flexUploadS3Btn")))

            # Use JavaScript click to avoid interception
            self.driver.execute_script("arguments[0].click();", upload_button)
            logger.info("Upload button clicked")

            # Wait for upload to complete and verify success message
            logger.info("Waiting for upload to complete...")

            try:
                # Wait for the specific success message with longer timeout
                success_msg = WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        "//*[contains(text(), 'Processor has been notified successfully.')]"
                    ))
                )
                logger.info(f"✓ Upload successful: {success_msg.text}")
                logger.info(f"✓ File uploaded: {file_path}")
                return True

            except Exception as e:
                logger.error(f"Failed to confirm upload success: {e}")
                logger.error("Did not see 'Processor has been notified successfully.' message")
                return False

        except Exception as e:
            logger.error(f"Failed to upload {file_path}: {e}")
            return False

    def upload_batch(self, files_list):
        """
        Upload multiple files sequentially.

        Args:
            files_list: List of tuples (upload_type, file_path)
        """
        results = []
        for idx, (upload_type, file_path) in enumerate(files_list, 1):
            logger.info(f"Processing file {idx}/{len(files_list)}")
            success = self.upload_file(upload_type, file_path)
            results.append({"file": file_path, "success": success})

            # Reload page between uploads to reset the form
            if idx < len(files_list):
                logger.info("Refreshing page for next upload...")
                self.driver.get(self.url)
                time.sleep(3)  # Wait for page to load

        return results

    def close(self):
        """Close the browser."""
        if self.driver:
            logger.info("Closing browser...")
            time.sleep(2)
            self.driver.quit()


if __name__ == "__main__":
    uploader = FileUploader()
    cc = Cookies(CAPACITY_UPLOADER_URL)

    try:
        # Get the cookies
        cookies_list = cc.main(as_string=False)

        # Setup driver and load cookies
        if not uploader.setup_driver(cookies_list):
            logger.error("Failed to setup driver. Exiting...")
            exit(1)

        # Example: Upload single file
        # uploader.upload_file("Exclusive Offer Allocation", r"C:\path\to\your\file.csv")

        # Example: Upload multiple files (list of tuples to support duplicate upload types)
        files_to_upload = [
            ("Exclusive Offer Allocation",  r"C:\Users\jklas\Downloads\file_number_1.csv"),
            ("Amzl_Dph_Override",           r"C:\Users\jklas\Downloads\file_number_2.csv"),
            ("Amzl_Volume_Override",        r"C:\Users\jklas\Downloads\file_number_3.csv"),
            ("Demand",                      r"C:\Users\jklas\Downloads\file_number_4.csv"),
            ("Demand",                      r"C:\Users\jklas\Downloads\file_number_5.csv")
        ]

        results = uploader.upload_batch(files_to_upload)

        # Print results
        for result in results:
            status = "✓" if result["success"] else "✗"
            logger.info(f"{status} {result['file']}")

        # For now, just pause to see the page
        logger.info("Browser ready. Waiting 10 seconds before closing...")
        time.sleep(10)

    finally:
        uploader.close()