"""
tests/test_architecture.py - Testes para demonstrar a nova arquitetura
"""

import pytest

from core.base import (
    Event, EventType, ActionType, ExecutionStatus,
    ActionStep, Plan, Result
)
from core.config import AppConfig, ConfigLoader, Environment
from core.logging_module import get_logger
from core.di_container import ServiceContainer
from core.state_machine import (
    StateMachine, AssistantState, Trigger, StateMachineFactory
)
from core.event_emitter import Priority, EventEmitterImpl


# ==================== TESTES DE BASE ====================

class TestEventStructure:
    """Testes para a estrutura de Event."""

    def test_event_creation(self):
        """Testa criação de evento."""
        event = Event(
            event_type=EventType.EXECUTION,
            data={"status": "ok"}
        )

        assert event.event_type == EventType.EXECUTION
        assert event.data["status"] == "ok"
        assert event.id is not None

    def test_event_serialization(self):
        """Testa serialização de evento."""
        event = Event(
            event_type=EventType.PLANNING,
            data={"plan": "test"}
        )

        serialized = event.to_dict()

        assert serialized["event_type"] == "PLANNING"
        assert serialized["data"]["plan"] == "test"
        assert "timestamp" in serialized
        assert "id" in serialized


class TestActionStep:
    """Testes para ActionStep."""

    def test_action_step_creation(self):
        """Testa criação de passo de ação."""
        step = ActionStep(
            action_type=ActionType.OPEN_APP,
            parameters={"target": "notepad"},
            priority=1
        )

        assert step.action_type == ActionType.OPEN_APP
        assert step.parameters["target"] == "notepad"
        assert step.status == ExecutionStatus.PENDING

    def test_action_step_serialization(self):
        """Testa serialização de passo."""
        step = ActionStep(
            action_type=ActionType.TYPE_TEXT,
            parameters={"content": "hello"}
        )

        serialized = step.to_dict()

        assert serialized["action_type"] == "TYPE_TEXT"
        assert serialized["status"] == "PENDING"


class TestResultPattern:
    """Testes para padrão Result[T]."""

    def test_result_ok(self):
        """Testa resultado bem-sucedido."""
        result = Result.ok("data", operation="test")

        assert result.success
        assert result.data == "data"
        assert result.error is None
        assert result.metadata["operation"] == "test"

    def test_result_error(self):
        """Testa resultado com erro."""
        result = Result.from_error("Something went wrong")

        assert not result.success
        assert result.data is None
        assert result.error == "Something went wrong"


class TestPlan:
    """Testes para Plan."""

    def test_plan_creation(self):
        """Testa criação de plano."""
        plan = Plan(name="Test Plan")

        step1 = ActionStep(action_type=ActionType.OPEN_APP)
        step2 = ActionStep(action_type=ActionType.TYPE_TEXT)

        plan.add_step(step1)
        plan.add_step(step2)

        assert len(plan.steps) == 2
        assert plan.name == "Test Plan"

    def test_plan_serialization(self):
        """Testa serialização de plano."""
        plan = Plan(name="Serialization Test")
        plan.add_step(ActionStep(action_type=ActionType.CLICK))

        serialized = plan.to_dict()

        assert serialized["name"] == "Serialization Test"
        assert len(serialized["steps"]) == 1
        assert serialized["steps"][0]["action_type"] == "CLICK"


# ==================== TESTES DE CONFIGURAÇÃO ====================

class TestConfigLoader:
    """Testes para carregamento de configuração."""

    def test_config_from_dict(self):
        """Testa carregamento de dict."""
        config_dict = {
            "env": "development",
            "debug": True,
            "openai": {
                "api_key": "test-key",
                "model": "gpt-4"
            }
        }

        config = ConfigLoader.from_dict(config_dict)

        assert config.env == Environment.DEVELOPMENT
        assert config.debug is True
        assert config.openai.api_key == "test-key"

    def test_config_defaults(self):
        """Testa valores padrão da configuração."""
        config = AppConfig()

        assert config.version == "2.0.0"
        assert config.env == Environment.DEVELOPMENT
        assert config.openai.model == "gpt-4o-mini"


