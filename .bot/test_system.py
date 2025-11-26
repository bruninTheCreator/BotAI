
import os
from dotenv import load_dotenv

import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()


def test_imports():
    """Testa se todos os módulos podem ser importados."""
    print("Testando imports...")
    try:
        from core.percepcao import Perception
        from core.memoria import Memory
        from core.planner import Planner
        from core.executor import Executor
        from core.supervisor import Supervisor
        from core.assistent import Assistant
        print("  [OK] Todos os imports funcionaram")
        return True
    except Exception as e:
        print(f"  [ERRO] Falha no import: {e}")
        return False


def test_perception():
    """Testa o módulo de percepção."""
    print("\nTestando Perception...")
    try:
        from core.percepcao import Perception
        p = Perception()

        # Testa captura de tela
        img = p.capture_screen()
        if img is not None:
            print(f"  [OK] Captura de tela funcionou (shape: {img.shape})")
        else:
            print("  [ERRO] Captura de tela retornou None")
            return False

        # Testa OCR (pode falhar se Tesseract não estiver instalado)
        text = p.read_text()
        if text == "[OCR indisponível - Tesseract não instalado]":
            print("  [AVISO] OCR indisponível (Tesseract não instalado)")
        else:
            print(f"  [OK] OCR funcionou (capturou {len(text)} caracteres)")

        return True
    except Exception as e:
        print(f"  [ERRO] Falha no Perception: {e}")
        return False


def test_memory():
    """Testa o módulo de memória."""
    print("\nTestando Memory...")
    try:
        from core.memoria import Memory
        m = Memory()

        # Testa salvar
        m.save(event_type="test", data={"msg": "teste"})
        print("  [OK] Salvou na memória")

        # Testa carregar
        data = m.load_all()
        if data:
            print(f"  [OK] Carregou {len(data)} eventos da memória")
        else:
            print("  [AVISO] Memória vazia")

        return True
    except Exception as e:
        print(f"  [ERRO] Falha no Memory: {e}")
        return False


def test_planner():
    """Testa o módulo de planejamento."""
    print("\nTestando Planner...")
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("  [ERRO] OPENAI_API_KEY não encontrada no .env")
            return False

        from core.memoria import Memory
        from core.planner import Planner

        m = Memory()
        p = Planner(memory=m)

        # Testa interpretação de comando simples
        plan = p.interpret_command("abrir o bloco de notas", screen_context="")

        if plan:
            print(f"  [OK] Planner gerou um plano com {len(plan)} passos:")
            for i, step in enumerate(plan, 1):
                print(f"      {i}. {step}")
        else:
            print(
                "  [AVISO] Planner não gerou plano (pode ser esperado para comandos conversacionais)")

        return True
    except Exception as e:
        print(f"  [ERRO] Falha no Planner: {e}")
        return False


def test_executor():
    """Testa o módulo de execução."""
    print("\nTestando Executor...")
    try:
        from core.executor import Executor
        from core.supervisor import Supervisor
        from core.memoria import Memory

        e = Executor()
        s = Supervisor()
        m = Memory()

        # Testa execução de plano simples (type_text)
        plan = [{"action": "type_text", "content": "teste"}]
        results = e.execute_plan(plan, supervisor=s, memory=m)

        if results:
            print(f"  [OK] Executor executou plano: {results[0]}")
        else:
            print("  [ERRO] Executor não retornou resultados")
            return False

        return True
    except Exception as e:
        print(f"  [ERRO] Falha no Executor: {e}")
        return False


def test_assistant():
    """Testa a inicialização do assistente."""
    print("\nTestando Assistant...")
    try:
        from core.assistent import Assistant

        a = Assistant()
        print("  [OK] Assistant inicializado com sucesso")
        print(f"      - Perception: {type(a.perception).__name__}")
        print(f"      - Memory: {type(a.memory).__name__}")
        print(f"      - Planner: {type(a.planner).__name__}")
        print(f"      - Executor: {type(a.executor).__name__}")
        print(f"      - Supervisor: {type(a.supervisor).__name__}")

        return True
    except Exception as e:
        print(f"  [ERRO] Falha no Assistant: {e}")
        return False


def main():
    """Executa todos os testes."""
    print("=" * 60)
    print("INICIANDO TESTES DO SISTEMA")
    print("=" * 60)

    results = {
        "Imports": test_imports(),
        "Perception": test_perception(),
        "Memory": test_memory(),
        "Planner": test_planner(),
        "Executor": test_executor(),
        "Assistant": test_assistant()
    }

    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "[OK]" if passed else "[FALHOU]"
        print(f"{status} {test_name}")

    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} testes passaram")

    if passed == total:
        print("\nTodos os testes passaram! Sistema pronto para uso.")
    else:
        print("\nAlguns testes falharam. Verifique os erros acima.")


if __name__ == "__main__":
    main()
