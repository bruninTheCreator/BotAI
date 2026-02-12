import asyncio
import os
from core.percepcao import PerceptionImpl
from core.planner import Planner
from core.executor import Executor
from core.memoria import Memory
from core.supervisor import Supervisor
from core.assistent import Assistant

# Garante que o CWD esteja na pasta do projeto (.bot)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)


def setup_and_run():
    """Cria componentes via 'manual DI' e executa o Assistant."""
    perception = PerceptionImpl()
    memory = Memory()
    planner = Planner(memory=memory)
    executor = Executor()
    supervisor = Supervisor()

    assistant = Assistant(
        perception=perception,
        memory=memory,
        planner=planner,
        executor=executor,
        supervisor=supervisor,
        auto_monitor=False,
    )

    # Run assistant in current thread (interactive)
    assistant.run()


if __name__ == '__main__':
    setup_and_run()

    
