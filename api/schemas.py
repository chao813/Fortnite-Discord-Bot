from typing import Dict, List

from pydantic import BaseModel


class SendMessagePayload(BaseModel):
    """Send message to Discord request payload."""
    message: str


class GameEliminationPayload(BaseModel):
    """Game elimination data request payload."""
    game_mode: str
    killed: Dict[str, List[str]]
    killed_by: Dict[str, List[str]]
