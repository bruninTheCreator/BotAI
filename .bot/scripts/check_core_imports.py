import sys
import traceback

ROOT = r"c:\Users\A21057836\OneDrive - GRUPO EQUATORIAL ENERGIA\\Área de Trabalho\BotAI\.bot"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

modules = [
    'core.base',
    'core.config',
    'core.logging_module',
    'core.di_container',
    'core.state_machine',
    'core.event_emitter',
    'core.percepcao',
    'core.planner_simple',
    'core.executor',
    'core.memoria',
    'core.detector_repeticao',
    'core.supervisor',
    'core.assistent',
]

for m in modules:
    try:
        __import__(m)
        print(f'OK: {m}')
    except Exception:
        print(f'ERROR importing {m}')
        traceback.print_exc()
        print('---')
