from snapshot_manager import SnapshotManager
from aof_manager import AOFManager
from utils import get_logger

logger = get_logger("node_persistence")

class NodePersistence:
    def __init__(self, port, cache_instance):
        self.snapshot_mgr = SnapshotManager(port, cache_instance)
        self.aof_mgr = AOFManager(port)
        
        original_save = self.snapshot_mgr.save_snapshot
        def wrapped_save():
            original_save()
            self.aof_mgr.clear()
            logger.info("AOF log cleared after snapshot.")
        self.snapshot_mgr.save_snapshot = wrapped_save

    def start(self):
        # Startup Flow:
        # Load snapshot, replay AOF
        self.snapshot_mgr.load_snapshot()
        self.aof_mgr.replay(self.snapshot_mgr.cache)
        
        self.aof_mgr.start()
        self.snapshot_mgr.start()

    def stop(self):
        self.snapshot_mgr.stop()
        self.aof_mgr.stop()

    def log_put(self, key, value, ttl):
        self.aof_mgr.log_put(key, value, ttl)

    def log_delete(self, key):
        self.aof_mgr.log_delete(key)
