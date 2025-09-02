from __future__ import annotations

import sys

from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QSizePolicy, QWidget
from core.core_enums import Alignment

class ButtonBar(QWidget):
    def __init__(self, margin: int = 0, spacing: int = 0):
        super(ButtonBar, self).__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum))

    def add_button(self, text: str, tool_tip: str="", clicked: Callable | None = None) -> QPushButton:
        """Add button to the layout"""
        button = QPushButton(text)
        button.setToolTip(tool_tip)
        if clicked:
            button.clicked.connect(clicked)
        return self.add_widget(button)

    def add_icon_button(self, image: Path, tool_tip: str, clicked: Callable):
        """Add icon button to the layout"""

    def add_stretch(self):
        """
        Add a stretch item to the layout
        """
        self.layout().addStretch(True)

    def add_widget(self, widget: QWidget) -> QWidget:
        """Add widget to the layout"""
        self.layout().addWidget(widget)
        return widget



if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = ButtonBar()
    widget.add_button("this is a button", tool_tip="this is a tool tip")
    widget.add_stretch()
    widget.show()
    app.exec()
