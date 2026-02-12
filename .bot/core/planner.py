from abc import ABC
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from .llm_client import LLMClient


class Planner(ABC):
    _APP_ALIASES = {
        "bloco de notas": "notepad",
        "notepad": "notepad",
        "calculadora": "calc",
        "calculator": "calc",
        "calc": "calc",
        "chrome": "chrome",
        "chorme": "chrome",
        "google chrome": "chrome",
        "edge": "edge",
        "msedge": "edge",
        "explorer": "explorer",
        "explorador de arquivos": "explorer",
        "explorador": "explorer",
        "excel": "excel",
        "outlook": "outlook",
        "word": "word",
    }

    _HOTKEY_ALIASES = {
        "control": "ctrl",
        "ctrl": "ctrl",
        "shift": "shift",
        "alt": "alt",
        "win": "win",
        "windows": "win",
        "enter": "enter",
        "return": "enter",
        "esc": "esc",
        "escape": "esc",
        "del": "delete",
        "delete": "delete",
        "tab": "tab",
        "space": "space",
        "barra": "space",
    }

    _SITE_URLS = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "github": "https://github.com",
        "wikipedia": "https://pt.wikipedia.org",
        "reddit": "https://www.reddit.com",
        "x": "https://x.com",
        "chatgpt": "https://chat.openai.com",
        "gmail": "https://mail.google.com",
    }

    _SITE_ALIASES = {
        "yt": "youtube",
        "youtube": "youtube",
        "google": "google",
        "github": "github",
        "wikipedia": "wikipedia",
        "wiki": "wikipedia",
        "reddit": "reddit",
        "twitter": "x",
        "x": "x",
        "chatgpt": "chatgpt",
        "gmail": "gmail",
    }

    _SITE_SEARCH_URLS = {
        "youtube": "https://www.youtube.com/results?search_query={q}",
        "wikipedia": "https://pt.wikipedia.org/wiki/Especial:Pesquisar?search={q}",
        "github": "https://github.com/search?q={q}",
        "reddit": "https://www.reddit.com/search/?q={q}",
    }

    _DOMAIN_TO_SITE = {
        "youtube.com": "youtube",
        "google.com": "google",
        "github.com": "github",
        "wikipedia.org": "wikipedia",
        "reddit.com": "reddit",
        "x.com": "x",
        "twitter.com": "x",
        "chat.openai.com": "chatgpt",
        "mail.google.com": "gmail",
    }

    def __init__(
        self,
        memory=None,
        openai_api_key: Optional[str] = None,
        llm_client: Optional[LLMClient] = None,
        use_llm: bool = True,
    ):
        self.memory = memory
        self.use_llm = use_llm
        if llm_client is not None:
            self.llm_client = llm_client
        elif use_llm:
            self.llm_client = LLMClient(api_key=openai_api_key)
        else:
            self.llm_client = None

    def initialize(self):
        return True

    def shutdown(self):
        return True

    def interpret_command(self, command, screen_context=None):
        command = (command or "").strip()
        if not command:
            return []

        screen_context = screen_context or ""

        if self.use_llm and self.llm_client and self.llm_client.is_available():
            llm_plan = self.llm_client.generate_plan(command, context=screen_context)
            llm_plan = self._validate_plan(llm_plan)
            if llm_plan:
                return llm_plan

        plan = self._build_rule_based_plan(command, screen_context=screen_context)
        return self._validate_plan(plan)

    def _build_rule_based_plan(self, command: str, screen_context: str = "") -> List[Dict[str, Any]]:
        command_lower = self._normalize_spaces(command.lower())
        plan: List[Dict[str, Any]] = []

        open_target = self._extract_open_target(command_lower)
        if open_target:
            plan.append({"action": "open_app", "target": open_target})

        direct_site_url = self._extract_direct_site_browse(command_lower)
        if direct_site_url:
            plan.append({"action": "browse", "url": direct_site_url})

        search_query = self._extract_search_query(command_lower)
        if search_query:
            site_hint = self._extract_search_site_hint(command_lower, direct_site_url=direct_site_url)
            if self._should_use_research_mode(command_lower):
                plan.append(
                    {
                        "action": "research_web",
                        "query": search_query,
                        "max_results": 10,
                        "top_k": 5,
                        "site_hint": site_hint,
                        "write_notepad": self._wants_notes_output(command_lower),
                        "open_tabs": False,
                    }
                )
            else:
                search_flow = self._build_sequential_search_steps(
                    command_lower,
                    first_query=search_query,
                    first_site_hint=site_hint,
                )
                if search_flow:
                    plan.extend(search_flow)
                else:
                    plan.append(self._build_search_step(search_query, site_hint=site_hint))

                if self._wants_notes_output(command_lower):
                    plan.append({"action": "open_app", "target": "notepad"})
                    plan.append({
                        "action": "type_text",
                        "content": f"Pesquisa iniciada: {search_query}\\nResumo das fontes principais:\\n- ",
                    })

        hotkey_keys = self._extract_hotkey_keys(command_lower)
        if hotkey_keys:
            plan.append({"action": "hotkey", "keys": hotkey_keys})

        click_step = self._extract_click_step(command_lower)
        if click_step:
            plan.append(click_step)

        wait_seconds = self._extract_wait_seconds(command_lower)
        if wait_seconds is not None:
            plan.append({"action": "wait", "seconds": wait_seconds})

        typed_content = self._extract_text_to_type(command)
        if typed_content:
            plan.append({"action": "type_text", "content": typed_content})
        elif "dialogo" in command_lower:
            plan.append({
                "action": "type_text",
                "content": "Iniciando dialogo entre humano e maquina...",
            })

        if not plan:
            plan.extend(self._context_recovery(command_lower, screen_context))

        return self._dedupe_browse_steps(plan)

    def _normalize_spaces(self, text: str) -> str:
        return " ".join((text or "").split())

    def _trim_punctuation(self, text: str) -> str:
        return (text or "").strip(" .,!?:;")

    def _cut_at_follow_up(self, text: str) -> str:
        if not text:
            return ""
        parts = re.split(
            r"(?:,|\bdepois\b|\bem seguida\b|\bthen\b|\be depois\b|\be dentro de\b|\bdentro de\b|\be pesquise\b|\be pesquisar\b|\be procure\b|\be procurar\b|\be buscar\b|\be acesse\b|\be acessar\b|\be entre\b|\be entrar\b|\be abra\b|\be abrir\b)",
            text,
            maxsplit=1,
            flags=re.IGNORECASE,
        )
        return self._trim_punctuation(parts[0] if parts else text)

    def _resolve_site_keyword(self, raw: str) -> Optional[str]:
        token = self._trim_punctuation(raw.lower())
        if not token:
            return None

        if token in self._SITE_ALIASES:
            return self._SITE_ALIASES[token]

        # Domain form
        token = token.replace("https://", "").replace("http://", "").replace("www.", "")
        token = token.split("/")[0]
        for domain, site in self._DOMAIN_TO_SITE.items():
            if token == domain or token.endswith("." + domain):
                return site
        return None

    def _ensure_url(self, raw: str) -> Optional[str]:
        raw = self._trim_punctuation(raw)
        if not raw:
            return None

        if raw.startswith("http://") or raw.startswith("https://"):
            return raw

        # known site keyword
        site = self._resolve_site_keyword(raw)
        if site and site in self._SITE_URLS:
            return self._SITE_URLS[site]

        # likely domain
        if "." in raw:
            return f"https://{raw}"

        return None

    def _extract_open_target(self, command_lower: str) -> Optional[str]:
        match = re.search(
            r"(?:abrir|abra|iniciar|inicie|open|launch|entrar|entre|ir|vai|v[aá])\s+(?:at[eé]\s+)?(?:no|na|em|o|a)?\s*(.+)",
            command_lower,
        )
        if not match:
            return None

        raw = self._cut_at_follow_up(match.group(1))
        raw = re.sub(r"^(?:o|a|os|as|um|uma|site)\s+", "", raw).strip()
        if not raw:
            return None

        # if command references a site, this should be browse instead of open_app
        if self._ensure_url(raw):
            return None

        if raw in self._APP_ALIASES:
            return self._APP_ALIASES[raw]

        for alias, target in self._APP_ALIASES.items():
            if raw.startswith(alias):
                return target

        return raw

    def _extract_direct_site_browse(self, command_lower: str) -> Optional[str]:
        match = re.search(
            r"(?:entre|entrar|acesse|acessar|ir para|vai para|go to|abra|abrir|v[aá] para)\s+(?:no|na|em|site|o site)?\s*([a-z0-9][a-z0-9\.\-\/:]*)",
            command_lower,
        )
        if not match:
            return None

        candidate = self._cut_at_follow_up(match.group(1))
        candidate = re.sub(r"^(?:o|a)\s+", "", candidate).strip()
        if not candidate:
            return None

        # ignore browser app names as direct site targets
        if candidate in {"chrome", "chorme", "edge", "msedge", "navegador"}:
            return None

        return self._ensure_url(candidate)

    def _extract_search_query(self, command_lower: str) -> Optional[str]:
        match = re.search(
            r"(?:pesquise|pesquisar|procurar|buscar|search(?:\s+for)?|google)\s+(.+)",
            command_lower,
        )
        if not match:
            return None

        query = self._cut_at_follow_up(match.group(1))
        query = self._normalize_search_phrase(query)
        query = re.sub(r"\b(?:no|na)\s+(?:chrome|chorme|edge|navegador)\b$", "", query).strip()
        return query or None

    def _normalize_search_phrase(self, text: str) -> str:
        query = self._trim_punctuation(text)
        query = re.sub(r"^(?:por|sobre|a respeito de|acerca de)\s+", "", query).strip()
        query = re.sub(r"^(?:a\s+m(?:u|ú)sica|o\s+v(?:i|í)deo|o\s+clipe)\s+", "", query).strip()
        return query

    def _extract_search_site_hint(self, command_lower: str, direct_site_url: Optional[str] = None) -> Optional[str]:
        if direct_site_url:
            hinted = self._resolve_site_keyword(direct_site_url)
            if hinted:
                return hinted

        hinted_match = re.search(r"\b(?:no|na|em|site)\s+([a-z0-9\.\-]+)\b", command_lower)
        if hinted_match:
            return self._resolve_site_keyword(hinted_match.group(1))
        return None

    def _build_search_step(self, query: str, site_hint: Optional[str] = None) -> Dict[str, Any]:
        query = self._normalize_search_phrase(query)
        if not query:
            return {"action": "browse", "url": "https://www.google.com"}

        query_as_url = self._ensure_url(query)
        if query_as_url and " " not in query:
            return {"action": "browse", "url": query_as_url}

        if site_hint in self._SITE_SEARCH_URLS:
            return {
                "action": "browse",
                "url": self._SITE_SEARCH_URLS[site_hint].format(q=quote_plus(query)),
            }

        # single-keyword that maps directly to a known site
        if " " not in query:
            site = self._resolve_site_keyword(query)
            if site and site in self._SITE_URLS:
                return {"action": "browse", "url": self._SITE_URLS[site]}

        return {"action": "browse", "url": f"https://www.google.com/search?q={quote_plus(query)}"}

    def _build_sequential_search_steps(
        self,
        command_lower: str,
        first_query: str,
        first_site_hint: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        steps: List[Dict[str, Any]] = []
        current_site = first_site_hint

        first_query = self._normalize_search_phrase(first_query)
        if first_query:
            first_site = self._resolve_site_keyword(first_query)
            if first_site:
                steps.append({"action": "browse", "url": self._SITE_URLS[first_site]})
                current_site = first_site
            else:
                steps.append(self._build_search_step(first_query, site_hint=current_site))

        nested_pattern = re.compile(
            r"(?:dentro|no|na|em)\s+(?:do|da|de)?\s*([a-z0-9\.\-]+)\s+"
            r"(?:pesquise|pesquisar|procure|procurar|buscar|busque)\s+"
            r"(?:por\s+)?(.+?)(?=,|\bdepois\b|$)",
            flags=re.IGNORECASE,
        )
        for match in nested_pattern.finditer(command_lower):
            site_raw = (match.group(1) or "").strip()
            query_raw = (match.group(2) or "").strip()
            site = self._resolve_site_keyword(site_raw)
            query = self._normalize_search_phrase(query_raw)
            if not query:
                continue
            if site:
                site_url = self._SITE_URLS.get(site)
                if site_url and (not steps or steps[-1].get("url") != site_url):
                    steps.append({"action": "browse", "url": site_url})
                steps.append(self._build_search_step(query, site_hint=site))
                current_site = site
            else:
                steps.append(self._build_search_step(query, site_hint=current_site))

        follow_pattern = re.compile(
            r"(?:depois|em seguida)\s+"
            r"(?:procure|procurar|pesquise|pesquisar|buscar|busque)\s+"
            r"(?:por\s+)?(.+?)(?=,|\bdepois\b|$)",
            flags=re.IGNORECASE,
        )
        for match in follow_pattern.finditer(command_lower):
            query = self._normalize_search_phrase(match.group(1) or "")
            if not query:
                continue
            steps.append(self._build_search_step(query, site_hint=current_site))

        return self._dedupe_browse_steps(steps)

    def _wants_notes_output(self, command_lower: str) -> bool:
        has_notepad_target = any(
            token in command_lower for token in ("bloco de notas", "blocos de notas", "notepad")
        )
        has_note_intent = any(
            token in command_lower for token in ("separe", "separar", "anote", "anotar", "resuma", "resumir")
        )
        return has_notepad_target and has_note_intent

    def _should_use_research_mode(self, command_lower: str) -> bool:
        markers = (
            "acesse todas",
            "acessar todas",
            "todas as reportagens",
            "fontes",
            "mais originais",
            "originais",
            "compare",
            "comparar",
            "investigue",
            "investigar",
            "analise",
            "analisar",
        )
        return any(marker in command_lower for marker in markers)

    def _dedupe_browse_steps(self, plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        deduped: List[Dict[str, Any]] = []
        last_browse_url = None
        for step in plan:
            if step.get("action") != "browse":
                deduped.append(step)
                continue
            url = step.get("url")
            if url and url == last_browse_url:
                continue
            deduped.append(step)
            last_browse_url = url
        return deduped

    def _extract_text_to_type(self, command: str) -> Optional[str]:
        quoted = re.search(r'"([^"]+)"', command)
        if not quoted:
            quoted = re.search(r"'([^']+)'", command)
        if quoted:
            return quoted.group(1).strip()

        command_lower = command.lower()
        match = re.search(r"(?:digite|digitar|escreva|escrever|type|write)\s+(.+)", command_lower)
        if not match:
            return None

        content = self._trim_punctuation(match.group(1))
        content = self._cut_at_follow_up(content)
        return content or None

    def _extract_hotkey_keys(self, command_lower: str) -> Optional[List[str]]:
        match = re.search(r"(?:atalho|hotkey|pressione|aperte|tecla(?:s)?)\s+([a-z0-9+\-_,\s]+)", command_lower)
        raw = None
        if match:
            raw = match.group(1)
        elif "+" in command_lower and any(k in command_lower for k in ("ctrl", "control", "alt", "shift", "win", "windows")):
            raw = command_lower

        if not raw:
            return None

        raw = raw.replace(" mais ", "+").replace("-", "+")
        tokens = [t.strip() for t in re.split(r"[+,\s]+", raw) if t.strip()]
        if not tokens:
            return None

        normalized: List[str] = []
        for token in tokens[:4]:
            key = self._HOTKEY_ALIASES.get(token, token)
            if key:
                normalized.append(key)

        if len(normalized) < 2:
            return None
        return normalized

    def _extract_click_step(self, command_lower: str) -> Optional[Dict[str, Any]]:
        match = re.search(r"(?:clique|click)\s*(?:em)?\s*\(?\s*(\d{1,5})\s*(?:,|x)\s*(\d{1,5})\s*\)?", command_lower)
        if not match:
            return None

        return {
            "action": "click",
            "x": int(match.group(1)),
            "y": int(match.group(2)),
        }

    def _extract_wait_seconds(self, command_lower: str) -> Optional[float]:
        match = re.search(
            r"(?:espere|aguarde|wait)\s*(\d+(?:[.,]\d+)?)?\s*(s|seg|segundo|segundos|min|minuto|minutos)?",
            command_lower,
        )
        if not match:
            return None

        raw_number = match.group(1)
        unit = (match.group(2) or "s").lower()
        if not raw_number:
            return 1.0

        seconds = float(raw_number.replace(",", "."))
        if unit.startswith("m"):
            seconds *= 60.0
        return max(0.0, seconds)

    def _context_recovery(self, command_lower: str, screen_context: str) -> List[Dict[str, Any]]:
        if not screen_context:
            return []

        asks_for_help = any(
            token in command_lower
            for token in ("ajuda", "help", "corrige", "corrigir", "resolver", "fix")
        )
        if not asks_for_help:
            return []

        context = screen_context.lower()
        if any(token in context for token in ("erro", "error", "falha", "exception", "traceback")):
            return [{
                "action": "type_text",
                "content": "Detectei erro na tela. Vou investigar e priorizar a correcao.",
            }]
        return []

    def _validate_plan(self, plan: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        if not plan:
            return []

        allowed = {"open_app", "type_text", "hotkey", "click", "browse", "wait", "research_web"}
        normalized: List[Dict[str, Any]] = []

        for step in plan:
            if not isinstance(step, dict):
                continue

            action = step.get("action")
            if not action or not isinstance(action, str):
                continue

            action = self._normalize_action(action)
            if action not in allowed:
                continue

            clean_step = dict(step)
            clean_step["action"] = action

            if action == "open_app":
                target = clean_step.get("target")
                if not isinstance(target, str) or not target.strip():
                    continue
                clean_step["target"] = target.strip()

            if action == "type_text":
                content = clean_step.get("content")
                if not isinstance(content, str) or not content.strip():
                    continue
                clean_step["content"] = content

            if action == "hotkey":
                keys = clean_step.get("keys")
                if isinstance(keys, str):
                    keys = [k.strip() for k in re.split(r"[+,\s]+", keys) if k.strip()]
                if not isinstance(keys, list) or len(keys) < 2:
                    continue
                clean_step["keys"] = keys[:4]

            if action == "click":
                x, y = clean_step.get("x"), clean_step.get("y")
                try:
                    clean_step["x"] = int(x)
                    clean_step["y"] = int(y)
                except Exception:
                    continue

            if action == "browse":
                url = clean_step.get("url") or clean_step.get("target")
                if not isinstance(url, str) or not url.strip():
                    continue
                clean_step["url"] = url.strip()
                clean_step.pop("target", None)

            if action == "wait":
                seconds = clean_step.get("seconds", 1)
                try:
                    clean_step["seconds"] = max(0.0, float(seconds))
                except Exception:
                    clean_step["seconds"] = 1.0

            if action == "research_web":
                query = clean_step.get("query")
                if not isinstance(query, str) or not query.strip():
                    continue
                clean_step["query"] = query.strip()
                for key, default in (("max_results", 10), ("top_k", 5)):
                    val = clean_step.get(key, default)
                    try:
                        clean_step[key] = max(1, int(val))
                    except Exception:
                        clean_step[key] = default
                clean_step["write_notepad"] = bool(clean_step.get("write_notepad", False))
                clean_step["open_tabs"] = bool(clean_step.get("open_tabs", False))

            normalized.append(clean_step)

        return normalized

    def _normalize_action(self, action: str) -> str:
        action = action.strip().lower()
        if action in {"type", "write", "input"}:
            return "type_text"
        if action in {"open", "launch"}:
            return "open_app"
        if action in {"browse_url", "open_url", "navigate"}:
            return "browse"
        if action in {"research", "web_research", "research_mode"}:
            return "research_web"
        return action
