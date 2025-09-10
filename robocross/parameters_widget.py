from functools import partial

from PySide6.QtWidgets import QCheckBox, QWidget, QLabel, QSizePolicy
from PySide6.QtCore import Signal, Qt, QSettings

from core import DEVELOPER
from core.core_enums import Alignment
from robocross.robocross_enums import Equipment
from robocross.workout_form import WorkoutForm
from widgets.generic_widget import GenericWidget
from widgets.scroll_widget import ScrollWidget


class ParametersWidget(GenericWidget):
    """Widget storing the workout parameters."""

    build_button_clicked = Signal()
    print_button_clicked = Signal()
    title = "Robocross Parameters Widget"

    def __init__(self):
        super().__init__(title=self.title)
        self.settings = QSettings(DEVELOPER, self.title)
        self.button_bar = self.add_button_bar()
        self.button_bar.add_button(text="Build", clicked=self.build_button_clicked.emit,
                                   tool_tip="Build the workout based on the info")
        self.button_bar.add_button(text="Save Session")
        self.button_bar.add_button(text="Print", tool_tip="Print the workout", clicked=self.print_button_clicked.emit)
        self.button_bar.add_stretch()
        content_pane = self.add_widget(GenericWidget(alignment=Alignment.horizontal))
        self.form: WorkoutForm = content_pane.add_widget(WorkoutForm(parent_widget=self))
        equipment_widget = content_pane.add_widget(GenericWidget())
        equipment_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        equipment_widget.add_label("Equipment List")
        self.equipment_check_boxes = [equipment_widget.add_widget(QCheckBox(x)) for x in self.equipment_names]
        self.info_label = QLabel()
        scroll_widget = self.add_widget(ScrollWidget())
        scroll_widget.widget.add_widget(self.info_label)
        scroll_widget.widget.add_stretch()
        self.setup_ui()

    @property
    def equipment_names(self):
        names = [member.name.title().replace('_', ' ') for member in Equipment]
        names.sort()
        return names

    @property
    def equipment_filter(self) -> list[Equipment]:
        """List of equipment being used."""
        return [Equipment.__members__.get(x.text().lower().replace(' ', '_')) \
                for x in self.equipment_check_boxes if not x.isChecked()]

    @property
    def zero_equipment(self) -> bool:
        """Return true if no equipment selected."""
        return len(self.equipment_filter) == len(Equipment)

    @property
    def info(self) -> str:
        return self.info_label.text()

    @info.setter
    def info(self, value: str):
        self.info_label.setText(value)

    def check_state_changed(self, *args):
        """Event for check box changed."""
        check_box = next(x for x in args if type(x) is QCheckBox)
        self.settings.setValue(check_box.text(), check_box.isChecked())

    def setup_ui(self):
        self.info_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        for checkbox in self.equipment_check_boxes:
            checkbox.setChecked(self.settings.value(checkbox.text(), True))
            checkbox.checkStateChanged.connect(partial(self.check_state_changed, checkbox))
