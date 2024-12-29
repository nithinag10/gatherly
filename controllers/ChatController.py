from flask import Blueprint, request, jsonify
from services.ChatService import ChatService
from repositories.ChatRepository import ChatRepository
from repositories.UserRepository import UserRepository
import uuid
from datetime import datetime
from entities.Message import Message
from services.SummaryService import SummaryService
import logging
import traceback

# Initialize logger
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Create Blueprint for chat routes
chat_controller = Blueprint('chat_controller', __name__)

# Initialize repositories and service
chat_repo = ChatRepository()
user_repo = UserRepository()
chat_service = ChatService(chat_repo, user_repo)

# Initialize SummaryService
summary_service = SummaryService(chat_repo, chat_service)

@chat_controller.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200



@chat_controller.route('/create', methods=['POST'])
def create_chat():
    """Create a new chat"""
    try:
        logger.debug("Request received to create a chat")
        data = request.get_json()
        
        if not data or 'creator_id' not in data or 'chat_name' not in data or 'agenda' not in data:
            logger.warning("Request missing required fields: creator_id, chat_name, agenda")
            return jsonify({
                "error": "Missing required fields: creator_id, chat_name, agenda"
            }), 400

        logger.debug("Request data: %s", data)
        chat_id = str(uuid.uuid4())
        logger.debug("Generated chat ID: %s", chat_id)
        
        # Simulate calling chat service (add logs inside chat_service too if needed)
        chat, message = chat_service.create_chat(
            creator_id=data['creator_id'],
            chat_id=chat_id,
            chat_name=data['chat_name'],
            agenda=data['agenda']
        )
        
        if not chat:
            logger.error("Failed to create chat: %s", message)
            return jsonify({"error": message}), 400
            
        logger.info("Chat created successfully: %s", chat.id)
        return jsonify({
            "message": message,
            "chat": {
                "id": chat.id,
                "admin_id": chat.admin_id,
                "participants": chat.participants,
                "chat_name": chat.chat_name,
                "agenda": chat.agenda
            }
        }), 201

    except Exception as e:
        logger.error("An error occurred while creating a chat: %s", str(e))
        print("Stack trace: %s", traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred"}), 500


@chat_controller.route('/<chat_id>/join', methods=['POST'])
def join_chat(chat_id):
    """Join an existing chat"""
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data:
            return jsonify({
                "error": "Missing required field: user_id"
            }), 400
        
        success, message = chat_service.join_chat(data['user_id'], chat_id)
        
        if not success:
            return jsonify({"error": message}), 400
            
        return jsonify({"message": message}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chat_controller.route('/<chat_id>/leave', methods=['POST'])
def leave_chat(chat_id):
    """Leave a chat"""
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data:
            return jsonify({
                "error": "Missing required field: user_id"
            }), 400
        
        success, message = chat_service.leave_chat(data['user_id'], chat_id)
        
        if not success:
            return jsonify({"error": message}), 400
            
        return jsonify({"message": message}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chat_controller.route('/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    """Get chat details"""
    try:
        chat = chat_repo.get_chat_by_id(chat_id)
        
        if not chat:
            return jsonify({"error": "Chat not found"}), 404
            
        return jsonify({
            "id": chat.id,
            "admin_id": chat.admin_id,
            "participants": chat.participants,
            "messages": [
                {
                    "id": msg.id,
                    "sender_id": msg.sender_id,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                } for msg in chat.messages
            ]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chat_controller.route('/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """Delete a chat"""
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data:
            return jsonify({
                "error": "Missing required field: user_id"
            }), 400
        
        success, message = chat_service.delete_chat(data['user_id'], chat_id)
        
        if not success:
            return jsonify({"error": message}), 400
            
        return jsonify({"message": message}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chat_controller.route('/<chat_id>/messages', methods=['GET'])
def get_messages(chat_id):
    """Get recent messages from a chat"""
    try:
        # Get limit from query params, default to 10
        limit = request.args.get('limit', default=10, type=int)
        
        # Get chat
        chat = chat_repo.get_chat_by_id(chat_id)
        if not chat:
            return jsonify({"error": "Chat not found"}), 404
        
        # Get messages ordered by timestamp
        messages = chat.messages[-limit:] if limit > 0 else chat.messages
        
        return jsonify({
            "chat_id": chat_id,
            "messages": [
                {
                    "id": msg.id,
                    "sender_id": msg.sender_id,
                    "sender_name": msg.sender_name,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                } for msg in messages
            ]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chat_controller.route('/<chat_id>/messages', methods=['POST'])
def send_message(chat_id):
    """Send a message in a chat"""
    try:
        data = request.get_json()
        if not data or 'user_id' not in data or 'content' not in data:
            return jsonify({
                "error": "Missing required fields: user_id, content"
            }), 400

        # Send message
        success, message = chat_service.send_message(
            data['user_id'], 
            chat_id, 
            data['content']
        )
        
        if not success:
            return jsonify({"error": message}), 400

        # Get current message count
        chat = chat_repo.get_chat_by_id(chat_id)
        if chat and len(chat.messages) % 10 == 0:  # Check every 10 messages
            # Trigger context validation
            validation_result, _ = summary_service.validate_chat_context(chat_id)
            
            return jsonify({
                "message": message,
                "validation_triggered": True,
                "validation_result": validation_result,
                "data": {
                    "chat_id": chat_id,
                    "sender_id": data['user_id'],
                    "content": data['content']
                }
            }), 201

        return jsonify({
            "message": message,
            "validation_triggered": False,
            "data": {
                "chat_id": chat_id,
                "sender_id": data['user_id'],
                "content": data['content']
            }
        }), 201

    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return jsonify({"error": str(e)}), 500 

@chat_controller.route('/<chat_id>/summary', methods=['GET'])
def get_chat_summary(chat_id):
    """Get a summary of the chat"""
    try:
        summary, message = summary_service.get_chat_summary(chat_id)
        
        if not summary:
            return jsonify({"error": message}), 404
            
        return jsonify({
            "message": message,
            "summary": summary
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chat_controller.route('/<chat_id>/validate', methods=['GET'])
def validate_chat_context(chat_id):
    """Validate if chat messages align with the agenda"""
    try:
        validation_result, message = summary_service.validate_chat_context(chat_id)
        
        if not validation_result:
            return jsonify({
                "error": message,
                "chat_id": chat_id
            }), 404

        return jsonify({
            "chat_id": chat_id,
            "is_on_topic": validation_result["is_on_topic"],
            "validation_details": validation_result["validation_details"],
            "chat_name": validation_result["chat_name"],
            "message_count": validation_result["message_count"],
            "agenda": validation_result["agenda"],
            "message": message
        }), 200

    except Exception as e:
        logger.error(f"Error in validate_chat_context: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

@chat_controller.route('/user/<user_id>/chats', methods=['GET'])
def get_user_chats(user_id):
    """Get all chats for a user"""
    try:
        chats = chat_repo.get_user_chats(user_id)

        return jsonify({
            "chats": [{
                "id": chat.id,
                "admin_id": chat.admin_id,
                "chat_name": chat.chat_name,
                "agenda": chat.agenda,
                "created_at": chat.created_at.isoformat(),
                "participant_count": len(chat.participants),
                "last_message": chat.messages[-1].content if chat.messages else None
            } for chat in chats]
        }), 200

    except Exception as e:
        print("Stack trace: %s", traceback.format_exc())
        logger.error(f"Error getting user chats: {str(e)}")
        return jsonify({"error": str(e)}), 500