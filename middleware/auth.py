from functools import wraps
from flask import request, jsonify
from utils.auth import verify_token

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({"error": "No token provided"}), 401

        try:
            payload = verify_token(token)
            request.user_id = payload['user_id']
        except Exception:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    return decorated