import threading
import time
import socket
from utils import get_logger, send_message, receive_message
from config import HEARTBEAT_INTERVAL, HEARTBEAT_TIMEOUT

logger = get_logger("heartbeat_monitor")

class HeartbeatMonitor:
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _monitor_loop(self):
        while self.running:
            time.sleep(HEARTBEAT_INTERVAL)
            self._check_nodes()

    def _check_nodes(self):
        nodes = self.coordinator.get_all_nodes()
        for node in nodes:
            is_alive = self._ping_node(node)
            if not is_alive:
                logger.warning(f"Node {node} failed heartbeat. Removing from cluster.")
                self.coordinator.remove_node(node)

    def _ping_node(self, node_address):
        host, port = node_address.split(':')
        try:
            with socket.create_connection((host, int(port)), timeout=HEARTBEAT_TIMEOUT) as sock:
                send_message(sock, {"cmd": "PING"})
                resp = receive_message(sock)
                if resp and resp.get("status") == "PONG":
                    return True
        except Exception:
            pass
        return False
