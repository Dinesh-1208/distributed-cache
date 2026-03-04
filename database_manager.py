import threading
import json
from datetime import datetime
from utils import get_logger
from config import DATABASE_TYPE, DATABASE_HOST, DATABASE_PORT, DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD, DB_FILE

logger = get_logger("database_manager")

class DatabaseManager:
    def __init__(self):
        self.lock = threading.Lock()
        self._init_db()

    def _get_connection(self):
        if DATABASE_TYPE == "sqlite":
            import sqlite3
            return sqlite3.connect(DB_FILE)
        elif DATABASE_TYPE == "postgresql":
            import psycopg2
            return psycopg2.connect(
                host=DATABASE_HOST,
                port=DATABASE_PORT,
                dbname=DATABASE_NAME,
                user=DATABASE_USER,
                password=DATABASE_PASSWORD
            )
        elif DATABASE_TYPE == "mysql":
            import mysql.connector
            return mysql.connector.connect(
                host=DATABASE_HOST,
                port=DATABASE_PORT,
                database=DATABASE_NAME,
                user=DATABASE_USER,
                password=DATABASE_PASSWORD
            )
        else:
            raise ValueError(f"Unsupported DB Type: {DATABASE_TYPE}")

    def _init_db(self):
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                if DATABASE_TYPE == "sqlite":
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS users (
                            user_id TEXT PRIMARY KEY,
                            value TEXT,
                            created_at TIMESTAMP
                        )
                    ''')
                elif DATABASE_TYPE == "postgresql":
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS users (
                            user_id TEXT PRIMARY KEY,
                            value TEXT,
                            created_at TIMESTAMP
                        )
                    ''')
                elif DATABASE_TYPE == "mysql":
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS users (
                            user_id VARCHAR(255) PRIMARY KEY,
                            value TEXT,
                            created_at TIMESTAMP
                        )
                    ''')
                
                # Insert mock data
                cursor.execute("SELECT COUNT(*) FROM users")
                count = cursor.fetchone()[0]
                if count == 0:
                    ph = "%s" if DATABASE_TYPE in ["postgresql", "mysql"] else "?"
                    now = datetime.now()
                    cursor.execute(f"INSERT INTO users (user_id, value, created_at) VALUES ('user1', {ph}, {ph})", ('{"name": "Alice", "age": 25}', now))
                    cursor.execute(f"INSERT INTO users (user_id, value, created_at) VALUES ('user2', {ph}, {ph})", ('{"name": "Bob", "age": 30}', now))
                    cursor.execute(f"INSERT INTO users (user_id, value, created_at) VALUES ('user3', {ph}, {ph})", ('{"name": "Charlie", "age": 28}', now))
                    
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")

    def get(self, key):
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                ph = "%s" if DATABASE_TYPE in ["postgresql", "mysql"] else "?"
                cursor.execute(f'SELECT value FROM users WHERE user_id={ph}', (key,))
                row = cursor.fetchone()
                cursor.close()
                conn.close()
                return row[0] if row else None
            except Exception as e:
                logger.error(f"DB Get Error: {e}")
                return None

    def put(self, key, value):
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                val_str = json.dumps(value) if isinstance(value, dict) else str(value)
                now = datetime.now()
                
                if DATABASE_TYPE == "sqlite":
                    cursor.execute('REPLACE INTO users (user_id, value, created_at) VALUES (?, ?, ?)', (key, val_str, now))
                elif DATABASE_TYPE == "postgresql":
                    cursor.execute('''
                        INSERT INTO users (user_id, value, created_at) 
                        VALUES (%s, %s, %s) 
                        ON CONFLICT (user_id) 
                        DO UPDATE SET value = EXCLUDED.value, created_at = EXCLUDED.created_at
                    ''', (key, val_str, now))
                elif DATABASE_TYPE == "mysql":
                    cursor.execute('''
                        REPLACE INTO users (user_id, value, created_at) 
                        VALUES (%s, %s, %s)
                    ''', (key, val_str, now))
                    
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                logger.error(f"DB Put Error: {e}")

    def delete(self, key):
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                ph = "%s" if DATABASE_TYPE in ["postgresql", "mysql"] else "?"
                cursor.execute(f'DELETE FROM users WHERE user_id={ph}', (key,))
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                logger.error(f"DB Delete Error: {e}")
