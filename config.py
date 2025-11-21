import os
from datetime import datetime

URL = "https://logistics.amazon.co.uk/internal/scheduling/dsps"

# User Downloads
LOGIN = os.getlogin()
DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")
COOKIES_FILE = f"mdw_cookie_{datetime.now().strftime("%Y-%m-%d")}.pkl"
COOKIES_PATH = os.path.join(DOWNLOADS, COOKIES_FILE)