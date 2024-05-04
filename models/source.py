from enum import Enum


class Source(Enum):
    """Source of Discord requests."""
    DISCORD = "Discord"
    API = "API"
