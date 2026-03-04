import socket
from utils import get_logger, send_message, receive_message
from config import SOCKET_TIMEOUT

logger = get_logger("replication_manager")

class ReplicationManager:
    def __init__(self):
        pass

    def replicate(self, node_address, key, value, ttl):
        host, port = node_address.split(':')
        try:
            with socket.create_connection((host, int(port)), timeout=SOCKET_TIMEOUT) as sock:
                msg = {
                    "cmd": "REPLICATE",
                    "key": key,
                    "value": value,
                    "ttl": ttl
                }
                send_message(sock, msg)
                resp = receive_message(sock)
                if resp and resp.get("status") == "OK":
                    return True
        except Exception as e:
            logger.error(f"Failed to replicate {key} to {node_address}: {e}")
            return False
        return False
        
    def delete_replica(self, node_address, key):
        host, port = node_address.split(':')
        try:
            with socket.create_connection((host, int(port)), timeout=SOCKET_TIMEOUT) as sock:
                msg = {
                    "cmd": "DELETE",
                    "key": key
                }
                send_message(sock, msg)
                receive_message(sock)
                return True
        except Exception:
            return False
