import socket
import threading
import argparse
import sys
from consistent_hash import ConsistentHashRing
from heartbeat_monitor import HeartbeatMonitor
from database_manager import DatabaseManager
from replication_manager import ReplicationManager
from config import COORDINATOR_HOST, COORDINATOR_PORT, DEFAULT_TTL, REPLICATION_FACTOR, SOCKET_TIMEOUT
from utils import get_logger, send_message, receive_message

logger = get_logger("coordinator")

class Coordinator:
    def __init__(self, host=COORDINATOR_HOST, port=COORDINATOR_PORT):
        self.host = host
        self.port = port
        self.hash_ring = ConsistentHashRing()
        self.db = DatabaseManager()
        self.repl_manager = ReplicationManager()
        self.nodes_lock = threading.Lock()
        
        self.hb_monitor = HeartbeatMonitor(self)
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            logger.info(f"Coordinator listening at {self.host}:{self.port}")
            self.hb_monitor.start()
            
            while True:
                client_sock, addr = self.server_socket.accept()
                threading.Thread(target=self._handle_client, args=(client_sock, addr), daemon=True).start()
        except KeyboardInterrupt:
            logger.info("Shutting down coordinator")
        except Exception as e:
            logger.error(f"Coordinator error: {e}")
        finally:
            self.hb_monitor.stop()
            self.server_socket.close()

    def _handle_client(self, client_sock, addr):
        try:
            while True:
                msg = receive_message(client_sock)
                if not msg:
                    break
                
                cmd = msg.get("cmd")
                reply = {"status": "ERROR", "msg": "Unknown command"}
                
                if cmd == "REGISTER":
                    node = msg.get("node")
                    self.add_node(node)
                    reply = {"status": "OK"}
                elif cmd == "GET":
                    key = msg.get("key")
                    reply = self._process_get(key)
                elif cmd == "PUT":
                    key = msg.get("key")
                    value = msg.get("value")
                    ttl = msg.get("ttl", DEFAULT_TTL)
                    reply = self._process_put(key, value, ttl)
                elif cmd == "DELETE":
                    key = msg.get("key")
                    reply = self._process_delete(key)
                elif cmd == "STATS":
                    reply = {"status": "OK", "nodes": self.get_all_nodes()}
                
                send_message(client_sock, reply)
        except Exception as e:
            pass
        finally:
            client_sock.close()

    def add_node(self, node_address):
        with self.nodes_lock:
            self.hash_ring.add_node(node_address)
        logger.info(f"Node joined: {node_address}. Total nodes: {len(self.hash_ring.nodes)}")

    def remove_node(self, node_address):
        with self.nodes_lock:
            self.hash_ring.remove_node(node_address)
        logger.info(f"Node removed: {node_address}. Total nodes: {len(self.hash_ring.nodes)}")

    def get_all_nodes(self):
        with self.nodes_lock:
            return list(self.hash_ring.nodes)

    def _process_get(self, key):
        with self.nodes_lock:
            target_nodes = self.hash_ring.get_nodes(key, REPLICATION_FACTOR)
        
        if not target_nodes:
            return {"status": "ERROR", "msg": "No cache nodes available"}

        for node in target_nodes:
            val = self._ask_node_get(node, key)
            if val is not None:
                logger.info(f"GET '{key}': Cache HIT on node {node}")
                return {"status": "OK", "value": val, "source": f"cache ({node})"}
        
        logger.info(f"GET '{key}': Cache MISS. Fetching from DB.")
        db_val = self.db.get(key)
        if db_val is not None:
            self._process_cache_write(key, db_val, DEFAULT_TTL, target_nodes)
            return {"status": "OK", "value": db_val, "source": "database"}
        
        return {"status": "NOT_FOUND"}

    def _process_put(self, key, value, ttl):
        self.db.put(key, value)
        logger.info(f"PUT '{key}': Updated Database")
        
        with self.nodes_lock:
            target_nodes = self.hash_ring.get_nodes(key, REPLICATION_FACTOR)
            
        if target_nodes:
            self._process_cache_write(key, value, ttl, target_nodes)
            
        return {"status": "OK"}

    def _process_delete(self, key):
        self.db.delete(key)
        logger.info(f"DELETE '{key}': Removed from Database")
        with self.nodes_lock:
            target_nodes = self.hash_ring.get_nodes(key, REPLICATION_FACTOR)
            
        if target_nodes:
            for node in target_nodes:
                self.repl_manager.delete_replica(node, key)
        return {"status": "OK"}

    def _process_cache_write(self, key, value, ttl, target_nodes):
        if not target_nodes:
            return
        primary = target_nodes[0]
        self._ask_node_put(primary, key, value, ttl)
        logger.info(f"Stored '{key}' on Primary Node: {primary}")
        if len(target_nodes) > 1:
            for replica in target_nodes[1:]:
                self.repl_manager.replicate(replica, key, value, ttl)
                logger.info(f"Replicated '{key}' to Replica Node: {replica}")

    def _ask_node_get(self, node_address, key):
        host, port = node_address.split(':')
        try:
            with socket.create_connection((host, int(port)), timeout=SOCKET_TIMEOUT) as sock:
                send_message(sock, {"cmd": "GET", "key": key})
                resp = receive_message(sock)
                if resp and resp.get("status") == "HIT":
                    return resp.get("value")
        except Exception:
            pass
        return None

    def _ask_node_put(self, node_address, key, value, ttl):
        host, port = node_address.split(':')
        try:
            with socket.create_connection((host, int(port)), timeout=SOCKET_TIMEOUT) as sock:
                send_message(sock, {"cmd": "PUT", "key": key, "value": value, "ttl": ttl})
                receive_message(sock)
        except Exception as e:
            logger.error(f"Failed to put to node {node_address}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0", type=str)
    parser.add_argument("--port", default=COORDINATOR_PORT, type=int)
    args = parser.parse_args()
    
    coord = Coordinator(args.host, args.port)
    coord.start()
