import os
from dotenv import load_dotenv
from core.assistent import Assistant

# Carrega a chave da API do OpenAI do arquivo .env
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("Atenção: Chave da API da OpenAI (OPENAI_API_KEY) não encontrada. Rodando em modo offline/fallback.")
    print("Se quiser usar recursos LLM, defina OPENAI_API_KEY no seu arquivo .env (não comite esse arquivo).")
else:
    print("OpenAI API key encontrada — modo LLM habilitado.")


def main():
    """Função principal para inicializar e executar o assistente."""
    assistant = Assistant(openai_api_key=openai_api_key)
    assistant.run()
    
if __name__ == "__main__":
    main()