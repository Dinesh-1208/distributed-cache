import json
import os
import threading
import time
from utils import get_logger
from config import SNAPSHOT_INTERVAL

logger = get_logger("snapshot_manager")

class SnapshotManager:
    def __init__(self, port, cache_instance):
        self.port = port
        self.cache = cache_instance
        self.filename = f"cache_snapshot_{self.port}.json"
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._snapshot_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _snapshot_loop(self):
        while self.running:
            time.sleep(SNAPSHOT_INTERVAL)
            self.save_snapshot()

    def save_snapshot(self):
        try:
            data = {}
            for k in list(self.cache.cache.keys()):
                v = self.cache.cache.get(k)
                ttl_time = self.cache.ttls.get(k)
                data[k] = {"value": v, "ttl": ttl_time}
            
            with open(self.filename, 'w') as f:
                json.dump(data, f)
            logger.info(f"Snapshot saved to {self.filename} with {len(data)} items")
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")

    def load_snapshot(self):
        if not os.path.exists(self.filename):
            return 0
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
            
            now = time.time()
            count = 0
            for k, meta in data.items():
                ttl_time = meta.get("ttl")
                if ttl_time is None or ttl_time > now:
                    rem_ttl = None
                    if ttl_time is not None:
                        rem_ttl = ttl_time - now
                    self.cache.put(k, meta["value"], rem_ttl)
                    count += 1
            logger.info(f"Loaded {count} items from snapshot {self.filename}")
            return count
        except Exception as e:
            logger.error(f"Failed to load snapshot: {e}")
            return 0
