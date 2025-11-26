from .executor import Executor
from .memoria import Memory
from .planner import Planner
from .percepcao import PerceptionImpl as Perception
from .detector_repeticao import find_patterns_in_memory
from .supervisor import Supervisor
import asyncio


class Assistant:
    def __init__(
        self,
        perception=None,
        memory=None,
        planner=None,
        executor=None,
        supervisor=None,
        openai_api_key=None
    ):
        # Configuração da API
        self.openai_api_key = openai_api_key

        # Núcleo do sistema (com injeção opcional de dependência)
        self.perception = perception if perception is not None else Perception()
        self.memory = memory if memory is not None else Memory()
        self.planner = planner if planner is not None else Planner(memory=self.memory)
        self.executor = executor if executor is not None else Executor()
        self.supervisor = supervisor if supervisor is not None else Supervisor()

        self.running = True

    def _read_text_sync(self):
        try:
            res = asyncio.run(self.perception.read_text())
            if hasattr(res, "success"):
                return res.data if res.success and res.data is not None else ""
            return res
        except Exception:
            return ""

    def run(self):
        print("Assistant iniciado. Pressione Enter para analisar a tela, digite um comando, ou 'sair' para parar.\n")

        while self.running:
            try:
                cmd = input("\n>>> ").strip()

                if not cmd:
                    print("Analisando a tela...")
                    screen_text = self._read_text_sync()
                    patterns = self._detect_patterns(screen_text)

                    if patterns:
                        print(f"Padrões detectados: {patterns}")
                        plan = self._suggest_action_for_patterns(patterns)

                        if plan:
                            print("Plano sugerido pelo Planner:")
                            for i, step in enumerate(plan, 1):
                                print(f"   {i}. {step}")

                            if input("Deseja executar o plano? (s/n): ").lower() == 's':
                                self._execute_and_log(plan)
                    else:
                        print("Nenhum padrão conhecido foi detectado.")
                    continue

                if cmd.lower() in ("sair", "exit", "quit"):
                    print("Assistente encerrado.")
                    break

                self.memory.save("user_command", {"command": cmd})

                print("Capturando contexto da tela...")
                screen_context = self._read_text_sync()

                print(f"Interpretando comando: {cmd}")
                plan = self.planner.interpret_command(cmd, screen_context=screen_context)

                if not plan:
                    print("Planner não conseguiu gerar plano.")
                    continue

                print("Plano sugerido:")
                for i, step in enumerate(plan, 1):
                    print(f"   {i}. {step}")

                if input("Executar plano? (s/n): ").lower() != 's':
                    print("Plano cancelado.")
                    continue

                self._execute_and_log(plan)

            except Exception as e:
                print(f"Erro inesperado: {e}")
                if hasattr(self, "supervisor"):
                    self.supervisor.log("error", {"message": str(e)})

    def _execute_and_log(self, plan):
        try:
            if hasattr(self.executor, 'execute_plan_sync'):
                results = self.executor.execute_plan_sync(plan, supervisor=self.supervisor, memory=self.memory)
            else:
                res = asyncio.run(self.executor.execute_plan(plan, supervisor=self.supervisor, memory=self.memory))
                results = res.data if getattr(res, 'success', False) else []
        except Exception as e:
            results = [f"Erro ao executar plano: {e}"]

        print("Resultados:")
        for res in results:
            print(f" - {res}")

        for i, res in enumerate(results):
            self.memory.save("execution_result", {
                "step": i + 1,
                "action": plan[i].get("action"),
                "result": res
            })

        print("Plano concluído.\n" + "-" * 30)

    def _detect_patterns(self, screen_text):
        patterns = []
        text_lower = screen_text.lower()

        if "erro" in text_lower or "error" in text_lower:
            patterns.append("erro_detectado")

        try:
            mem_patterns = find_patterns_in_memory(self.memory, 3, 2, 2)
            if mem_patterns.get("frequent_events"):
                patterns.append("padrao_memoria_detectado")
        except:
            pass

        return patterns

    def _suggest_action_for_patterns(self, patterns):
        if "erro_detectado" in patterns:
            return [
                {"action": "open_app", "target": "logs"},
                {"action": "type_text", "content": "verificar erro"}
            ]
        return None