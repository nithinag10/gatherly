from dataclasses import dataclass, field
from typing import List
from .Message import Message
from datetime import datetime
from typing import Optional

@dataclass
class Chat:
    id: str
    admin_id: str
    chat_name: str
    agenda: str
    created_at: datetime
    participants: List[str] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list)
    created_at : Optional[datetime] = None