import os
import json
import time
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any

from .base import Memory as MemoryABC, Result, Event


class Memory(MemoryABC):
    def __init__(self, file_path: str = "data/memory_log.jsonl"):
        self.file_path = file_path
        os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)

    # Backwards-compatible synchronous save used by legacy code
    def save(self, event_type: str, data: dict):
        entry = {
            "id": str(time.time()).replace('.', ''),
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        with open(self.file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry["id"]

    # Async methods to satisfy the abstract Repository/Memory interface
    async def save_item(self, item: Dict[str, Any]) -> Result[str]:
        try:
            # item may already be an Event-like dict
            _id = self.save(item.get('event_type', 'event'), item.get('data', {}))
            return Result.ok(_id)
        except Exception as e:
            return Result.from_error(str(e))

    async def load(self, id: str) -> Result[Optional[Dict[str, Any]]]:
        try:
            if not os.path.exists(self.file_path):
                return Result.ok(None)
            with open(self.file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    obj = json.loads(line)
                    if str(obj.get('id')) == str(id):
                        return Result.ok(obj)
            return Result.ok(None)
        except Exception as e:
            return Result.from_error(str(e))

    async def delete(self, id: str) -> Result[None]:
        try:
            if not os.path.exists(self.file_path):
                return Result.ok(None)
            lines = []
            with open(self.file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    obj = json.loads(line)
                    if str(obj.get('id')) != str(id):
                        lines.append(obj)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                for obj in lines:
                    f.write(json.dumps(obj, ensure_ascii=False) + "\n")
            return Result.ok(None)
        except Exception as e:
            return Result.from_error(str(e))

    async def list_all(self) -> Result[List[Dict[str, Any]]]:
        try:
            if not os.path.exists(self.file_path):
                return Result.ok([])
            with open(self.file_path, 'r', encoding='utf-8') as f:
                items = [json.loads(line) for line in f if line.strip()]
            return Result.ok(items)
        except Exception as e:
            return Result.from_error(str(e))

    async def get_recent(self, limit: int = 10) -> Result[List[Dict[str, Any]]]:
        res = await self.list_all()
        if not res.success:
            return res
        items = res.data or []
        return Result.ok(items[-limit:] if len(items) > limit else items)

    async def search(self, criteria: Dict[str, Any]) -> Result[List[Dict[str, Any]]]:
        try:
            res = await self.list_all()
            if not res.success:
                return res
            items = res.data or []
            # Very simple filter: each key in criteria must match in event.data
            def match(item):
                data = item.get('data', {})
                for k, v in criteria.items():
                    if data.get(k) != v:
                        return False
                return True

            filtered = [it for it in items if match(it)]
            return Result.ok(filtered)
        except Exception as e:
            return Result.from_error(str(e))

    # Convenience/legacy helpers
    def load_all(self):
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return [json.loads(line) for line in f if line.strip()]
        except Exception:
            return []

    def get_recent_context(self, limit: int = 10):
        all_events = self.load_all()
        return all_events[-limit:] if len(all_events) > limit else all_events

    def clear(self):
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
            return True
        return False
