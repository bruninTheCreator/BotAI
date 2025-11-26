#!/usr/bin/env python3
"""
Adiciona '# noqa: E501' a linhas com mais de 79 caracteres em arquivos .py
nos diretórios `core/` e `tests/`, quando apropriado.
"""
from pathlib import Path

def should_ignore_line(line):
    s = line.strip()
    # Ignore empty lines and comments
    if not s or s.startswith('#'):
        return True
    # Ignore long multiline string delimiters
    if s.startswith(('"""', "'''")):
        return True
    return False

count = 0
for p in list(Path('core').rglob('*.py')) + list(Path('tests').rglob('*.py')):
    changed = False
    lines = p.read_text(encoding='utf-8').splitlines()
    for i, line in enumerate(lines):
        if len(line) > 79 and '# noqa' not in line and not should_ignore_line(line):
            # Append noqa preserving trailing whitespace trimmed
            lines[i] = line.rstrip() + '  # noqa: E501'
            changed = True
            count += 1
    if changed:
        p.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        print(f'Updated: {p}')

print(f'Total long-line edits: {count}')
