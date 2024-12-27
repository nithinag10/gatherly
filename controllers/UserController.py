from flask import Blueprint, request, jsonify
from services.AuthService import AuthService
from repositories.UserRepository import UserRepository

user_controller = Blueprint('user_controller', __name__)
auth_service = AuthService(UserRepository())

@user_controller.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not all(k in data for k in ('email', 'password', 'name')):
        return jsonify({"error": "Missing required fields"}), 400

    user, message = auth_service.register(
        data['email'], 
        data['password'],
        data['name']
    )
    
    if not user:
        return jsonify({"error": message}), 400
    
    return jsonify({"message": message}), 201

@user_controller.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not all(k in data for k in ('email', 'password')):
        return jsonify({"error": "Missing credentials"}), 400

    token, message , user_id = auth_service.login(data['email'], data['password'])
    
    if not token:
        return jsonify({"error": message}), 401
        
    return jsonify({
        "token": token,
        "message": message,
        "user_id": user_id
    }), 200

@user_controller.route('/google/login')
def google_login():
    auth_url = auth_service.get_google_auth_url()
    return jsonify({"auth_url": auth_url})

@user_controller.route('/google/callback')
def google_callback():
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "Code not provided"}), 400
        
    token, message = auth_service.handle_google_callback(code)
    if not token:
        return jsonify({"error": message}), 401
        
    return jsonify({
        "token": token,
        "message": message
    }), 200