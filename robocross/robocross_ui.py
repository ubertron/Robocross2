"""PySide ui for Robocross2."""
import getpass
import sys

from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit, QSpinBox, QLabel

from core.core_enums import Position
from robocross.routine import Routine, NOPE_LIST
from widgets import form_widget
from widgets.generic_widget import GenericWidget
from widgets.button_bar import ButtonBar


class RoboCrossUI(GenericWidget):
    name = 'RoboCross'
    version = '2.0'
    codename = 'dragonfly'
    title = f'{name} v{version} [{codename}]'
    default_workout_length = 30
    default_interval_time = 120
    default_rest_time = 30
    workout_types = [
        "cardio",
        "strength",
        "cardio/strength",
        "random"
    ]

    def __init__(self, parent=None):
        super(RoboCrossUI, self).__init__(title=self.title, parent=parent)
        self.button_bar: ButtonBar = self.add_widget(ButtonBar())
        self.button_bar.add_button(text="Build", clicked=self.build_button_clicked, tool_tip="Build the workout based on the info")
        self.button_bar.add_button(text="Play/Pause")
        self.button_bar.add_button(text="Stop")
        self.button_bar.add_button(text="Reset")
        self.button_bar.add_button(text="Save Session")
        self.button_bar.add_button(text="Print", tool_tip="Print the workout", clicked=self.print_button_clicked)
        self.button_bar.add_stretch()
        self.form: form_widget.FormWidget = self.add_widget(form_widget.FormWidget())
        self.workout_length_spin_box: QSpinBox = self.form.add_int_field(label="Workout length (minutes)", default_value=self.default_workout_length)
        self.interval_spin_box: QSpinBox = self.form.add_int_field(label="Interval (seconds)", default_value=self.default_interval_time)
        self.rest_time_spin_box: QSpinBox = self.form.add_int_field(label="Rest Time (seconds)", default_value=self.default_rest_time)
        self.workout_type_combo_box: QComboBox = self.form.add_combo_box(label="Workout Type", items=self.workout_types, default_index=2)
        self.workout_label: QLabel = self.add_label(text="Workout Info", position=Position.left)
        self.add_stretch()
        self.routine = None
        self.setup_ui()

    @property
    def date_time_string(self) -> str:
        return datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    @property
    def info_string(self) -> str:
        self.routine = Routine(
            interval=self.interval,
            workout_length=self.workout_length,
            rest_time=self.rest_time,
            nope_list=NOPE_LIST
        )
        workout_list = (
            self.routine.cardio_workout,
            self.routine.strength_workout,
            self.routine.cardio_strength_mix,
            self.routine.random_workout,
        )[self.workout_types.index(self.workout_type)]
        return "\n".join(f"{index + 1}:\t{item.name}" for index, item in enumerate(workout_list))

    @property
    def interval(self) -> int:
        return self.interval_spin_box.value()

    @property
    def rest_time(self) -> int:
        return self.rest_time_spin_box.value()

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
            f"Workout Length: {self.workout_length_spin_box.value()}\n"
            f"Interval: {self.interval}\n"
            f"Rest Time: {self.rest_time}\n"
            f"{line}\n"
            f"{self.info_string}"
        )
        return report

    @property
    def workout_length(self) -> int:
        return self.workout_length_spin_box.value()

    @property
    def workout_type(self) -> str:
        return self.workout_type_combo_box.currentText()

    def build_button_clicked(self):
        """Event for build button."""
        self.workout_label.setText(self.workout_report)

    def print_button_clicked(self):
        """Event for print button."""
        LOGGER.info(self.workout_report)

    def setup_ui(self):
        self.workout_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByKeyboard | Qt.TextInteractionFlag.TextSelectableByMouse)



if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = RoboCrossUI()
    widget.show()
    sys.exit(app.exec())
