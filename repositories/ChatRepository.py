from typing import Optional, List
from datetime import datetime
from entities.Chat import Chat
from entities.Message import Message
from sqlalchemy import text
from storage.database import pool

class ChatRepository:
    def get_chat_by_id(self, chat_id: str) -> Optional[Chat]:
        """Retrieve a chat by its ID"""
        with pool.connect() as conn:
            chat_data = conn.execute(
                text("SELECT * FROM chats WHERE id = :chat_id"),
                {"chat_id": chat_id}
            ).fetchone()

            if not chat_data:
                return None

            participants_data = conn.execute(
                text("SELECT user_id FROM chat_participants WHERE chat_id = :chat_id"),
                {"chat_id": chat_id}
            ).fetchall()
            participants = [row.user_id for row in participants_data]

            messages_data = conn.execute(
                text("""SELECT * FROM messages 
                        WHERE chat_id = :chat_id 
                        ORDER BY timestamp"""),
                {"chat_id": chat_id}
            ).fetchall()

            messages = [
                Message(
                    id=row.id,
                    sender_id=row.sender_id,
                    content=row.content,
                    timestamp=row.timestamp
                ) for row in messages_data
            ]

            return Chat(
                id=chat_data.id,
                admin_id=chat_data.admin_id,
                chat_name=chat_data.chat_name,
                agenda=chat_data.agenda,
                participants=participants,
                messages=messages
            )

    def save_chat(self, chat: Chat) -> Chat:
        """Save or update a chat"""
        try:
            with pool.begin() as conn:  # begin() starts a transaction
                conn.execute(
                    text("""INSERT INTO chats (id, admin_id, chat_name, agenda) 
                            VALUES (:id, :admin_id, :chat_name, :agenda)
                            ON DUPLICATE KEY UPDATE 
                                admin_id = :admin_id,
                                chat_name = :chat_name,
                                agenda = :agenda"""),
                    {
                        "id": chat.id,
                        "admin_id": chat.admin_id,
                        "chat_name": chat.chat_name,
                        "agenda": chat.agenda
                    }
                )

                conn.execute(
                    text("DELETE FROM chat_participants WHERE chat_id = :chat_id"),
                    {"chat_id": chat.id}
                )

                for participant in chat.participants:
                    conn.execute(
                        text("""INSERT INTO chat_participants (chat_id, user_id) 
                                VALUES (:chat_id, :user_id)"""),
                        {"chat_id": chat.id, "user_id": participant}
                    )
            return chat
        except Exception:
            # Transaction will rollback automatically on exception
            raise


    def add_participant(self, chat_id: str, participant_id: str) -> bool:
        """Add a participant to a chat"""
        try:
            with pool.begin() as conn:
                chat_data = conn.execute(
                    text("SELECT 1 FROM chats WHERE id = :chat_id"),
                    {"chat_id": chat_id}
                ).fetchone()

                if not chat_data:
                    return False

                conn.execute(
                    text("""INSERT INTO chat_participants (chat_id, user_id) 
                            VALUES (:chat_id, :user_id)
                            ON DUPLICATE KEY UPDATE user_id = :user_id"""),
                    {"chat_id": chat_id, "user_id": participant_id}
                )
            return True
        except Exception:
            raise

    def add_message(self, chat_id: str, message: Message) -> bool:
        """Add a message to a chat"""
        try:
            with pool.begin() as conn:
                chat_data = conn.execute(
                    text("SELECT 1 FROM chats WHERE id = :chat_id"),
                    {"chat_id": chat_id}
                ).fetchone()
                if not chat_data:
                    return False

                conn.execute(
                    text("""INSERT INTO messages (id, chat_id, sender_id, content, timestamp) 
                            VALUES (:id, :chat_id, :sender_id, :content, :timestamp)"""),
                    {"id": message.id, "chat_id": chat_id, "sender_id": message.sender_id, 
                     "content": message.content, "timestamp": message.timestamp.isoformat()}
                )
            return True
        except Exception:
            raise

    def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat"""
        try:
            with pool.begin() as conn:
                conn.execute(
                    text("DELETE FROM chats WHERE id = :chat_id"),
                    {"chat_id": chat_id}
                )
                # Check if chat still exists
                count = conn.execute(
                    text("SELECT COUNT(*) as cnt FROM chats WHERE id = :chat_id"),
                    {"chat_id": chat_id}
                ).fetchone().cnt
                return count > 0
        except Exception:
            raise

    def get_user_chats(self, user_id: str) -> List[Chat]:
        """Get all chats for a user"""
        try:
            with pool.connect() as conn:
                chats_data = conn.execute(
                    text("""SELECT DISTINCT c.id 
                            FROM chats c
                            JOIN chat_participants cp ON c.id = cp.chat_id
                            WHERE cp.user_id = :user_id"""),
                    {"user_id": user_id}
                ).fetchall()

            return [self.get_chat_by_id(chat.id) for chat in chats_data]
        except Exception:
            raise

    def remove_participant(self, chat_id: str, user_id: str) -> bool:
        """Remove a participant from a chat"""
        try:
            with pool.begin() as conn:
                conn.execute(
                    text("""DELETE FROM chat_participants 
                            WHERE chat_id = :chat_id AND user_id = :user_id"""),
                    {"chat_id": chat_id, "user_id": user_id}
                )
                count = conn.execute(
                    text("SELECT COUNT(*) as cnt FROM chats WHERE id = :chat_id"),
                    {"chat_id": chat_id}
                ).fetchone().cnt
                return count > 0
        except Exception:
            raise

    def is_participant(self, chat_id: str, user_id: str) -> bool:
        """Check if a user is a participant in a chat"""
        try:
            with pool.connect() as conn:
                chat_data = conn.execute(
                    text("""SELECT 1 FROM chat_participants 
                            WHERE chat_id = :chat_id AND user_id = :user_id"""),
                    {"chat_id": chat_id, "user_id": user_id}
                ).fetchone()
                return chat_data is not None
        except Exception:
            raise
