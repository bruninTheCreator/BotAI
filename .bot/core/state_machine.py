"""
Máquina de Estados (State Machine) para orquestração do assistente.
Implementa o padrão State com transições seguras e callbacks.
"""

from typing import Dict, Callable, Optional, Set, List
from datetime import datetime
from enum import Enum, auto
from dataclasses import dataclass, field

from .logging_module import Logger, get_logger


class AssistantState(Enum):
    """Estados possíveis do assistente."""
    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    PLANNING = auto()
    EXECUTING = auto()
    ERROR = auto()
    SHUTDOWN = auto()


class Trigger(Enum):
    """Triggers para transições de estado."""
    START = auto()
    INPUT_RECEIVED = auto()
    PLAN_GENERATED = auto()
    EXECUTION_STARTED = auto()
    EXECUTION_COMPLETED = auto()
    EXECUTION_FAILED = auto()
    ERROR_OCCURRED = auto()
    RESET = auto()
    STOP = auto()


@dataclass
class Transition:
    """Define uma transição entre estados."""
    from_state: AssistantState
    to_state: AssistantState
    trigger: Trigger
    guard: Optional[Callable[[], bool]] = None  # Condição para executar
    action: Optional[Callable[[], None]] = None  # Ação ao fazer transição

    def can_execute(self) -> bool:
        """Verifica se a transição pode ser executada."""
        if self.guard is None:
            return True
        try:
            return self.guard()
        except Exception:
            return False


@dataclass
class StateMetadata:
    """Metadados sobre um estado."""
    name: str
    entered_at: Optional[datetime] = None
    exited_at: Optional[datetime] = None
    entry_count: int = 0
    duration_seconds: float = 0.0
    last_trigger: Optional[Trigger] = None
    metadata: Dict = field(default_factory=dict)


