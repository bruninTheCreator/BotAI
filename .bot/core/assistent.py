from .executor import Executor
from .memoria import Memory
from .planner import Planner
from .percepcao import PerceptionImpl as Perception
from .detector_repeticao import find_patterns_in_memory
from .supervisor import Supervisor
from .pattern_engine import PatternEngine
from .observation_loop import ObservationLoop
import asyncio
import threading
from .policy import Policy, PermissionLevel


class Assistant:
    def __init__(
        self,
        perception=None,
        memory=None,
        planner=None,
        executor=None,
        supervisor=None,
        openai_api_key=None,
        monitor_interval_s: int = 30,
        auto_monitor: bool = False,
        auto_execute_patterns: bool = False,
        pattern_engine=None,
        observation_loop=None,
    ):
        # Configuração da API
        self.openai_api_key = openai_api_key

        # Núcleo do sistema (com injeção opcional de dependência)
        self.perception = perception if perception is not None else Perception()
        self.memory = memory if memory is not None else Memory()
        self.planner = planner if planner is not None else Planner(
            memory=self.memory,
            openai_api_key=openai_api_key,
        )
        self.executor = executor if executor is not None else Executor()
        self.supervisor = supervisor if supervisor is not None else Supervisor()
        self.policy = Policy()

        # Pattern intelligence (mining + background observation)
        self.pattern_engine = pattern_engine if pattern_engine is not None else PatternEngine(memory=self.memory)
        self.observation_loop = observation_loop if observation_loop is not None else ObservationLoop(
            read_text_fn=self._read_text_sync,
            memory=self.memory,
            pattern_engine=self.pattern_engine,
            on_pattern_match=self._on_pattern_match,
            interval_s=monitor_interval_s,
        )
        self.auto_monitor = auto_monitor
        self.auto_execute_patterns = auto_execute_patterns
        self._monitoring = False
        self._perception_lock = threading.Lock()

        self.running = True

    def _read_text_sync(self):
        try:
            with self._perception_lock:
                res = asyncio.run(self.perception.read_text())
                if hasattr(res, "success"):
                    return res.data if res.success and res.data is not None else ""
                return res
        except Exception:
            return ""

    def run(self):
        print("Assistant iniciado. Pressione Enter para analisar a tela, digite um comando, ou 'sair' para parar.\n")
        print("Comandos: monitor on/off, patterns [n], auto on/off")
        if self.auto_monitor:
            self._start_monitoring()
            print(f"[monitor] iniciado a cada {self.observation_loop.interval_s}s")

        while self.running:
            try:
                cmd = input("\n>>> ").strip()

                # Permite comandos de controle múltiplos na mesma linha:
                # "auto on, monitor on"
                if "," in cmd:
                    sub_cmds = [c.strip() for c in cmd.split(",") if c.strip()]
                    if sub_cmds and all(
                        c.lower().startswith(("monitor", "patterns", "auto"))
                        for c in sub_cmds
                    ):
                        for sub in sub_cmds:
                            if sub.lower().startswith("monitor"):
                                self._handle_monitor_command(sub)
                            elif sub.lower().startswith("patterns"):
                                self._handle_patterns_command(sub)
                            elif sub.lower().startswith("auto"):
                                self._handle_auto_command(sub)
                        continue

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

                if cmd.lower().startswith("monitor"):
                    self._handle_monitor_command(cmd)
                    continue

                if cmd.lower().startswith("patterns"):
                    self._handle_patterns_command(cmd)
                    continue

                if cmd.lower().startswith("auto"):
                    self._handle_auto_command(cmd)
                    continue

                if cmd.lower() in ("sair", "exit", "quit", "encerrar", "fechar"):
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
        if self.observation_loop and self.observation_loop.is_running():
            self._stop_monitoring()

    def _execute_and_log(self, plan, auto: bool = False):
        plan = self._apply_policy(plan, auto=auto)
        if not plan:
            print("Plano bloqueado pela política ou vazio.")
            return
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
            step_action = None
            try:
                step_action = plan[i].get("action") if isinstance(plan[i], dict) else None
            except Exception:
                step_action = None
            self.memory.save("execution_result", {
                "step": i + 1,
                "action": step_action,
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

    def _start_monitoring(self):
        if not self.observation_loop:
            return
        started = self.observation_loop.start()
        if started:
            self._monitoring = True

    def _stop_monitoring(self):
        if not self.observation_loop:
            return
        self.observation_loop.stop()
        self._monitoring = False

    def _handle_monitor_command(self, cmd: str):
        parts = cmd.lower().split()
        if "on" in parts or "start" in parts:
            self._start_monitoring()
            print("[monitor] on")
            return
        if "off" in parts or "stop" in parts:
            self._stop_monitoring()
            print("[monitor] off")
            return
        # toggle
        if self.observation_loop and self.observation_loop.is_running():
            self._stop_monitoring()
            print("[monitor] off")
        else:
            self._start_monitoring()
            print("[monitor] on")

    def _handle_patterns_command(self, cmd: str):
        top = 10
        parts = cmd.lower().split()
        for p in parts:
            if p.isdigit():
                top = int(p)
                break
        patterns = self.pattern_engine.list_patterns(top=top)
        if not patterns:
            print("Nenhum padrao ainda.")
            return
        print(f"Padroes (top {len(patterns)}):")
        for i, p in enumerate(patterns, 1):
            label = p.get("label", "pattern")
            count = p.get("count", 0)
            conf = p.get("confidence", 0)
            print(f"  {i}. {label} | count={count} | conf={conf}")

    def _handle_auto_command(self, cmd: str):
        parts = cmd.lower().split()
        if "on" in parts or "start" in parts:
            self.auto_execute_patterns = True
            print("[auto] on")
            return
        if "off" in parts or "stop" in parts:
            self.auto_execute_patterns = False
            print("[auto] off")
            return
        status = "on" if self.auto_execute_patterns else "off"
        print(f"[auto] {status}")

    def _on_pattern_match(self, pattern: dict, score: float):
        label = pattern.get("label", "pattern")
        print(f"[pattern] match: {label} | score={score:.2f}")

        if not self.auto_execute_patterns:
            return
        if pattern.get("mode") != "auto":
            return
        action = pattern.get("action")
        if not action:
            return

        # action can be a single step dict or a list of steps
        plan = action if isinstance(action, list) else [action]
        try:
            self._execute_and_log(plan, auto=True)
        except Exception:
            pass

    def _apply_policy(self, plan, auto: bool = False):
        if not plan:
            return []
        filtered = []
        for step in plan:
            if not isinstance(step, dict):
                continue
            action = step.get("action")
            if not action:
                continue
            perm = PermissionLevel.SYSTEM_CONTROL
            if action in ("browse", "browse_url", "research_web"):
                perm = PermissionLevel.NETWORK
            allowed, reason = self.policy.validate_action(
                action,
                permission_level=perm
            )
            if not allowed:
                print(f"[policy] bloqueado: {action} ({reason})")
                continue
            if reason and "requires user confirmation" in reason:
                if auto:
                    print(f"[policy] confirmação requerida, pulando: {action}")
                    continue
                confirm = input(f"Ação '{action}' requer confirmação. Executar? (s/n): ").lower()
                if confirm != "s":
                    continue
            filtered.append(step)
        return filtered
