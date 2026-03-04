import logging

LOG_LEVEL = logging.INFO
COORDINATOR_HOST = '0.0.0.0'
COORDINATOR_PORT = 5000

# Demo-friendly parameters
CACHE_SIZE = 5                  # Small enough to easily trigger eviction (range 5-10)
DEFAULT_TTL = 120               # Long enough for observe, short enough for expiration
SNAPSHOT_INTERVAL = 30          # RDB Snapshot spacing (seconds)
HEARTBEAT_INTERVAL = 5          # Failover detection ping interval
HEARTBEAT_TIMEOUT = 3           # Timeout for heartbeat responses
REPLICATION_FACTOR = 2          # Primary + 1 Replica
SOCKET_TIMEOUT = 2              # Timeout for standard network operations

DATABASE_TYPE = "sqlite" # sqlite, postgresql, mysql
DATABASE_HOST = "localhost"
DATABASE_PORT = 5432
DATABASE_NAME = "distributed_cache"
DATABASE_USER = "admin"
DATABASE_PASSWORD = "password"
DB_FILE = 'cache_database.db' # Used if DATABASE_TYPE is sqlite

DEFAULT_EVICTION_POLICY = 'LRU' # 'LRU' or 'LFU'
VIRTUAL_NODES = 3
