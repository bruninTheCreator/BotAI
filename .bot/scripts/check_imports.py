import sys
import traceback

# Adiciona a raiz do projeto ao path
ROOT = r"c:\Users\A21057836\OneDrive - GRUPO EQUATORIAL ENERGIA\\Área de Trabalho\BotAI\.bot"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

print('SYS.PATH[0]=', sys.path[0])

try:
    import tests.test_architecture as t
    print('IMPORT_OK')
except Exception:
    traceback.print_exc()
    print('IMPORT_FAILED')
