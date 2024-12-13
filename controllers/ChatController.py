from flask import Blueprint, request, jsonify
from services.ChatService import ChatService
from repositories.ChatRepository import ChatRepository
from repositories.UserRepository import UserRepository
import uuid
from datetime import datetime
from entities.Message import Message

# Create Blueprint for chat routes
chat_controller = Blueprint('chat_controller', __name__)

# Initialize repositories and service
chat_repo = ChatRepository()
user_repo = UserRepository()
chat_service = ChatService(chat_repo, user_repo)

@chat_controller.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@chat_controller.route('/chats', methods=['POST'])
def create_chat():
    """Create a new chat"""
    try:
        data = request.get_json()
        
        if not data or 'creator_id' not in data:
            return jsonify({
                "error": "Missing required fields: creator_id"
            }), 400

        chat_id = str(uuid.uuid4())
        chat, message = chat_service.create_chat(data['creator_id'], chat_id)
        
        if not chat:
            return jsonify({"error": message}), 400
            
        return jsonify({
            "message": message,
            "chat": {
                "id": chat.id,
                "admin_id": chat.admin_id,
                "participants": chat.participants
            }
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chat_controller.route('/chats/<chat_id>/join', methods=['POST'])
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

@chat_controller.route('/chats/<chat_id>/leave', methods=['POST'])
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

@chat_controller.route('/chats/<chat_id>', methods=['GET'])
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

@chat_controller.route('/chats/<chat_id>', methods=['DELETE'])
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

@chat_controller.route('/chats/<chat_id>/messages', methods=['GET'])
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
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                } for msg in messages
            ]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chat_controller.route('/chats/<chat_id>/messages', methods=['POST'])
def send_message(chat_id):
    """Send a message in a chat"""
    try:
        data = request.get_json()
        
        # Validate request data
        if not data or 'user_id' not in data or 'content' not in data:
            return jsonify({
                "error": "Missing required fields: user_id, content"
            }), 400
        
        # Create message with UUID
        message_id = str(uuid.uuid4())
        message = Message(
            id=message_id,
            sender_id=data['user_id'],
            content=data['content'],
            timestamp=datetime.now()
        )
        
        # Send message using service
        success, response_message = chat_service.send_message(
            data['user_id'], 
            chat_id, 
            data['content']
        )
        
        if not success:
            return jsonify({"error": response_message}), 400
            
        return jsonify({
            "message": response_message,
            "data": {
                "message_id": message_id,
                "chat_id": chat_id,
                "sender_id": data['user_id'],
                "content": data['content'],
                "timestamp": message.timestamp.isoformat()
            }
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500 