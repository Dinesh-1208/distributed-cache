import socket
import argparse
import sys
from utils import send_message, receive_message
from config import COORDINATOR_HOST, COORDINATOR_PORT, SOCKET_TIMEOUT

class CacheClient:
    def __init__(self, host=COORDINATOR_HOST, port=COORDINATOR_PORT):
        self.host = host
        self.port = port
        
    def _send_cmd(self, msg_dict):
        try:
            with socket.create_connection((self.host, self.port), timeout=SOCKET_TIMEOUT) as sock:
                send_message(sock, msg_dict)
                reply = receive_message(sock)
                return reply
        except Exception as e:
            print(f"Connection error: {e}")
            return None

    def get(self, key):
        reply = self._send_cmd({"cmd": "GET", "key": key})
        if reply:
            if reply.get("status") == "OK":
                print(f"Value: {reply.get('value')}")
                print(f"Source: {reply.get('source')}")
            else:
                print(f"Not found / Error: {reply.get('msg', 'NOT_FOUND')}")

    def put(self, key, value, ttl=None):
        reply = self._send_cmd({"cmd": "PUT", "key": key, "value": value, "ttl": ttl})
        if reply:
            print(f"Put status: {reply.get('status')}")

    def delete(self, key):
        reply = self._send_cmd({"cmd": "DELETE", "key": key})
        if reply:
            print(f"Delete status: {reply.get('status')}")

    def stats(self):
        reply = self._send_cmd({"cmd": "STATS"})
        if reply:
            print(f"Nodes in cluster: {reply.get('nodes', [])}")

def interactive_shell(host, port):
    client = CacheClient(host, port)
    print("========================================")
    print("Connected to Distributed Cache System")
    print(f"Coordinator: {host}:{port}")
    print("========================================")
    print("Commands:")
    print("  GET <key>")
    print("  PUT <key> <value> [ttl]")
    print("  DELETE <key>")
    print("  STATS")
    print("  EXIT")
    print("========================================")
    while True:
        try:
            cmd_line = input("\ncache> ").strip()
            if not cmd_line:
                continue
                
            parts = cmd_line.split()
            cmd = parts[0].upper()
            
            if cmd == "EXIT":
                break
            elif cmd == "STATS":
                client.stats()
            elif cmd == "GET" and len(parts) >= 2:
                client.get(parts[1])
            elif cmd == "PUT" and len(parts) >= 3:
                key = parts[1]
                value = " ".join(parts[2:])
                ttl = None
                # Basic parsing string vs TTL logic (if last part is digit, treat as TTL)
                if parts[-1].isdigit():
                    ttl = int(parts[-1])
                    value = " ".join(parts[2:-1])
                client.put(key, value, ttl)
            elif cmd == "DELETE" and len(parts) >= 2:
                client.delete(parts[1])
            else:
                print("Invalid command syntax.")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--coordinator-host", default=COORDINATOR_HOST, type=str)
    parser.add_argument("--coordinator-port", default=COORDINATOR_PORT, type=int)
    parser.add_argument("cmd", nargs="*", help="Command to execute (e.g. GET key)")
    args = parser.parse_args()
    
    if not args.cmd:
        interactive_shell(args.coordinator_host, args.coordinator_port)
    else:
        client = CacheClient(args.coordinator_host, args.coordinator_port)
        cmd = args.cmd[0].upper()
        if cmd == "GET" and len(args.cmd) >= 2:
            client.get(args.cmd[1])
        elif cmd == "PUT" and len(args.cmd) >= 3:
            key = args.cmd[1]
            if args.cmd[-1].isdigit():
                ttl = int(args.cmd[-1])
                value = " ".join(args.cmd[2:-1])
            else:
                ttl = None
                value = " ".join(args.cmd[2:])
            client.put(key, value, ttl)
        elif cmd == "DELETE" and len(args.cmd) >= 2:
            client.delete(args.cmd[1])
        elif cmd == "STATS":
            client.stats()
        else:
            print("Invalid command.")
