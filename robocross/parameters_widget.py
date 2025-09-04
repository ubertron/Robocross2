from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtCore import Signal, Qt

from robocross.workout_form import WorkoutForm
from widgets.generic_widget import GenericWidget
from widgets.scroll_widget import ScrollWidget


class ParametersWidget(GenericWidget):
    """Widget storing the workout parameters."""

    build_button_clicked = Signal()
    print_button_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.button_bar = self.add_button_bar()
        self.button_bar.add_button(text="Build", clicked=self.build_button_clicked.emit, tool_tip="Build the workout based on the info")
        self.button_bar.add_button(text="Save Session")
        self.button_bar.add_button(text="Print", tool_tip="Print the workout", clicked=self.print_button_clicked.emit)
        self.button_bar.add_stretch()
        self.form: WorkoutForm = self.add_widget(WorkoutForm(parent_widget=self))
        self.info_label = QLabel()
        scroll_widget = self.add_widget(ScrollWidget())
        scroll_widget.widget.add_widget(self.info_label)
        scroll_widget.widget.add_stretch()
        self.setup_ui()

    @property
    def info(self) -> str:
        return self.info_label.text()

    @info.setter
    def info(self, value: str):
        self.info_label.setText(value)

    def setup_ui(self):
        self.info_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
