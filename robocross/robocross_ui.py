"""PySide ui for Robocross2."""
from __future__ import annotations

import getpass
import logging
import sys

from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit, QSpinBox, QLabel, QSizePolicy, QTabWidget

from core.core_enums import Position
from core.logging_utils import get_logger
from robocross import WorkoutType, REST_PERIOD
from robocross.routine import Routine
from robocross.parameters_widget import ParametersWidget
from robocross.workout import Workout
from robocross.workout_form import WorkoutForm
from robocross.workout_viewer import WorkoutViewer
from widgets import form_widget
from widgets.generic_widget import GenericWidget
from widgets.panel_widget import PanelWidget


LOGGER: logging.Logger = get_logger(name=__name__, level=logging.DEBUG)


class RoboCrossUI(GenericWidget):
    name = 'RoboCross'
    version = '2.0'
    codename = 'dragonfly'
    title = f'{name} v{version} [{codename}]'
    minimum_width = 640

    def __init__(self, parent=None):
        super(RoboCrossUI, self).__init__(title=self.title, parent=parent)
        self.tab_widget = self.add_widget(QTabWidget())
        self.parameters_widget: ParametersWidget = ParametersWidget()
        self.form = self.parameters_widget.form
        self.tab_widget.addTab(self.parameters_widget, 'Create')
        self.viewer: WorkoutViewer = WorkoutViewer()
        self.tab_widget.addTab(self.viewer, 'Workout')
        self.info = ""
        self.routine = None
        self.workout_list = []
        self.setup_ui()

    def setup_ui(self):
        self.parameters_widget.build_button_clicked.connect(self.build_button_clicked)
        self.parameters_widget.print_button_clicked.connect(self.print_button_clicked)
        self.setMinimumWidth(self.minimum_width)

    @property
    def date_time_string(self) -> str:
        return datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    @property
    def info(self) -> str:
        return self._info

    @info.setter
    def info(self, info: str) -> None:
        self._info = info

    @property
    def routine(self) -> Routine | None:
        return self._routine

    @routine.setter
    def routine(self, routine: Routine | None):
        self._routine = routine
        workout_list = routine.get_workout_list(self.form.workout_type) if routine else []
        self.workout_list = workout_list
        self.viewer.info = "get ready..."

    @property
    def user(self) -> str:
        return getpass.getuser()

    @property
    def workout_list(self):
        return self._workout_list

    @workout_list.setter
    def workout_list(self, workout_list: list[Workout]):
        self._workout_list = workout_list
        self.viewer.workout_list = workout_list
        self.parameters_widget.info = self.workout_report

    @property
    def workout_report(self) -> str:
        return '\n'.join(f"• {x.name}" for x in self.workout_list if x.name != REST_PERIOD)

    def build_button_clicked(self):
        """Create the routine."""
        self.routine = Routine(
            interval=self.form.interval,
            workout_length=self.form.length,
            rest_time=self.form.rest_time,
            nope_list=self.form.nope_list,
        )

    def print_button_clicked(self):
        """Event for print button."""
        LOGGER.info(self.workout_report)


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = RoboCrossUI()
    widget.show()
    sys.exit(app.exec())
