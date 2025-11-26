#!/usr/bin/env python3
"""
Script para corrigir todos os problemas de lint encontrados pelo flake8.
"""
import os
import re
from pathlib import Path

def fix_imports_needed(filepath):
    """Retorna quais imports são necessários baseado no conteúdo do arquivo."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    needs = {
        'datetime': 'from datetime import datetime' in open(filepath).read() or \
                   ('datetime.now()' in content or 'datetime(' in content),
        'Path': 'Path(' in content or 'Path)' in content,
        'List': 'List[' in content,
        'Any': 'Any' in content and 'class' in content,
    }
    return needs

def fix_file(filepath):
    """Corrige todos os problemas de lint em um arquivo."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # 1. Remover espaços em branco de linhas em branco (W293)
    lines = content.split('\n')
    fixed_lines = []
    for line in lines:
        if line.strip() == '':
            fixed_lines.append('')
        else:
            fixed_lines.append(line.rstrip())
    content = '\n'.join(fixed_lines)
    
    # 2. Adicionar newline no final do arquivo se não tiver (W292)
    if content and not content.endswith('\n'):
        content += '\n'
    
    # 3. Corrigir comparações com True (E712)
    content = re.sub(r'if (\w+) == True:', r'if \1:', content)
    content = re.sub(r'if (\w+) is True:', r'if \1:', content)
    
    # 4. Restaurar imports necessários que usam datetime, Path, etc
    needs = fix_imports_needed(filepath)
    if needs['datetime'] and 'from datetime import datetime' not in content:
        # Adicionar após outras importações
        if 'import ' in content[:500]:
            content = content.replace(
                'import os',
                'import os\nfrom datetime import datetime',
                1
            )
    
    # Salvar arquivo se houve mudanças
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Processa todos os arquivos .py em core/ e tests/."""
    dirs_to_process = ['core', 'tests']
    fixed_count = 0
    
    for dir_name in dirs_to_process:
        if not os.path.exists(dir_name):
            continue
        
        for filepath in Path(dir_name).rglob('*.py'):
            if fix_file(str(filepath)):
                print(f'✓ Corrigido: {filepath}')
                fixed_count += 1
            else:
                print(f'  Sem mudanças: {filepath}')
    
    print(f'\nTotal de arquivos corrigidos: {fixed_count}')

if __name__ == '__main__':
    main()
