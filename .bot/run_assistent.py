# Este arquivo agora é apenas o ponto de entrada.
from core.assistent import Assistant


def main():
    """
    Inicializa e executa o assistente de monitoramento.
    """
    assistant = Assistant()
    assistant.run()


if __name__ == "__main__":
    main()
