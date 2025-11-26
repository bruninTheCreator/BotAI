"""World Model: representação estruturada do estado da IA e do mundo.

Define estruturas de dados (Belief, Goal, Fact, Context) que a IA usa para
raciocinar sobre si mesma, o ambiente e as ações.
"""

from __future__ import annotations

import dataclasses
import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class ConfidenceLevel(Enum):
    """Níveis de confiança em crenças e objetivos."""
    CERTAIN = 1.0
    HIGH = 0.8
    MEDIUM = 0.5
    LOW = 0.3
    UNKNOWN = 0.0


@dataclasses.dataclass
class Belief:
    """Uma crença sobre o mundo ou sobre si mesmo."""
    fact: str
    confidence: float = 0.5  # 0.0 (unknown) a 1.0 (certain)
    source: str = "unknown"  # "memory", "perception", "inference", "llm", etc.
    timestamp: datetime = dataclasses.field(default_factory=datetime.now)
    context: Dict[str, Any] = dataclasses.field(default_factory=dict)

    def is_reliable(self, threshold: float = 0.7) -> bool:
        """Retorna True se a confiança está acima do threshold."""
        return self.confidence >= threshold

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact": self.fact,
            "confidence": self.confidence,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
        }


@dataclasses.dataclass
class Goal:
    """Um objetivo que a IA tenta alcançar."""
    description: str
    priority: int = 0  # maior = mais importante
    deadline: Optional[datetime] = None
    parent_goal: Optional[str] = None  # id do goal pai (hierarquia)
    status: str = "pending"  # "pending", "in_progress", "completed", "failed"
    confidence: float = 1.0  # confiança de que é alcançável

    def is_active(self) -> bool:
        return self.status in ("pending", "in_progress")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "priority": self.priority,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "parent_goal": self.parent_goal,
            "status": self.status,
            "confidence": self.confidence,
        }


@dataclasses.dataclass
class Fact:
    """Um fato estruturado (sujeito, predicado, objeto)."""
    subject: str
    predicate: str
    obj: str
    confidence: float = 1.0
    timestamp: datetime = dataclasses.field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.obj,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclasses.dataclass
class Context:
    """Contexto atual: informações sobre o estado do sistema/ambiente."""
    screen_state: str = ""  # descrição/OCR da tela
    active_window: str = ""  # janela ativa
    user_intent: str = ""  # último comando/intenção do usuário
    recent_actions: List[str] = dataclasses.field(default_factory=list)
    memory_snippets: List[str] = dataclasses.field(default_factory=list)
    timestamp: datetime = dataclasses.field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "screen_state": self.screen_state,
            "active_window": self.active_window,
            "user_intent": self.user_intent,
            "recent_actions": self.recent_actions,
            "memory_snippets": self.memory_snippets,
            "timestamp": self.timestamp.isoformat(),
        }


class WorldModel:
    """Modelo do mundo: mantém crenças, objetivos, fatos e contexto."""

    def __init__(self) -> None:
        self._beliefs: Dict[str, Belief] = {}  # key -> Belief
        self._goals: Dict[str, Goal] = {}  # key -> Goal
        self._facts: Dict[str, Fact] = {}  # key (subject+predicate+object) -> Fact
        self._context: Optional[Context] = None

    # ---- Beliefs ----
    def add_belief(self, key: str, belief: Belief) -> None:
        """Adiciona ou atualiza uma crença."""
        self._beliefs[key] = belief

    def get_belief(self, key: str) -> Optional[Belief]:
        """Retorna uma crença por chave."""
        return self._beliefs.get(key)

    def get_reliable_beliefs(self, threshold: float = 0.7) -> List[Belief]:
        """Retorna crenças com confiança >= threshold."""
        return [b for b in self._beliefs.values() if b.is_reliable(threshold)]

    def remove_belief(self, key: str) -> None:
        """Remove uma crença."""
        self._beliefs.pop(key, None)

    # ---- Goals ----
    def add_goal(self, key: str, goal: Goal) -> None:
        """Adiciona ou atualiza um objetivo."""
        self._goals[key] = goal

    def get_goal(self, key: str) -> Optional[Goal]:
        """Retorna um objetivo por chave."""
        return self._goals.get(key)

    def get_active_goals(self) -> List[Goal]:
        """Retorna objetivos ativos (pending ou in_progress)."""
        return [g for g in self._goals.values() if g.is_active()]

    def mark_goal_complete(self, key: str) -> None:
        """Marca um objetivo como completo."""
        if key in self._goals:
            self._goals[key].status = "completed"

    def mark_goal_failed(self, key: str) -> None:
        """Marca um objetivo como falhado."""
        if key in self._goals:
            self._goals[key].status = "failed"

    # ---- Facts ----
    def add_fact(self, fact: Fact) -> None:
        """Adiciona ou atualiza um fato."""
        key = f"{fact.subject}|{fact.predicate}|{fact.obj}"
        self._facts[key] = fact

    def query_facts(self, subject: Optional[str] = None, predicate: Optional[str] = None) -> List[Fact]:
        """Consulta fatos por sujeito e/ou predicado."""
        results = []
        for fact in self._facts.values():
            match = True
            if subject is not None and fact.subject != subject:
                match = False
            if predicate is not None and fact.predicate != predicate:
                match = False
            if match:
                results.append(fact)
        return results

    # ---- Context ----
    def set_context(self, context: Context) -> None:
        """Define o contexto atual."""
        self._context = context

    def get_context(self) -> Optional[Context]:
        """Retorna o contexto atual."""
        return self._context

    # ---- Serialization ----
    def to_dict(self) -> Dict[str, Any]:
        return {
            "beliefs": {k: v.to_dict() for k, v in self._beliefs.items()},
            "goals": {k: v.to_dict() for k, v in self._goals.items()},
            "facts": {k: v.to_dict() for k, v in self._facts.items()},
            "context": self._context.to_dict() if self._context else None,
        }

    def to_json(self) -> str:
        """Serializa para JSON (com timestamp convertido)."""
        data = self.to_dict()
        return json.dumps(data, indent=2, default=str)


__all__ = ["Belief", "Goal", "Fact", "Context", "ConfidenceLevel", "WorldModel"]
