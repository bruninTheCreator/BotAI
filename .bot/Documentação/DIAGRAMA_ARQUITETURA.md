# 🏛️ DIAGRAMA VISUAL DA ARQUITETURA

## Visão Geral do Sistema

```bash
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                             │
│  (main.py, gui/, scripts/, external integrations)              │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                 DOMAIN/SERVICE LAYER                             │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │   Assistant      │  │    Observer      │  │  Repository  │  │
│  │   Orchestrator   │  │  Implementations │  │ Persistence  │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
│                                                                   │
│  ┌────────────────────┐  ┌────────────────────────────────────┐  │
│  │  Planner Service   │  │   Executor Service                 │  │
│  │ (OpenAI, LLM)      │  │ (PyAutoGUI, actions)               │  │
│  └────────────────────┘  └────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────┐  ┌────────────────────────────────────┐  │
│  │ Perception Service │  │   Memory Service                   │  │
│  │ (OCR, CV)          │  │ (Persistência, busca)              │  │
│  └────────────────────┘  └────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│          CORE INFRASTRUCTURE LAYER                               │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              STATE MACHINE                                  │  │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐             │  │
│  │  │  IDLE    │───▶│LISTENING │───▶│PROCESSING             │  │
│  │  └──────────┘    └──────────┘    └──────┬───┘             │  │
│  │       ▲                                   │                │  │
│  │       │                                   ▼                │  │
│  │       └──────────────────────────────EXECUTING             │  │
│  │                                      │                      │  │
│  │                                      ▼                      │  │
│  │                                    ERROR                    │  │
│  │                                      │                      │  │
│  │                                      ▼                      │  │
│  │                                   SHUTDOWN                  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                EVENT BUS (Pub/Sub)                          │  │
│  │                                                              │  │
│  │  EventType:  PERCEPTION, PLANNING, EXECUTION, ERROR, etc   │  │
│  │  Priority:   CRITICAL, HIGH, NORMAL, LOW                   │  │
│  │  Features:   Filtering, History, Async dispatch             │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              MEMORY REPOSITORY                              │  │
│  │                                                              │  │
│  │  - Save/Load Events                                         │  │
│  │  - Search/Query                                             │  │
│  │  - Vectorization (future)                                   │  │
│  └────────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│              FOUNDATION LAYER                                    │
│                                                                   │
│  ┌───────────────────┐  ┌───────────────────┐  ┌─────────────┐  │
│  │  Configuration    │  │  DI Container     │  │  Logging    │  │
│  │                   │  │                   │  │             │  │
│  │ - AppConfig       │  │ - Singleton       │  │ - Structured│  │
│  │ - Environment     │  │ - Transient       │  │ - JSON      │  │
│  │ - Validation      │  │ - Scoped          │  │ - Context   │  │
│  │ - Profiles        │  │ - Resolution      │  │ - Perf Track│  │
│  └───────────────────┘  └───────────────────┘  └─────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                BASE TYPES & INTERFACES                      │  │
│  │                                                              │  │
│  │  - Event, ActionStep, Plan, Result[T]                       │  │
│  │  - Component, Service, Observer                             │  │
│  │  - Executor, Perception, Memory, Planner                    │  │
│  │  - EventEmitter, StateManager, Repository                   │  │
│  │  - Enums: EventType, ActionType, ExecutionStatus             │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Fluxo de Dados

```bash
USER INPUT
    │
    ▼
┌─────────────┐
│ Perception  │  ◀─ Captura tela, OCR, TCR
│   Service   │
└──────┬──────┘
       │ Event(PERCEPTION)
       ▼
┌─────────────────────────┐
│   Event Bus             │
│  (emit to subscribers)  │
└──────┬──────────────────┘
       │
       ├──▶ Logging Observer
       │
       ├──▶ State Machine (triggers)
       │
       └──▶ Planning Service
                │
                ▼
            ┌─────────────┐
            │   Planner   │  ◀─ Calls LLM (OpenAI)
            │   Service   │
            └──────┬──────┘
                   │ Event(PLANNING)
                   ▼
            ┌─────────────┐
            │ Event Bus   │
            └──────┬──────┘
                   │
                   ├──▶ State Machine (transitions)
                   │
                   └──▶ Executor Service
                            │
                            ▼
                       ┌─────────────┐
                       │  Executor   │  ◀─ PyAutoGUI, etc
                       │  Service    │
                       └──────┬──────┘
                              │
                              ▼
                       ┌─────────────┐
                       │ Event Bus   │ Event(EXECUTION)
                       └──────┬──────┘
                              │
                              ├──▶ Memory Service (save)
                              │
                              ├──▶ Logging Observer
                              │
                              └──▶ State Machine (transitions)
                                       │
                                       ▼
                                   LISTENING STATE
                                   (volta ao início)
