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
from .web_research import run_research

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
                "logs": "notepad.exe",
            }
            app_executable = app_map.get((target or "").lower(), target)
            os.system(f"start {app_executable}")
            time.sleep(2)
            return f"Aplicativo {target} aberto com sucesso."
        except Exception as e:
            return f"Erro ao abrir o aplicativo {target}: {e}"

    def _type_text(self, content: str) -> str:
        """Digita um texto usando o teclado."""
        try:
            if pyautogui is None:
                return "Erro ao digitar texto: pyautogui indisponivel."
            pyautogui.write(content, interval=0.03)
            return f"Texto digitado com sucesso ({len(content)} caracteres)."
        except Exception as e:
            return f"Erro ao digitar texto: {e}"

    def _hotkey(self, keys: list) -> str:
        """Pressiona uma combinacao de teclas de atalho."""
        try:
            if pyautogui is None:
                return "Erro ao pressionar atalho: pyautogui indisponivel."
            normalized_keys = [k.lower().strip() for k in keys]
            pyautogui.hotkey(*normalized_keys)
            return f"Atalho {'+'.join(normalized_keys)} pressionado."
        except Exception as e:
            return f"Erro ao pressionar atalho: {e}"

    def _click(self, x: int, y: int, button: str = "left") -> str:
        """Clica em uma coordenada especifica da tela."""
        try:
            if pyautogui is None:
                return "Erro ao clicar: pyautogui indisponivel."
            pyautogui.click(x, y, button=button)
            return f"Clique realizado em ({x}, {y})."
        except Exception as e:
            return f"Erro ao clicar: {e}"

    def _browse(self, url: str) -> str:
        """Abre o navegador padrao para uma URL."""
        if not url:
            return "Erro ao executar 'browse': URL nao fornecida."

        try:
            if not url.startswith("http://") and not url.startswith("https://"):
                if "." not in url:
                    url = f"https://www.{url}.com"
                else:
                    url = f"https://{url}"

            webbrowser.open(url)
            return f"Navegando para: {url}"
        except Exception as e:
            return f"Erro ao abrir navegador: {e}"

    def _wait(self, seconds: float = 1.0) -> str:
        """Espera por um tempo."""
        try:
            secs = float(seconds)
        except Exception:
            secs = 1.0
        time.sleep(max(0.0, secs))
        return f"Aguardou {secs:.1f}s."

    def _research_web(
        self,
        query: str,
        max_results: int = 10,
        top_k: int = 5,
        site_hint: str | None = None,
        write_notepad: bool = False,
        open_tabs: bool = False,
    ) -> str:
        """Executa pesquisa web estruturada e opcionalmente escreve no Notepad."""
        query = (query or "").strip()
        if not query:
            return "Erro ao executar 'research_web': query nao fornecida."

        try:
            result = run_research(
                query=query,
                max_results=max(3, int(max_results)),
                top_k=max(1, int(top_k)),
                site_hint=site_hint,
            )
        except Exception as e:
            return f"Erro ao pesquisar na web: {e}"

        items = result.get("items") or []
        report_text = result.get("report_text") or f"Pesquisa concluida para: {query}"

        if open_tabs and items:
            for item in items:
                url = item.get("url")
                if not url:
                    continue
                try:
                    webbrowser.open_new_tab(url)
                    time.sleep(0.2)
                except Exception:
                    pass

        if write_notepad:
            self._open_app("notepad")
            time.sleep(0.4)
            self._type_text(report_text[:12000])

        return f"Pesquisa concluida: {len(items)} fontes ranqueadas."

    async def execute(self, action: ActionStep) -> Result[str]:
        try:
            if action.action_type == ActionType.OPEN_APP:
                target = action.parameters.get("target")
                if not target:
                    return Result.from_error("'target' nao especificado para OPEN_APP")
                return Result.ok(self._open_app(target))

            if action.action_type == ActionType.TYPE_TEXT:
                content = action.parameters.get("content")
                if not content:
                    return Result.from_error("'content' nao especificado para TYPE_TEXT")
                return Result.ok(self._type_text(content))

            if action.action_type == ActionType.HOTKEY:
                keys = action.parameters.get("keys")
                if not keys:
                    return Result.from_error("'keys' nao especificado para HOTKEY")
                if isinstance(keys, str):
                    keys = keys.split("+")
                return Result.ok(self._hotkey(keys))

            if action.action_type == ActionType.CLICK:
                x = action.parameters.get("x")
                y = action.parameters.get("y")
                if x is None or y is None:
                    return Result.from_error("Coordenadas x/y nao fornecidas para CLICK")
                return Result.ok(self._click(int(x), int(y)))

            if action.action_type == ActionType.BROWSE:
                url = action.parameters.get("url")
                if not url:
                    return Result.from_error("'url' nao especificada para BROWSE")
                return Result.ok(self._browse(url))

            if action.action_type == ActionType.WAIT:
                seconds = action.parameters.get("seconds", 1)
                return Result.ok(self._wait(seconds))

            if action.action_type == ActionType.RESEARCH_WEB:
                query = action.parameters.get("query")
                if not query:
                    return Result.from_error("'query' nao especificada para RESEARCH_WEB")
                return Result.ok(
                    self._research_web(
                        query=query,
                        max_results=action.parameters.get("max_results", 10),
                        top_k=action.parameters.get("top_k", 5),
                        site_hint=action.parameters.get("site_hint"),
                        write_notepad=bool(action.parameters.get("write_notepad", False)),
                        open_tabs=bool(action.parameters.get("open_tabs", False)),
                    )
                )

            return Result.from_error(f"Acao {action.action_type} nao e suportada")
        except Exception as e:
            logger.exception("Erro ao executar acao")
            return Result.from_error(str(e))

    async def execute_plan_async(self, plan, supervisor=None, memory=None) -> Result[list]:
        """Executa um plano (async). Aceita Plan ou lista de dicts."""
        try:
            action_steps = []
            if isinstance(plan, Plan):
                action_steps = plan.steps
            elif isinstance(plan, list):
                for step in plan:
                    if isinstance(step, ActionStep):
                        action_steps.append(step)
                    elif isinstance(step, dict):
                        atype = step.get("action")
                        params = {k: v for k, v in step.items() if k != "action"}
                        try:
                            a_type_enum = ActionType[str(atype).upper()]
                        except Exception:
                            a_type_enum = ActionType.WAIT
                        action_steps.append(ActionStep(action_type=a_type_enum, parameters=params))
            else:
                return Result.from_error("Plano em formato invalido")

            results = []
            for i, action_step in enumerate(action_steps, 1):
                if asyncio.get_event_loop().is_running():
                    res = await asyncio.to_thread(lambda: self._execute_sync_action(action_step))
                else:
                    res_obj = await self.execute(action_step)
                    res = res_obj.data if res_obj.success else res_obj.error

                results.append(res)

                try:
                    if memory and hasattr(memory, "save"):
                        memory.save(
                            event_type="execution_result",
                            data={
                                "step": i,
                                "action": getattr(action_step.action_type, "name", str(action_step.action_type)),
                                "result": res,
                            },
                        )
                except Exception:
                    pass

            return Result.ok(results)
        except Exception as e:
            logger.exception("Erro ao executar plano")
            return Result.from_error(str(e))

    def _execute_sync_action(self, action: ActionStep) -> str:
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
            if action.action_type == ActionType.WAIT:
                return self._wait(action.parameters.get("seconds", 1))
            if action.action_type == ActionType.RESEARCH_WEB:
                return self._research_web(
                    query=action.parameters.get("query"),
                    max_results=action.parameters.get("max_results", 10),
                    top_k=action.parameters.get("top_k", 5),
                    site_hint=action.parameters.get("site_hint"),
                    write_notepad=bool(action.parameters.get("write_notepad", False)),
                    open_tabs=bool(action.parameters.get("open_tabs", False)),
                )
            return f"Acao {action.action_type} nao e suportada"
        except Exception as e:
            return f"Erro ao executar acao: {e}"

    def execute_plan_sync(self, plan: list, supervisor=None, memory=None):
        res = asyncio.run(self.execute_plan_async(plan, supervisor=supervisor, memory=memory))
        return res.data if res.success else [res.error]

    def execute_plan(self, plan: list, supervisor=None, memory=None):
        return self.execute_plan_sync(plan, supervisor=supervisor, memory=memory)

    async def initialize(self) -> Result[None]:
        self.initialized = True
        return Result.ok(None)

    async def shutdown(self) -> Result[None]:
        self.initialized = False
        return Result.ok(None)
