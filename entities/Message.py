from dataclasses import dataclass
from datetime import datetime

@dataclass
class Message:
    sender_id: str
    content: str