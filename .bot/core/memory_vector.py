"""Memória vetorial simples com fallback puro-Python.

Este módulo fornece uma store que indexa textos e faz consultas por similaridade.
Preferências:
- Se `sentence_transformers` estiver instalado, usa embeddings do modelo
  `all-MiniLM-L6-v2` por padrão.
- Caso contrário, usa um fallback baseado em contagem de tokens e similaridade
  por cosseno implementada em Python puro (funciona sem dependências).

API mínima:
- `MemoryVectorStore.index_texts(texts, ids=None)`
- `MemoryVectorStore.add_text(text, id=None)`
- `MemoryVectorStore.query_similar(query, k=5)` -> List of (id, score, text)

O objetivo é oferecer RAG/recall simples sem obrigar instalação de libs.
"""

from __future__ import annotations

import json
import math
import os
import re
import threading
import uuid
from typing import Dict, Iterable, List, Optional, Tuple

_TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)


def _token_counts(text: str) -> Dict[str, float]:
    tokens = _TOKEN_RE.findall((text or "").lower())
    counts: Dict[str, float] = {}
    for t in tokens:
        counts[t] = counts.get(t, 0.0) + 1.0
    return counts


def _dict_dot(a: Dict[str, float], b: Dict[str, float]) -> float:
    s = 0.0
    # iterate over smaller dict for efficiency
    if len(a) > len(b):
        a, b = b, a
    for k, va in a.items():
        vb = b.get(k)
        if vb is not None:
            s += va * vb
    return s


def _dict_norm(a: Dict[str, float]) -> float:
    s = 0.0
    for v in a.values():
        s += v * v
    return math.sqrt(s) if s > 0.0 else 1.0


class MemoryVectorStore:
    """Store simples para textos e embeddings.

    Usa sentence-transformers quando disponível, senão fallback token-counts.
    """

    def __init__(self, persist_path: Optional[str] = None, model_name: str = "all-MiniLM-L6-v2", st_model: Optional[object] = None):
        self._lock = threading.RLock()
        self._texts: Dict[str, str] = {}
        self._embeddings: Dict[str, Dict[str, float]] = {}
        self._norms: Dict[str, float] = {}
        self.persist_path = persist_path
        self._st_model = st_model
        self._st_available = False
        self._model_name = model_name

        # Detect availability of the sentence-transformers package but do NOT
        # instantiate a model here to avoid downloading large models at import
        # time (which can hang the test environment). If you want to use a
        # preloaded model, pass it via the `st_model` argument.
        try:
            import sentence_transformers  # type: ignore
            self._st_available = True
        except Exception:
            self._st_available = False

        if persist_path and os.path.exists(persist_path):
            try:
                self.load(persist_path)
            except Exception:
                # ignore load errors
                pass

    # ---- embedding helpers ----
    def _embed(self, text: str) -> Dict[str, float]:
        text = text or ""
        if self._st_model is not None:
            try:
                vec = self._st_model.encode(text, normalize_embeddings=True)
                # convert to list if numpy
                try:
                    arr = vec.tolist()
                except Exception:
                    arr = list(vec)
                return {str(i): float(v) for i, v in enumerate(arr)}
            except Exception:
                # model failed; fallback to token counts
                pass
        # fallback: token counts
        return _token_counts(text)

    # ---- public API ----
    def index_texts(self, texts: Iterable[str], ids: Optional[Iterable[str]] = None) -> List[str]:
        """Indexa múltiplos textos em lote e retorna a lista de ids criados/associados."""
        ids_list: List[str] = []
        with self._lock:
            if ids is None:
                for t in texts:
                    ids_list.append(self.add_text(t))
            else:
                for t, i in zip(texts, ids):
                    self.add_text(t, id=i)
                    ids_list.append(i)
            if self.persist_path:
                try:
                    self.save(self.persist_path)
                except Exception:
                    pass
        return ids_list

    def add_text(self, text: str, id: Optional[str] = None) -> str:
        """Adiciona um único texto e retorna o id usado."""
        with self._lock:
            _id = id or str(uuid.uuid4())
            emb = self._embed(text)
            norm = _dict_norm(emb)
            self._texts[_id] = text
            self._embeddings[_id] = emb
            self._norms[_id] = norm
            return _id

    def query_similar(self, query: str, k: int = 5) -> List[Tuple[str, float, str]]:
        """Retorna top-k tuplas `(id, score, text)` ordenadas por score desc.

        Score é a similaridade de cosseno (0..1 para vetores normalizados).
        """
        q_emb = self._embed(query)
        q_norm = _dict_norm(q_emb)
        results: List[Tuple[str, float, str]] = []
        with self._lock:
            for _id, emb in self._embeddings.items():
                dot = _dict_dot(q_emb, emb)
                denom = q_norm * (self._norms.get(_id, 1.0) or 1.0)
                score = float(dot / denom) if denom != 0.0 else 0.0
                results.append((_id, score, self._texts.get(_id, "")))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]

    # ---- persistence (simple) ----
    def save(self, path: str) -> None:
        data = {"texts": self._texts}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        texts = data.get("texts", {})
        # reindex texts (recompute embeddings)
        with self._lock:
            self._texts.clear()
            self._embeddings.clear()
            self._norms.clear()
            for _id, txt in texts.items():
                self.add_text(txt, id=_id)


__all__ = ["MemoryVectorStore"]