class TestOpenAIConfig:
    """Testes para configuração do OpenAI."""

    def test_openai_config_validation(self):
        """Testa validação de configuração do OpenAI."""
        from core.config import OpenAIConfig

        # Sem API key
        config_invalid = OpenAIConfig(api_key="")
        assert not config_invalid.is_valid()

        # Com API key
        config_valid = OpenAIConfig(api_key="sk-test")
        assert config_valid.is_valid()


# ==================== TESTES DE MÁQUINA DE ESTADOS ====================

class TestStateMachine:
    """Testes para máquina de estados."""

    def test_state_machine_initialization(self):
        """Testa inicialização da máquina."""
        machine = StateMachine()

        assert machine.get_current_state() == AssistantState.IDLE

    def test_state_machine_transition(self):
        """Testa transição básica."""
        machine = StateMachine()
        machine.add_transition(
            AssistantState.IDLE,
            AssistantState.LISTENING,
            Trigger.START
        )

        success = machine.trigger(Trigger.START)

        assert success
        assert machine.get_current_state() == AssistantState.LISTENING

    def test_state_machine_guard(self):
        """Testa guard em transição."""
        machine = StateMachine()

        guard_passed = False

        def my_guard():
            return guard_passed

        machine.add_transition(
            AssistantState.IDLE,
            AssistantState.LISTENING,
            Trigger.START,
            guard=my_guard
        )

        # Guard falha
        success = machine.trigger(Trigger.START)
        assert not success
        assert machine.get_current_state() == AssistantState.IDLE

        # Guard passa
        guard_passed = True
        success = machine.trigger(Trigger.START)
        assert success
        assert machine.get_current_state() == AssistantState.LISTENING

    def test_state_machine_callbacks(self):
        """Testa callbacks de entrada/saída."""
        machine = StateMachine()
        machine.build_default_transitions()

        enter_called = []
        exit_called = []

        machine.on_enter(
            AssistantState.LISTENING,
            lambda: enter_called.append(True)
        )
        machine.on_exit(
            AssistantState.IDLE,
            lambda: exit_called.append(True)
        )

        machine.trigger(Trigger.START)

        assert len(enter_called) == 1
        assert len(exit_called) == 1

    def test_default_transitions(self):
        """Testa construção de transições padrão."""
        machine = StateMachineFactory.create_default()

        # IDLE -> LISTENING
        assert machine.trigger(Trigger.START)
        assert machine.get_current_state() == AssistantState.LISTENING

    def test_state_metadata(self):
        """Testa metadados de estado."""
        machine = StateMachine()
        machine.add_transition(
            AssistantState.IDLE,
            AssistantState.LISTENING,
            Trigger.START
        )

        machine.trigger(Trigger.START)

        metadata = machine.get_metadata(AssistantState.LISTENING)
        assert metadata.entry_count == 1
        assert metadata.last_trigger == Trigger.START


# ==================== TESTES DE EVENTOS ====================

@pytest.mark.asyncio
class TestEventEmitter:
    """Testes para sistema de eventos."""

    async def test_event_emission(self):
        """Testa emissão de evento."""
        from core.base import Observer

        class TestObserver(Observer):
            def __init__(self):
                self.received_events = []

            async def on_event(self, event: Event):
                self.received_events.append(event)

        emitter = EventEmitterImpl()
        observer = TestObserver()

        emitter.subscribe(observer)

        event = Event(event_type=EventType.EXECUTION)
        await emitter.emit(event)

        assert len(observer.received_events) == 1
        assert observer.received_events[0].event_type == EventType.EXECUTION

    async def test_event_filtering(self):
        """Testa filtro de eventos."""
        from core.base import Observer

        class FilterObserver(Observer):
            def __init__(self):
                self.events = []

            async def on_event(self, event: Event):
                self.events.append(event)

        emitter = EventEmitterImpl()
        observer = FilterObserver()

        # Subscreve apenas a eventos de EXECUTION
        emitter.subscribe(
            observer,
            event_types={EventType.EXECUTION}
        )

        # Emite EXECUTION
        event1 = Event(event_type=EventType.EXECUTION)
        await emitter.emit(event1)

        # Emite SYSTEM
        event2 = Event(event_type=EventType.SYSTEM)
        await emitter.emit(event2)

        # Deve receber apenas EXECUTION
        assert len(observer.events) == 1
        assert observer.events[0].event_type == EventType.EXECUTION

    async def test_event_priority(self):
        """Testa prioridade de observadores."""
        from core.base import Observer

        call_order = []

        class PriorityObserver(Observer):
            def __init__(self, name: str):
                self.name = name

            async def on_event(self, event: Event):
                call_order.append(self.name)

        emitter = EventEmitterImpl()

        # Registra com diferentes prioridades
        emitter.subscribe(
            PriorityObserver("low"),
            priority=Priority.LOW
        )
        emitter.subscribe(
            PriorityObserver("high"),
            priority=Priority.HIGH
        )
        emitter.subscribe(
            PriorityObserver("normal"),
            priority=Priority.NORMAL
        )

        event = Event(event_type=EventType.SYSTEM)
        await emitter.emit(event)

        # High deve ser executado primeiro
        assert call_order[0] == "high"


