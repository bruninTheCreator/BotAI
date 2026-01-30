"""
Módulo base com classes abstratas e interfaces para toda a arquitetura.
Define contratos que todos os componentes devem respeitar.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum, auto
import uuid

# ==================== TIPOS GENÉRICOS ====================

T = TypeVar('T')
ResultT = TypeVar('ResultT')


# ==================== ENUMS ====================

class EventType(Enum):
    """Tipos de eventos no sistema."""
    USER_COMMAND = auto()
    PERCEPTION = auto()
    PLANNING = auto()
    EXECUTION = auto()
    ERROR = auto()
    SYSTEM = auto()
    MEMORY = auto()


class ActionType(Enum):
    """Tipos de ações executáveis."""
    OPEN_APP = auto()
    TYPE_TEXT = auto()
    HOTKEY = auto()
    CLICK = auto()
    BROWSE = auto()
    SCREENSHOT = auto()
    OCR = auto()
    WAIT = auto()
    NOOP = "NOOP"
    ASK_CLARIFICATION = "ask_clarification"


class ExecutionStatus(Enum):
    """Status de execução."""
    PENDING = auto()
    EXECUTING = auto()
    SUCCESS = auto()
    FAILED = auto()
    CANCELLED = auto()


# ==================== DATACLASSES ====================

@dataclass
class Event:
    """Representa um evento no sistema."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.SYSTEM
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa o evento para dicionário."""
        return {
            'id': self.id,
            'event_type': self.event_type.name,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'metadata': self.metadata
        }


@dataclass
class ActionStep:
    """Representa um passo de ação."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action_type: ActionType = ActionType.WAIT
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serializa a ação para dicionário."""
        return {
            'id': self.id,
            'action_type': self.action_type.name,
            'parameters': self.parameters,
            'priority': self.priority,
            'status': self.status.name,
            'result': self.result,
            'error': self.error
        }


@dataclass
class Plan:
    """Representa um plano de execução."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Unnamed Plan"
    steps: List[ActionStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    status: ExecutionStatus = ExecutionStatus.PENDING
    priority: int = 0

    def add_step(self, step: ActionStep) -> None:
        """Adiciona um passo ao plano."""
        self.steps.append(step)

    def __iter__(self):
        return iter(self.steps)

    def __len__(self):
        return len(self.steps)

    def __getitem__(self, index):
        return self.steps[index]

    def to_dict(self) -> Dict[str, Any]:
        """Serializa o plano para dicionário."""
        return {
            'id': self.id,
            'name': self.name,
            'steps': [step.to_dict() for step in self.steps],
            'created_at': self.created_at.isoformat(),
            'status': self.status.name,
            'priority': self.priority
        }

@dataclass
class Result(Generic[ResultT]):
    """Padrão de resultado para operações."""
    success: bool
    data: Optional[ResultT] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, data: ResultT, **metadata) -> 'Result[ResultT]':
        """Cria um resultado bem-sucedido."""
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def from_error(cls, error: str, **metadata) -> 'Result[ResultT]':
        """Cria um resultado com erro."""
        return cls(success=False, error=error, metadata=metadata)


# ==================== INTERFACES/ABSTRATAS ====================

class Component(ABC):
    """Base para todos os componentes do sistema."""

    def __init__(self, name: str):
        self.name = name
        self.initialized = False

    @abstractmethod
    async def initialize(self) -> Result[None]:
        """Inicializa o componente."""
        pass

    @abstractmethod
    async def shutdown(self) -> Result[None]:
        """Encerra o componente."""
        pass

    def is_ready(self) -> bool:
        """Verifica se o componente está pronto."""
        return self.initialized


class Observer(ABC):
    """Padrão Observer para notificações."""

    @abstractmethod
    async def on_event(self, event: Event) -> None:
        """Chamado quando um evento é emitido."""
        pass


class EventEmitter(ABC):
    """Interface para emissão de eventos."""

    @abstractmethod
    async def emit(self, event: Event) -> None:
        """Emite um evento para todos os observadores."""
        pass

    @abstractmethod
    def subscribe(self, observer: Observer) -> None:
        """Adiciona um observador."""
        pass

    @abstractmethod
    def unsubscribe(self, observer: Observer) -> None:
        """Remove um observador."""
        pass


class Repository(ABC, Generic[T]):
    """Padrão Repository para persistência."""

    @abstractmethod
    async def save(self, item: T) -> Result[str]:
        """Salva um item."""
        pass

    @abstractmethod
    async def load(self, id: str) -> Result[Optional[T]]:
        """Carrega um item por ID."""
        pass

    @abstractmethod
    async def delete(self, id: str) -> Result[None]:
        """Deleta um item."""
        pass

    @abstractmethod
    async def list_all(self) -> Result[List[T]]:
        """Lista todos os itens."""
        pass


class Service(Component):
    """Base para services de negócio."""

    async def initialize(self) -> Result[None]:
        self.initialized = True
        return Result.ok(None)

    async def shutdown(self) -> Result[None]:
        self.initialized = False
        return Result.ok(None)


class Executor(Component):
    """Interface para execução de ações."""

    @abstractmethod
    async def execute(self, action: ActionStep) -> Result[str]:
        """Executa uma ação individual."""
        pass

    @abstractmethod
    async def execute_plan(self, plan: Plan) -> Result[List[str]]:
        """Executa um plano completo."""
        pass


class Perception(Component):
    """Interface para percepção (visão, OCR, etc)."""

    @abstractmethod
    async def read_text(self, region: Optional[tuple] = None) -> Result[str]:
        """Captura texto da tela."""
        pass

    @abstractmethod
    async def capture_screen(self, region: Optional[tuple] = None) -> Result[Any]:  # noqa: E501
        """Captura a tela."""
        pass


class Memory(Repository[Event]):
    """Interface para sistema de memória."""

    @abstractmethod
    async def get_recent(self, limit: int = 10) -> Result[List[Event]]:
        """Retorna eventos recentes."""
        pass

    @abstractmethod
    async def search(self, criteria: Dict[str, Any]) -> Result[List[Event]]:
        """Busca eventos por critério."""
        pass


class Planner(Component):
    """Interface para planejamento de ações."""

    @abstractmethod
    async def interpret_command(self, command: str, context: str = "") -> Result[Plan]:  # noqa: E501
        """Interpreta comando e gera plano."""
        pass

    @abstractmethod
    async def optimize_plan(self, plan: Plan) -> Result[Plan]:
        """Otimiza um plano existente."""
        pass


class StateManager(ABC):
    """Gerenciador de estado para máquina de estados."""

    @abstractmethod
    async def get_state(self) -> str:
        """Retorna o estado atual."""
        pass

    @abstractmethod
    async def set_state(self, state: str) -> Result[None]:
        """Define o novo estado."""
        pass

    @abstractmethod
    async def transition(self, trigger: str) -> Result[None]:
        """Executa uma transição de estado."""
        pass
