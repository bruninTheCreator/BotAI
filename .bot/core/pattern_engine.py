"""
Pattern mining and persistence for BotAI.

This module discovers repeated screen-text patterns using semantic similarity
and simple temporal heuristics. It stores patterns to disk so they can be
reviewed and later linked to actions.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from .detector_repeticao import normalize_text
from .memory_vector import MemoryVectorStore


def _iso_from_ts(ts: float) -> str:
    try:
        return datetime.fromtimestamp(ts).isoformat()
    except Exception:
        return datetime.now().isoformat()


def _event_ts(event: Dict[str, Any]) -> float:
    ts = event.get("timestamp")
    if isinstance(ts, (int, float)):
        return float(ts)
    dt = event.get("datetime")
    if isinstance(dt, str):
        try:
            return datetime.fromisoformat(dt).timestamp()
        except Exception:
            return time.time()
    return time.time()


def _short_hash(text: str, size: int = 12) -> str:
    h = hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()
    return h[:size]


def _extract_keywords(texts: Iterable[str], max_words: int = 4) -> List[str]:
    stop = {
        "a", "o", "e", "de", "da", "do", "das", "dos", "um", "uma", "uns", "umas",
        "para", "por", "em", "no", "na", "nos", "nas", "com", "sem", "que", "se",
        "ao", "aos", "as", "os", "the", "and", "or", "to", "in", "on", "for",
        "of", "is", "are", "this", "that", "it", "you", "your", "me", "my",
    }
    counts: Counter[str] = Counter()
    for t in texts:
        norm = normalize_text(t)
        for token in norm.split():
            if token and token not in stop and len(token) > 2:
                counts[token] += 1
    if not counts:
        return []
    return [w for w, _ in counts.most_common(max_words)]


@dataclass
class Pattern:
    id: str
    label: str
    count: int
    confidence: float
    first_seen: str
    last_seen: str
    hours: Dict[str, int] = field(default_factory=dict)
    examples: List[str] = field(default_factory=list)
    mode: str = "suggest"
    enabled: bool = True
    action: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "count": self.count,
            "confidence": self.confidence,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "hours": self.hours,
            "examples": self.examples,
            "mode": self.mode,
            "enabled": self.enabled,
            "action": self.action,
        }


class PatternMiner:
    def __init__(
        self,
        similarity_threshold: float = 0.75,
        min_count: int = 3,
        min_text_chars: int = 20,
        max_examples: int = 3,
    ) -> None:
        self.similarity_threshold = similarity_threshold
        self.min_count = min_count
        self.min_text_chars = min_text_chars
        self.max_examples = max_examples

    def _extract_observations(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        obs: List[Dict[str, Any]] = []
        for e in events:
            if (e.get("event_type") or "") != "observation":
                continue
            data = e.get("data") or {}
            text = data.get("text") or ""
            norm = data.get("text_norm") or normalize_text(text)
            if not norm:
                continue
            ts = _event_ts(e)
            obs.append({"text": text, "norm": norm, "ts": ts})
        return obs

    def mine(self, events: List[Dict[str, Any]]) -> List[Pattern]:
        observations = self._extract_observations(events)
        if not observations:
            return []

        store = MemoryVectorStore()
        clusters: Dict[str, Dict[str, Any]] = {}

        for ob in observations:
            norm = ob["norm"]
            if len(norm) < self.min_text_chars:
                continue

            best_id = None
            best_score = 0.0
            if clusters:
                top = store.query_similar(norm, k=1)
                if top:
                    best_id, best_score, _ = top[0]

            if best_id and best_score >= self.similarity_threshold:
                c = clusters[best_id]
                c["count"] += 1
                c["last_ts"] = max(c["last_ts"], ob["ts"])
                if len(c["examples"]) < self.max_examples:
                    c["examples"].append(ob["text"])
                hour = datetime.fromtimestamp(ob["ts"]).strftime("%H")
                c["hours"][hour] = c["hours"].get(hour, 0) + 1
            else:
                pid = f"pat_{_short_hash(norm)}"
                if pid in clusters:
                    pid = f"{pid}_{_short_hash(norm + str(len(clusters)))}"
                store.add_text(norm, id=pid)
                clusters[pid] = {
                    "rep": norm,
                    "count": 1,
                    "first_ts": ob["ts"],
                    "last_ts": ob["ts"],
                    "examples": [ob["text"]],
                    "hours": {datetime.fromtimestamp(ob["ts"]).strftime('%H'): 1},
                }

        patterns: List[Pattern] = []
        for pid, c in clusters.items():
            if c["count"] < self.min_count:
                continue
            freq_score = min(1.0, c["count"] / max(self.min_count * 2, 6))
            hour_peak = max(c["hours"].values()) / float(c["count"])
            confidence = round((freq_score * 0.5) + (hour_peak * 0.5), 3)

            keywords = _extract_keywords(c["examples"])
            label = "pattern"
            if keywords:
                label = "pattern: " + " ".join(keywords)

            patterns.append(
                Pattern(
                    id=pid,
                    label=label,
                    count=c["count"],
                    confidence=confidence,
                    first_seen=_iso_from_ts(c["first_ts"]),
                    last_seen=_iso_from_ts(c["last_ts"]),
                    hours=c["hours"],
                    examples=c["examples"],
                )
            )

        patterns.sort(key=lambda p: (p.confidence, p.count), reverse=True)
        return patterns


class PatternStore:
    def __init__(self, path: str) -> None:
        self.path = path
        self._patterns: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.path):
            self._patterns = {}
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                self._patterns = {p["id"]: p for p in data if isinstance(p, dict) and "id" in p}
            elif isinstance(data, dict):
                self._patterns = {p["id"]: p for p in data.get("patterns", []) if isinstance(p, dict)}
            else:
                self._patterns = {}
        except Exception:
            self._patterns = {}

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        data = list(self._patterns.values())
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_patterns(self) -> List[Dict[str, Any]]:
        return list(self._patterns.values())

    def update_pattern(self, pattern_id: str, **fields: Any) -> bool:
        if not pattern_id or pattern_id not in self._patterns:
            return False
        self._patterns[pattern_id].update(fields)
        self._save()
        return True

    def merge(self, patterns: List[Pattern]) -> List[Pattern]:
        new_patterns: List[Pattern] = []
        for p in patterns:
            if p.id in self._patterns:
                existing = self._patterns[p.id]
                existing["count"] = p.count
                existing["confidence"] = p.confidence
                existing["first_seen"] = existing.get("first_seen") or p.first_seen
                existing["last_seen"] = p.last_seen
                existing["hours"] = p.hours
                if p.examples:
                    existing["examples"] = p.examples
                # keep mode/enabled/action from existing
                self._patterns[p.id] = existing
            else:
                self._patterns[p.id] = p.to_dict()
                new_patterns.append(p)
        self._save()
        return new_patterns


class PatternEngine:
    def __init__(
        self,
        memory: Any,
        patterns_path: Optional[str] = None,
        miner: Optional[PatternMiner] = None,
        max_events: int = 800,
    ) -> None:
        self.memory = memory
        self.miner = miner or PatternMiner()
        if not patterns_path:
            base = None
            try:
                base = os.path.dirname(getattr(memory, "file_path"))
            except Exception:
                base = None
            patterns_path = os.path.join(base, "patterns.json") if base else "data/patterns.json"
        self.store = PatternStore(patterns_path)
        self.max_events = max_events

    def _load_events(self) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        try:
            if hasattr(self.memory, "load_all") and callable(getattr(self.memory, "load_all")):
                events = self.memory.load_all() or []
            elif hasattr(self.memory, "list_all") and callable(getattr(self.memory, "list_all")):
                res = self.memory.list_all()
                try:
                    import asyncio
                    if asyncio.iscoroutine(res):
                        res = asyncio.run(res)
                except Exception:
                    pass
                if hasattr(res, "success") and res.success:
                    events = res.data or []
                elif isinstance(res, list):
                    events = res
        except Exception:
            events = []
        if self.max_events and len(events) > self.max_events:
            events = events[-self.max_events:]
        return events

    def update(self) -> List[Pattern]:
        events = self._load_events()
        patterns = self.miner.mine(events)
        return self.store.merge(patterns)

    def list_patterns(self, top: int = 10, sort_by: str = "confidence") -> List[Dict[str, Any]]:
        patterns = self.store.list_patterns()
        if sort_by == "count":
            patterns.sort(key=lambda p: p.get("count", 0), reverse=True)
        else:
            patterns.sort(key=lambda p: p.get("confidence", 0), reverse=True)
        if top and len(patterns) > top:
            patterns = patterns[:top]
        return patterns

    def match_text(self, text: str, threshold: float = 0.78) -> Optional[Dict[str, Any]]:
        norm = normalize_text(text or "")
        if len(norm) < 10:
            return None

        patterns = [p for p in self.store.list_patterns() if p.get("enabled", True)]
        if not patterns:
            return None

        store = MemoryVectorStore()
        id_to_pattern: Dict[str, Dict[str, Any]] = {}
        for p in patterns:
            corpus = " ".join((p.get("examples") or [])[:2]).strip()
            if not corpus:
                corpus = p.get("label", "")
            if not corpus:
                continue
            pid = p.get("id")
            if not pid:
                continue
            store.add_text(corpus, id=pid)
            id_to_pattern[pid] = p

        if not id_to_pattern:
            return None

        top = store.query_similar(norm, k=1)
        if not top:
            return None
        pid, score, _ = top[0]
        if score < threshold:
            return None
        return {"pattern": id_to_pattern.get(pid), "score": score}
