import requests
from datetime import datetime
import json

from cookie_scrape import Cookies

def main(url, cookies):
    try:
        response = requests.get(
            url=url,
            headers={
                "Cookie": cookies,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
            },
            params={
                "utcStartDateTime": "",
                "utcEndDateTime": "",
                "fileType": "",
                "uploadedBy": "rikenkup",
                "token": "",
                "_": int(datetime.now().timestamp() * 1000)
            }
        )

        print()
        if response.status_code == 200:
            print(f"Success. Status code = {200}")
            for i in response.json()["statusRecordList"]:                
                print(i)
                print()

        else:
            print(f"Failed. Status code = {response.status_code}")
            print(response.text[:300])

    except Exception as e:
        print(f"Failed due to: {e}")



if __name__ == "__main__":
    # url = "https://logistics.amazon.co.uk/getBannerNotifications?route=/internal/capacity/uploader"
    # url= "https://logistics.amazon.co.uk/internal/capacity/api/checkUpdateAuth?_=1763809042489"
    url = "https://logistics.amazon.co.uk/internal/capacity/api/statusRecordPage"
    cc = Cookies(url)

    main(url, cc.main())