import os
from utils import get_logger

logger = get_logger("aof_manager")

class AOFManager:
    def __init__(self, port):
        self.port = port
        self.filename = f"cache_aof_{self.port}.log"
        self.file = None

    def start(self):
        self.file = open(self.filename, 'a')

    def stop(self):
        if self.file:
            self.file.close()
            self.file = None

    def log_put(self, key, value, ttl):
        if self.file:
            ttl_str = str(ttl) if ttl is not None else "None"
            self.file.write(f"PUT {key} {value} {ttl_str}\n")
            self.file.flush()

    def log_delete(self, key):
        if self.file:
            self.file.write(f"DELETE {key}\n")
            self.file.flush()

    def clear(self):
        if self.file:
            self.file.close()
        open(self.filename, 'w').close()
        self.file = open(self.filename, 'a')

    def replay(self, cache_instance):
        if not os.path.exists(self.filename):
            return 0
        
        count = 0
        try:
            with open(self.filename, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if not parts:
                        continue
                    cmd = parts[0]
                    if cmd == "PUT" and len(parts) >= 3:
                        key = parts[1]
                        ttl_str = parts[-1]
                        value = " ".join(parts[2:-1])
                        ttl = None
                        if ttl_str != "None":
                            try:
                                ttl = float(ttl_str)
                            except ValueError:
                                pass
                        cache_instance.put(key, value, ttl)
                        count += 1
                    elif cmd == "DELETE" and len(parts) >= 2:
                        key = parts[1]
                        cache_instance.delete(key)
                        count += 1
            logger.info(f"Replayed {count} operations from AOF {self.filename}")
            return count
        except Exception as e:
            logger.error(f"Failed to replay AOF: {e}")
            return 0