# ==================== TESTES DE DI CONTAINER ====================

class TestServiceContainer:
    """Testes para injeção de dependência."""

    def test_singleton_registration(self):
        """Testa registro de singleton."""
        class Service:
            pass

        container = ServiceContainer()
        container.register_singleton(Service, Service)

        instance1 = container.resolve(Service)
        instance2 = container.resolve(Service)

        assert instance1 is instance2

    def test_transient_registration(self):
        """Testa registro de transient."""
        class Service:
            pass

        container = ServiceContainer()
        container.register_transient(Service, Service)

        instance1 = container.resolve(Service)
        instance2 = container.resolve(Service)

        assert instance1 is not instance2

    def test_instance_registration(self):
        """Testa registro de instância."""
        class Service:
            def __init__(self, name):
                self.name = name

        container = ServiceContainer()
        service_instance = Service("test")

        container.register_instance(Service, service_instance)

        resolved = container.resolve(Service)

        assert resolved is service_instance
        assert resolved.name == "test"

    def test_unregistered_service(self):
        """Testa erro ao resolver serviço não registrado."""
        class UnknownService:
            pass

        container = ServiceContainer()

        with pytest.raises(ValueError):
            container.resolve(UnknownService)


# ==================== TESTES DE LOGGING ====================

class TestLogger:
    """Testes para sistema de logging."""

    def test_logger_context(self):
        """Testa context manager de logger."""
        logger = get_logger("test")

        # Não deve falhar
        with logger.context(user_id=123, request_id="xyz"):
            logger.info("Teste com contexto")

    def test_logger_levels(self):
        """Testa diferentes níveis de log."""
        logger = get_logger("test")

        # Não deve lançar exceções
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")


# ==================== TESTES DE INTEGRAÇÃO ====================

@pytest.mark.asyncio
class TestIntegration:
    """Testes de integração entre componentes."""

    async def test_end_to_end_workflow(self):
        """Testa fluxo completo."""
        # Setup
        state_machine = StateMachineFactory.create_default()
        event_bus = EventEmitterImpl()

        # Setup observer
        from core.base import Observer

        class WorkflowObserver(Observer):
            def __init__(self):
                self.events = []

            async def on_event(self, event: Event):
                self.events.append(event)

        observer = WorkflowObserver()
        event_bus.subscribe(observer)

        # Executa workflow: IDLE -> LISTENING
        assert state_machine.trigger(Trigger.START)
        assert state_machine.get_current_state() == AssistantState.LISTENING
        await event_bus.emit(Event(event_type=EventType.PERCEPTION))

        # LISTENING -> PROCESSING
        assert state_machine.trigger(Trigger.INPUT_RECEIVED)
        assert state_machine.get_current_state() == AssistantState.PROCESSING
        await event_bus.emit(Event(event_type=EventType.PLANNING))

        # PROCESSING -> PLANNING
        assert state_machine.trigger(Trigger.INPUT_RECEIVED)
        assert state_machine.get_current_state() == AssistantState.PLANNING

        # Verificações finais
        assert len(observer.events) == 2


# ==================== FIXTURES ====================

@pytest.fixture
def app_config():
    """Fornece configuração de teste."""
    return AppConfig(
        env=Environment.TESTING,
        debug=True
    )


@pytest.fixture
def test_logger(app_config):
    """Fornece logger de teste."""
    return get_logger("test", app_config)


@pytest.fixture
def state_machine():
    """Fornece máquina de estados."""
    return StateMachineFactory.create_default()


# ==================== EXECUÇÃO ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
