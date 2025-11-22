import os
from datetime import datetime

SUI_URL = "https://logistics.amazon.co.uk/internal/scheduling/dsps/api/getProviderDemandData"
CAPACITY_UPLOADER_URL = "https://logistics.amazon.co.uk/internal/capacity/uploader"

# User Downloads
LOGIN = os.getlogin()
DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")
COOKIES_FILE = f"mdw_cookie_{datetime.now().strftime("%Y-%m-%d")}.pkl"
COOKIES_PATH = os.path.join(DOWNLOADS, COOKIES_FILE)
SITE_MAP = r"\\ant\dept-eu\TBA\UK\Business Analyses\CentralOPS\Scheduling\UK\FlexData\UKManagedMappings.csv"
SAVE_PATH = os.path.join(DOWNLOADS, "scrape.csv")
