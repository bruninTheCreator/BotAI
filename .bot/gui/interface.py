import os
import sys
import json

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QApplication,
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QTableWidget,
        QTableWidgetItem,
        QAbstractItemView,
        QPushButton,
        QPlainTextEdit,
        QSplitter,
        QDialog,
        QMessageBox,
    )
except Exception as e:
    raise SystemExit("PySide6 não está instalado. Rode: pip install PySide6") from e

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.memoria import Memory
from core.pattern_engine import PatternEngine
from core.llm_client import LLMClient


class ActionEditorDialog(QDialog):
    def __init__(self, parent=None, action_data=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Ação (JSON)")
        self.setMinimumSize(500, 400)

        self.text = QPlainTextEdit(self)
        if action_data:
            try:
                self.text.setPlainText(json.dumps(action_data, indent=2, ensure_ascii=False))
            except Exception:
                self.text.setPlainText(str(action_data))
        else:
            self.text.setPlainText("[]")

        btn_save = QPushButton("Salvar")
        btn_cancel = QPushButton("Cancelar")
        btn_save.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        row = QHBoxLayout()
        row.addWidget(btn_save)
        row.addWidget(btn_cancel)

        layout = QVBoxLayout()
        layout.addWidget(self.text)
        layout.addLayout(row)
        self.setLayout(layout)

    def get_action(self):
        raw = self.text.toPlainText().strip()
        if not raw:
            return None
        try:
            data = json.loads(raw)
        except Exception:
            raise ValueError("JSON inválido")
        if not isinstance(data, (list, dict)):
            raise ValueError("Ação deve ser lista ou objeto JSON")
        return data


class PatternManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BotAI - Padrões")
        self.setMinimumSize(900, 600)

        data_dir = os.path.join(ROOT, "data")
        self.memory = Memory(file_path=os.path.join(data_dir, "memory_log.jsonl"))
        self.engine = PatternEngine(memory=self.memory, patterns_path=os.path.join(data_dir, "patterns.json"))

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Label", "Count", "Conf", "Mode", "Enabled"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setColumnHidden(0, True)
        self.table.itemSelectionChanged.connect(self._update_details)

        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.table)
        splitter.addWidget(self.details)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        btn_refresh = QPushButton("Refresh")
        btn_mine = QPushButton("Mine Now")
        btn_toggle = QPushButton("Enable/Disable")
        btn_suggest = QPushButton("Mode: Suggest")
        btn_auto = QPushButton("Mode: Auto")
        btn_edit_action = QPushButton("Edit Action")
        btn_clear_action = QPushButton("Clear Action")
        btn_suggest_action = QPushButton("Suggest Action (LLM)")

        btn_refresh.clicked.connect(self.refresh)
        btn_mine.clicked.connect(self.mine_now)
        btn_toggle.clicked.connect(self.toggle_enabled)
        btn_suggest.clicked.connect(lambda: self.set_mode("suggest"))
        btn_auto.clicked.connect(lambda: self.set_mode("auto"))
        btn_edit_action.clicked.connect(self.edit_action)
        btn_clear_action.clicked.connect(self.clear_action)
        btn_suggest_action.clicked.connect(self.suggest_action_llm)

        row = QHBoxLayout()
        row.addWidget(btn_refresh)
        row.addWidget(btn_mine)
        row.addWidget(btn_toggle)
        row.addWidget(btn_suggest)
        row.addWidget(btn_auto)
        row.addWidget(btn_edit_action)
        row.addWidget(btn_clear_action)
        row.addWidget(btn_suggest_action)
        row.addStretch(1)

        wrapper = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        layout.addLayout(row)
        wrapper.setLayout(layout)
        self.setCentralWidget(wrapper)

        self.refresh()

    def _selected_pattern_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.text() if item else None

    def _load_patterns(self):
        return self.engine.list_patterns(top=0, sort_by="confidence")

    def refresh(self):
        patterns = self._load_patterns()
        self.table.setRowCount(0)
        for p in patterns:
            row = self.table.rowCount()
            self.table.insertRow(row)

            pid = str(p.get("id", ""))
            label = p.get("label", "pattern")
            count = str(p.get("count", 0))
            conf = str(p.get("confidence", 0))
            mode = p.get("mode", "suggest")
            enabled = "yes" if p.get("enabled", True) else "no"

            self.table.setItem(row, 0, QTableWidgetItem(pid))
            self.table.setItem(row, 1, QTableWidgetItem(label))
            self.table.setItem(row, 2, QTableWidgetItem(count))
            self.table.setItem(row, 3, QTableWidgetItem(conf))
            self.table.setItem(row, 4, QTableWidgetItem(mode))
            self.table.setItem(row, 5, QTableWidgetItem(enabled))

        self._update_details()

    def mine_now(self):
        self.engine.update()
        self.refresh()

    def _update_details(self):
        row = self.table.currentRow()
        if row < 0:
            self.details.setPlainText("")
            return
        pid = self.table.item(row, 0).text()
        patterns = self._load_patterns()
        pat = next((p for p in patterns if p.get("id") == pid), None)
        if not pat:
            self.details.setPlainText("")
            return
        examples = pat.get("examples", [])
        info = {
            "id": pat.get("id"),
            "label": pat.get("label"),
            "count": pat.get("count"),
            "confidence": pat.get("confidence"),
            "mode": pat.get("mode"),
            "enabled": pat.get("enabled"),
            "hours": pat.get("hours"),
            "examples": examples,
            "action": pat.get("action"),
        }
        self.details.setPlainText(json.dumps(info, indent=2, ensure_ascii=False))

    def toggle_enabled(self):
        pid = self._selected_pattern_id()
        if not pid:
            return
        patterns = self._load_patterns()
        pat = next((p for p in patterns if p.get("id") == pid), None)
        if not pat:
            return
        new_val = not pat.get("enabled", True)
        self.engine.store.update_pattern(pid, enabled=new_val)
        self.refresh()

    def set_mode(self, mode: str):
        pid = self._selected_pattern_id()
        if not pid:
            return
        if mode not in {"suggest", "auto"}:
            return
        self.engine.store.update_pattern(pid, mode=mode)
        self.refresh()

    def edit_action(self):
        pid = self._selected_pattern_id()
        if not pid:
            return
        patterns = self._load_patterns()
        pat = next((p for p in patterns if p.get("id") == pid), None)
        if not pat:
            return
        dlg = ActionEditorDialog(self, action_data=pat.get("action"))
        if dlg.exec() != QDialog.Accepted:
            return
        try:
            action = dlg.get_action()
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))
            return
        self.engine.store.update_pattern(pid, action=action)
        self.refresh()

    def clear_action(self):
        pid = self._selected_pattern_id()
        if not pid:
            return
        self.engine.store.update_pattern(pid, action=None)
        self.refresh()

    def suggest_action_llm(self):
        pid = self._selected_pattern_id()
        if not pid:
            return
        patterns = self._load_patterns()
        pat = next((p for p in patterns if p.get("id") == pid), None)
        if not pat:
            return

        llm = LLMClient()
        if not llm.is_available():
            QMessageBox.information(self, "LLM indisponível", "OPENAI_API_KEY não configurada.")
            return

        plan = llm.suggest_action_for_pattern(pat.get("label", "pattern"), pat.get("examples", []))
        if not plan:
            QMessageBox.warning(self, "Sem sugestão", "Não foi possível gerar uma ação.")
            return
        self.engine.store.update_pattern(pid, action=plan, mode="suggest")
        self.refresh()


def run():
    app = QApplication(sys.argv)
    win = PatternManager()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
