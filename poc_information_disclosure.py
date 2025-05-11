import asyncio
import aiohttp
import os
from colorama import init, Fore

init(autoreset=True)

base_url = "https://targets.com/"
payloads_file = "wordlists.txt"
file_extensions = ["txt", "zip", "html", "php", "aspx", "tar", "tar.gz", "bak", "old"]
MAX_CONNS = 20
BATCH_SIZE = 500

async def load_wordlists(path):
    if os.path.exists(path):
        with open(path) as f:
            return [line.strip() for line in f if line.strip()]
    print(Fore.RED + f"[!] File Not Found: {path}")
    return []

async def check_url(sem, session, dirname, ext):
    url = f"{base_url.rstrip('/')}/{dirname}.{ext}"
    async with sem:
        try:
            async with session.get(url, allow_redirects=False) as resp:
                if resp.status == 200:
                    print(Fore.GREEN + f"[+] Found: {dirname}.{ext} (200)")
        except Exception:

            pass

async def main():
    names = await load_wordlists(payloads_file)
    if not names:
        return

    sem = asyncio.Semaphore(MAX_CONNS)
    connector = aiohttp.TCPConnector(limit=MAX_CONNS, keepalive_timeout=60)
    timeout = aiohttp.ClientTimeout(total=None, connect=5)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:

        jobs = [(name, ext) for name in names for ext in file_extensions]

        for i in range(0, len(jobs), BATCH_SIZE):
            batch = jobs[i : i + BATCH_SIZE]    
            tasks = [
                check_url(sem, session, name, ext)
                for name, ext in batch
            ]

            await asyncio.gather(*tasks, return_exceptions=True)

        print(Fore.CYAN + "🟢 Scan completed.")

if __name__ == "__main__":
    asyncio.run(main())
