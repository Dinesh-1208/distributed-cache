import time
from collections import defaultdict
from utils import get_logger

logger = get_logger("node")

class LFUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}
        self.freq = {}
        self.ttls = {}
        self.freq_keys = defaultdict(list)
        self.min_freq = 0

    def get(self, key):
        if key in self.cache:
            if self._is_expired(key):
                self.delete(key)
                return None
            self._update_freq(key)
            return self.cache[key]
        return None

    def put(self, key, value, ttl=None):
        if self.capacity == 0:
            return

        if key in self.cache:
            self.cache[key] = value
            self._update_freq(key)
        else:
            if len(self.cache) >= self.capacity:
                self._evict()
            self.cache[key] = value
            self.freq[key] = 1
            self.min_freq = 1
            self.freq_keys[1].append(key)

        if ttl:
            self.ttls[key] = time.time() + ttl

    def delete(self, key):
        if key in self.cache:
            del self.cache[key]
            f = self.freq.pop(key)
            self.freq_keys[f].remove(key)
            self.ttls.pop(key, None)

    def _update_freq(self, key):
        f = self.freq[key]
        self.freq[key] = f + 1
        self.freq_keys[f].remove(key)
        if not self.freq_keys[f] and self.min_freq == f:
            self.min_freq += 1
        self.freq_keys[f + 1].append(key)

    def _evict(self):
        if not self.freq_keys[self.min_freq]:
            return
        key_to_evict = self.freq_keys[self.min_freq][0]
        logger.info(f"[LFU Eviction] Removing key '{key_to_evict}' due to capacity limit ({self.capacity})")
        self.delete(key_to_evict)

    def _is_expired(self, key):
        if key in self.ttls and time.time() > self.ttls[key]:
            logger.info(f"[Eviction] Key '{key}' expired due to TTL")
            return True
        return False

    def clean_expired(self):
        expired_keys = [k for k in self.cache if self._is_expired(k)]
        for k in expired_keys:
            self.delete(k)
