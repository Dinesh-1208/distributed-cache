import hashlib
from config import VIRTUAL_NODES

class ConsistentHashRing:
    def __init__(self, virtual_nodes=VIRTUAL_NODES):
        self.virtual_nodes = virtual_nodes
        self.ring = {}
        self.sorted_keys = []
        self.nodes = set()

    def _hash(self, key):
        # Switched to SHA-256: 256-bit hash provides astronomical resilience 
        # against generic collisions for 5 billion users compared to MD5.
        return int(hashlib.sha256(key.encode('utf-8')).hexdigest(), 16)

    def add_node(self, node):
        if node in self.nodes:
            return
        self.nodes.add(node)
        for i in range(self.virtual_nodes):
            v_node_key = f"{node}-{i}"
            original_h = self._hash(v_node_key)
            h = original_h
            
            # Collision Resolution Mechanism (Quadratic Probing)
            # If a hash slot is taken by another node, we step away using i^2.
            # Using 2**256 as the modulo space since we are using SHA-256.
            attempt = 0
            while h in self.ring and self.ring[h] != node:
                attempt += 1
                h = (original_h + attempt**2) % (2**256)
                
            self.ring[h] = node
            self.sorted_keys.append(h)
        self.sorted_keys.sort()

    def remove_node(self, node):
        if node not in self.nodes:
            return
        self.nodes.remove(node)
        for i in range(self.virtual_nodes):
            v_node_key = f"{node}-{i}"
            original_h = self._hash(v_node_key)
            h = original_h
            
            # Same Collision Resolution traversal to successfully find and remove the precise quadratically-probed hash
            attempt = 0
            while h in self.ring:
                if self.ring[h] == node:
                    self.ring.pop(h, None)
                    try:
                        self.sorted_keys.remove(h)
                    except ValueError:
                        pass
                    break  # Found and removed our node's hash, exit while
                else:
                    attempt += 1
                    h = (original_h + attempt**2) % (2**256)

    def get_nodes(self, key, count=2):
        if not self.ring:
            return []
        nodes = []
        h = self._hash(key)
        
        start_idx = 0
        for i, node_hash in enumerate(self.sorted_keys):
            if h <= node_hash:
                start_idx = i
                break
                
        for i in range(len(self.sorted_keys)):
            idx = (start_idx + i) % len(self.sorted_keys)
            node = self.ring[self.sorted_keys[idx]]
            if node not in nodes:
                nodes.append(node)
            if len(nodes) == count or len(nodes) == len(self.nodes):
                break
        return nodes
