# 📦 INSTRUÇÕES DE INSTALAÇÃO E SETUP

## Pré-requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)
- Virtual environment (venv)

---

## 1. Preparar Ambiente Virtual

### Windows (PowerShell)

```powershell
# Ativar o repositório
cd "c:\Users\A21057836\OneDrive - GRUPO EQUATORIAL ENERGIA\Área de Trabalho\BotAI\.bot"

# Criar virtual environment (se não existir)
python -m venv .venv

# Ativar
.\.venv\Scripts\Activate.ps1

# Atualizar pip
python -m pip install --upgrade pip
```

### macOS/Linux

```bash
cd /caminho/para/.bot

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

---

## 2. Instalar Dependências Base

```bash
# Copiar requirements.txt existente e adicionar novas dependências
pip install -r requirements.txt

# Instalar pacotes adicionais para nova arquitetura
pip install pytest pytest-asyncio pytest-cov black flake8 mypy
```

### Conteúdo Recomendado do `requirements.txt`

```bash
# Versão atualizada com suporte à nova arquitetura

# Core
openai>=1.0.0
python-dotenv>=1.0.0

# Automation
pyautogui>=0.9.54
pynput>=1.7.6

# Vision/OCR
pytesseract>=0.3.10
opencv-python>=4.8.0
Pillow>=10.0.0
numpy>=1.24.0

# Async
asyncio>=3.4.3

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0

# Quality
black>=23.0.0
flake8>=6.0.0
mypy>=1.4.0
bandit>=1.7.0

# API (Future)
fastapi>=0.100.0
uvicorn>=0.23.0
pydantic>=2.0.0

# Database (Future)
sqlalchemy>=2.0.0
alembic>=1.12.0

# Observability (Future)
prometheus-client>=0.17.0
```

---

## 3. Instalar Tesseract-OCR (Windows)

### Opção A: Instalação Automática (Recomendado)

```powershell
# Download do instalador
# URL: https://github.com/UB-Mannheim/tesseract/releases

# Fazer download da versão mais recente:
# tesseract-ocr-w64-setup-v5.x.x.exe

# Executar o instalador (Windows Explorer)
# - Deixar caminho padrão: C:\Program Files\Tesseract-OCR
# - Instalar todas as linguagens (português incluído)

# Depois de instalar, o Python deverá encontrar automaticamente
```

### Opção B: Instalação Manual

```powershell
# 1. Download da versão portável
# URL: https://github.com/UB-Mannheim/tesseract/wiki

# 2. Extrair para C:\Tesseract-OCR

# 3. Adicionar ao .env
# TESSERACT_CMD=C:\Tesseract-OCR\tesseract.exe

# 4. Verificar instalação
python -c "import pytesseract; pytesseract.pytesseract.tesseract_cmd"
```

### Opção C: Via Conda (Se usando Anaconda)

```bash
conda install -c conda-forge tesseract
```

---

## 4. Configurar Arquivo .env

### Criar arquivo `.env` na raiz do projeto

```bash
# Linux/macOS
touch .env

# Windows PowerShell
New-Item -Name ".env" -ItemType "file"
```

### Adicionar Configurações

```bash
# .env - Arquivo de configuração

# ============================================
# AMBIENTE
# ============================================
ENV=development
DEBUG=true

# ============================================
# OPENAI
# ============================================
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=1000

# ============================================
# PERCEPÇÃO (OCR)
# ============================================
# Windows
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# Linux/macOS (opcional, será encontrado no PATH)
# TESSERACT_CMD=/usr/bin/tesseract

OCR_LANG=por
USE_OCR_PREPROCESSING=true
OCR_PREPROCESSING_SCALE=1.5

# ============================================
# MEMÓRIA
# ============================================
MEMORY_PATH=data/memory_log.jsonl
BACKUP_ENABLED=true
VECTOR_STORAGE=false

# ============================================
# LOGGING
# ============================================
LOG_LEVEL=INFO
LOG_DIR=data/logs
CONSOLE_OUTPUT=true
FILE_OUTPUT=true

# ============================================
# EXECUTOR
# ============================================
ENABLE_CONFIRMATION=true
AUTO_RETRY=true
MAX_RETRIES=3
```

**⚠️ IMPORTANTE:** Adicione `.env` ao `.gitignore` para não expor chaves:

```bash
# .gitignore
.env
.env.local
.venv/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.coverage
htmlcov/
```

---

## 5. Verificar Instalação

### Testar imports principais

```bash
# Ativar ambiente
.\.venv\Scripts\Activate.ps1

