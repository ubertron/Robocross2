from __future__ import annotations

import sys
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QStackedLayout, QVBoxLayout, QWidget, QLabel, QPushButton, QSpacerItem

from core.core_enums import Alignment, Position
from widgets.button_bar import ButtonBar
from widgets.panel_widget import PanelWidget


class GenericWidget(QWidget):
    def __init__(self, title: str = '', parent=None, alignment: Alignment = Alignment.vertical, margin: int = 2,
                 spacing: int = 2):
        super(GenericWidget, self).__init__(parent)
        self.setWindowTitle(title)
        layout = {
            Alignment.horizontal: QHBoxLayout(),
            Alignment.stacked: QStackedLayout(),
            Alignment.vertical: QVBoxLayout()
        }[alignment]
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        self.setLayout(layout)

    @property
    def widgets(self) -> list[QWidget]:
        widgets = []
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item.widget():  # Check if the item contains a widget
                widgets.append(item.widget())
            elif item.layout():  # If the item contains a nested layout, recurse
                widgets.extend(get_widgets_from_layout(item.layout()))
        return widgets

    def add_label(self, text: str = "", position: Position = Position.center) -> QLabel:
        """Add label to the layout"""
        alignment: Qt.AlignmentFlag = {
            position.center: Qt.AlignmentFlag.AlignCenter,
            position.left: Qt.AlignmentFlag.AlignLeft,
            position.right: Qt.AlignmentFlag.AlignRight,
        }
        return self.add_widget(QLabel(text, alignment=alignment[position]))

    def add_button(self, text: str, tool_tip: str = "", clicked: Callable | None = None) -> QPushButton:
        """Add button to the layout"""
        button = QPushButton(text)
        button.setToolTip(tool_tip)
        if clicked:
            button.clicked.connect(clicked)
        return self.add_widget(button)

    def add_button_bar(self) -> ButtonBar:
        """Add button bar"""
        button_bar = self.add_widget(ButtonBar())
        return button_bar

    def add_panel(self, widget: QWidget) -> tuple[PanelWidget, QWidget]:
        """Add panel to the layout"""
        panel = PanelWidget(widget=widget)
        self.add_widget(panel)
        return panel, widget

    def add_stretch(self):
        """
        Add a stretch item to the layout
        """
        self.layout().addStretch(True)

    def add_widget(self, widget: QWidget) -> QWidget:
        """Add widget to the layout"""
        self.layout().addWidget(widget)
        return widget

    def clear_layout(self):
        """Remove all widgets and spacer items from the current layout."""
        for i in reversed(range(self.layout().count())):
            item = self.layout().itemAt(i)
            if isinstance(item, QSpacerItem):
                self.layout().takeAt(i)
            else:
                item.widget().setParent(None)


class ExampleWidget(GenericWidget):
    def __init__(self):
        super(ExampleWidget, self).__init__(title="Example Widget", margin=4)
        self.label = self.add_label("Label")
        self.add_button(text="Button 1", tool_tip="Button 1", clicked=lambda: self.label.setText("Button 1"))
        self.setFixedSize(320, 240)


class StackedWidget(GenericWidget):
    def __init__(self):
        super(StackedWidget, self).__init__(title="Stacked Widget", alignment=Alignment.stacked)
        self.label = self.add_label("fruity old tart face")
        # self.label.setStyleSheet("background-color: rgb(255, 0, 255);")
        self.text = self.add_label(text="CLOWNS")
        self.text.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        self.text.setStyleSheet("color: rgb(0, 255, 0);")


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    example_widget = StackedWidget()
    example_widget.show()
    print(type(example_widget.layout()))
    app.exec()
