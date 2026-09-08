"""
Database Persistence Layer

Manages SQLite storage for BMI records, parameterized CRUD operations,
connection life cycles, and database error handling.
"""

import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional


class DatabaseError(Exception):
    """Custom exception class for database operations."""
    pass


class DatabaseManager:
    """Encapsulates SQLite database operations for the BMI application."""

    def __init__(self, db_path: str = "bmi_records.db"):
        """
        Initialize the database manager with a database path.
        
        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """
        Create and return a database connection configured with row factory.
        
        Returns:
            sqlite3.Connection: Connected SQLite database instance.
            
        Raises:
            DatabaseError: If connection cannot be established.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to connect to database: {e}") from e

    def init_db(self) -> None:
        """
        Initialize the database tables and indexes if they do not exist.
        
        Raises:
            DatabaseError: If database initialization fails.
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS bmi_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            weight REAL NOT NULL,
            height REAL NOT NULL,
            bmi REAL NOT NULL,
            category TEXT NOT NULL,
            recorded_at TEXT NOT NULL
        );
        """
        create_index_sql = """
        CREATE INDEX IF NOT EXISTS idx_user_name ON bmi_records (user_name);
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                cursor.execute(create_index_sql)
                conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Database initialization error: {e}") from e

    def add_record(
        self,
        user_name: str,
        weight: float,
        height: float,
        bmi: float,
        category: str,
        recorded_at: Optional[str] = None
    ) -> int:
        """
        Insert a new BMI record.
        
        Args:
            user_name: Name of the user (must not be empty)
            weight: Weight in kg
            height: Height in meters
            bmi: Calculated BMI
            category: BMI classification category
            recorded_at: Timestamp string (YYYY-MM-DD HH:MM:SS), defaults to current local time.
            
        Returns:
            int: The inserted record's auto-generated primary key ID.
            
        Raises:
            DatabaseError: If record insertion fails.
        """
        if not user_name or not user_name.strip():
            raise DatabaseError("User name cannot be empty when saving a record.")
            
        if recorded_at is None:
            recorded_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        insert_sql = """
        INSERT INTO bmi_records (user_name, weight, height, bmi, category, recorded_at)
        VALUES (?, ?, ?, ?, ?, ?);
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    insert_sql,
                    (user_name.strip(), float(weight), float(height), float(bmi), category, recorded_at)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to save BMI record: {e}") from e

    def get_records_by_user(self, user_name: str, order_asc: bool = True) -> List[Dict[str, Any]]:
        """
        Retrieve all BMI records for a specific user.
        
        Args:
            user_name: Name of the user to query.
            order_asc: True for chronological order (oldest first, ideal for charts),
                       False for reverse chronological order (newest first, ideal for history table).
                       
        Returns:
            List[Dict[str, Any]]: List of dictionary representations of records.
            
        Raises:
            DatabaseError: If query execution fails.
        """
        order = "ASC" if order_asc else "DESC"
        select_sql = f"""
        SELECT id, user_name, weight, height, bmi, category, recorded_at
        FROM bmi_records
        WHERE user_name = ?
        ORDER BY datetime(recorded_at) {order}, id {order};
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(select_sql, (user_name.strip(),))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch records for user '{user_name}': {e}") from e

    def get_all_users(self) -> List[str]:
        """
        Retrieve a sorted list of all distinct user names with recorded data.
        
        Returns:
            List[str]: Alphabetically sorted list of user names.
            
        Raises:
            DatabaseError: If query execution fails.
        """
        select_sql = """
        SELECT DISTINCT user_name
        FROM bmi_records
        ORDER BY user_name COLLATE NOCASE ASC;
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(select_sql)
                rows = cursor.fetchall()
                return [row["user_name"] for row in rows]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch user list: {e}") from e

    def delete_record(self, record_id: int) -> bool:
        """
        Delete a single record by its ID.
        
        Args:
            record_id: Primary key of the record to delete.
            
        Returns:
            bool: True if a record was deleted, False if record_id was not found.
            
        Raises:
            DatabaseError: If deletion operation fails.
        """
        delete_sql = "DELETE FROM bmi_records WHERE id = ?;"
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(delete_sql, (record_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to delete record ID {record_id}: {e}") from e

    def clear_user_records(self, user_name: str) -> int:
        """
        Delete all records for a specific user.
        
        Args:
            user_name: User name whose records should be deleted.
            
        Returns:
            int: Number of deleted records.
            
        Raises:
            DatabaseError: If deletion fails.
        """
        delete_sql = "DELETE FROM bmi_records WHERE user_name = ?;"
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(delete_sql, (user_name.strip(),))
                conn.commit()
                return cursor.rowcount
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to clear records for user '{user_name}': {e}") from e

    def get_user_count(self) -> int:
        """Get total number of distinct users."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(DISTINCT user_name) AS cnt FROM bmi_records;")
                row = cursor.fetchone()
                return row["cnt"] if row else 0
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to count users: {e}") from e

    def get_total_record_count(self) -> int:
        """Get total number of records stored across all users."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) AS cnt FROM bmi_records;")
                row = cursor.fetchone()
                return row["cnt"] if row else 0
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to count records: {e}") from e
