from collections import OrderedDict
import time
from utils import get_logger

logger = get_logger("node")

class LRUCache:
    def __init__(self, capacity):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.ttls = {}

    def get(self, key):
        if key in self.cache:
            if self._is_expired(key):
                self.delete(key)
                return None
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def put(self, key, value, ttl=None):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if ttl:
            self.ttls[key] = time.time() + ttl
            
        if len(self.cache) > self.capacity:
            oldest = next(iter(self.cache))
            logger.info(f"[LRU Eviction] Removing key '{oldest}' due to capacity limit ({self.capacity})")
            self.delete(oldest)

    def delete(self, key):
        if key in self.cache:
            del self.cache[key]
            self.ttls.pop(key, None)

    def _is_expired(self, key):
        if key in self.ttls and time.time() > self.ttls[key]:
            logger.info(f"[Eviction] Key '{key}' expired due to TTL")
            return True
        return False

    def clean_expired(self):
        expired_keys = [k for k in self.cache if self._is_expired(k)]
        for k in expired_keys:
            self.delete(k)