# Testar imports
python -c "
from core import (
    AppConfig, ConfigLoader, Logger, 
    StateMachine, EventBus, ServiceContainer
)
print('✅ Todos os imports funcionando!')
"
```

### Testar Tesseract

```bash
python -c "
import pytesseract
from PIL import Image
print('✅ Tesseract encontrado em:', pytesseract.pytesseract.tesseract_cmd)
"
```

### Testar OpenAI

```bash
python -c "
from openai import OpenAI
from core.config import get_config
config = get_config()
if config.openai.is_valid():
    print('✅ Configuração OpenAI válida!')
else:
    print('❌ Configure OPENAI_API_KEY no .env')
"
```

---

## 6. Executar Testes

```bash
# Ativar ambiente
.\.venv\Scripts\Activate.ps1

# Executar testes
pytest tests/test_architecture.py -v

# Com cobertura
pytest tests/test_architecture.py --cov=core --cov-report=html

# Resultado em: htmlcov/index.html
```

---

## 7. Executar Verificação de Qualidade

```bash
# Black (formatação)
black core/ tests/

# Flake8 (linting)
flake8 core/ tests/ --max-line-length=100

# MyPy (type checking)
mypy core/ --strict

# Bandit (segurança)
bandit -r core/
```

---

## 8. Estrutura de Diretórios Esperada

```bash
.bot/
├── .venv/                          # Virtual environment
├── .env                            # Configuração (não versionar!)
├── .gitignore                      # Git ignore
│
├── core/                           # Módulos principais
│   ├── __init__.py                 # ✅ Exports
│   ├── base.py                     # ✅ Interfaces base
│   ├── config.py                   # ✅ Configuração
│   ├── logging_module.py           # ✅ Logging
│   ├── di_container.py             # ✅ DI
│   ├── state_machine.py            # ✅ State machine
│   ├── event_emitter.py            # ✅ Events
│   ├── percepcao.py                # ✅ Refatorado
│   ├── planner.py                  # (a refatorar)
│   ├── executor.py                 # (a refatorar)
│   ├── memoria.py                  # (a refatorar)
│   └── detector_repeticao.py       # (a integrar)
│
├── data/                           # Dados
│   ├── memory_log.jsonl
│   ├── memory.json
│   └── logs/
│
├── tests/                          # Testes
│   ├── __init__.py
│   ├── test_architecture.py        # ✅ Suite de testes
│   ├── test_unit.py                # (existente)
│   └── test_detector.py            # (existente)
│
├── scripts/
│   ├── run_smoke.py
│   └── export_patterns.py
│
├── gui/
│   └── interface.py
│
├── requirements.txt                # ✅ Dependências atualizadas
├── main.py                         # (a atualizar)
├── README.md                       # (documentação existente)
│
├── ARCHITECTURE.md                 # ✅ Arquitetura
├── GUIA_PRATICO.md                 # ✅ Guia de uso
├── RESUMO_EXECUTIVO.md             # ✅ Overview
├── PLANO_IMPLEMENTACAO.md          # ✅ Roadmap
├── DIAGRAMA_ARQUITETURA.md         # ✅ Diagramas
├── SUMARIO_ENTREGA.md              # ✅ Entrega
└── SETUP_INSTALACAO.md             # ✅ Este arquivo
```

---

## 9. Troubleshooting

### Problema: Tesseract não encontrado

```bash
# Solução 1: Instalar via Choco (Windows)
choco install tesseract

# Solução 2: Adicionar manualmente no .env
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# Solução 3: Verificar instalação
where tesseract  # Windows
which tesseract  # macOS/Linux
```

### Problema: OpenAI API Key inválida

```bash
# Verificar se .env foi criado
ls -la .env  # macOS/Linux
dir .env     # Windows

# Verificar se a chave está correta
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('OPENAI_API_KEY')[:10] + '...')"
```

### Problema: Virtual environment não ativa

```bash
# Recriar venv
rm -rf .venv

# Criar novo
python -m venv .venv

# Ativar
.\.venv\Scripts\Activate.ps1
```

### Problema: Testes falhando

```bash
# Limpar cache
rm -rf __pycache__ .pytest_cache .mypy_cache

# Reinstalar dependências
pip install --upgrade -r requirements.txt

# Executar novamente
pytest tests/test_architecture.py -v
```

---

## 10. Próximos Passos

1. ✅ Instalar dependências
2. ✅ Configurar .env
3. ✅ Executar testes
4. ⬜ Ler GUIA_PRATICO.md
5. ⬜ Refatorar módulos legacy
6. ⬜ Atualizar main.py
7. ⬜ Escalar a aplicação

---

## 📞 Suporte

Se encontrar problemas:

1. Verifique se Python 3.10+ está instalado: `python --version`
2. Verifique se venv está ativado: `python -m site`
3. Consulte o Troubleshooting acima
4. Verifique ARCHITECTURE.md para detalhes técnicos

---

**Setup concluído com sucesso!** ✅

Próximo: `python main_v2.py` (após refatoração do main.py)
