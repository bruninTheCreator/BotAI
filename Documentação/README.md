# .bot — Assistente de Escritório (smoke/dev)

Este repositório contém um assistente experimental de automação de tarefas de escritório.

Principais componentes

- `core/percepcao.py`: captura de tela e OCR (usa pytesseract). No Windows, instale o Tesseract (UB Mannheim) e adicione ao PATH.
- `core/memoria.py`: grava eventos em `data/memory_log.jsonl` (memória persistente).
- `core/detector_repeticao.py`: detector leve de padrões/repetições em memória.
- `core/planner.py`: integra com OpenAI para gerar planos (requer `OPENAI_API_KEY` no `.env`).
- `core/executor.py`: executa ações (pyautogui, abrir apps, teclas de atalho).
- `core/assistent.py`: loop interativo e orquestração.

Como rodar (Windows / PowerShell)

1. Ative o ambiente virtual do projeto (se existir):

```powershell
& ".\.venv\Scripts\Activate.ps1"
```

1. Instale dependências (opcional se já instaladas):

```powershell
pip install -r requirements.txt
```

1. (Recomendado) Instale Tesseract para OCR no Windows: veja o build [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) e adicione o executável `tesseract.exe` ao PATH.

1. Rodar testes:

```powershell
& ".\.venv\Scripts\python.exe" -m unittest -v
```

1. Smoke-run (não interativo, faz checagens rápidas e sai):

```powershell
& ".\.venv\Scripts\python.exe" scripts\run_smoke.py
```

1. Rodar o assistente interativo (requer `.env` com `OPENAI_API_KEY` se quiser usar o Planner):

```powershell
# Crie um arquivo .env com sua chave
echo "OPENAI_API_KEY=sua_chave_aqui" > .env
& ".\.venv\Scripts\python.exe" main.py
```

Interface gráfica (opcional)

```powershell
& ".\.venv\Scripts\python.exe" main_gui.py
```

Comandos do assistente

- `monitor on/off` ativa/desativa o monitoramento contínuo (OCR em background)
- `patterns [n]` lista padrões detectados (top n)
- `auto on/off` permite execução automática para padrões com `mode: "auto"`

Notas e recomendações

- O detector de repetição é leve e baseado em hash/assinaturas; para maior robustez considere embeddings e clustering.
- Sempre confirme ações automatizadas sensíveis; a aplicação pede confirmação antes de executar planos.
- Se não quiser integrar com OpenAI, o Planner continuará inativo (cliente não inicializado) e o assistente operará em modo limitado.

Próximos passos sugeridos

- Melhorar agrupamento semântico dos OCRs (sentence-transformers).
- Exportar padrões detectados para uma UI/relatório e permitir regras de automação aprovadas pelo usuário.

— fim —
