import boto3
import pandas as pd
from datetime import datetime
import getpass
import pickle
import time
import requests
import json
import os
from collections import defaultdict
from src.config.settings import *

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options

class API():
    def __init__(self, url, driver, cookies_file, local_file, file_name, cookies=None, routes=None):
        self.url = url
        self.cookies = cookies
        self.driver = driver
        self.cookies_file = cookies_file
        self.local_file = local_file
        self.routes = routes
        self.file_name = file_name
        self.session = requests.Session()
        self.is_headless = False
    
    def enable_GUI(self):
        """Show the browser window by maximizing it"""
        try:
            self.driver.set_window_position(800, 400)
            # self.driver.maximize_window()
            print('PING: Shows Window')
        except Exception as e:
            print(f"Error maximizing window: {e}")
        return

    def disable_GUI(self):
        """Hide the browser window by minimizing it"""
        try:
            self.driver.set_window_position(-32000, -32000)
            self.driver.minimize_window()
            print('PING: Minimizes Window')
        except Exception as e:
            print(f"Error minimizing window: {e}")
        return
    
    def authenticate(self):
        self.driver.get(self.url)

        wait = WebDriverWait(self.driver, timeout=999999)
        wait.until_not(EC.url_contains("midway-auth.amazon.com"))
                                   
        return 
    
    def save_cookies(self):
        self.cookies_file = cookies_file
        cookies = self.driver.get_cookies()
        
        # Extend expiry time for each cookie by 24 hours
        for cookie in cookies:
            if 'expiry' in cookie:
                cookie['expiry'] = int(cookie['expiry']) + (60 * 60 * 24)
                print(f"Extended cookie {cookie['name']} expiry to: {datetime.fromtimestamp(cookie['expiry'])}")
        
        self.cookies = cookies

        directory = os.path.dirname(self.cookies_file)
        os.makedirs(directory, exist_ok=True)
        
        with open(self.cookies_file, 'wb') as file:
            pickle.dump(self.cookies, file)
            print(f"Successfully saved cookies to {cookies_file}")
            
        return

    def refresh_cookies(self):
        try:
            # Load existing cookies
            with open(self.cookies_file, 'rb') as f:
                existing_cookies = pickle.load(f)
                
            # Update the expiry times
            for cookie in existing_cookies:
                if 'expiry' in cookie:
                    cookie['expiry'] = int(datetime.now().timestamp()) + (60 * 30) # Add 30 minutes to expiry
                    
            self.cookies = existing_cookies
            
            # Save updated cookies
            with open(self.cookies_file, 'wb') as file:
                pickle.dump(self.cookies, file)
                print("Successfully refreshed cookies")
                
        except Exception as e:
            print(f"Error refreshing cookies: {str(e)}")
            self.send_chime_alert()
            self.driver.quit()

    def refresh_authentication(self):
            """
            Periodically visit the authentication page to refresh the session cookies.
            """
            try:
                print("Refreshing authentication (heartbeat)...")
                # Navigate to the midway authentication page.
                # Replace the URL below with the actual midway URL used by your authentication flow.
                midway_url = "https://midway-auth.amazon.com/login"
                self.driver.get(midway_url)
                
                # Wait until the page loads. Adjust the condition as needed.
                wait = WebDriverWait(self.driver, timeout=15)
                wait.until(EC.url_contains("midway-auth.amazon.com"))
                
                # After the page loads, refresh cookies (they should now be updated).
                self.save_cookies()
                print("Authentication refreshed successfully.")
            except Exception as e:
                print(f"Error during authentication refresh: {str(e)}")
                self.send_chime_alert()
                self.driver.quit()

    def load_cookies(self):
        # Load cookies
        try:
            with open(self.cookies_file, 'rb') as f:
                loaded_cookies = pickle.load(f)
                self.cookies = loaded_cookies
        except (FileNotFoundError, pickle.UnpicklingError) as e:
            print(f"Error loading cookies: {str(e)}")
            return False
            
        # First visit the target domain
        domain = self.url.split("//")[1].split("/")[0]
        self.driver.get(f"https://{domain}")
        self.disable_GUI()
        time.sleep(1)

        cookie_load_errors = 0
        for cookie in loaded_cookies:
            try:
                # Create clean cookie dictionary
                cookie_dict = {
                    'name': cookie['name'],
                    'value': cookie['value'],
                    'path': '/'
                }
                
                if 'expiry' in cookie:
                    cookie_dict['expiry'] = int(cookie['expiry'])
                if 'secure' in cookie:
                    cookie_dict['secure'] = cookie['secure']
                    
                self.driver.add_cookie(cookie_dict)
                
                # Only print expiry if it exists
                if 'expiry' in cookie:
                    print(f"Added cookie: {cookie['name']} Expiry: {datetime.fromtimestamp(cookie['expiry'])} hours")
                else:
                    print(f"Added cookie: {cookie['name']} (no expiry)")
                
            except Exception as e:
                print(f"Error adding cookie {cookie['name']}: {str(e)}")
                cookie_load_errors += 1

        # Only send alert and quit if too many cookies failed to load
        if cookie_load_errors > len(loaded_cookies) // 2:  # If more than half of cookies failed
            print("Too many cookies failed to load. Session might be invalid.")
            self.send_chime_alert()
            self.driver.quit()
            return False

        return True

   
    def get_data(self):
        self.routes = defaultdict(list)
        
        headers = {
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "If-Modified-Since": "Sat, 1 Jan 2000 00:00:00 GMT"
        }
        
         # Convert cookies list to dictionary format
        cookies_dict = {}
        for cookie in self.cookies:
            cookies_dict[cookie.get('name')] = cookie.get('value')
        
        for _, row in control_table.iterrows():
            pull_station = row["Station"]
            pull_date = datetime.now() #strptime('2025-01-20', "%Y-%m-%d") #'2025-01-20'
            pull_service_area = row["area_id"]
            url_date = pull_date.strftime("%Y-%m-%d")

            params = {
                "serviceAreaId": pull_service_area,
                "providerDemandType": "Forecast",   
                "date": url_date,
                "_": int(datetime.now().timestamp())
                }

            response = requests.get(url_template, headers=headers, params=params, cookies=cookies_dict)
            response.raise_for_status()
            
            if response.status_code == 200:
                data = response.json()

                for service_type_id, service_data in data.items():
                    service_type = service_data.get("serviceTypeName")
                    provider_demand_list = service_data.get("providerDemandList", [])

                    counter = 0
                    for demand in provider_demand_list:
                        capacity_type = demand.get("capacityType")
                        start_time = datetime.fromtimestamp(demand.get("startTime") / 1000)
                        wave = demand.get("waveGroupId")
                        duration = demand.get("durationInMinutes")
                        scheduled = demand.get("requiredQuantity")
                        accepted = demand.get("scheduledQuantity")

                        if capacity_type == "CSP":
                            key = f"{pull_station}-{service_type}-{wave}-{start_time}-{duration}"
                            self.routes[key].append({
                                "station": pull_station,
                                "service_type": service_type,
                                "wave": wave,
                                "start_time": start_time,
                                "duration": duration,
                                "scheduled": scheduled,
                                "accepted": accepted
                            })
                    if counter == 10:
                        break
        print('Status Response:')
        print(response.status_code)
        return response.status_code
    
    def save_file_locally(self):
        try:
            records = []
            
            for key, route_list in self.routes.items():
                for route in route_list:
                    record = {
                        "Last_Refresh": pd.Timestamp(datetime.now()).floor('min'),  
                        "Block_Date_Time": pd.Timestamp(route["start_time"]).floor('min'),
                        "Station": route["station"],
                        "ServiceType": route["service_type"],
                        "Cycle": route["wave"],
                        "Duration": route["duration"],
                        "Scheduled": route["scheduled"],
                        "Accepted": route["accepted"]
                    }
                    records.append(record)
            
            # Create and modify df
            df = pd.DataFrame(records)
            df = df.sort_values('Block_Date_Time')
            
            df_co = pd.DataFrame(records)
            df_co = df_co.rename(columns={'Last_Refresh': 'Runtime'})
            df_co['OFDDate'] = df_co['Block_Date_Time'].dt.date
            df_co['Pending'] = df_co['Scheduled'] - df_co['Accepted'] 
            df_co['Fill'] = round(df_co['Accepted'] / df_co['Scheduled'], 1)
            df_co = df_co.query('Pending > 0')
            df_co['Next Wave Start'] = (df_co['Block_Date_Time'] + pd.Timedelta(minutes=15)).dt.time

            columns_order = ['Runtime', 'OFDDate', 'Station', 'Cycle', 'ServiceType', 
                            'Scheduled', 'Accepted', 'Pending', 'Fill', 'Next Wave Start'] 
            df_co = df_co[columns_order]

            csv_path_1 = os.path.join(self.local_file, 'CO_Format_Pull.csv')
            csv_path_2 = os.path.join(self.local_file, f'{self.file_name}.csv')
            parquet_path = os.path.join(self.local_file, f'{self.file_name}.parquet')
            
            df_co.to_csv(csv_path_1, index=False)
            df.to_csv(csv_path_2, index=False)
            df.to_parquet(parquet_path, index=False)
            print(f"Files successfully saved to:\n{csv_path_1}\n{csv_path_2}\n{parquet_path}")
            print(df.head(3))
            
        except Exception as e:
            print(f"Error saving files: {str(e)}")
    
    def send_chime_alert(self):
        webhook_url = "https://hooks.chime.aws/incomingwebhooks/5da7cfc0-b439-43ae-a10e-abecc8e49595?token=VG00WlNCRG98MXxBcThELU9ZOG16ZGdJYzVCTDhyZWg1WmUwUEJZejBBZGJ6emh1cnFpOThr"

        message = "@Present Members \n ALERT: The Fill Report Failed. Re-authentication is necessary."
        
        headers = {'Content-Type': 'application/json'}
        payload = {'Content': message}
        
        response = requests.post(webhook_url, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 200:
            print("Chime message sent.")
        else:
            print(f"Failed to send Chime message. Status code: {response.status_code}")
        return