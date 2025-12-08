"""
Database connection and utilities
"""
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from typing import Optional, Dict, List, Any
from loguru import logger
from execution.config import get_database_url


class Database:
    """Database connection manager"""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or get_database_url()
        self._connection = None

    def connect(self):
        """Establish database connection"""
        if not self._connection or self._connection.closed:
            try:
                self._connection = psycopg2.connect(
                    self.database_url,
                    cursor_factory=psycopg2.extras.RealDictCursor
                )
                logger.info("Database connected successfully")
            except Exception as e:
                logger.error(f"Database connection failed: {e}")
                raise
        return self._connection

    def close(self):
        """Close database connection"""
        if self._connection and not self._connection.closed:
            self._connection.close()
            logger.info("Database connection closed")

    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor"""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()

    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction failed: {e}")
            raise

    def execute(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Execute query and return results"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            if cursor.description:
                return cursor.fetchall()
            return []

    def execute_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict]:
        """Execute query and return single result"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            if cursor.description:
                return cursor.fetchone()
            return None

    def insert(self, table: str, data: Dict[str, Any]) -> Optional[str]:
        """Insert data and return ID"""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING *"

        with self.get_cursor() as cursor:
            cursor.execute(query, tuple(data.values()))
            result = cursor.fetchone()
            return result

    def update(self, table: str, data: Dict[str, Any], where: Dict[str, Any]) -> bool:
        """Update data"""
        set_clause = ", ".join([f"{k} = %s" for k in data.keys()])
        where_clause = " AND ".join([f"{k} = %s" for k in where.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

        params = tuple(data.values()) + tuple(where.values())

        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount > 0


# Global database instance
db = Database()


def get_db() -> Database:
    """Get database instance"""
    return db
