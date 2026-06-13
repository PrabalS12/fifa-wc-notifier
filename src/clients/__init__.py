"""External API clients."""

from src.clients.football import FootballClient
from src.clients.whatsapp import WhatsAppClient
from src.clients.youtube import highlights_url

__all__ = ["FootballClient", "WhatsAppClient", "highlights_url"]
