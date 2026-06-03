"""플러그인 관리 다이얼로그."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QDialogButtonBox,
)
from PyQt6.QtCore import Qt

from core.plugin_loader import PluginLoader
from core.settings import Settings


class PluginDialog(QDialog):
    def __init__(self, loader: PluginLoader, settings: Settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("플러그인 관리")
        self.resize(480, 340)
        self._loader = loader
        self._settings = settings
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self._list = QListWidget()
        self._list.currentItemChanged.connect(self._on_item_changed)
        layout.addWidget(self._list)

        self._lbl_detail = QLabel("플러그인을 선택하세요.")
        self._lbl_detail.setWordWrap(True)
        layout.addWidget(self._lbl_detail)

        btn_row = QHBoxLayout()
        self._btn_toggle = QPushButton("활성화")
        self._btn_toggle.setEnabled(False)
        self._btn_toggle.clicked.connect(self._on_toggle)
        btn_row.addWidget(self._btn_toggle)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _refresh_list(self):
        current_name = None
        current_item = self._list.currentItem()
        if current_item:
            current_name = current_item.data(Qt.ItemDataRole.UserRole)

        self._list.clear()
        loaded = self._loader.get_loaded()
        discovered = self._loader.discover()

        if not discovered:
            self._list.addItem("(설치된 플러그인 없음)")
            self._btn_toggle.setEnabled(False)
            return

        for name in discovered:
            status = "[활성]  " if name in loaded else "[비활성]"
            li = QListWidgetItem(f"{status}  {name}")
            li.setData(Qt.ItemDataRole.UserRole, name)
            self._list.addItem(li)

        if current_name:
            for i in range(self._list.count()):
                if self._list.item(i).data(Qt.ItemDataRole.UserRole) == current_name:
                    self._list.setCurrentRow(i)
                    return
        if self._list.count():
            self._list.setCurrentRow(0)

    def _on_item_changed(self, item: QListWidgetItem):
        name = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not name:
            self._lbl_detail.setText("플러그인을 선택하세요.")
            self._btn_toggle.setEnabled(False)
            return

        loaded = self._loader.get_loaded()
        if name in loaded:
            p = loaded[name]
            detail = f"<b>{p.name or name}</b> v{p.version}"
            if p.description:
                detail += f"<br>{p.description}"
            if p.author:
                detail += f"<br><small>작성자: {p.author}</small>"
            self._lbl_detail.setText(detail)
            self._btn_toggle.setText("비활성화")
        else:
            self._lbl_detail.setText(f"<b>{name}</b><br>비활성 상태입니다.")
            self._btn_toggle.setText("활성화")

        self._btn_toggle.setEnabled(True)

    def _on_toggle(self):
        item = self._list.currentItem()
        if item is None:
            return

        name = item.data(Qt.ItemDataRole.UserRole)
        if not name:
            return

        loaded = self._loader.get_loaded()
        enabled: list = list(self._settings.get("enabled_plugins", []))

        if name in loaded:
            self._loader.unload(name)
            if name in enabled:
                enabled.remove(name)
        else:
            self._loader.load(name)
            if name not in enabled:
                enabled.append(name)

        self._settings.set("enabled_plugins", enabled)
        self._refresh_list()
