from typing import Optional, Tuple
from entities.User import User
from repositories.UserRepository import UserRepository
from utils.auth import hash_password, verify_password, create_token
import uuid
import requests
from config.oauth import client, GOOGLE_DISCOVERY_URL, GOOGLE_CLIENT_ID

class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def register(self, email: str, password: str, name: str) -> Tuple[Optional[User], str]:
        if self.user_repository.get_user_by_email(email):
            return None, "Email already exists"
        
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            name=name,
            password_hash=hash_password(password)
        )
        saved_user = self.user_repository.save_user(user)
        return saved_user, "Registration successful"

    def login(self, email: str, password: str) -> Tuple[Optional[str], str]:
        user = self.user_repository.get_user_by_email(email)

        print("Printing got user")
        print(user)

        if not user or not verify_password(password, user.password_hash):
            return None, "Invalid credentials"
            
        token = create_token(user.id)
        return token, "Login successful"

    def get_google_auth_url(self) -> str:
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        
        return client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=GOOGLE_REDIRECT_URI,
            scope=["openid", "email", "profile"],
        )

    def handle_google_callback(self, code: str) -> Tuple[Optional[str], str]:
        try:
            google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
            token_endpoint = google_provider_cfg["token_endpoint"]

            # Get tokens
            token_url, headers, body = client.prepare_token_request(
                token_endpoint,
                authorization_response=code,
                redirect_url=GOOGLE_REDIRECT_URI,
                client_secret=GOOGLE_CLIENT_SECRET
            )
            token_response = requests.post(token_url, headers=headers, data=body)
            client.parse_request_body_response(token_response.text)

            # Get user info
            userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
            uri, headers, body = client.add_token(userinfo_endpoint)
            userinfo_response = requests.get(uri, headers=headers, data=body)
            
            if userinfo_response.json().get("email_verified"):
                google_id = userinfo_response.json()["sub"]
                email = userinfo_response.json()["email"]
                name = userinfo_response.json()["given_name"]
                
                # Check if user exists
                user = self.user_repository.get_user_by_email(email)
                if not user:
                    # Create new user
                    user = User(
                        id=str(uuid.uuid4()),
                        email=email,
                        name=name,
                        google_id=google_id
                    )
                    self.user_repository.save_user(user)
                
                # Generate token
                token = create_token(user.id)
                return token, "Login successful"
            
            return None, "Google authentication failed"
            
        except Exception as e:
            return None, str(e)