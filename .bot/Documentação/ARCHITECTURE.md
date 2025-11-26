# 🏗️ Arquitetura Sofisticada - BotAI 2.0

## Visão Geral

O projeto foi transformado de uma arquitetura procedural simples para um **sistema profissional orientado a objetos** com padrões de design avançados, tipos sofisticados e observabilidade completa.

---

## 📦 Novos Módulos Implementados

### 1. **`core/base.py`** - Fundação de Tipos e Interfaces

Fornece as bases para toda a arquitetura:

**Classes Base Abstratas:**

- `Component`: Base para todos os componentes do sistema
- `Service`: Serviço com ciclo de vida
- `Observer`: Padrão Observer
- `EventEmitter`: Emissão de eventos
- `Repository`: Persistência de dados (genérico)
- `Executor`: Execução de ações
- `Perception`: Captura de percepção
- `Memory`: Memória com repositório
- `Planner`: Planejamento
- `StateManager`: Gerenciamento de estado

**Enums Sofisticados:**  

```python
EventType           # Tipos de eventos
ActionType          # Tipos de ações
ExecutionStatus     # Status de execução
```

**Dataclasses Tipadas:**

- `Event`: Evento estruturado
- `ActionStep`: Passo de ação
- `Plan`: Plano de execução
- `Result[T]`: Padrão de resultado genérico

  ```python
  # Uso:
  result = Result.ok(data="sucesso")
  if result.success:
      print(result.data)
  ```

---

### 2. **`core/config.py`** - Configuração Centralizada

**Sistema de Configuração em Camadas:**

```python
AppConfig (central)
├── OpenAIConfig
├── PerceptionConfig
├── ExecutorConfig
├── MemoryConfig
└── LoggingConfig
```

**Funcionalidades:**

- ✅ Carregamento de múltiplas fontes (.env, JSON, dict)
- ✅ Validação automática
- ✅ Profiles (dev, prod, testing)
- ✅ Singleton global thread-safe
- ✅ Serialização/desserialização

**Exemplo:**

```python
from core.config import ConfigLoader, get_config

# Carrega de .env
config = ConfigLoader.from_env()

# Ou de arquivo
config = ConfigLoader.from_file("config.json")

# Acesso global
config = get_config()
```

---

### 3. **`core/logging_module.py`** - Logging Estruturado

**Recursos Avançados:**

- ✅ Logs estruturados em JSON
- ✅ Múltiplos handlers (console + arquivo)
- ✅ Rotação automática de logs
- ✅ Context manager para rastreamento
- ✅ Performance tracking com decorator

**Exemplo:**

```python
from core.logging_module import get_logger, PerformanceTracker

logger = get_logger("meu_modulo")

# Log simples
logger.info("Iniciando...", user_id=123)

# Com contexto
with logger.context(request_id="xyz", user="admin"):
    logger.info("Executando operação")

# Performance tracking
@PerformanceTracker.track(logger)
def expensive_operation():
    pass
```

---

### 4. **`core/di_container.py`** - Injeção de Dependência

**Padrão Service Locator com Ciclos de Vida:**

**Ciclos de Vida:**

- `SINGLETON`: Criado uma vez, compartilhado
- `TRANSIENT`: Criado a cada requisição
- `SCOPED`: Criado por escopo

**Exemplo:**

```python
from core.di_container import ServiceContainer, LifecycleType

container = ServiceContainer()

# Registra um singleton
container.register_singleton(MyService, MyServiceImpl)

# Registra transient
container.register_transient(Logger, LoggerImpl)

# Resolve
service = container.resolve(MyService)

# Com injeção de dependência
@inject(MyService)
def my_function(service: MyService = None):
    service.do_something()
```

---

### 5. **`core/state_machine.py`** - Máquina de Estados

**Características:**

- ✅ Estados bem definidos com `AssistantState` enum
- ✅ Triggers para transições
- ✅ Guards (condições) para transições
- ✅ Callbacks on_enter/on_exit
- ✅ Histórico de transições
- ✅ Metadados de estado

**Estados do Assistente:**

```bash
IDLE → LISTENING → PROCESSING → PLANNING → EXECUTING → LISTENING
                                             ↓
                                          ERROR → LISTENING
                ↓ (STOP)
              SHUTDOWN
```

**Exemplo:**

```python
from core.state_machine import StateMachineFactory, Trigger

machine = StateMachineFactory.create_default()

# Registra callback
machine.on_enter(AssistantState.EXECUTING, lambda: print("Executando!"))

# Dispara trigger
if machine.trigger(Trigger.EXECUTION_COMPLETED):
    current = machine.get_current_state()
    print(f"Estado: {current.name}")

# Verifica triggers válidos
valid_triggers = machine.get_valid_triggers()
```

---

### 6. **`core/event_emitter.py`** - Padrão Observer/Pub-Sub

**Sistema de Eventos Robusto:**

