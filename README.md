# Distributed Cache System for High-Traffic Applications (Redis-Inspired)

A simplified distributed in-memory cache system inspired by Redis and Memcached, built in Python 3. It demonstrates core distributed systems capabilities such as Consistent Hashing, Cache Eviction (LRU/LFU), Replication, Node Failure Detection/Failover, and Cache Invalidation (TTL).

## System Architecture

The project consists of three main runnable components:
1. **Coordinator**: The central router that maintains the Consistent Hashing ring, delegates requests to nodes, connects to the SQLite backend Database on cache misses (Cache-Aside Pattern), handles replication, and queries nodes with heartbeat pings to detect failures.
2. **Nodes**: Independent cache servers that store key-value pairs in memory using LRU or LFU logic. They apply TTL rules and respond to Coordinator GET/PUT commands. Nodes NEVER talk direct to the database.
3. **Client**: A CLI application with an interactive shell for sending GET, PUT, DELETE, and STATS commands to the Coordinator.

## Multi-Machine Deployment (Example with 3 Laptops)

You can run this system across several laptops on the same network. Below are commands for an example configuration.

### Coordinator Laptop (192.168.1.5)
Start the Coordinator so it listens on all network interfaces:
```bash
python coordinator.py --host 0.0.0.0 --port 5000
```
*(Optionally start the Client on this laptop as well)*

### Laptop 1 (Node A) -> IP 192.168.1.10
Start a Node telling it where to find the Coordinator:
```bash
python node.py --host 192.168.1.10 --port 5001 --coordinator-host 192.168.1.5
```

### Laptop 2 (Node B) -> IP 192.168.1.11
```bash
python node.py --host 192.168.1.11 --port 5002 --coordinator-host 192.168.1.5
```

### Laptop 3 (Node C) -> IP 192.168.1.12
```bash
python node.py --host 192.168.1.12 --port 5003 --coordinator-host 192.168.1.5
```

## Running Locally

If you don't have multiple laptops, you can run all components in different terminals on the same machine.

**Terminal 1:** (Coordinator)
```bash
python coordinator.py
```

**Terminal 2:** (Node 1)
```bash
python node.py --host 127.0.0.1 --port 5001
```

**Terminal 3:** (Node 2)
```bash
python node.py --host 127.0.0.1 --port 5002
```

**Terminal 4:** (Node 3)
```bash
python node.py --host 127.0.0.1 --port 5003
```

**Terminal 5:** (Client Shell)
```bash
python client.py
```

## Demonstrations

**Use Case 1: Cache Miss**
1. In the client shell, request `GET user1`
2. You will see output `Source: database` (This indicates a Cache Miss; the coordinator fetched it from the SQLite DB and stored it in the cache)

**Use Case 2: Cache Hit**
1. Send `GET user1` again.
2. You will see output `Source: cache (127.0.0.1:5001)` (The coordinator grabbed it directly from the primary Cache Node).

**Use Case 3: Cache Eviction**
*The Cache Size is intentionally set to `3` in `config.py` for easy testing.*
1. Insert 4 new keys: `PUT k1 v1`, `PUT k2 v2`, `PUT k3 v3`, `PUT k4 v4`.
2. Check the logs of the Cache Nodes. You will see an `[LRU Eviction]` log reporting that an old key was removed due to capacity limits.

**Use Case 4: Node Failure**
1. Terminate one of your running `node.py` processes (`Ctrl+C`).
2. Within `5` seconds, the Coordinator logs will show `failed heartbeat. Removing from cluster.`.
3. Try a `GET` command on a key that was on the failed node. The Coordinator will automatically retrieve the value from the Replica Node or the Database gracefully.

## Customization
Read `config.py` to change caching policy (`LRU` vs `LFU`), heartbeat intervals, CACHE_SIZE per node, TTL default lifetimes, etc.
