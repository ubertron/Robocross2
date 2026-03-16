import logging
import re

from PySide6.QtWidgets import QWidget, QLineEdit
from PySide6.QtCore import QSettings

from core import APPLICATION_NAME, DEVELOPER
from core.logging_utils import get_logger
from robocross import WorkoutType
from widgets.form_widget import FormWidget


LOGGER: logging.Logger = get_logger(name=__name__, level=logging.DEBUG)


class WorkoutForm(FormWidget):
    default_workout_length = 30
    default_interval_time = 120
    default_rest_time = 30
    default_workout_type_index = 2
    default_nope_list = ["burpees"]
    workout_name_key = "workout name"
    length_key = "length"
    interval_key = "interval"
    rest_time_key = "rest time"
    workout_type_key = "workout type"
    nope_list_key = "nope list"

    def __init__(self, parent_widget: QWidget):
        super(WorkoutForm, self).__init__(title="Workout Parameters")
        self.parent_widget = parent_widget
        self.settings = QSettings(DEVELOPER, APPLICATION_NAME)
        self.workout_name_line_edit: QLineEdit = self.add_line_edit(label="Workout Name", placeholder_text="Untitled Workout")
        self.length_spin_box: QSpinBox = self.add_int_field(label="Workout length (minutes)")
        self.interval_spin_box: QSpinBox = self.add_int_field(label="Interval (seconds)")
        self.rest_time_spin_box: QSpinBox = self.add_int_field(label="Approximate Rest Time (seconds)")
        self.workout_type_combo_box: QComboBox = self.add_combo_box(label="Workout Type", items=WorkoutType.values())
        self.nope_list_line_edit: QLineEdit = self.add_line_edit(label="Nope List", placeholder_text="List exercises to avoid here")
        self.setup_ui()

    @property
    def interval(self) -> int:
        return self.interval_spin_box.value()

    @property
    def rest_time(self) -> int:
        return self.rest_time_spin_box.value()

    @property
    def length(self) -> int:
        return self.length_spin_box.value()

    @property
    def workout_type(self) -> WorkoutType:
        return WorkoutType.get_by_value(self.workout_type_combo_box.currentText())

    @property
    def workout_type_index(self) -> int:
        return self.workout_type_combo_box.currentIndex()

    @property
    def nope_list(self) -> list[str]:
        if self.nope_list_line_edit.text():
            return [x.strip() for x in self.nope_list_line_edit.text().split(",")]
        return []

    @property
    def workout_name(self) -> str:
        """Get workout name."""
        return self.workout_name_line_edit.text()

    @property
    def workout_name_snake_case(self) -> str:
        """Convert workout name to snake_case for filename."""
        name = self.workout_name.lower()
        # Replace non-alphanumeric with underscores
        name = re.sub(r'[^a-z0-9]+', '_', name)
        # Strip leading/trailing underscores
        return name.strip('_')

    def setup_ui(self):
        self.workout_name_line_edit.setText(self.settings.value(self.workout_name_key, ""))
        self.length_spin_box.setValue(self.settings.value(self.length_key, self.default_workout_length))
        self.interval_spin_box.setValue(self.settings.value(self.interval_key, self.default_interval_time))
        self.rest_time_spin_box.setValue(self.settings.value(self.rest_time_key, self.default_rest_time))
        self.workout_type_combo_box.setCurrentIndex(self.settings.value(self.workout_type_key, self.default_workout_type_index))
        nope_list_value = self.settings.value(self.nope_list_key, self.default_nope_list)
        self.nope_list_line_edit.setText(", ".join(nope_list_value))
        self.workout_name_line_edit.textChanged.connect(self._on_workout_name_changed)
        self.length_spin_box.valueChanged.connect(lambda: self.settings.setValue(self.length_key, self.length))
        self.interval_spin_box.valueChanged.connect(lambda: self.settings.setValue(self.interval_key, self.interval))
        self.rest_time_spin_box.valueChanged.connect(lambda: self.settings.setValue(self.rest_time_key, self.rest_time))
        self.workout_type_combo_box.currentIndexChanged.connect(lambda: self.settings.setValue(self.workout_type_key, self.workout_type_index))
        self.nope_list_line_edit.returnPressed.connect(lambda: self.settings.setValue(self.nope_list_key, self.nope_list))

    def _on_workout_name_changed(self):
        """Filter workout name input to only allow lowercase letters and underscores."""
        current_text = self.workout_name_line_edit.text()
        cursor_position = self.workout_name_line_edit.cursorPosition()

        # Convert to lowercase and replace invalid characters with underscores
        filtered_text = ""
        for char in current_text:
            if char.islower() or char == '_':
                filtered_text += char
            elif char.isupper():
                filtered_text += char.lower()
            elif char == ' ' or not char.isalnum():
                # Spaces and special characters become underscores
                if filtered_text and filtered_text[-1] != '_':  # Avoid consecutive underscores
                    filtered_text += '_'
            # Numbers are ignored (not added)

        # Update if changed
        if filtered_text != current_text:
            self.workout_name_line_edit.blockSignals(True)
            self.workout_name_line_edit.setText(filtered_text)
            self.workout_name_line_edit.setCursorPosition(min(cursor_position, len(filtered_text)))
            self.workout_name_line_edit.blockSignals(False)

        # Save to settings
        self.settings.setValue(self.workout_name_key, filtered_text)