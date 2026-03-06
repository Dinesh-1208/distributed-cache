import socket
import threading
import argparse
import sys
from lru_cache import LRUCache
from lfu_cache import LFUCache
from config import CACHE_SIZE, DEFAULT_EVICTION_POLICY, COORDINATOR_HOST, COORDINATOR_PORT, SOCKET_TIMEOUT
from utils import get_logger, send_message, receive_message
from node_persistence import NodePersistence

logger = get_logger("node")

class CacheNode:
    def __init__(self, host, port, coordinator_host=COORDINATOR_HOST, coordinator_port=COORDINATOR_PORT, policy=DEFAULT_EVICTION_POLICY, advertise_host=None):
        self.host = host
        self.port = port
        # advertise_host is the hostname other services use to reach this node (e.g. Docker service name)
        self.advertise_host = advertise_host or host
        self.address = f"{self.advertise_host}:{port}"
        self.coordinator_host = coordinator_host
        self.coordinator_port = coordinator_port
        
        if policy == "LRU":
            self.cache = LRUCache(CACHE_SIZE)
        else:
            self.cache = LFUCache(CACHE_SIZE)
            
        self.persistence = NodePersistence(self.port, self.cache)
            
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            logger.info(f"Node started at {self.address} with {self.cache.__class__.__name__} (Size: {CACHE_SIZE})")
            
            self.persistence.start()
            self.register_with_coordinator()
            
            while True:
                client_sock, addr = self.server_socket.accept()
                threading.Thread(target=self._handle_request, args=(client_sock, addr)).start()
        except KeyboardInterrupt:
            logger.info("Shutting down node")
        except Exception as e:
            logger.error(f"Node error: {e}")
        finally:
            self.persistence.stop()
            self.server_socket.close()

    def register_with_coordinator(self, retries=10, delay=2):
        for attempt in range(1, retries + 1):
            try:
                with socket.create_connection((self.coordinator_host, self.coordinator_port), timeout=SOCKET_TIMEOUT) as sock:
                    send_message(sock, {"cmd": "REGISTER", "node": self.address})
                    resp = receive_message(sock)
                    if resp and resp.get("status") == "OK":
                        logger.info("Successfully registered with coordinator")
                        return
                    else:
                        logger.error("Registration failed")
            except Exception as e:
                logger.warning(f"Attempt {attempt}/{retries} - Could not connect to coordinator at {self.coordinator_host}:{self.coordinator_port}: {e}")
                if attempt < retries:
                    import time
                    time.sleep(delay)
        logger.error("Failed to register with coordinator after all retries")

    def _handle_request(self, client_sock, addr):
        try:
            while True:
                msg = receive_message(client_sock)
                if not msg:
                    break
                
                cmd = msg.get("cmd")
                reply = {"status": "ERROR", "msg": "Unknown command"}
                
                self.cache.clean_expired()
                
                if cmd == "PING":
                    reply = {"status": "PONG"}
                elif cmd == "GET":
                    key = msg.get("key")
                    val = self.cache.get(key)
                    if val is not None:
                        logger.info(f"Served GET '{key}' -> HIT")
                        reply = {"status": "HIT", "value": val}
                    else:
                        logger.info(f"Served GET '{key}' -> MISS")
                        reply = {"status": "MISS"}
                elif cmd in ("PUT", "REPLICATE"):
                    key = msg.get("key")
                    val = msg.get("value")
                    ttl = msg.get("ttl")
                    is_replica = (cmd == "REPLICATE")
                    self.cache.put(key, val, ttl)
                    self.persistence.log_put(key, val, ttl)
                    logger.info(f"Stored '{key}' (Replica: {is_replica})")
                    reply = {"status": "OK"}
                elif cmd == "DELETE":
                    key = msg.get("key")
                    self.cache.delete(key)
                    self.persistence.log_delete(key)
                    logger.info(f"Deleted '{key}'")
                    reply = {"status": "OK"}
                elif cmd == "STATS":
                    # For python 3 dict vs ordered dict
                    keys_list = list(self.cache.cache.keys())
                    reply = {"status": "OK", "keys": keys_list}
                
                send_message(client_sock, reply)
        except Exception:
            pass
        finally:
            client_sock.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True, type=str)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--advertise-host", default=None, type=str, help="Hostname to advertise to coordinator (e.g. Docker service name)")
    parser.add_argument("--coordinator-host", default=COORDINATOR_HOST, type=str)
    parser.add_argument("--coordinator-port", default=COORDINATOR_PORT, type=int)
    parser.add_argument("--policy", default=DEFAULT_EVICTION_POLICY, choices=["LRU", "LFU"])
    args = parser.parse_args()
    
    node = CacheNode(args.host, args.port, args.coordinator_host, args.coordinator_port, args.policy, args.advertise_host)
    node.start()
