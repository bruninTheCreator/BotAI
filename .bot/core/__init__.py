"""
Core module - Fundação do BotAI 2.0

Exporta todos os componentes principais para uso fácil.
"""

from .base import (
    # Enums
    EventType,
    ActionType,
    ExecutionStatus,
    # Dataclasses
    Event,
    ActionStep,
    Plan,
    Result,
    # Interfaces
    Component,
    Service,
    Observer,
    EventEmitter,
    Repository,
    Executor,
    Perception,
    Memory,
    Planner,
    StateManager,
)

from .config import (
    AppConfig,
    OpenAIConfig,
    PerceptionConfig,
    ExecutorConfig,
    MemoryConfig,
    LoggingConfig,
    ConfigLoader,
    Environment,
    get_config,
    set_config,
)

from .logging_module import (
    Logger,
    StructuredFormatter,
    PerformanceTracker,
    get_logger,
    get_root_logger,
)

from .di_container import (
    ServiceContainer,
    ServiceDescriptor,
    InjectionContext,
    LifecycleType,
    inject,
    setup_di_container,
)

from .state_machine import (
    StateMachine,
    AssistantState,
    Trigger,
    Transition,
    StateMetadata,
    StateMachineFactory,
)

from .event_emitter import (
    EventEmitterImpl,
    EventBus,
    Priority,
    ObserverRegistration,
)

from .percepcao import (
    PerceptionImpl,
    ImagePreprocessor,
)

__all__ = [
    # Base
    'EventType',
    'ActionType',
    'ExecutionStatus',
    'Event',
    'ActionStep',
    'Plan',
    'Result',
    'Component',
    'Service',
    'Observer',
    'EventEmitter',
    'Repository',
    'Executor',
    'Perception',
    'Memory',
    'Planner',
    'StateManager',
    # Config
    'AppConfig',
    'OpenAIConfig',
    'PerceptionConfig',
    'ExecutorConfig',
    'MemoryConfig',
    'LoggingConfig',
    'ConfigLoader',
    'Environment',
    'get_config',
    'set_config',
    # Logging
    'Logger',
    'StructuredFormatter',
    'PerformanceTracker',
    'get_logger',
    'get_root_logger',
    # DI
    'ServiceContainer',
    'ServiceDescriptor',
    'InjectionContext',
    'LifecycleType',
    'inject',
    'setup_di_container',
    # State Machine
    'StateMachine',
    'AssistantState',
    'Trigger',
    'Transition',
    'StateMetadata',
    'StateMachineFactory',
    # Events
    'EventEmitterImpl',
    'EventBus',
    'Priority',
    'ObserverRegistration',
    # Perception
    'PerceptionImpl',
    'ImagePreprocessor',
]

__version__ = "2.0.0"
__author__ = "BotAI Team"
