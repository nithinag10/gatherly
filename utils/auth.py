from passlib.hash import bcrypt
import jwt
import os
from datetime import datetime, timedelta

JWT_SECRET = os.getenv('JWT_SECRET', 'dev-secret')

def hash_password(password: str) -> str:
    return bcrypt.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.verify(password, hashed)

def create_token(user_id: str) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])