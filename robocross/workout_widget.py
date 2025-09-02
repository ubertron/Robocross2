from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget

from core.core_enums import Position
from widgets.generic_widget import GenericWidget
from widgets.stopwatch import Stopwatch


class WorkoutWidget(GenericWidget):
    def __init__(self, parent_widget: QWidget):
        super().__init__(title="Workout")
        self.parent_widget = parent_widget
        self.stopwatch = self.add_widget(Stopwatch())
        self.info_label = self.add_label(text="Workout information", position=Position.left)

    @property
    def info(self):
        return self.info_label.text()

    @info.setter
    def info(self, value):
        self.info_label.setText(value)