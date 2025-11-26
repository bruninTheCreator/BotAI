from abc import ABC, abstractmethod


class Planner(ABC):
    def __init__(self, memory=None):
        self.memory = memory


    # ===== MÉTODOS OBRIGATÓRIOS =====

    def initialize(self):
        """Inicialização do planner"""
        return True


    def shutdown(self):
        """Finalização do planner"""
        return True


    # ===== MÉTODO PRINCIPAL =====

    def interpret_command(self, command, screen_context=None):
        """
        Interpreta o comando do usuário e gera um plano de ação.
        Retorna uma lista de passos.
        """

        command_lower = command.lower()

        plan = []

        if "bloco de notas" in command_lower or "notepad" in command_lower:
            plan.append({
                "action": "open_app",
                "target": "notepad"
            })

            if '"' in command:
                conteudo = command.split('"')[1]
                plan.append({
                    "action": "type_text",
                    "content": conteudo
                })

        if "dialogo" in command_lower:
            plan.append({
                "action": "type_text",
                "content": "Iniciando diálogo entre humano e máquina..."
            })

        return plan
