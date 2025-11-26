import time


class Assistent:
    def __init__(self):
        print("Assistant iniciado. Pressione Ctrl+C para parar.")

    def run(self):
        """
        Loop principal do assistente.
        """
        try:
            while True:
                print("Verificando a tela...")

                # Exemplo de uso da função importada:
                # text = get_text_from_screen()
                # if text:
                #     print("Texto detectado:", text.strip())

                # Adicione sua lógica de automação aqui

                time.sleep(5)
        except KeyboardInterrupt:
            print("\nAssistente parado pelo usuário.")
