# flake8: noqa
"""Exporta padrões detectados na memória para um arquivo JSON.

Uso:
  python scripts/export_patterns.py [out.json]

Se `out.json` não for fornecido, escreve em `data/patterns_report.json`.
"""
from core.detector_repeticao import export_patterns_json
from core.memoria import Memory
import os
import sys

# garante import do pacote
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main():
    out = sys.argv[1] if len(
        sys.argv) > 1 else os.path.join(
        'data',
        'patterns_report.json')
    mem = Memory()
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    path = export_patterns_json(mem, out_path=out)
    print(f"Relatório de padrões exportado para: {path}")


if __name__ == '__main__':
    main()
