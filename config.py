import os
from datetime import datetime

# URL = "https://logistics.amazon.co.uk/internal/scheduling/dsps"
URL = "https://logistics.amazon.co.uk/internal/scheduling/dsps/api/getProviderDemandData"
# URL = "https://logistics.amazon.co.uk/internal/scheduling/dsps/api/getProviderDemandData?dates=%5B%222025-11-22%22%2C%222025-11-23%22%2C%222025-11-24%22%2C%222025-11-25%22%2C%222025-11-26%22%2C%222025-11-27%22%2C%222025-11-28%22%5D&serviceAreaId=e43f8832-a501-4f67-a244-6b5b2017ac15&providerDemandType=Forecast&_=1763764418618"

# User Downloads
LOGIN = os.getlogin()
DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")
COOKIES_FILE = f"mdw_cookie_{datetime.now().strftime("%Y-%m-%d")}.pkl"
COOKIES_PATH = os.path.join(DOWNLOADS, COOKIES_FILE)
SITE_MAP = r"\\ant\dept-eu\TBA\UK\Business Analyses\CentralOPS\Scheduling\UK\FlexData\UKManagedMappings.csv"
SAVE_PATH = os.path.join(DOWNLOADS, "scrape.csv")
