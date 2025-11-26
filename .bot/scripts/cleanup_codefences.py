"""Limpa blocos de código e marcadores inválidos dentro de arquivos .py no diretório core/.
Faz backup dos arquivos alterados (*.bak) antes de sobrescrever.
Uso: python scripts/cleanup_codefences.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core"

pattern_backticks = re.compile(r"```(?:python)?\n")
pattern_backticks_end = re.compile(r"\n```\n")

files_changed = []

for p in CORE.glob("*.py"):
    text = p.read_text(encoding="utf-8")
    original = text
    # Remove occurrences of ```python and closing ``` (and surrounding blank lines)
    text = re.sub(r"```python\n", "", text)
    text = re.sub(r"\n```\n", "\n", text)
    text = re.sub(r"```\n", "", text)
    text = text.replace('\r\n', '\n')

    # Remove accidental triple-quoted blocks that appear as standalone markers
    # e.g. lines that consist only of "```" or "```python"
    lines = text.splitlines()
    cleaned_lines = []
    skip_next_blank = False
    for ln in lines:
        if ln.strip() in ("```", "```python"):
            skip_next_blank = True
            continue
        if skip_next_blank and ln.strip() == "":
            skip_next_blank = False
            continue
        cleaned_lines.append(ln)
    text = "\n".join(cleaned_lines)

    # Remove duplicated adjacent imports (simple heuristic)
    text = re.sub(r"(import .*\n)(\1)+", r"\1", text)

    if text != original:
        bak = p.with_suffix(p.suffix + ".bak")
        bak.write_text(original, encoding="utf-8")
        p.write_text(text, encoding="utf-8")
        files_changed.append(str(p.relative_to(ROOT)))

print("Finished cleanup.")
if files_changed:
    print("Modified files:")
    for f in files_changed:
        print(" -", f)
else:
    print("No files changed.")
