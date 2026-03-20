import logging
import re

from PySide6.QtWidgets import QWidget, QLineEdit, QCheckBox, QComboBox, QSpinBox, QGroupBox, QVBoxLayout, QGridLayout, QLabel, QFormLayout
from PySide6.QtCore import QSettings

from core import APPLICATION_NAME, DEVELOPER
from core.logging_utils import get_logger
from widgets.form_widget import FormWidget


LOGGER: logging.Logger = get_logger(name=__name__, level=logging.DEBUG)


class WorkoutForm(FormWidget):
    default_workout_length = 30
    default_interval_time = 120
    default_rest_time = 30
    default_selected_categories = ["cardio", "strength"]  # Default categories
    workout_name_key = "workout name"
    length_key = "length"
    interval_key = "interval"
    rest_time_key = "rest time"
    workout_structure_key = "workout structure"

    def __init__(self, parent_widget: QWidget):
        super(WorkoutForm, self).__init__(title="Workout Parameters")
        self.parent_widget = parent_widget
        self.settings = QSettings(DEVELOPER, APPLICATION_NAME)

        # Workout Properties group box
        workout_props_group = QGroupBox("Workout Properties")
        workout_props_layout = QFormLayout()

        # Create workout form fields
        self.workout_name_line_edit = QLineEdit(placeholderText="Untitled Workout")
        self.workout_name_line_edit.setToolTip("Name for this workout session (used when saving)")
        self.workout_name_line_edit.setMinimumWidth(300)
        workout_props_layout.addRow("Workout Name:", self.workout_name_line_edit)

        self.length_spin_box = QSpinBox()
        self.length_spin_box.setMinimum(0)
        self.length_spin_box.setMaximum(999)
        self.length_spin_box.setToolTip("Total duration of a single circuit in minutes")
        workout_props_layout.addRow("Circuit Length (minutes):", self.length_spin_box)

        self.workout_cycles_spin_box = QSpinBox()
        self.workout_cycles_spin_box.setMinimum(0)
        self.workout_cycles_spin_box.setMaximum(999)
        self.workout_cycles_spin_box.setToolTip("Number of times to repeat the circuit (total time = circuit length × cycles)")
        workout_props_layout.addRow("Workout Cycles:", self.workout_cycles_spin_box)

        self.interval_spin_box = QSpinBox()
        self.interval_spin_box.setMinimum(0)
        self.interval_spin_box.setMaximum(999)
        self.interval_spin_box.setToolTip("Duration of each exercise in seconds")
        workout_props_layout.addRow("Interval (seconds):", self.interval_spin_box)

        self.rest_time_spin_box = QSpinBox()
        self.rest_time_spin_box.setMinimum(0)
        self.rest_time_spin_box.setMaximum(999)
        self.rest_time_spin_box.setToolTip("Rest duration between exercises in seconds")
        workout_props_layout.addRow("Approximate Rest Time (seconds):", self.rest_time_spin_box)

        workout_props_group.setLayout(workout_props_layout)
        self.layout().addRow(workout_props_group)

        # Category checkboxes in a group box (read from workout data)
        self.category_checkboxes: dict[str, QCheckBox] = {}
        from robocross.workout_data import WorkoutData
        workout_data = WorkoutData()
        category_tooltips = {
            "cardio": "Include cardiovascular exercises (running, jumping, etc.)",
            "strength": "Include strength training exercises (weights, resistance, etc.)",
            "combat": "Include combat/martial arts exercises",
            "flexibility": "Include stretching and flexibility exercises"
        }

        # Create group box for exercise types with 2-column layout
        exercise_type_group = QGroupBox("Exercise Type")
        exercise_type_layout = QGridLayout()

        # Read categories from workout data (top-level keys in JSON)
        categories = sorted(workout_data.categories)
        for index, category in enumerate(categories):
            checkbox = QCheckBox(category.title())
            checkbox.setToolTip(category_tooltips.get(category, f"Include {category} exercises"))
            row = index // 2
            col = index % 2
            exercise_type_layout.addWidget(checkbox, row, col)
            self.category_checkboxes[category] = checkbox

        # Add Workout Structure combo-box at the bottom of the group box
        num_rows = (len(categories) + 1) // 2  # Number of rows used by checkboxes
        structure_label = QLabel("Workout Structure:")
        self.workout_structure_combo_box = QComboBox()
        self.workout_structure_combo_box.addItems(["Random", "Sequence"])
        self.workout_structure_combo_box.setToolTip("Random: shuffle exercises each time, Sequence: use exercises in order")
        exercise_type_layout.addWidget(structure_label, num_rows, 0)
        exercise_type_layout.addWidget(self.workout_structure_combo_box, num_rows, 1)

        exercise_type_group.setLayout(exercise_type_layout)
        self.layout().addRow(exercise_type_group)

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
    def workout_cycles(self) -> int:
        return self.workout_cycles_spin_box.value()

    @property
    def selected_categories(self) -> list[str]:
        """Return list of selected category names."""
        return [category for category, checkbox in self.category_checkboxes.items() if checkbox.isChecked()]

    @property
    def workout_structure(self) -> str:
        """Return 'Random' or 'Sequence'."""
        return self.workout_structure_combo_box.currentText()

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

    def _save_workout_name_to_settings(self):
        """Save workout name to settings."""
        workout_name = self.workout_name_line_edit.text()
        self.settings.setValue(self.workout_name_key, workout_name)
        LOGGER.debug(f"Saved workout name to settings: {workout_name}")

    def setup_ui(self):
        self.workout_name_line_edit.setText(self.settings.value(self.workout_name_key, ""))
        # Save workout name to settings when editing is finished (return pressed or focus lost)
        self.workout_name_line_edit.editingFinished.connect(self._save_workout_name_to_settings)
        self.length_spin_box.setValue(self.settings.value(self.length_key, self.default_workout_length))
        self.interval_spin_box.setValue(self.settings.value(self.interval_key, self.default_interval_time))
        self.rest_time_spin_box.setValue(self.settings.value(self.rest_time_key, self.default_rest_time))
        self.workout_cycles_spin_box.setValue(1)  # Always defaults to 1 (NOT saved to settings)

        # Initialize category checkboxes from settings
        for category, checkbox in self.category_checkboxes.items():
            # Default to checked if in default_selected_categories
            default_checked = category in self.default_selected_categories
            is_checked = self.settings.value(f"category_{category}", default_checked, type=bool)
            checkbox.setChecked(is_checked)
            checkbox.stateChanged.connect(
                lambda state, cat=category: self.settings.setValue(f"category_{cat}", self.category_checkboxes[cat].isChecked())
            )

        # Initialize workout structure combo-box
        structure_value = self.settings.value(self.workout_structure_key, "Random")
        structure_index = 0 if structure_value == "Random" else 1
        self.workout_structure_combo_box.setCurrentIndex(structure_index)

        # Connect signals
        self.workout_name_line_edit.textChanged.connect(self._on_workout_name_changed)
        self.length_spin_box.valueChanged.connect(lambda: self.settings.setValue(self.length_key, self.length))
        self.interval_spin_box.valueChanged.connect(lambda: self.settings.setValue(self.interval_key, self.interval))
        self.rest_time_spin_box.valueChanged.connect(lambda: self.settings.setValue(self.rest_time_key, self.rest_time))
        self.workout_structure_combo_box.currentIndexChanged.connect(
            lambda: self.settings.setValue(self.workout_structure_key, self.workout_structure)
        )

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