```

---

## Padrões de Design

```bash
┌────────────────────────────────────────────────────────────────┐
│                    DESIGN PATTERNS                              │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. OBSERVER                                                    │
│     ┌──────────────┐         ┌──────────────┐                 │
│     │ EventEmitter │────────▶│ Observer 1   │                 │
│     └──────────────┘         └──────────────┘                 │
│            │                  ┌──────────────┐                 │
│            └─────────────────▶│ Observer 2   │                 │
│                               └──────────────┘                 │
│                                                                 │
│  2. STATE MACHINE                                               │
│     Trigger ──▶ Guard ──▶ Action ──▶ Transition ──▶ New State │
│                                                                 │
│  3. DEPENDENCY INJECTION                                        │
│     Container ──▶ Register ──▶ Resolve ──▶ Instance            │
│                                                                 │
│  4. REPOSITORY                                                  │
│     Repository[T] ──▶ Save/Load/Delete/Query                   │
│                                                                 │
│  5. FACTORY                                                     │
│     StateMachineFactory.create_default() ──▶ StateMachine      │
│                                                                 │
│  6. SERVICE                                                     │
│     Component ──▶ Initialize() ──▶ Do Work ──▶ Shutdown()      │
│                                                                 │
│  7. RESULT PATTERN                                              │
│     Operation ──▶ Result[T] ──▶ .success/.data/.error          │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Componentização

```bash
┌─────────────────────────────────────────────────────────────────┐
│                      COMPONENTES                                 │
├──────────────────────────┬──────────────────────────────────────┤
│  PERCEIÇÃO              │  PROCESSAMENTO                         │
│  - Captura tela         │  - Planejamento (LLM)                 │
│  - OCR                  │  - Detecção de padrões                │
│  - Template matching    │  - Otimização de planos               │
│  - Análise de cores     │  - Validação                          │
├──────────────────────────┼──────────────────────────────────────┤
│  EXECUÇÃO               │  MEMÓRIA & PERSISTÊNCIA                │
│  - Controle do mouse    │  - Armazenamento de eventos           │
│  - Teclado              │  - Busca semântica                    │
│  - Janelas              │  - Histórico                          │
│  - Aplicativos          │  - Backup automático                  │
├──────────────────────────┼──────────────────────────────────────┤
│  ORQUESTRAÇÃO           │  OBSERVABILIDADE                       │
│  - State machine        │  - Logging estruturado                │
│  - Event emitter        │  - Performance tracking               │
│  - Error handling       │  - Métricas                           │
│  - Scheduling           │  - Health checks                      │
└──────────────────────────┴──────────────────────────────────────┘
```

---

## Ciclos de Vida de Componentes

```bash
    START (Boot)
        │
        ▼
    ┌──────────────────┐
    │  configure()     │  ◀─ Carrega config
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  initialize()    │  ◀─ Setup DI, criar componentes
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  is_ready()      │  ◀─ Check health
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  running()       │  ◀─ Main loop
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  shutdown()      │  ◀─ Cleanup
    └────────┬─────────┘
             │
             ▼
    STOPPED (Exit)
```

---

## Integração com OpenAI

```bash
┌─────────────────────────────────────────────────────┐
│           Planner Service Flow                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. User Command (string)                           │
│         │                                           │
│         ▼                                           │
│  2. Build Prompt                                   │
│     - Command                                       │
│     - Screen Context (OCR)                         │
│     - Recent History (Memory)                      │
│         │                                           │
│         ▼                                           │
│  3. Call OpenAI API                                │
│     ┌────────────────────────────────────────────┐ │
│     │ Model: gpt-4o-mini                         │ │
│     │ Temperature: 0.7                           │ │
│     │ Max Tokens: 1000                           │ │
│     │ Timeout: 30s                               │ │
│     └────────────────────────────────────────────┘ │
│         │                                           │
│         ▼                                           │
│  4. Parse Response (JSON)                          │
│     [ActionStep, ActionStep, ...]                 │
│         │                                           │
│         ▼                                           │
│  5. Return Plan                                    │
│     Result[Plan] { success, data, error }         │
│         │                                           │
│         ▼                                           │
│  6. Executor executa Plan                         │
│                                                    │
└─────────────────────────────────────────────────────┘
```

---

## Fluxo de Teste