- ✅ Pub/sub com prioridades
- ✅ Filtros de eventos
- ✅ Histórico de eventos
- ✅ Async-first

**Exemplo:**

```python
from core.event_emitter import EventBus, Priority
from core.base import EventType, Observer

class MyObserver(Observer):
    async def on_event(self, event):
        print(f"Evento recebido: {event.event_type}")

bus = EventBus.get_instance()

# Subscreve
observer = MyObserver()
bus.subscribe(
    observer,
    event_types={EventType.EXECUTION},
    priority=Priority.HIGH,
    filters=[lambda e: e.data.get('status') == 'error']
)

# Emite
event = Event(event_type=EventType.EXECUTION, data={...})
await bus.emit(event)
```

---

## 🏛️ Arquitetura em Camadas

```bash
┌─────────────────────────────────────────────┐
│         Application Layer                    │
         (main.py, gui, scripts)                │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│       Domain/Service Layer                  │
│  (Assistente, coordenação de componentes)  │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│       Core Infrastructure Layer             │
│  (State Machine, Event Bus, Memory)        │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│      Foundation Layer                       │
│  (Config, DI, Logging, Base Classes)       │
└─────────────────────────────────────────────┘
```

---

## 🎯 Padrões de Design Implementados

| Padrão | Arquivo | Descrição |
|--------|---------|-----------|
| **Observer** | event_emitter.py | Pub/Sub com prioridades |
| **State Machine** | state_machine.py | Máquina de estados |
| **Dependency Injection** | di_container.py | IoC container |
| **Repository** | base.py | Abstração de persistência |
| **Factory** | state_machine.py | Criação de objetos |
| **Strategy** | (próximo) | Diferentes estratégias de ação |
| **Adapter** | (próximo) | Adaptadores para APIs externas |

---

## 🔧 Próximos Passos

1. ✅ Refatorar componentes core com novas interfaces
2. ✅ Implementar testes unitários/integração
3. ✅ Adicionar validação robusta com Pydantic
4. ✅ Sistema de cache distribuído
5. ✅ Métricas e observabilidade
6. ✅ API REST/gRPC
7. ✅ Documentação com Sphinx

---

## 📖 Como Usar a Nova Arquitetura

### Setup Básico

```python
from core.config import ConfigLoader
from core.di_container import setup_di_container
from core.logging_module import get_logger

# 1. Carrega configuração
config = ConfigLoader.from_env()

# 2. Setup DI
container = setup_di_container()

# 3. Obtém logger
logger = get_logger("app")

logger.info("Aplicação iniciada", config_env=config.env.value)
```

### Criar um Novo Componente

```python
from core.base import Component, Result
from core.logging_module import get_logger

class MyComponent(Component):
    def __init__(self):
        super().__init__("MyComponent")
        self.logger = get_logger("MyComponent")
    
    async def initialize(self) -> Result[None]:
        self.logger.info("Inicializando...")
        self.initialized = True
        return Result.ok(None)
    
    async def shutdown(self) -> Result[None]:
        self.logger.info("Encerrando...")
        self.initialized = False
        return Result.ok(None)
```

### Registrar no DI Container

```python
container.register_singleton(
    MyComponent,
    MyComponent,
    logger=get_logger("app")
)

# Usar
component = container.resolve(MyComponent)
```

---

## 🚀 Benefícios da Nova Arquitetura

✅ **Type Safety**: Tipos completos com TypeHints
✅ **Maintainability**: Código modular e testável
✅ **Scalability**: Pronto para crescimento
✅ **Observability**: Logging e eventos estruturados
✅ **Flexibility**: Injeção de dependência
✅ **Robustness**: Tratamento de erros estruturado
✅ **Performance**: Lazy loading e caching
✅ **Testability**: Mock-friendly com interfaces

---

## 📊 Estrutura de Diretórios (Esperada)

```bash
.bot/
├── core/
│   ├── __init__.py
│   ├── base.py                 # ✅ Interfaces e tipos base
│   ├── config.py               # ✅ Configuração centralizada
│   ├── logging_module.py       # ✅ Logging estruturado
│   ├── di_container.py         # ✅ Injeção de dependência
│   ├── state_machine.py        # ✅ Máquina de estados
│   ├── event_emitter.py        # ✅ Pub/sub
│   ├── services/               # (Próximo) Serviços de negócio
│   ├── adapters/               # (Próximo) Adaptadores
│   └── repositories/           # (Próximo) Persistência
├── data/
├── tests/
├── main.py
└── requirements.txt
```

---

## 🎓 Conclusão

A nova arquitetura transforma o BotAI em um sistema **enterprise-ready** com:

- Separação clara de responsabilidades
- Componentes reutilizáveis e testáveis
- Observabilidade completa
- Facilidade de manutenção e evolução

Pronto para integração com AI, APIs, e scaling em produção!
