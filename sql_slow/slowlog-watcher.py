import time
import re
import os
import requests
from datetime import datetime
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler

WEBHOOK_URL = "https://discordapp.com/api/webhooks/1398857139232964608/IgYnfQDKAbmomLLcUVIP5JK2b74KT16CNZU77F0TnqeiBuFRdHsv_iNQMbdgwQw6vCqH"
LOG_FILE_PATH = "/var/log/mysql/mysql-slow.log"
POSITION_FILE = "/var/log/mysql/.slowlog_pos"
LOG_OUTPUT = "/var/log/slowlog-watcher.log"
SLOW_QUERY_THRESHOLD = 8.0  # seconds

def log(msg):
    with open(LOG_OUTPUT, "a") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

def get_line_count(filepath):
    try:
        with open(filepath, 'r') as f:
            return sum(1 for _ in f)
    except Exception as e:
        log(f"[ERROR] Gagal hitung jumlah baris log: {e}")
        return 0

def load_last_position():
    if os.path.exists(POSITION_FILE):
        try:
            pos = int(open(POSITION_FILE).read().strip())
            current_line_count = get_line_count(LOG_FILE_PATH)
            if pos > current_line_count:
                log("[WARN] Posisi lebih besar dari jumlah baris, log kemungkinan di-rotate. Reset ke 0.")
                return 0
            return pos
        except Exception as e:
            log(f"[ERROR] Gagal baca posisi baris terakhir: {e}")
    return 0

def save_last_position(line_number):
    with open(POSITION_FILE, "w") as f:
        f.write(str(line_number))

def send_to_discord(log_block):
    prefix = f"**⚠️ Slow Query Detected (> {SLOW_QUERY_THRESHOLD}s):**\n```sql\n"
    postfix = "\n```"
    payload = {"content": f"{prefix}{log_block}{postfix}"}
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        if response.status_code not in [200, 204]:
            log(f"[ERROR] Gagal kirim Discord: {response.status_code} - {response.text}")
        else:
            log(f"[OK] Berhasil kirim slow query ke Discord")
    except Exception as e:
        log(f"[ERROR] Exception kirim ke Discord: {str(e)}")

class LogFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == LOG_FILE_PATH:
            log("[INFO] Deteksi perubahan log, mulai proses...")
            try:
                lines = open(LOG_FILE_PATH).readlines()
                last_pos = load_last_position()
                new_lines = lines[last_pos:]
                save_last_position(len(lines))

                new_content = "".join(new_lines).strip()
                log_blocks = re.split(r"(?=^# Time: )", new_content, flags=re.MULTILINE)

                for log_block in log_blocks:
                    if not log_block.strip():
                        continue
                    match = re.search(r"^# Query_time: (\d+\.\d+)", log_block, re.MULTILINE)
                    if match:
                        duration = float(match.group(1))
                        log(f"[INFO] Ditemukan query_time: {duration}s")
                        if duration > SLOW_QUERY_THRESHOLD:
                            send_to_discord(log_block.strip())
                        else:
                            log("[INFO] Query_time kurang dari threshold, dilewati.")
            except Exception as e:
                log(f"[ERROR] Gagal baca log: {str(e)}")
            log("[INFO] Proses log selesai.")

if __name__ == "__main__":
    log("[START] 🟢 Memulai observer slow log...")
    event_handler = LogFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(LOG_FILE_PATH), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

