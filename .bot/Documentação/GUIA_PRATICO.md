# 🎯 Guia Prático - Como Usar a Nova Arquitetura

## 1. Setup Básico da Aplicação

```python
"""
main.py - Novo entry point sofisticado
"""

import asyncio
from pathlib import Path

from core.config import ConfigLoader
from core.di_container import setup_di_container, InjectionContext
from core.logging_module import get_logger
from core.state_machine import StateMachineFactory, Trigger
from core.event_emitter import EventBus
from core.base import Event, EventType


async def main():
    """Main entry point com nova arquitetura."""
    
    # 1. Carrega configuração
    config = ConfigLoader.from_env()
    
    # 2. Setup de DI (injeção de dependência)
    di_container = setup_di_container()
    InjectionContext.set_instance(
        InjectionContext(di_container)
    )
    
    # 3. Logger
    logger = get_logger("BotAI")
    logger.info(
        "Aplicação iniciada",
        environment=config.env.value,
        version=config.version
    )
    
    # 4. Máquina de estados
    state_machine = StateMachineFactory.create_default()
    
    # 5. Event Bus
    event_bus = EventBus.get_instance()
    
    # Registra callbacks na máquina de estados
    state_machine.on_enter(
        AssistantState.EXECUTING,
        lambda: logger.info("Iniciando execução")
    )
    
    # Dispara primeiro trigger
    state_machine.trigger(Trigger.START)
    
    logger.info(f"Estado atual: {state_machine.get_current_state().name}")
    
    # Emite evento
    event = Event(
        event_type=EventType.SYSTEM,
        data={"message": "Sistema pronto"}
    )
    await event_bus.emit(event)


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 2. Criar um Componente Personalizado

```python
"""
core/components/my_processor.py - Exemplo de componente customizado
"""

from typing import Optional
from core.base import Component, Result, Service
from core.logging_module import get_logger


class MyProcessor(Service):
    """Processador customizado de dados."""
    
    def __init__(self):
        super().__init__("MyProcessor")
        self.logger = get_logger("MyProcessor")
        self.data_cache = []
    
    async def initialize(self) -> Result[None]:
        """Inicializa o processador."""
        self.logger.info("Processador inicializando...")
        # Aqui você pode executar setup
        self.initialized = True
        return Result.ok(None)
    
    async def shutdown(self) -> Result[None]:
        """Encerra o processador."""
        self.logger.info("Processador encerrando...")
        self.data_cache.clear()
        self.initialized = False
        return Result.ok(None)
    
    async def process(self, data: str) -> Result[str]:
        """Processa dados."""
        try:
            if not self.is_ready():
                return Result.error("Processador não está pronto")
            
            with self.logger.context(data_length=len(data)):
                self.logger.info(f"Processando {len(data)} caracteres")
                
                # Lógica de processamento
                result = data.upper()
                self.data_cache.append(result)
                
                return Result.ok(result)
        except Exception as e:
            return Result.error(f"Erro ao processar: {e}")


# Registra no DI container
def register_processor(container):
    from core.di_container import LifecycleType
    container.register_singleton(
        MyProcessor,
        MyProcessor,
        lifecycle=LifecycleType.SINGLETON
    )
```

---

## 3. Sistema de Observadores para Eventos

```python
"""
core/observers/logging_observer.py - Observer que registra eventos
"""

from core.base import Observer, Event
from core.logging_module import get_logger


class LoggingObserver(Observer):
    """Observer que registra todos os eventos."""
    
    def __init__(self):
        self.logger = get_logger("LoggingObserver")
    
    async def on_event(self, event: Event) -> None:
        """Registra evento em log."""
        self.logger.info(
            f"Evento recebido: {event.event_type.name}",
            event_id=event.id,
            data=event.data
        )


# Uso:
async def setup_observers(event_bus):
    observer = LoggingObserver()
    event_bus.subscribe(observer)
```

---

## 4. Máquina de Estados com Guards e Actions

```python
"""
Exemplo de máquina de estados avançada
"""

from core.state_machine import (
    StateMachine,
    AssistantState,
    Trigger
)
from core.logging_module import get_logger


def create_advanced_state_machine():
    """Cria máquina de estados com lógica avançada."""
    
    machine = StateMachine()
    logger = get_logger("StateMachine")
    
    # Guard: Verifica se há plano gerado
    def has_plan() -> bool:
        return True  # Aqui você checaria seu estado real
    
    # Action: Registra transição
    def on_plan_generated():
        logger.info("Plano foi gerado!")
    
    # Transição com guard e action
    machine.add_transition(
        from_state=AssistantState.PLANNING,
        to_state=AssistantState.EXECUTING,
        trigger=Trigger.PLAN_GENERATED,
        guard=has_plan,
        action=on_plan_generated
    )
    
    return machine
```

---

## 5. Repository Pattern para Persistência

```python
"""
core/repositories/memory_repository.py - Exemplo de Repository
"""

from typing import List, Optional
from core.base import Memory, Repository, Event, Result
from core.logging_module import get_logger
import json
from pathlib import Path


