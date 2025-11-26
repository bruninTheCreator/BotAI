"""Ciclo de Autorreflexão: a IA avalia seus próprios planos e ações.

Após executar um plano, a IA:
- Avalia sucesso/falha
- Extrai lições aprendidas
- Atualiza crenças e confiança
- Armazena episódios para aprendizado futuro
"""

from __future__ import annotations

import dataclasses
import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from core.memory_vector import MemoryVectorStore
from core.world_model import Belief, WorldModel


class ReflectionType(Enum):
    """Tipo de reflexão."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    LEARNING = "learning"


@dataclasses.dataclass
class ReflectionRecord:
    """Registro de uma reflexão sobre uma ação/plano."""
    plan_name: str
    execution_trace: str  # descrição do que aconteceu
    reflection_type: ReflectionType
    lessons_learned: List[str]
    confidence_update: float  # delta de confiança (-1.0 a +1.0)
    timestamp: datetime = dataclasses.field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_name": self.plan_name,
            "execution_trace": self.execution_trace,
            "reflection_type": self.reflection_type.value,
            "lessons_learned": self.lessons_learned,
            "confidence_update": self.confidence_update,
            "timestamp": self.timestamp.isoformat(),
        }


class Reflector:
    """Componente de reflexão: avalia ações e gera insights."""

    def __init__(self, world_model: Optional[WorldModel] = None, memory: Optional[MemoryVectorStore] = None) -> None:
        self.world_model = world_model or WorldModel()
        self.memory = memory or MemoryVectorStore()
        self._reflection_history: List[ReflectionRecord] = []

    def reflect_on_execution(
        self,
        plan_name: str,
        execution_trace: str,
        success: bool,
        partial: bool = False,
    ) -> ReflectionRecord:
        """Executa reflexão sobre uma ação/plano executado."""
        # Determina tipo de reflexão
        if success and not partial:
            reflection_type = ReflectionType.SUCCESS
            confidence_delta = 0.1
        elif partial or (success and partial):
            reflection_type = ReflectionType.PARTIAL_SUCCESS
            confidence_delta = 0.0
        else:
            reflection_type = ReflectionType.FAILURE
            confidence_delta = -0.2

        # Extrai lições
        lessons = self._extract_lessons(plan_name, execution_trace, reflection_type)

        # Cria registro
        record = ReflectionRecord(
            plan_name=plan_name,
            execution_trace=execution_trace,
            reflection_type=reflection_type,
            lessons_learned=lessons,
            confidence_update=confidence_delta,
        )

        # Atualiza world model (crenças)
        self._update_beliefs(record)

        # Armazena para aprendizado futuro
        self._store_episode(record)

        self._reflection_history.append(record)
        return record

    def _extract_lessons(self, plan_name: str, trace: str, rtype: ReflectionType) -> List[str]:
        """Extrai lições do trace de execução."""
        lessons: List[str] = []

        if rtype == ReflectionType.SUCCESS:
            lessons.append(f"Plan '{plan_name}' succeeded: similar plans may work again.")
        elif rtype == ReflectionType.FAILURE:
            lessons.append(f"Plan '{plan_name}' failed: need alternative approach.")
            if "timeout" in trace.lower():
                lessons.append("Timeout detected: operations took longer than expected.")
            if "permission" in trace.lower():
                lessons.append("Permission denied: check access levels for similar tasks.")
        elif rtype == ReflectionType.PARTIAL_SUCCESS:
            lessons.append(f"Plan '{plan_name}' partially succeeded: refinement needed.")

        return lessons

    def _update_beliefs(self, record: ReflectionRecord) -> None:
        """Atualiza crenças no world model baseado na reflexão."""
        key = f"plan_confidence_{record.plan_name}"
        belief = Belief(
            fact=f"Plan '{record.plan_name}' has confidence adjusted by {record.confidence_update}",
            confidence=min(1.0, max(0.0, 0.5 + record.confidence_update)),
            source="reflection",
            context={"reflection_type": record.reflection_type.value},
        )
        self.world_model.add_belief(key, belief)

    def _store_episode(self, record: ReflectionRecord) -> None:
        """Armazena episódio na memória vetorial para aprendizado futuro."""
        episode_text = f"{record.plan_name}: {record.reflection_type.value}. Lessons: {'; '.join(record.lessons_learned)}"
        self.memory.add_text(episode_text, id=f"episode_{record.plan_name}_{record.timestamp.isoformat()}")

    def get_lessons_for_goal(self, goal: str, k: int = 3) -> List[str]:
        """Recupera lições aprendidas similares a um goal."""
        similar = self.memory.query_similar(goal, k=k)
        lessons: List[str] = []
        for _id, score, text in similar:
            if score > 0.3:  # threshold mínimo de relevância
                lessons.append(text)
        return lessons

    def get_reflection_history(self, limit: Optional[int] = None) -> List[ReflectionRecord]:
        """Retorna histórico de reflexões."""
        hist = self._reflection_history
        if limit:
            hist = hist[-limit:]
        return hist

    def export_reflections(self, path: str) -> None:
        """Exporta reflexões em JSON."""
        data = [r.to_dict() for r in self._reflection_history]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)


__all__ = ["Reflector", "ReflectionRecord", "ReflectionType"]