```bash
TESTE UNITÁRIO
    │
    ├─▶ Test Event Creation
    │
    ├─▶ Test Plan Steps
    │
    ├─▶ Test Result[T]
    │
    └─▶ Test Individual Components

TESTE DE INTEGRAÇÃO
    │
    ├─▶ Test Component Interaction
    │
    ├─▶ Test State Machine Flow
    │
    ├─▶ Test Event Emission
    │
    ├─▶ Test DI Resolution
    │
    └─▶ Test End-to-End Workflow
        (perception → planning → execution)

TESTE DE PERFORMANCE
    │
    ├─▶ OCR Speed
    │
    ├─▶ State Transitions
    │
    ├─▶ Event Emission
    │
    └─▶ Memory Usage
```

---

## Escopo de Responsabilidades

```bash
PERCEPTION LAYER
│
├─ O quê: Capturar dados do ambiente
├─ Como: OCR, CV, templates
└─ Saída: Texto, imagens, metadados

PLANNING LAYER
│
├─ O quê: Converter intenções em planos
├─ Como: LLM, heurísticas
└─ Saída: Plano executável

EXECUTION LAYER
│
├─ O quê: Executar ações no sistema
├─ Como: PyAutoGUI, APIs
└─ Saída: Resultados, logs

MEMORY LAYER
│
├─ O quê: Persistência e busca
├─ Como: JSON, vetores, SQL
└─ Saída: Histórico, contexto

STATE LAYER
│
├─ O quê: Controlar fluxo da máquina
├─ Como: FSM, guards, callbacks
└─ Saída: Transições, eventos

LOGGING LAYER
│
├─ O quê: Observabilidade completa
├─ Como: Structured logging, metrics
└─ Saída: Logs, traces, metrics
```

---

## Distribuição de Código

```bash
FOUNDATION (20%)
├─ base.py:              400+ linhas
├─ config.py:            350+ linhas
├─ logging_module.py:    300+ linhas
└─ di_container.py:      280+ linhas
  Total: ~1.330 linhas

INFRASTRUCTURE (25%)
├─ state_machine.py:     380+ linhas
├─ event_emitter.py:     320+ linhas
└─ percepcao.py:         350+ linhas
  Total: ~1.050 linhas

DOMAIN (40%)
├─ planner.py:           (a refatorar)
├─ executor.py:          (a refatorar)
├─ memoria.py:           (a refatorar)
└─ detector_repeticao:   (a integrar)
  Total: ~1.200 linhas

APPLICATION (15%)
├─ main.py:              (a atualizar)
├─ assistant.py:         (a refatorar)
└─ tests/:               500+ linhas
  Total: ~700 linhas

TOTAL: ~4.280 linhas de código arquitetônico
```

---

## Stack Tecnológico

```bash
RUNTIME
├─ Python 3.10+
├─ Async/Await (asyncio)
└─ Type Hints (mypy compatible)

CORE LIBRARIES
├─ pytesseract (OCR)
├─ opencv-python (CV)
├─ pyautogui (Automation)
├─ pillow (Image processing)
└─ python-dotenv (Config)

AI/ML
├─ OpenAI API (LLM)
├─ numpy (Numerics)
└─ (ChromaDB - future)

INFRASTRUCTURE
├─ FastAPI (Future API)
├─ SQLAlchemy (Future DB)
├─ Pydantic (Validation)
└─ Prometheus (Metrics - Future)

TESTING
├─ pytest
├─ pytest-asyncio
├─ pytest-cov
└─ unittest.mock

QUALITY
├─ black (Formatting)
├─ flake8 (Linting)
├─ mypy (Type checking)
└─ bandit (Security)
```

---

## Roadmap Visual

```bash
2024 Q4 (CURRENT)
│
├─ ✅ Arquitetura base
├─ ✅ Padrões de design
├─ ✅ Documentação
└─ 🔄 Refatoração de módulos

2025 Q1
│
├─ 🔄 Integração completa
├─ 🔄 Testes extensivos
├─ 🔄 Performance tuning
└─ 🔄 First stable release

2025 Q2
│
├─ 📌 API REST (FastAPI)
├─ 📌 WebSocket support
├─ 📌 Database (SQL + Vector)
└─ 📌 Kubernetes deployment

2025 Q3+
│
├─ 📌 Multimodal AI
├─ 📌 Distributed processing
├─ 📌 Advanced caching
└─ 📌 Enterprise features

Legend:
✅ = Completed
🔄 = In Progress
📌 = Planned
```

---

Esta visualização representa a **transformação arquitetônica completa do BotAI** em um sistema enterprise-ready! 🚀
