import os
from gui.interface import run

# Garante que o CWD esteja na pasta do projeto (.bot)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)


if __name__ == "__main__":
    run()
