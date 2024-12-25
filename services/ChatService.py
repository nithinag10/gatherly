from typing import Optional, List, Tuple
from entities.Chat import Chat
from entities.User import User
from entities.Message import Message
from repositories.ChatRepository import ChatRepository
from repositories.UserRepository import UserRepository
import uuid

class ChatService:
    def __init__(self, chat_repository: ChatRepository, user_repository: UserRepository):
        """
        Initialize ChatService with required repositories
        
        Args:
            chat_repository (ChatRepository): Repository for chat operations
            user_repository (UserRepository): Repository for user operations
        """
        self.chat_repository = chat_repository
        self.user_repository = user_repository

    def create_chat(self, creator_id: str, chat_id: str, chat_name: str, agenda: str) -> Tuple[Optional[Chat], str]:
        """
        Create a new chat with the given creator as admin
        
        Args:
            creator_id (str): ID of the user creating the chat
            chat_id (str): Desired chat ID
            chat_name (str): Name of the chat
            agenda (str): Agenda of the chat
            
        Returns:
            Tuple[Optional[Chat], str]: (Chat object or None, success/error message)
        """
        # Check if chat ID already exists
        if self.chat_repository.get_chat_by_id(chat_id):
            return None, "Chat ID already exists"

        # Verify creator exists
        creator = self.user_repository.get_user_by_id(creator_id)
        if not creator:
            return None, "Creator not found"

        # Create new chat
        new_chat = Chat(
            id=chat_id,
            admin_id=creator_id,
            participants=[creator_id],
            chat_name=chat_name,
            agenda=agenda
        )
        
        saved_chat = self.chat_repository.save_chat(new_chat)
        return saved_chat, "Chat created successfully"


    def join_chat(self, user_id: str, chat_id: str) -> Tuple[bool, str]:
        """
        Add a user to an existing chat
        
        Args:
            user_id (str): ID of the user joining the chat
            chat_id (str): ID of the chat to join
            
        Returns:
            Tuple[bool, str]: (Success status, success/error message)
        """
        # Verify user exists
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            return False, "User not found"

        # Verify chat exists
        chat = self.chat_repository.get_chat_by_id(chat_id)
        if not chat:
            return False, "Chat not found"

        # Check if user is already in chat using is_participant
        if self.chat_repository.is_participant(chat_id, user_id):
            return False, "User is already in the chat"

        # Add user to chat
        success = self.chat_repository.add_participant(chat_id, user_id)
        if success:
            return True, "User joined chat successfully"
        return False, "Failed to add user to chat"

    def send_message(self, user_id: str, chat_id: str, content: str) -> Tuple[bool, str]:
        """
        Send a message in a chat
        
        Args:
            user_id (str): ID of the message sender
            chat_id (str): ID of the chat
            content (str): Message content
            
        Returns:
            Tuple[bool, str]: (Success status, success/error message)
        """
        # Verify chat exists
        chat = self.chat_repository.get_chat_by_id(chat_id)
        if not chat:
            return False, "Chat not found"

        # Verify user is in chat using is_participant
        if not self.chat_repository.is_participant(chat_id, user_id):
            return False, "User is not a participant in this chat"

        # Create and add message
        message = Message(
            id=str(uuid.uuid4()),  # Using UUID for message ID
            sender_id=user_id,
            content=content
        )
        
        success = self.chat_repository.add_message(chat_id, message)
        if success:
            return True, "Message sent successfully"
        return False, "Failed to send message"

    def leave_chat(self, user_id: str, chat_id: str) -> Tuple[bool, str]:
        """
        Remove a user from a chat
        
        Args:
            user_id (str): ID of the user leaving the chat
            chat_id (str): ID of the chat
            
        Returns:
            Tuple[bool, str]: (Success status, success/error message)
        """
        chat = self.chat_repository.get_chat_by_id(chat_id)
        if not chat:
            return False, "Chat not found"

        # Check if user is in chat using is_participant
        if not self.chat_repository.is_participant(chat_id, user_id):
            return False, "User is not in the chat"

        if user_id == chat.admin_id:
            return False, "Admin cannot leave the chat"

        success = self.chat_repository.remove_participant(chat_id, user_id)
        if success:
            return True, "User left chat successfully"
        return False, "Failed to remove user from chat"

    def get_chat_summary(self, chat_id: str) -> Tuple[Optional[dict], str]:
        """
        Get a summary of the chat
        
        Args:
            chat_id (str): ID of the chat
            
        Returns:
            Tuple[Optional[dict], str]: (Chat summary or None, success/error message)
        """
        summary = self.chat_repository.get_chat_summary(chat_id)
        if summary:
            return summary, "Summary retrieved successfully"
        return None, "Chat not found"

    def delete_chat(self, user_id: str, chat_id: str) -> Tuple[bool, str]:
        """
        Delete a chat (admin only)
        
        Args:
            user_id (str): ID of the user requesting deletion
            chat_id (str): ID of the chat to delete
            
        Returns:
            Tuple[bool, str]: (Success status, success/error message)
        """
        chat = self.chat_repository.get_chat_by_id(chat_id)
        if not chat:
            return False, "Chat not found"

        if user_id != chat.admin_id:
            return False, "Only admin can delete the chat"

        success = self.chat_repository.delete_chat(chat_id)
        if success:
            return True, "Chat deleted successfully"
        return False, "Failed to delete chat"
