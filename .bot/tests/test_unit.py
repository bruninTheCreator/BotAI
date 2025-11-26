
import unittest
import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            '..')))

from core.percepcao import PerceptionImpl  # noqa: E402
from core.memoria import Memory  # noqa: E402
from core.executor import Executor  # noqa: E402
from core.supervisor import Supervisor  # noqa: E402


class TestPerception(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.perception = PerceptionImpl()

    async def test_capture_screen(self):
        """Testa se a captura de tela funciona."""
        result = await self.perception.capture_screen()
        self.assertTrue(result.success)
        img = result.data
        self.assertIsNotNone(img)
        # Deve ter 3 dimensões (altura, largura, canais)
        self.assertEqual(len(img.shape), 3)

    async def test_read_text(self):
        """Testa se o OCR retorna uma string."""
        result = await self.perception.read_text()
        self.assertTrue(result.success)
        text = result.data
        self.assertIsInstance(text, str)


class TestMemory(unittest.TestCase):
    def setUp(self):
        self.memory = Memory()

    def test_save_and_load(self):
        """Testa salvar e carregar da memória."""
        test_data = {"test": "data", "value": 123}
        self.memory.save(event_type="test_event", data=test_data)

        all_data = self.memory.load_all()
        self.assertIsInstance(all_data, list)
        self.assertGreater(len(all_data), 0)

        # Verifica se o último evento salvo está presente
        last_event = all_data[-1]
        self.assertEqual(last_event["event_type"], "test_event")
        self.assertEqual(last_event["data"], test_data)


class TestExecutor(unittest.TestCase):
    def setUp(self):
        self.executor = Executor()
        self.supervisor = Supervisor()
        self.memory = Memory()

    def test_type_text(self):
        """Testa digitação de texto."""
        plan = [{"action": "type_text", "content": "test"}]
        results = self.executor.execute_plan(
            plan, self.supervisor, self.memory)

        self.assertEqual(len(results), 1)
        self.assertIn("sucesso", results[0].lower())

    def test_invalid_action(self):
        """Testa ação inválida."""
        plan = [{"action": "invalid_action"}]
        results = self.executor.execute_plan(
            plan, self.supervisor, self.memory)

        self.assertEqual(len(results), 1)
        # Aceita tanto "não reconhecida" quanto "não é suportada"
        self.assertTrue(
            "não reconhecida" in results[0].lower() or "não é suportada" in results[0].lower(),  # noqa: E501
            f"Mensagem inesperada: {results[0]}")

    def test_click_without_coordinates(self):
        """Testa click sem coordenadas."""
        plan = [{"action": "click"}]
        results = self.executor.execute_plan(
            plan, self.supervisor, self.memory)

        self.assertEqual(len(results), 1)
        self.assertIn("erro", results[0].lower())


class TestSupervisor(unittest.TestCase):
    def setUp(self):
        self.supervisor = Supervisor()

    def test_log(self):
        """Testa se o log funciona sem erros."""
        try:
            self.supervisor.log("test_event", {"data": "test"})
            success = True
        except Exception:
            success = False

        self.assertTrue(success)


if __name__ == '__main__':
    unittest.main()
