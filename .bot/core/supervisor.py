import os
import time
import json
import logging
from typing import Any

from .base import Observer, Event

logger = logging.getLogger("core.supervisor")


class Supervisor(Observer):
    def __init__(self, log_dir: str = "data/logs"):
        os.makedirs(log_dir, exist_ok=True)
        self.logfile = os.path.join(log_dir, f"log_{int(time.time())}.ndjson")

    async def on_event(self, event: Event) -> None:
        try:
            entry = {
                "timestamp": time.time(),
                "event_type": event.event_type.name if hasattr(event, 'event_type') else str(event),
                "data": getattr(event, 'data', None),
                "metadata": getattr(event, 'metadata', None)
            }
            with open(self.logfile, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, default=str, ensure_ascii=False) + "\n")
        except Exception:
            logger.exception("Falha ao gravar evento no supervisor")

    # Backwards-compatible helper
    def log(self, event: str, payload: Any):
        try:
            entry = {
                "timestamp": time.time(),
                "event": event,
                "payload": payload
            }
            with open(self.logfile, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, default=str, ensure_ascii=False) + "\n")
        except Exception:
            logger.exception("Falha ao gravar log no supervisor")
