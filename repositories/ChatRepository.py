import sqlite3
from typing import Dict, List, Optional
from datetime import datetime
from entities.Chat import Chat
from entities.Message import Message
from pathlib import Path

class ChatRepository:
    def __init__(self):
        """Initialize SQLite connection"""
        self.db_path = str(Path("storage/chat_db.sqlite"))

    def _get_connection(self):
        """Get SQLite connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_chat_by_id(self, chat_id: str) -> Optional[Chat]:
        """Retrieve a chat by its ID"""
        conn = self._get_connection()
        try:
            # Get chat basic info
            cursor = conn.execute(
                "SELECT * FROM chats WHERE id = ?", 
                (chat_id,)
            )
            chat_data = cursor.fetchone()
            
            if not chat_data:
                return None

            # Get participants from chat_participants table
            cursor = conn.execute(
                "SELECT user_id FROM chat_participants WHERE chat_id = ?", 
                (chat_id,)
            )
            participants = [row['user_id'] for row in cursor.fetchall()]

            # Get messages
            cursor = conn.execute(
                """SELECT * FROM messages 
                WHERE chat_id = ? 
                ORDER BY timestamp""", 
                (chat_id,)
            )
            messages = [
                Message(
                    id=row['id'],
                    sender_id=row['sender_id'],
                    content=row['content'],
                    timestamp=datetime.fromisoformat(row['timestamp'])
                ) for row in cursor.fetchall()
            ]

            return Chat(
                id=chat_data['id'],
                admin_id=chat_data['admin_id'],
                participants=participants,
                messages=messages
            )

        finally:
            conn.close()

    def save_chat(self, chat: Chat) -> Chat:
        """Save or update a chat"""
        conn = self._get_connection()
        try:
            # Save chat basic info
            conn.execute(
                """INSERT OR REPLACE INTO chats (id, admin_id) 
                VALUES (?, ?)""",
                (chat.id, chat.admin_id)
            )

            # Update participants
            conn.execute(
                "DELETE FROM chat_participants WHERE chat_id = ?",
                (chat.id,)
            )
            conn.executemany(
                """INSERT INTO chat_participants (chat_id, user_id) 
                VALUES (?, ?)""",
                [(chat.id, participant) for participant in chat.participants]
            )

            conn.commit()
            return chat
        finally:
            conn.close()

    def add_participant(self, chat_id: str, participant_id: str) -> bool:
        """Add a participant to a chat"""
        conn = self._get_connection()
        try:
            # Check if chat exists
            cursor = conn.execute(
                "SELECT 1 FROM chats WHERE id = ?",
                (chat_id,)
            )
            if not cursor.fetchone():
                return False

            # Add participant if not exists
            conn.execute(
                """INSERT OR IGNORE INTO chat_participants (chat_id, user_id) 
                VALUES (?, ?)""",
                (chat_id, participant_id)
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def add_message(self, chat_id: str, message: Message) -> bool:
        """Add a message to a chat"""
        conn = self._get_connection()
        try:
            # Check if chat exists
            cursor = conn.execute(
                "SELECT 1 FROM chats WHERE id = ?",
                (chat_id,)
            )
            if not cursor.fetchone():
                return False

            conn.execute(
                """INSERT INTO messages (id, chat_id, sender_id, content, timestamp) 
                VALUES (?, ?, ?, ?, ?)""",
                (message.id, chat_id, message.sender_id, message.content, 
                 message.timestamp.isoformat())
            )
            conn.commit()
            return True
        finally:
            conn.close()


    def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat"""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "DELETE FROM chats WHERE id = ?",
                (chat_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def get_user_chats(self, user_id: str) -> List[Chat]:
        """Get all chats for a user"""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """SELECT DISTINCT c.* 
                FROM chats c
                JOIN chat_participants cp ON c.id = cp.chat_id
                WHERE cp.user_id = ?""",
                (user_id,)
            )
            chats = []
            for chat_data in cursor.fetchall():
                chat = self.get_chat_by_id(chat_data['id'])
                if chat:
                    chats.append(chat)
            return chats
        finally:
            conn.close()

    def remove_participant(self, chat_id: str, user_id: str) -> bool:
        """Remove a participant from a chat"""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """DELETE FROM chat_participants 
                WHERE chat_id = ? AND user_id = ?""",
                (chat_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def is_participant(self, chat_id: str, user_id: str) -> bool:
        """Check if a user is a participant in a chat"""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """SELECT 1 FROM chat_participants 
                WHERE chat_id = ? AND user_id = ?""",
                (chat_id, user_id)
            )
            return cursor.fetchone() is not None
        finally:
            conn.close()
