"""
Sistema de Evento/Observer para comunicação entre componentes.
Implementa pub/sub com suporte a prioridades e filtros.
"""

from typing import Dict, List, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum

from .base import Event, EventType, Observer
from .logging_module import Logger, get_logger


class Priority(Enum):
    """Prioridades de observador."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class ObserverRegistration:
    """Registro de um observador."""
    observer: Observer
    priority: Priority = Priority.NORMAL
    event_types: Optional[Set[EventType]] = None  # None = todos os tipos
    filters: List[Callable[[Event], bool]] = field(default_factory=list)

    def matches(self, event: Event) -> bool:
        """Verifica se o evento corresponde aos critérios."""
        # Verifica tipo de evento
        if self.event_types and event.event_type not in self.event_types:
            return False

        # Verifica filtros
        for filter_fn in self.filters:
            if not filter_fn(event):
                return False

        return True


class EventEmitterImpl:
    """Implementação do padrão Observer/Event Emitter."""

    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or get_logger("EventEmitter")
        self._observers: Dict[str, List[ObserverRegistration]] = {}
        self._event_history: List[Event] = []
        self._max_history_size = 1000
        self._is_emitting = False

    def subscribe(
        self,
        observer: Observer,
        event_types: Optional[Set[EventType]] = None,
        priority: Priority = Priority.NORMAL,
        filters: Optional[List[Callable]] = None
    ) -> str:
        """
        Subscreve um observador a eventos.

        Args:
            observer: Observador a registrar
            event_types: Tipos de evento de interesse (None = todos)
            priority: Prioridade do observador
            filters: Lista de funções de filtro

        Returns:
            ID da subscrição
        """
        observer_id = id(observer)
        registration = ObserverRegistration(
            observer=observer,
            priority=priority,
            event_types=event_types,
            filters=filters or []
        )

        if observer_id not in self._observers:
            self._observers[observer_id] = []

        self._observers[observer_id].append(registration)

        self.logger.info(
            "Observador inscrito",
            observer=observer.__class__.__name__,
            event_types=str(event_types),
            priority=priority.name
        )

        return observer_id

    def unsubscribe(self, observer: Observer) -> bool:
        """Remove um observador."""
        observer_id = id(observer)
        if observer_id in self._observers:
            del self._observers[observer_id]
            self.logger.info(f"Observador removido: {observer.__class__.__name__}")  # noqa: E501
            return True
        return False

    def unsubscribe_all(self) -> None:
        """Remove todos os observadores."""
        self._observers.clear()
        self.logger.info("Todos os observadores foram removidos")

    async def emit(self, event: Event) -> None:
        """
        Emite um evento para todos os observadores interessados.

        Args:
            event: Evento a emitir
        """
        # Evita re-entrada
        if self._is_emitting:
            self.logger.warning("Emissão recursiva detectada, ignorando evento")  # noqa: E501
            return

        self._is_emitting = True
        try:
            # Registra no histórico
            self._event_history.append(event)
            if len(self._event_history) > self._max_history_size:
                self._event_history.pop(0)

            self.logger.debug(
                f"Evento emitido: {event.event_type.name}",
                event_id=event.id
            )

            # Coleta observadores interessados e ordena por prioridade
            interested_registrations = []
            for registrations in self._observers.values():
                for registration in registrations:
                    if registration.matches(event):
                        interested_registrations.append(registration)

            # Ordena por prioridade
            interested_registrations.sort(
                key=lambda r: r.priority.value
            )

            # Notifica observadores
            for registration in interested_registrations:
                try:
                    await registration.observer.on_event(event)
                except Exception as e:
                    self.logger.error(
                        f"Erro ao notificar observador: {e}",
                        observer=registration.observer.__class__.__name__,
                        event_id=event.id
                    )

        finally:
            self._is_emitting = False

    def get_event_history(self, limit: Optional[int] = None) -> List[Event]:
        """Retorna histórico de eventos."""
        if limit is None:
            return self._event_history.copy()
        return self._event_history[-limit:]

    def get_observer_count(self) -> int:
        """Retorna o número de observadores registrados."""
        return len(self._observers)

    def clear_history(self) -> None:
        """Limpa o histórico de eventos."""
        self._event_history.clear()
        self.logger.debug("Histórico de eventos limpo")


class EventBus:
    """Bus de eventos global para a aplicação."""

    _instance: Optional[EventEmitterImpl] = None

    @classmethod
    def get_instance(cls, logger: Optional[Logger] = None) -> EventEmitterImpl:
        """Obtém a instância global do bus de eventos."""
        if cls._instance is None:
            cls._instance = EventEmitterImpl(logger)
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reseta o bus de eventos (útil para testes)."""
        cls._instance = None
