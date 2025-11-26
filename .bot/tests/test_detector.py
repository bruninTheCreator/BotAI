import unittest

from core.detector_repeticao import find_patterns_in_memory
from core.memory import Memory as InMemory


class TestDetectorRepeticao(unittest.TestCase):
    def test_detect_frequent_events(self):
        mem = InMemory()
        # salva eventos repetidos
        mem.save(
            event_type="user_command", data={
                "command": "abrir relatório"})
        mem.save(
            event_type="user_command", data={
                "command": "abrir relatório"})
        mem.save(
            event_type="user_command", data={
                "command": "abrir relatório"})

        patterns = find_patterns_in_memory(
            mem, min_event_count=2, seq_n=2, min_seq_count=2)
        self.assertIn("frequent_events", patterns)
        self.assertTrue(len(patterns["frequent_events"]) >= 1)
        # valida estrutura de exemplos
        for sig, info in patterns["frequent_events"].items():
            self.assertIn("count", info)
            self.assertIn("examples", info)

    def test_detect_frequent_sequences(self):
        mem = InMemory()
        # cria uma sequência repetida: comando -> execução
        mem.save(event_type="user_command", data={"command": "abrir logs"})
        mem.save(
            event_type="execution_result",
            data={
                "action": "open_app",
                "result": "ok"})
        mem.save(event_type="user_command", data={"command": "abrir logs"})
        mem.save(
            event_type="execution_result",
            data={
                "action": "open_app",
                "result": "ok"})

        patterns = find_patterns_in_memory(
            mem, min_event_count=1, seq_n=2, min_seq_count=2)
        self.assertIn("frequent_sequences", patterns)
        self.assertTrue(len(patterns["frequent_sequences"]) >= 1)
        # valida que cada sequência tem examples e count
        for seq, info in patterns["frequent_sequences"].items():
            self.assertIn("count", info)
            self.assertIn("examples", info)


if __name__ == '__main__':
    unittest.main()
