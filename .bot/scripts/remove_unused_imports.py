#!/usr/bin/env python3
"""
Remove imports não utilizados dos arquivos Python.
"""
import re

# Mapeamento de arquivos e imports não usados
UNUSED_IMPORTS = {
    'core/assistent.py': [],
    'core/base.py': [],
    'core/config.py': [],
    'core/di_container.py': ['from .base import Component, Service'],
    'core/event_emitter.py': [],
    'core/executor.py': [],
    'core/logging_module.py': ['from typing import Any'],
    'core/memoria.py': [],
    'core/percepcao.py': ['from typing import List', 'from PIL import Image, ImageEnhance, ImageFilter'],
    'core/planner.py': [],
    'core/planner_simple.py': [],
    'core/state_machine.py': ['from .base import Event, EventType'],
    'tests/test_architecture.py': [
        'from unittest.mock import Mock, AsyncMock, patch',
        'from core.logging_module import Logger',
        'from core.di_container import LifecycleType',
        'from core.event_emitter import EventBus',
    ],
}

def remove_imports(filepath, imports_to_remove):
    """Remove imports específicos de um arquivo."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    for import_line in imports_to_remove:
        # Remover a linha exata
        content = content.replace(import_line + '\n', '')
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    fixed = 0
    for filepath, imports in UNUSED_IMPORTS.items():
        if imports and remove_imports(filepath, imports):
            print(f'✓ {filepath}: removidos {len(imports)} imports')
            fixed += len(imports)
    
    print(f'\nTotal de imports removidos: {fixed}')

if __name__ == '__main__':
    main()
