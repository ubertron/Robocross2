"""PySide ui for Robocross2."""
import getpass
import logging
import sys

from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit, QSpinBox, QLabel

from core.core_enums import Position
from core.logging_utils import get_logger
from robocross.routine import Routine
from robocross.workout_form import WorkoutForm
from robocross.workout_widget import WorkoutWidget
from widgets import form_widget
from widgets.generic_widget import GenericWidget
from widgets.panel_widget import PanelWidget


LOGGER: logging.Logger = get_logger(name=__name__, level=logging.DEBUG)


class RoboCrossUI(GenericWidget):
    name = 'RoboCross'
    version = '2.0'
    codename = 'dragonfly'
    title = f'{name} v{version} [{codename}]'

    def __init__(self, parent=None):
        super(RoboCrossUI, self).__init__(title=self.title, parent=parent)
        self.button_bar = self.add_button_bar()
        self.button_bar.add_button(text="Build", clicked=self.build_button_clicked, tool_tip="Build the workout based on the info")
        self.button_bar.add_button(text="Save Session")
        self.button_bar.add_button(text="Print", tool_tip="Print the workout", clicked=self.print_button_clicked)
        self.button_bar.add_stretch()
        self.form_panel, self.form = self.add_panel(widget=WorkoutForm(parent_widget=self))
        self.workout_panel, self.workout_widget = self.add_panel(WorkoutWidget(parent_widget=self))
        self.add_stretch()
        self.routine = None

    @property
    def date_time_string(self) -> str:
        return datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    @property
    def info_string(self) -> str:
        self.routine = Routine(
            interval=self.form.interval,
            workout_length=self.form.length,
            rest_time=self.form.rest_time,
            nope_list=self.form.nope_list
        )
        workout_list = (
            self.routine.cardio_workout,
            self.routine.strength_workout,
            self.routine.cardio_strength_mix,
            self.routine.random_workout,
        )[self.form.workout_types.index(self.form.workout_type)]
        return "\n".join(f"{index + 1}:\t{item.name}" for index, item in enumerate(workout_list))

    @property
    def routine(self) -> Routine:
        return self._routine

    @routine.setter
    def routine(self, value: str):
        self._routine = value

    @property
    def user(self) -> str:
        return getpass.getuser()

    @property
    def workout_report(self) -> str:
        """Printable workout report."""
        line = "-" * 64
        report = (
            f"{line}\n"
            f"User: {self.user}\n"
            f"Date: {self.date_time_string}\n"
            f"Workout Length: {self.form.length}\n"
            f"Interval: {self.form.interval}\n"
            f"Rest Time: {self.form.rest_time}\n"
            f"{line}\n"
            f"{self.info_string}"
        )
        return report

    def build_button_clicked(self):
        """Create the workout report and send to the workout widget."""
        self.workout_widget.info = self.workout_report

    def print_button_clicked(self):
        """Event for print button."""
        LOGGER.info(self.workout_report)

if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = RoboCrossUI()
    widget.show()
    sys.exit(app.exec())
