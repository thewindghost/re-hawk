import asyncio, aiohttp, os, sys
from colorama import Fore, init
init(autoreset=True)

# ─────────── Config ───────────
BASE_URL      = "https://targets.com/"
WORDLIST_FILE = "wordlists.txt"
EXTS          = ["txt","zip","xml","tar","tar.gz","bak","old"]
MAX_CONNS     = 20
BATCH_SIZE    = 500
BAR_WIDTH     = 42

# ─────── progress helpers ───────
progress_lock = asyncio.Lock()
done = 0

def paint_bar(done_cnt, total_cnt):
    pct  = int(done_cnt * 100 / total_cnt)
    fill = int(BAR_WIDTH * done_cnt / total_cnt)
    bar  = "=" * fill + "-" * (BAR_WIDTH - fill)
    sys.stdout.write(Fore.LIGHTMAGENTA_EX + f"\rScanning: |{bar}| {pct:3}% ({done_cnt}/{total_cnt})")
    sys.stdout.flush()

async def tick(total_cnt):
    global done
    async with progress_lock:
        done += 1
        paint_bar(done, total_cnt)

# ─────────── wordlist ───────────
async def load_wordlists(path):
    if not os.path.exists(path):
        print(Fore.RED + f"[!] File Not Found: {path}")
        return []
    with open(path, encoding="utf-8", errors="ignore") as f:
        return [line.strip() for line in f if line.strip()]

# ─────────── worker ────────────
async def check_url(sem, session, url, total_cnt):
    async with sem:
        try:

            async with session.get(url, allow_redirects=False) as resp:
                if resp.status == 200:
                    async with progress_lock:
                        sys.stdout.write('\r\033[2K')
                        sys.stdout.flush()
                        print(Fore.GREEN + f"🟢 Found: {url} (200)")

        except Exception:
            pass
        finally:

            await tick(total_cnt)

# ─────────── main ──────────────
async def main():
    names = await load_wordlists(WORDLIST_FILE)
    if not names:
        return

    targets = [f"{BASE_URL.rstrip('/')}/{dirname}.{extension_file}"
               for dirname in names for extension_file in EXTS]
    total_cnt = len(targets)
    paint_bar(0, total_cnt)

    sem  = asyncio.Semaphore(MAX_CONNS)
    conn = aiohttp.TCPConnector(limit=MAX_CONNS, keepalive_timeout=60)
    timeout = aiohttp.ClientTimeout(total=None, connect=5)

    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as sess:
        for i in range(0, total_cnt, BATCH_SIZE):
            batch = targets[i:i+BATCH_SIZE]
            await asyncio.gather(
                *(check_url(sem, sess, url, total_cnt) for url in batch),
                return_exceptions=True
            )

    print("\n" + Fore.LIGHTBLUE_EX + "✔️  Scan completed.")

if __name__ == "__main__":       
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n" + Fore.LIGHTCYAN_EX + "🛑 Scan interrupted by user. Exiting cleanly.")
        sys.exit(0)
