"""Política de segurança: validações, guardrails e controle de ações.

Define o conjunto de ações permitidas, níveis de permissão, e checagens
de segurança antes de executar ações potencialmente perigosas.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, List, Optional, Set, Tuple


class PermissionLevel(Enum):
    """Níveis de permissão para executar ações."""
    NONE = 0
    READ_ONLY = 1
    SYSTEM_CONTROL = 2
    FILE_OPERATIONS = 3
    NETWORK = 4
    ADMIN = 5


@dataclass
class ActionPermission:
    """Define permissões para uma ação."""
    action_name: str
    required_level: PermissionLevel
    requires_confirmation: bool = False
    description: str = ""


class Policy:
    """Gerenciador de política de segurança."""

    def __init__(self) -> None:
        # Ações blacklisted (nunca permitidas)
        self._blacklist: Set[str] = {
            r"rm\s+-rf",  # remove recursively
            r"format\s+[a-z]:",  # format drives
            r"del\s+.*:\*",  # delete entire drive
            r"shutdown\s+/s",  # system shutdown
            r"regedit",  # Windows registry
        }

        # Ações que requerem confirmação
        self._require_confirmation: Set[str] = {
            r"delete",
            r"remove",
            r"uninstall",
            r"format",
        }

        # Mapeamento de ações permitidas por nível
        self._allowed_actions: Dict[PermissionLevel, Set[str]] = {
            PermissionLevel.READ_ONLY: {
                "read_file",
                "list_directory",
                "query_web",
                "get_screen",
            },
            PermissionLevel.FILE_OPERATIONS: {
                "write_file",
                "create_directory",
                "delete_file",
                "move_file",
            },
            PermissionLevel.SYSTEM_CONTROL: {
                "click",
                "type",
                "type_text",
                "open_app",
                "close_app",
                "hotkey",
                "wait",
            },
            PermissionLevel.NETWORK: {
                "browse",
                "browse_url",
                "send_http_request",
                "research_web",
            },
            PermissionLevel.ADMIN: {
                "execute_script",
                "install_package",
                "modify_config",
            },
        }

    def validate_action(
        self,
        action: str,
        args: Optional[Dict] = None,
        permission_level: PermissionLevel = PermissionLevel.SYSTEM_CONTROL,
    ) -> Tuple[bool, Optional[str]]:
        """Valida se uma ação é permitida.

        Retorna (allowed: bool, reason: Optional[str]).
        """
        # Allow callers to pass permission_level as the second positional
        # argument (legacy/tests). Detect and adjust if needed.
        if isinstance(args, PermissionLevel):
            permission_level = args
            args = None

        args = args or {}

        # 1. Checar blacklist
        for pattern in self._blacklist:
            if re.search(pattern, action, re.IGNORECASE):
                return False, f"Action '{action}' is blacklisted for security reasons."

        # 2. Checar se é uma ação permitida
        allowed_for_level = self._collect_allowed_actions(permission_level)
        if action not in allowed_for_level:
            return False, f"Action '{action}' not allowed at permission level {permission_level.name}."

        # 3. Checar confirmação
        if self._requires_confirmation(action):
            return True, f"Action '{action}' requires user confirmation."

        return True, None

    def _collect_allowed_actions(self, level: PermissionLevel) -> Set[str]:
        """Coleta todas as ações permitidas até o nível especificado."""
        allowed = set()
        for perm_level, actions in self._allowed_actions.items():
            if perm_level.value <= level.value:
                allowed.update(actions)
        return allowed

    def _requires_confirmation(self, action: str) -> bool:
        """Retorna True se a ação requer confirmação."""
        for pattern in self._require_confirmation:
            if re.search(pattern, action, re.IGNORECASE):
                return True
        return False

    def is_safe_path(self, path: str) -> bool:
        """Valida se um caminho é seguro (não em diretórios críticos)."""
        dangerous_paths = [
            r"c:\\windows",
            r"c:\\program\s+files",
            r"/etc",
            r"/sys",
            r"/boot",
        ]
        for pattern in dangerous_paths:
            if re.search(pattern, path, re.IGNORECASE):
                return False
        return True

    def sanitize_command(self, command: str) -> str:
        """Remove/escapa caracteres perigosos em comandos."""
        # Simples sanitização: remover ; | & ` $ etc.
        dangerous_chars = r"[;&|`$\n\r]"
        return re.sub(dangerous_chars, "", command)


__all__ = ["Policy", "PermissionLevel", "ActionPermission"]
