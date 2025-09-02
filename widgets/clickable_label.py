import enum

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QMouseEvent


class ClickableLabel(QLabel):
    clicked: Signal = Signal(QPoint)

    def __init__(self, *args, global_context: bool = True, button: enum = Qt.MouseButton.LeftButton):
        super(ClickableLabel, self).__init__(*args)
        self.global_context: bool = global_context
        self.button: enum = button

    def mousePressEvent(self, event):
        global_position = event.globalPosition().toPoint()
        local_position = self.window().mapFromGlobal(global_position)
        position = global_position if self.global_context else local_position

        if event.button() == self.button:
            self.clicked.emit(position)