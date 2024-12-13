import sqlite3
from typing import Optional, List
from entities.User import User
from pathlib import Path

class UserRepository:
    def __init__(self):
        """Initialize SQLite connection"""
        self.db_path = str(Path("storage/chat_db.sqlite"))

    def _get_connection(self):
        """Get SQLite connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve a user by their ID
        
        Args:
            user_id (str): The unique identifier of the user
            
        Returns:
            Optional[User]: The user object if found, None otherwise
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,)
            )
            user_data = cursor.fetchone()
            
            if user_data:
                return User(
                    id=user_data['id'],
                    name=user_data['name']
                )
            return None
        finally:
            conn.close()

    def save_user(self, user: User) -> User:
        """
        Save or update a user
        
        Args:
            user (User): The user object to save
            
        Returns:
            User: The saved user object
        """
        conn = self._get_connection()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO users (id, name) 
                VALUES (?, ?)""",
                (user.id, user.name)
            )
            conn.commit()
            return user
        finally:
            conn.close()

    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user
        
        Args:
            user_id (str): The user ID to delete
            
        Returns:
            bool: True if successful, False if user not found
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "DELETE FROM users WHERE id = ?",
                (user_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def get_all_users(self) -> List[User]:
        """
        Get all users
        
        Returns:
            List[User]: List of all users
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM users")
            return [
                User(
                    id=row['id'],
                    name=row['name']
                ) for row in cursor.fetchall()
            ]
        finally:
            conn.close()
