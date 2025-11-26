import os
import time
import webbrowser
import logging
import asyncio

try:
    import pyautogui
except Exception:
    pyautogui = None

from .base import Executor as ExecutorABC, Result, ActionStep, ActionType, Plan

logger = logging.getLogger("core.executor")


class Executor(ExecutorABC):
    def __init__(self):
        super().__init__(name="Executor")
        self.initialized = False

    def _open_app(self, target: str) -> str:
        """Abre um aplicativo."""
        try:
            app_map = {
                "bloco de notas": "notepad.exe",
                "notepad": "notepad.exe",
                "calculadora": "calc.exe",
                "calculator": "calc.exe",
                "calc": "calc.exe",
                "chrome": "chrome.exe",
                "edge": "msedge.exe",
                "msedge": "msedge.exe",
                "explorer": "explorer.exe",
                "excel": "excel.exe",
                "outlook": "outlook.exe",
                "word": "winword.exe",
                "logs": "notepad.exe"
            }
            app_executable = app_map.get(target.lower(), target)
            os.system(f'start {app_executable}')
            time.sleep(2)  # Aguarda o app abrir
            return f"Aplicativo {target} aberto com sucesso."
        except Exception as e:
            return f"Erro ao abrir o aplicativo {target}: {e}"

    def _type_text(self, content: str) -> str:
        """Digita um texto usando o teclado."""
        try:
            # Usa write() para suportar caracteres especiais e acentos
            pyautogui.write(content, interval=0.05)
            return f"Texto digitado com sucesso ({len(content)} caracteres)."
        except Exception as e:
            return f"Erro ao digitar texto: {e}"

    def _hotkey(self, keys: list) -> str:
        """Pressiona uma combinação de teclas de atalho."""
        try:
            # Normaliza as teclas para minúsculas
            normalized_keys = [k.lower().strip() for k in keys]
            pyautogui.hotkey(*normalized_keys)
            return f"Atalho {'+'.join(normalized_keys)} pressionado."
        except Exception as e:
            return f"Erro ao pressionar atalho: {e}"

    def _click(self, x: int, y: int, button: str = 'left') -> str:
        """Clica em uma coordenada específica da tela."""
        try:
            pyautogui.click(x, y, button=button)
            return f"Clique realizado em ({x}, {y})."
        except Exception as e:
            return f"Erro ao clicar: {e}"

    def _browse(self, url: str) -> str:
        """Abre o navegador padrão para uma URL."""
        if not url:
            return "Erro ao executar 'browse': URL não fornecida."

        try:
            # Garante que a URL tenha protocolo
            if not url.startswith(
                    "http://") and not url.startswith("https://"):
                # Se for um nome de site conhecido, adiciona https://www.
                if "." not in url:
                    url = f"https://www.{url}.com"
                else:
                    url = f"https://{url}"

            webbrowser.open(url)
            return f"Navegando para: {url}"
        except Exception as e:
            return f"Erro ao abrir navegador: {e}"

    async def execute(self, action: ActionStep) -> Result[str]:
        try:
            # Handle known action types
            if action.action_type == ActionType.OPEN_APP:
                target = action.parameters.get("target")
                if not target:
                    return Result.from_error("'target' não especificado para OPEN_APP")
                return Result.ok(self._open_app(target))

            if action.action_type == ActionType.TYPE_TEXT:
                content = action.parameters.get("content")
                if not content:
                    return Result.from_error("'content' não especificado para TYPE_TEXT")
                return Result.ok(self._type_text(content))

            if action.action_type == ActionType.HOTKEY:
                keys = action.parameters.get("keys")
                if not keys:
                    return Result.from_error("'keys' não especificado para HOTKEY")
                if isinstance(keys, str):
                    keys = keys.split("+")
                return Result.ok(self._hotkey(keys))

            if action.action_type == ActionType.CLICK:
                x = action.parameters.get("x")
                y = action.parameters.get("y")
                if x is None or y is None:
                    return Result.from_error("Coordenadas x/y não fornecidas para CLICK")
                return Result.ok(self._click(int(x), int(y)))

            if action.action_type == ActionType.BROWSE:
                url = action.parameters.get("url")
                if not url:
                    return Result.from_error("'url' não especificada para BROWSE")
                return Result.ok(self._browse(url))

            return Result.from_error(f"Ação {action.action_type} não é suportada")
        except Exception as e:
            logger.exception("Erro ao executar ação")
            return Result.from_error(str(e))

    async def execute_plan_async(self, plan, supervisor=None, memory=None) -> Result[list]:
        """Executa um plano (async). Aceita um `Plan` ou lista de dicionários.
        Retorna `Result` com lista de resultados.
        """
        try:
            # Normalize plan to list of ActionStep
            action_steps = []
            if isinstance(plan, Plan):
                action_steps = plan.steps
            elif isinstance(plan, list):
                for step in plan:
                    if isinstance(step, ActionStep):
                        action_steps.append(step)
                    elif isinstance(step, dict):
                        # Map legacy dict to ActionStep (best-effort)
                        atype = step.get("action")
                        params = {k: v for k, v in step.items() if k != "action"}
                        # Try to map string action names to ActionType
                        try:
                            a_type_enum = ActionType[atype.upper()]
                        except Exception:
                            # fallback to WAIT for unknown
                            a_type_enum = ActionType.WAIT
                        action_steps.append(ActionStep(action_type=a_type_enum, parameters=params))
            else:
                return Result.from_error("Plano em formato inválido")

            results = []
            for i, a in enumerate(action_steps, 1):
                # execute each action (run in thread if blocking)
                if asyncio.get_event_loop().is_running():
                    # run sync helper in thread to avoid blocking
                    res = await asyncio.to_thread(lambda: self._execute_sync_action(a))
                else:
                    res_obj = await self.execute(a)
                    res = res_obj.data if res_obj.success else res_obj.error

                results.append(res)

                # save to memory if available
                try:
                    if memory and hasattr(memory, "save"):
                        memory.save(event_type="execution_result", data={
                            "step": i,
                            "action": getattr(a.action_type, 'name', str(a.action_type)),
                            "result": res
                        })
                except Exception:
                    pass

            return Result.ok(results)
        except Exception as e:
            logger.exception("Erro ao executar plano")
            return Result.from_error(str(e))

    def _execute_sync_action(self, action: ActionStep) -> str:
        """Helper sync used when running inside an existing event loop."""
        # Map to existing helpers similarly to execute()
        try:
            if action.action_type == ActionType.OPEN_APP:
                return self._open_app(action.parameters.get("target"))
            if action.action_type == ActionType.TYPE_TEXT:
                return self._type_text(action.parameters.get("content"))
            if action.action_type == ActionType.HOTKEY:
                keys = action.parameters.get("keys")
                if isinstance(keys, str):
                    keys = keys.split("+")
                return self._hotkey(keys)
            if action.action_type == ActionType.CLICK:
                return self._click(int(action.parameters.get("x")), int(action.parameters.get("y")))
            if action.action_type == ActionType.BROWSE:
                return self._browse(action.parameters.get("url"))
            return f"Ação {action.action_type} não é suportada"
        except Exception as e:
            return f"Erro ao executar ação: {e}"

    # Backwards-compatible synchronous wrapper
    def execute_plan_sync(self, plan: list, supervisor=None, memory=None):
        res = asyncio.run(self.execute_plan_async(plan, supervisor=supervisor, memory=memory))
        return res.data if res.success else [res.error]

    def execute_plan(self, plan: list, supervisor=None, memory=None):
        """Legacy-compatible synchronous entrypoint (keeps tests and older code working)."""
        return self.execute_plan_sync(plan, supervisor=supervisor, memory=memory)

    async def initialize(self) -> Result[None]:
        self.initialized = True
        return Result.ok(None)

    async def shutdown(self) -> Result[None]:
        self.initialized = False
        return Result.ok(None)
