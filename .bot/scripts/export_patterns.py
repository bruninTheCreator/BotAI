# flake8: noqa
"""Exporta padrões detectados na memória para um arquivo JSON.

Uso:
  python scripts/export_patterns.py [out.json]

Se `out.json` não for fornecido, escreve em `data/patterns_report.json`.
"""
from core.memoria import Memory
from core.pattern_engine import PatternEngine
import os
import sys

# garante import do pacote
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join('data', 'patterns_report.json')
    mem = Memory()
    engine = PatternEngine(memory=mem)
    engine.update()
    patterns = engine.list_patterns(top=0, sort_by="confidence")
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        import json
        json.dump(patterns, f, ensure_ascii=False, indent=2)
    print(f"Relatório de padrões exportado para: {out}")


if __name__ == '__main__':
    main()
