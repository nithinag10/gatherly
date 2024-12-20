from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    id: str
    email: str
    name: str
    password_hash: str = None  # Optional for OAuth users
    google_id: str = None
    created_at: datetime = datetime.utcnow()