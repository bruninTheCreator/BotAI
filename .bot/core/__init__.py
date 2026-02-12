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

from .percepcao import (
    PerceptionImpl,
    ImagePreprocessor,
)
from .pattern_engine import PatternEngine
from .observation_loop import ObservationLoop
from .llm_client import LLMClient

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
    # Perception
    'PerceptionImpl',
    'ImagePreprocessor',
    # Pattern / LLM
    'PatternEngine',
    'ObservationLoop',
    'LLMClient',
]

__version__ = "2.0.0"
__author__ = "BotAI Team"
