# flake8: noqa
"""Script de smoke-run não interativo para validar comportamento básico do Assistant.

Este script instancia o Assistant, captura o texto da tela via Perception (ou o placeholder
quando Tesseract não está disponível), executa detecção de padrões e imprime um resumo.
É seguro para execução automática e não entra no loop interativo.
"""
from core.assistent import Assistant
import os
import sys

# Garante que o diretório raiz do projeto esteja no sys.path quando
# executado como script
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def smoke_run():
    a = Assistant()
    print("[smoke] Capturando texto da tela (pode ser placeholder se OCR ausente)...")
    text = a._read_text_sync()
    print(f"[smoke] Texto (resumo 200 chars): {text[:200]!r}")

    patterns = a._detect_patterns(text)
    print(f"[smoke] Padrões detectados: {patterns}")

    # Detecta padrões na memória com detalhes
    try:
        new_patterns = a.pattern_engine.update()
        total = len(a.pattern_engine.list_patterns(top=0))
        print(f"[smoke] PatternEngine: novos={len(new_patterns)}, total={total}")
    except Exception as e:
        print(f"[smoke] Erro ao rodar detector: {e}")


if __name__ == '__main__':
    smoke_run()
