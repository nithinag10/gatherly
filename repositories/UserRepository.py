from typing import Optional, List
from entities.User import User
from sqlalchemy import text
from storage.database import pool

class UserRepository:
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        try:
            with pool.connect() as conn:
                user_data = conn.execute(
                    text("SELECT * FROM users WHERE id = :user_id"),
                    {"user_id": user_id}
                ).fetchone()
                if user_data:
                    return User(id=user_data.id, name=user_data.name)
                return None
        except Exception:
            raise

    def get_user_by_email(self, email: str) -> Optional[User]:
        try:
            with pool.connect() as conn:
                result = conn.execute(
                    text("SELECT * FROM users WHERE email = :email"),
                    {"email": email}
                ).fetchone()
                
                if result is None:
                    return None
                    
                # Convert Row to dictionary using _mapping
                return User(**result._mapping)
        except Exception:
            raise

    def save_user(self, user: User) -> User:
        try:
            with pool.begin() as conn:
                conn.execute(
                    text("""
                    INSERT INTO users (id, email, name, password_hash, created_at)
                    VALUES (:id, :email, :name, :password_hash, :created_at)
                    """),
                    user.__dict__
                )
            return user
        except Exception:
            raise

    def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        try:
            with pool.begin() as conn:
                result = conn.execute(
                    text("DELETE FROM users WHERE id = :user_id"),
                    {"user_id": user_id}
                )
            return result.rowcount > 0
        except Exception:
            raise

    def get_all_users(self) -> List[User]:
        """Get all users"""
        try:
            with pool.connect() as conn:
                result = conn.execute(text("SELECT * FROM users"))
                return [User(id=row.id, name=row.name) for row in result.fetchall()]
        except Exception:
            raise
