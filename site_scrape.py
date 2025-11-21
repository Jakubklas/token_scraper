import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import logging

from config import *
from cookie_scrape import Cookies

logger = logging.getLogger(__name__)

class SiteScraper:
    def __init__(self, url=URL, site_map=SITE_MAP):
        self.url = url
        self.site_map = site_map

    def get_sites(self):
        """Returns a list of managed sites and service areas"""
        try:
            logger.info("Fetching & renaming sites...")
            sites = pd.read_csv(self.site_map)
            for c in sites.columns:
                sites.rename(columns={c: c.lower().replace(" ", "_")}, inplace=True)
            logger.info(f"Found {sites.shape[0]} site mappings.")
            return sites.to_dict(orient="records")

        except Exception as e:
            logger.error(f"Failed to fetch the site mappings. Is the VPN on? Error {e}")

    def scrape_site_data(self, area_id, num_days=7, cookie=None):
        """
        Scrapes provider demand data for given service area.
        """
        try:
            dates_list = [(datetime.today() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(num_days)]
            dates_param = json.dumps(dates_list)

            response = requests.get(
                url=self.url,
                headers={
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                    "Cookie": cookie,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
                },
                params={
                    "dates": dates_param,
                    "serviceAreaId": area_id,
                    "providerDemandType": "Forecast",
                    "_": int(datetime.now().timestamp() * 1000)
                }
            )

            if response.status_code == 200:
                logger.info(f"Response {response.status_code}. Successful scrape")
                try:
                    data = response.json()
                    return data
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.error(f"Response preview: {response.text[:50]}")
                    return None
            else:
                logger.error(f"Response {response.status_code}. Failed")
                logger.error(f"Response preview: {response.text[:50]}")
                return None

        except Exception as e:
            logger.error(f"Failed to scrape site data: {e}")
        



if __name__ == "__main__":
    scraper = SiteScraper(URL)
    cc = Cookies(URL)

    cookies = cc.unpack()
    sites = scraper.get_sites()

    data = []
    for idx, site in enumerate(sites):
        if not site["station"].startswith("D"):
            continue
        logger.info(f"Scraping site {idx+1}: {site["station"]}")
        station_data = scraper.scrape_site_data(site["area_id"], num_days=7, cookie=cookies)
        data.append(station_data)

    if data:
        # Flatten: [{date: [records]}, ...] -> [{date, ...record}, ...]
        records = [
            {"date": date, **record}
            for site_data in data
            if site_data
            for date, recs in site_data.items()
            for record in recs
        ]
        df = pd.DataFrame(records)
        df = df[df["capacityType"]=="CSP"]
        df['startTime'] = pd.to_datetime(df['startTime'], unit='ms')

        logger.info(f"DataFrame shape: {df.shape}")
        print(df[['date', 'startTime', 'requiredQuantity', 'scheduledQuantity', 'waveGroupId']].head(20))
        df.to_csv(SAVE_PATH, index=False)
    
    else:
        logger.error("No data retrieved")