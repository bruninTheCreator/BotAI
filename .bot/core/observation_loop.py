"""
Background observation loop for periodic OCR and pattern mining.
"""

from __future__ import annotations

import hashlib
import threading
import time
from typing import Any, Callable, Optional

from .detector_repeticao import normalize_text


class ObservationLoop:
    def __init__(
        self,
        read_text_fn: Callable[[], str],
        memory: Any,
        pattern_engine: Optional[Any] = None,
        on_pattern_match: Optional[Callable[[dict, float], None]] = None,
        interval_s: int = 30,
        min_text_chars: int = 20,
        mine_every: int = 5,
        match_threshold: float = 0.78,
        match_cooldown_s: int = 600,
    ) -> None:
        self.read_text_fn = read_text_fn
        self.memory = memory
        self.pattern_engine = pattern_engine
        self.on_pattern_match = on_pattern_match
        self.interval_s = max(5, int(interval_s))
        self.min_text_chars = max(5, int(min_text_chars))
        self.mine_every = max(1, int(mine_every))
        self.match_threshold = float(match_threshold)
        self.match_cooldown_s = max(0, int(match_cooldown_s))

        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_hash: Optional[str] = None
        self._since_mine = 0
        self._last_match_id: Optional[str] = None
        self._last_match_ts: float = 0.0

    def start(self) -> bool:
        if self._thread and self._thread.is_alive():
            return False
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="ObservationLoop", daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        self._stop.set()

    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self._tick()
            except Exception:
                # keep loop alive on errors
                pass
            self._stop.wait(self.interval_s)

    def _tick(self) -> None:
        text = ""
        try:
            text = self.read_text_fn() or ""
        except Exception:
            text = ""

        norm = normalize_text(text)
        if len(norm) < self.min_text_chars:
            return

        h = hashlib.sha1(norm.encode("utf-8", errors="ignore")).hexdigest()[:16]
        if h == self._last_hash:
            return
        self._last_hash = h

        try:
            if hasattr(self.memory, "save") and callable(getattr(self.memory, "save")):
                self.memory.save(
                    "observation",
                    {
                        "text": text,
                        "text_norm": norm,
                        "text_hash": h,
                        "source": "ocr",
                    },
                )
        except Exception:
            return

        self._since_mine += 1
        if self.pattern_engine and self._since_mine >= self.mine_every:
            new_patterns = []
            try:
                new_patterns = self.pattern_engine.update()
            except Exception:
                new_patterns = []
            self._since_mine = 0
            if new_patterns:
                # lightweight notification to console
                try:
                    print(f"[pattern] new patterns: {len(new_patterns)}")
                except Exception:
                    pass

        # pattern recognition (real-time)
        if self.pattern_engine and hasattr(self.pattern_engine, "match_text"):
            try:
                match = self.pattern_engine.match_text(text, threshold=self.match_threshold)
            except Exception:
                match = None
            if match and match.get("pattern"):
                pid = match["pattern"].get("id")
                now = time.time()
                if pid != self._last_match_id or (now - self._last_match_ts) > self.match_cooldown_s:
                    self._last_match_id = pid
                    self._last_match_ts = now
                    if self.on_pattern_match:
                        try:
                            self.on_pattern_match(match["pattern"], float(match.get("score", 0.0)))
                        except Exception:
                            pass
                    else:
                        try:
                            label = match["pattern"].get("label", "pattern")
                            print(f"[pattern] match: {label}")
                        except Exception:
                            pass
