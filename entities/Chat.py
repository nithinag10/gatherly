from dataclasses import dataclass, field
from typing import List
from .Message import Message

@dataclass
class Chat:
    id: str
    admin_id: str
    participants: List[str] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list) 