"""
Unit Tests for Database Persistence Layer
"""

import os
import tempfile
import pytest
from database import DatabaseManager, DatabaseError


@pytest.fixture
def temp_db():
    """Create a temporary database file for isolated testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(path)
    yield db
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


class TestDatabaseManager:
    """Test suite for SQLite DatabaseManager CRUD operations."""

    def test_database_initialization(self, temp_db):
        # Database table should exist
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bmi_records';")
            table = cursor.fetchone()
            assert table is not None
            assert table["name"] == "bmi_records"

    def test_add_record_and_retrieve_by_user(self, temp_db):
        rec_id = temp_db.add_record(
            user_name="John Doe",
            weight=72.0,
            height=1.75,
            bmi=23.51,
            category="Normal",
            recorded_at="2026-08-21 10:00:00"
        )
        assert rec_id == 1

        records = temp_db.get_records_by_user("John Doe")
        assert len(records) == 1
        rec = records[0]
        assert rec["id"] == 1
        assert rec["user_name"] == "John Doe"
        assert rec["weight"] == 72.0
        assert rec["height"] == 1.75
        assert rec["bmi"] == 23.51
        assert rec["category"] == "Normal"
        assert rec["recorded_at"] == "2026-08-21 10:00:00"

    def test_multi_user_isolation(self, temp_db):
        # Add records for User A (John) and User B (Sarah)
        temp_db.add_record("John", 70.0, 1.75, 22.86, "Normal", "2026-08-21 10:00:00")
        temp_db.add_record("John", 72.0, 1.75, 23.51, "Normal", "2026-08-21 11:00:00")
        temp_db.add_record("Sarah", 58.0, 1.65, 21.30, "Normal", "2026-08-21 12:00:00")

        # Verify John's records
        john_records = temp_db.get_records_by_user("John")
        assert len(john_records) == 2
        for r in john_records:
            assert r["user_name"] == "John"

        # Verify Sarah's records
        sarah_records = temp_db.get_records_by_user("Sarah")
        assert len(sarah_records) == 1
        assert sarah_records[0]["user_name"] == "Sarah"
        assert sarah_records[0]["weight"] == 58.0

        # Verify non-existent user returns empty list
        alex_records = temp_db.get_records_by_user("Alex")
        assert alex_records == []

    def test_get_all_users(self, temp_db):
        temp_db.add_record("Sarah", 60, 1.65, 22.0, "Normal")
        temp_db.add_record("John", 75, 1.75, 24.5, "Normal")
        temp_db.add_record("Alice", 50, 1.60, 19.5, "Normal")
        temp_db.add_record("John", 76, 1.75, 24.8, "Normal")

        users = temp_db.get_all_users()
        assert users == ["Alice", "John", "Sarah"]

    def test_delete_single_record(self, temp_db):
        id1 = temp_db.add_record("John", 70.0, 1.75, 22.86, "Normal")
        id2 = temp_db.add_record("John", 72.0, 1.75, 23.51, "Normal")

        assert temp_db.delete_record(id1) is True
        assert temp_db.delete_record(9999) is False  # Non-existent ID

        records = temp_db.get_records_by_user("John")
        assert len(records) == 1
        assert records[0]["id"] == id2

    def test_clear_user_records(self, temp_db):
        temp_db.add_record("John", 70.0, 1.75, 22.86, "Normal")
        temp_db.add_record("John", 72.0, 1.75, 23.51, "Normal")
        temp_db.add_record("Sarah", 60.0, 1.65, 22.04, "Normal")

        deleted_count = temp_db.clear_user_records("John")
        assert deleted_count == 2

        assert len(temp_db.get_records_by_user("John")) == 0
        assert len(temp_db.get_records_by_user("Sarah")) == 1

    def test_empty_user_name_insertion_raises_error(self, temp_db):
        with pytest.raises(DatabaseError, match="User name cannot be empty"):
            temp_db.add_record("", 70.0, 1.75, 22.86, "Normal")

    def test_invalid_database_path_handling(self):
        # Invalid directory path
        invalid_path = r"Z:\non_existent_folder_xyz_123\bmi.db"
        with pytest.raises(DatabaseError):
            DatabaseManager(invalid_path)
