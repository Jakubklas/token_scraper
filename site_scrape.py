import asyncio
import aiohttp
import json
import pandas as pd
from datetime import datetime, timedelta
import logging

from config import *
from cookie_scrape import Cookies

logger = logging.getLogger(__name__)

class SiteScraper:
    def __init__(self, url=URL, site_map=SITE_MAP, num_days=7):
        self.url = url
        self.site_map = site_map
        self.counter = 0
        self.dates_list = [(datetime.today() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(num_days)]
        self.data = []

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
            return []

    async def scrape_site_data(self, session, site, semaphore):
        """
        Scrapes provider demand data for given service area.
        """
        async with semaphore:
            try:
                self.counter += 1
                logger.info(f"Scraping site {self.counter}: {site['station']}")

                async with session.get(
                    self.url,
                    params={
                        "dates": json.dumps(self.dates_list),
                        "serviceAreaId": site["area_id"],
                        "providerDemandType": "Forecast",
                        "_": int(datetime.now().timestamp() * 1000)
                    }
                ) as response:

                    if response.status == 200:
                        logger.info(f"Response {response.status}. Successful scrape")
                        try:
                            data = await response.json()
                            return data
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse JSON response: {e}")
                            text = await response.text()
                            logger.error(f"Response preview: {text[:50]}")
                            return None
                    else:
                        logger.error(f"Response {response.status}. Failed")
                        text = await response.text()
                        logger.error(f"Response preview: {text[:50]}")
                        return None

            except Exception as e:
                logger.error(f"Failed to scrape site data {site["station"]}: {e}")
                return None

    async def scrape_all(self, sites, cookie, max_concurrent=15):
        """Scrapes all sites concurrently with rate limiting."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async with aiohttp.ClientSession(
            headers={
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Cookie": cookie,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
            }
        ) as session:
            tasks = [self.scrape_site_data(session, site, semaphore) for site in sites]
            results = await asyncio.gather(*tasks)
            return [r for r in results if r is not None]
            


async def main():
    scraper = SiteScraper(URL, num_days=7)
    cc = Cookies(URL)

    cookies = cc.main()
    sites = scraper.get_sites()

    # Filter sites starting with "D"
    sites = [site for site in sites if site.get("station", "").startswith("D")]
    logger.info(f"Filtered to {len(sites)} sites starting with 'D'")

    # Scrape all sites asynchronously
    all_data = await scraper.scrape_all(sites, cookies, max_concurrent=15)

    if all_data:
        # Flatten: [{date: [records]}, ...] -> [{date, ...record}, ...]
        records = [
            {"date": date, **record}
            for site_data in all_data
            if site_data
            for date, recs in site_data.items()
            for record in recs
        ]
        df = pd.DataFrame(records)
        df = df[df["capacityType"] == "CSP"]
        df['startTime'] = pd.to_datetime(df['startTime'], unit='ms')

        logger.info(f"DataFrame shape: {df.shape}")
        print(df[['date', 'startTime', 'requiredQuantity', 'scheduledQuantity', 'waveGroupId']].head(20))
        df.to_csv(SAVE_PATH, index=False)
        logger.info(f"Data saved to {SAVE_PATH}")
    else:
        logger.error("No data retrieved")


if __name__ == "__main__":
    asyncio.run(main())