class StateMachine:
    """Máquina de estados com transições e callbacks."""

    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or get_logger("StateMachine")
        self._current_state = AssistantState.IDLE
        self._transitions: Dict[tuple, Transition] = {}
        self._on_enter_callbacks: Dict[AssistantState, List[Callable]] = {}
        self._on_exit_callbacks: Dict[AssistantState, List[Callable]] = {}
        self._state_metadata: Dict[AssistantState, StateMetadata] = {}
        self._transition_history: List[tuple] = []
        self._max_history_size = 100

        # Inicializa metadados para todos os estados
        for state in AssistantState:
            self._state_metadata[state] = StateMetadata(name=state.name)
            self._on_enter_callbacks[state] = []
            self._on_exit_callbacks[state] = []

    def add_transition(
        self,
        from_state: AssistantState,
        to_state: AssistantState,
        trigger: Trigger,
        guard: Optional[Callable] = None,
        action: Optional[Callable] = None
    ) -> 'StateMachine':
        """
        Adiciona uma transição à máquina de estados.

        Args:
            from_state: Estado de origem
            to_state: Estado de destino
            trigger: Trigger que causa a transição
            guard: Função de validação (opcional)
            action: Função a executar na transição (opcional)
        """
        key = (from_state, trigger)
        if key in self._transitions:
            self.logger.warning(
                f"Transição já existe: {from_state.name} --{trigger.name}--> {to_state.name}"  # noqa: E501
            )

        transition = Transition(
            from_state=from_state,
            to_state=to_state,
            trigger=trigger,
            guard=guard,
            action=action
        )
        self._transitions[key] = transition

        self.logger.debug(
            f"Transição adicionada: {from_state.name} --{trigger.name}--> {to_state.name}"  # noqa: E501
        )
        return self

    def on_enter(self, state: AssistantState, callback: Callable) -> 'StateMachine':  # noqa: E501
        """Registra callback ao entrar em estado."""
        self._on_enter_callbacks[state].append(callback)
        return self

    def on_exit(self, state: AssistantState, callback: Callable) -> 'StateMachine':  # noqa: E501
        """Registra callback ao sair de estado."""
        self._on_exit_callbacks[state].append(callback)
        return self

    def trigger(self, trigger: Trigger) -> bool:
        """
        Dispara um trigger para executar uma transição.

        Args:
            trigger: Trigger a ser disparado

        Returns:
            True se a transição foi executada, False caso contrário
        """
        key = (self._current_state, trigger)

        if key not in self._transitions:
            self.logger.warning(
                f"Nenhuma transição definida: {self._current_state.name} --{trigger.name}-->"  # noqa: E501
            )
            return False

        transition = self._transitions[key]

        # Verifica guard
        if not transition.can_execute():
            self.logger.warning(
                f"Guard falhou para transição: {self._current_state.name} --{trigger.name}-->"  # noqa: E501
            )
            return False

        # Executa saída do estado atual
        try:
            for callback in self._on_exit_callbacks[self._current_state]:
                callback()
        except Exception as e:
            self.logger.error(f"Erro ao sair de {self._current_state.name}: {e}")  # noqa: E501
            return False

        # Atualiza metadados do estado anterior
        old_state = self._current_state
        old_metadata = self._state_metadata[old_state]
        old_metadata.exited_at = datetime.now()
        if old_metadata.entered_at:
            old_metadata.duration_seconds = (
                old_metadata.exited_at - old_metadata.entered_at
            ).total_seconds()

        # Executa ação da transição
        if transition.action:
            try:
                transition.action()
            except Exception as e:
                self.logger.error(f"Erro ao executar ação de transição: {e}")
                return False

        # Muda estado
        self._current_state = transition.to_state

        # Atualiza metadados do novo estado
        new_metadata = self._state_metadata[transition.to_state]
        new_metadata.entered_at = datetime.now()
        new_metadata.entry_count += 1
        new_metadata.last_trigger = trigger  # Registra o trigger que causou a entrada neste estado  # noqa: E501

        # Executa entrada do novo estado
        try:
            for callback in self._on_enter_callbacks[transition.to_state]:
                callback()
        except Exception as e:
            self.logger.error(f"Erro ao entrar em {transition.to_state.name}: {e}")  # noqa: E501
            return False

        # Registra na história
        self._transition_history.append(
            (old_state, trigger, transition.to_state, datetime.now())
        )
        if len(self._transition_history) > self._max_history_size:
            self._transition_history.pop(0)

        self.logger.info(
            f"Transição executada: {old_state.name} --{trigger.name}--> {transition.to_state.name}"  # noqa: E501
        )

        return True

    def get_current_state(self) -> AssistantState:
        """Retorna o estado atual."""
        return self._current_state

    def can_trigger(self, trigger: Trigger) -> bool:
        """Verifica se um trigger pode ser disparado agora."""
        key = (self._current_state, trigger)
        if key not in self._transitions:
            return False
        transition = self._transitions[key]
        return transition.can_execute()

    def get_valid_triggers(self) -> Set[Trigger]:
        """Retorna todos os triggers válidos para o estado atual."""
        valid_triggers = set()
        for (state, trigger), transition in self._transitions.items():
            if state == self._current_state and transition.can_execute():
                valid_triggers.add(trigger)
        return valid_triggers

    def get_metadata(self, state: AssistantState) -> StateMetadata:
        """Retorna metadados de um estado."""
        return self._state_metadata[state]

    def get_transition_history(self) -> List[tuple]:
        """Retorna histórico de transições."""
        return self._transition_history.copy()

    def reset(self) -> None:
        """Reseta a máquina de estados para o estado inicial."""
        self.logger.info("Máquina de estados resetada")
        self._current_state = AssistantState.IDLE
        self._transition_history.clear()

        for state in AssistantState:
            self._state_metadata[state] = StateMetadata(name=state.name)

    def build_default_transitions(self) -> 'StateMachine':
        """
        Constrói as transições padrão para um assistente.
        """
        # IDLE -> LISTENING
        self.add_transition(
            AssistantState.IDLE,
            AssistantState.LISTENING,
            Trigger.START
        )

        # LISTENING -> PROCESSING
        self.add_transition(
            AssistantState.LISTENING,
            AssistantState.PROCESSING,
            Trigger.INPUT_RECEIVED
        )

        # PROCESSING -> PLANNING
        self.add_transition(
            AssistantState.PROCESSING,
            AssistantState.PLANNING,
            Trigger.INPUT_RECEIVED
        )

        # PLANNING -> EXECUTING
        self.add_transition(
            AssistantState.PLANNING,
            AssistantState.EXECUTING,
            Trigger.PLAN_GENERATED
        )

        # EXECUTING -> LISTENING (sucesso)
        self.add_transition(
            AssistantState.EXECUTING,
            AssistantState.LISTENING,
            Trigger.EXECUTION_COMPLETED
        )

        # EXECUTING -> ERROR
        self.add_transition(
            AssistantState.EXECUTING,
            AssistantState.ERROR,
            Trigger.EXECUTION_FAILED
        )

        # ERROR -> LISTENING (reset)
        self.add_transition(
            AssistantState.ERROR,
            AssistantState.LISTENING,
            Trigger.RESET
        )

        # Qualquer estado -> SHUTDOWN
        for state in AssistantState:
            if state != AssistantState.SHUTDOWN:
                self.add_transition(
                    state,
                    AssistantState.SHUTDOWN,
                    Trigger.STOP
                )

        return self


# Factory para criar máquinas de estado padrão
class StateMachineFactory:
    """Factory para criar máquinas de estado configuradas."""

    @staticmethod
    def create_default() -> StateMachine:
        """Cria uma máquina de estado padrão para o assistente."""
        machine = StateMachine()
        machine.build_default_transitions()
        return machine
