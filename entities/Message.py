from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Message:  
    sender_id: str
    content: str
    id: Optional[str] = None
    timestamp: Optional[datetime] = None
    sender_name: Optional[str] = None