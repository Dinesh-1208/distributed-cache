import subprocess
import time
import sys

def run():
    print("Starting coordinator...")
    coord = subprocess.Popen([sys.executable, "coordinator.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(1)
    
    print("Starting nodes...")
    n1 = subprocess.Popen([sys.executable, "node.py", "--host", "127.0.0.1", "--port", "5001"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    n2 = subprocess.Popen([sys.executable, "node.py", "--host", "127.0.0.1", "--port", "5002"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    n3 = subprocess.Popen([sys.executable, "node.py", "--host", "127.0.0.1", "--port", "5003"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(2)
    
    print("\n--- Use Case 1: Cache Miss ---")
    out = subprocess.check_output([sys.executable, "client.py", "GET", "user1"], text=True)
    print(out)
    
    print("\n--- Use Case 2: Cache Hit ---")
    out = subprocess.check_output([sys.executable, "client.py", "GET", "user1"], text=True)
    print(out)
    
    print("\n--- Use Case 3: Cache Eviction ---")
    # Add many keys to trigger eviction
    for i in range(1, 15):
        subprocess.check_output([sys.executable, "client.py", "PUT", f"k{i}", f"v{i}"], text=True)
    
    time.sleep(1)
    
    print("\n--- Use Case 4: Node Failure ---")
    print("Stopping node 1...")
    n1.terminate()
    time.sleep(6) # Wait for heartbeat timeout
    
    print("Trying to GET user1 after node failure...")
    out = subprocess.check_output([sys.executable, "client.py", "GET", "user1"], text=True)
    print(out)
    
    # Stop everything
    coord.terminate()
    n2.terminate()
    n3.terminate()

    print("\nLogs from Coordinator:")
    try:
        out_coord, _ = coord.communicate(timeout=2)
        print(out_coord)
    except Exception:
        pass
    
    print("\nLogs from Node 2:")
    try:
        out_n2, _ = n2.communicate(timeout=2)
        print(out_n2)
    except Exception:
        pass

    print("\nLogs from Node 3:")
    try:
        out_n3, _ = n3.communicate(timeout=2)
        print(out_n3)
    except Exception:
        pass

if __name__ == '__main__':
    run()
