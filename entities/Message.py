from dataclasses import dataclass
from datetime import datetime

@dataclass
class Message:
    id: str
    sender_id: str
    content: str
    timestamp: datetime = datetime.now() 