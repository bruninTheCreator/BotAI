
import datetime


class Memory:
    def __init__(self):
        self.events = []

    def save(self, event_type: str, data: dict):
        """Salva um evento na memória com um timestamp."""
        timestamp = datetime.datetime.now().isoformat()
        self.events.append({
            "timestamp": timestamp,
            "type": event_type,
            "data": data
        })

    def load_all(self):
        """Carrega todos os eventos da memória."""
        return self.events

    def clear(self):
        """Limpa todos os eventos da memória."""
        self.events = []
