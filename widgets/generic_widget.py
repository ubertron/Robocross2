from __future__ import annotations

import sys
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QLabel, QPushButton
from core.core_enums import Alignment, Position


class GenericWidget(QWidget):
    def __init__(self, title: str = '', parent=None, alignment: Alignment = Alignment.vertical, margin: int = 2,
                 spacing: int = 2):
        super(GenericWidget, self).__init__(parent)
        self.setWindowTitle(title)
        layout = QVBoxLayout() if alignment is Alignment.vertical else QHBoxLayout()
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        self.setLayout(layout)

    def add_widget(self, widget: QWidget) -> QWidget:
        """Add widget to the layout"""
        self.layout().addWidget(widget)
        return widget

    def add_label(self, text: str, position: Position = Position.center) -> QLabel:
        """Add label to the layout"""
        alignment: Qt.AlignmentFlag = {
            position.center: Qt.AlignmentFlag.AlignCenter,
            position.left: Qt.AlignmentFlag.AlignLeft,
            position.right: Qt.AlignmentFlag.AlignRight,
        }
        return self.add_widget(QLabel(text, alignment=alignment[position]))

    def add_button(self, text: str, tool_tip: str, clicked: Callable | None = None) -> QPushButton:
        """Add button to the layout"""
        button = QPushButton(text)
        button.setToolTip(tool_tip)
        button.clicked.connect(clicked)
        return self.add_widget(button)


class ExampleWidget(GenericWidget):
    def __init__(self):
        super(ExampleWidget, self).__init__(title="Example Widget", margin=4)
        self.label = self.add_label("Label")
        self.add_button(text="Button 1", tool_tip="Button 1", clicked=lambda: self.label.setText("Button 1"))
        self.setFixedSize(320, 240)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    example_widget = ExampleWidget()
    example_widget.show()
    app.exec()
