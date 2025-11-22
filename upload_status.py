import requests
from datetime import datetime, timedelta
import time
import logging

from config import *
from cookie_scrape import Cookies

logger = logging.getLogger(__name__)

def get_upload_status(url, upload_type, filename, cookies):
    try:
        response = requests.get(
            url=url,
            headers={
                "Cookie": cookies,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
            },
            params={
                "utcEndDateTime": "",
                "utcStartDateTime": "",
                "fileType": upload_type,
                "fileName": filename,
                "uploadedBy": "",
                "token": "",
                "_": int(datetime.now().timestamp() * 1000)
            }
        )

        if response.status_code == 200:
            logger.info(f"Verifying upload status of file")
            try:
                status = response.json()["statusRecordList"]

                # Filter for recent uploads (last 30 minutes)
                cutoff_time = datetime.now() - timedelta(minutes=300)
                status_filtered = []

                for s in status:
                    upload_time = datetime.fromtimestamp(s["uploadedDateTime"] / 1000)
                    if upload_time >= cutoff_time:
                        status_filtered.append(s)

                return status_filtered[0] if status_filtered else status
            except Exception as e:
                logger.error(f"Issues finding status...{e}")
                


        else:
            logger.info(f"Failed to verify upload status. No recent records found.")

    except Exception as e:
        print(f"Failed due to: {e}")


def get_processed_status(url, upload_type, filename, cookies):
    """Queries for status until it's uploaded or processed"""
    max_attempts = 5
    attempts = 0

    while attempts < max_attempts:
        status = get_upload_status(url, upload_type, filename, cookies)
        if not status:
            logger.warning("No status returned, waiting...")
            time.sleep(1)
            attempts += 1
            continue

        current_status = status.get("status", "")
        if current_status not in ["PROCESSING", "UPLOADING"]:
            break

        logger.info(f"File {status.get('fileName', filename)} still processing. Status: {current_status}")
        time.sleep(2)
        attempts += 1

    logger.info(f"File upload status: {status.get('status', '')}, Message: {status.get('message', '')}")
    return status


if __name__ == "__main__":
    # url = "https://logistics.amazon.co.uk/getBannerNotifications?route=/internal/capacity/uploader"
    # url= "https://logistics.amazon.co.uk/internal/capacity/api/checkUpdateAuth?_=1763809042489"
    url = "https://logistics.amazon.co.uk/internal/capacity/api/statusRecordPage"
    cc = Cookies(url)

    status = get_upload_status(STATUS_URL, "Exclusive Offer Allocation", "file_number_1", cc.main())

    print(status)