class JSONMemoryRepository(Memory):
    """Repository que persiste em JSON."""
    
    def __init__(self, file_path: str = "data/memory.json"):
        super().__init__("JSONMemoryRepository")
        self.file_path = Path(file_path)
        self.logger = get_logger("JSONMemoryRepository")
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def save(self, item: Event) -> Result[str]:
        """Salva um evento."""
        try:
            events = await self._load_all()
            events.append(item.to_dict())
            
            with open(self.file_path, 'w') as f:
                json.dump(events, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Evento salvo: {item.id}")
            return Result.ok(item.id)
        except Exception as e:
            return Result.error(f"Erro ao salvar: {e}")
    
    async def load(self, id: str) -> Result[Optional[Event]]:
        """Carrega um evento por ID."""
        try:
            events = await self._load_all()
            for event_data in events:
                if event_data.get('id') == id:
                    return Result.ok(event_data)
            return Result.ok(None)
        except Exception as e:
            return Result.error(f"Erro ao carregar: {e}")
    
    async def list_all(self) -> Result[List[Event]]:
        """Lista todos os eventos."""
        try:
            events = await self._load_all()
            return Result.ok(events)
        except Exception as e:
            return Result.error(f"Erro ao listar: {e}")
    
    async def delete(self, id: str) -> Result[None]:
        """Deleta um evento."""
        try:
            events = await self._load_all()
            events = [e for e in events if e.get('id') != id]
            
            with open(self.file_path, 'w') as f:
                json.dump(events, f, indent=2, ensure_ascii=False)
            
            return Result.ok(None)
        except Exception as e:
            return Result.error(f"Erro ao deletar: {e}")
    
    async def get_recent(self, limit: int = 10) -> Result[List[Event]]:
        """Retorna eventos recentes."""
        try:
            events = await self._load_all()
            return Result.ok(events[-limit:])
        except Exception as e:
            return Result.error(f"Erro ao buscar recentes: {e}")
    
    async def _load_all(self) -> list:
        """Helper para carregar todos."""
        if self.file_path.exists():
            with open(self.file_path, 'r') as f:
                return json.load(f)
        return []
```

---

## 6. Integração com OpenAI (Planner)

```python
"""
core/services/planner_service.py - Serviço sofisticado de planejamento
"""

from typing import Optional
import asyncio
from openai import AsyncOpenAI

from core.base import Planner, Plan, ActionStep, ActionType, Result
from core.config import get_config
from core.logging_module import get_logger


class OpenAIPlannerService(Planner):
    """Serviço de planejamento usando OpenAI."""
    
    def __init__(self):
        super().__init__("OpenAIPlannerService")
        self.config = get_config()
        self.logger = get_logger("OpenAIPlannerService")
        self.client = AsyncOpenAI(api_key=self.config.openai.api_key)
    
    async def initialize(self) -> Result[None]:
        """Inicializa o serviço."""
        if not self.config.openai.is_valid():
            return Result.error("Configuração de OpenAI inválida")
        
        self.initialized = True
        self.logger.info("OpenAI Planner Service inicializado")
        return Result.ok(None)
    
    async def interpret_command(self, command: str, context: str = "") -> Result[Plan]:
        """Interpreta comando e gera plano."""
        try:
            prompt = f"""
Você é um assistente de automação. Analise o comando e gere um plano.

Comando: {command}
Contexto: {context}

Responda em JSON com a estrutura:
{{
    "plan": {{
        "name": "Nome do plano",
        "steps": [
            {{"action": "open_app", "parameters": {{"target": "notepad"}}}},
            {{"action": "type_text", "parameters": {{"content": "Hello"}}}}
        ]
    }}
}}
"""
            
            response = await self.client.chat.completions.create(
                model=self.config.openai.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.openai.temperature,
                max_tokens=self.config.openai.max_tokens
            )
            
            # Parse response (aqui você implementaria a lógica)
            plan = Plan(name=f"Plan for: {command}")
            
            self.logger.info(f"Plano gerado para: {command}")
            return Result.ok(plan)
        except Exception as e:
            return Result.error(f"Erro ao gerar plano: {e}")
    
    async def optimize_plan(self, plan: Plan) -> Result[Plan]:
        """Otimiza um plano existente."""
        # Implementar otimização
        return Result.ok(plan)
```

---

## 7. Configuração em .env

```bash
# .env - Novo formato estruturado

# Ambiente
ENV=development
DEBUG=true

# OpenAI
OPENAI_API_KEY=sk-...seu-key...
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7

# Percepção
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
OCR_LANG=por

# Memória
MEMORY_PATH=data/memory_log.jsonl
VECTOR_STORAGE=false

# Logging
LOG_LEVEL=INFO
LOG_DIR=data/logs
```

---

## 8. Testando Componentes

```python
"""
tests/test_my_processor.py - Exemplo de teste
"""

import pytest
from core.components.my_processor import MyProcessor
from core.config import AppConfig


@pytest.fixture
async def processor():
    p = MyProcessor()
    await p.initialize()
    yield p
    await p.shutdown()


@pytest.mark.asyncio
async def test_processor_process(processor):
    result = await processor.process("hello")
    assert result.success
    assert result.data == "HELLO"


@pytest.mark.asyncio
async def test_processor_error_when_not_ready():
    p = MyProcessor()
    result = await p.process("test")
    assert not result.success
    assert "não está pronto" in result.error
```

---

## 9. Executar com Nova Arquitetura

```bash
# Ativar ambiente virtual
.\.venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt

# Rodar aplicação
python main.py

# Rodar testes
pytest tests/ -v

# Verificar cobertura
pytest --cov=core tests/
```

---

## 📝 Checklist de Migração

- [ ] Atualizar `main.py` com novo setup
- [ ] Refatorar componentes legacy para herdar de `Component`/`Service`
- [ ] Mover lógica de negócio para observers
- [ ] Implementar repositories para persistência
- [ ] Adicionar type hints em todos os módulos
- [ ] Escrever testes para componentes críticos
- [ ] Atualizar `.env` com nova configuração
- [ ] Documentar casos de uso específicos

---

Essa arquitetura agora é **profissional, testável e escalável**! 🚀
