from PySide6.QtWidgets import QWidget, QLineEdit
from widgets.form_widget import FormWidget
from widgets.generic_widget import GenericWidget


class WorkoutForm(FormWidget):
    default_workout_length = 30
    default_interval_time = 120
    default_rest_time = 30
    default_nope_list = "burpees"
    workout_types = [
        "cardio",
        "strength",
        "cardio/strength",
        "random"
    ]

    def __init__(self, parent_widget: QWidget):
        super(WorkoutForm, self).__init__(title="Workout Parameters")
        self.parent_widget = parent_widget
        self.length_spin_box: QSpinBox = self.add_int_field(label="Workout length (minutes)", default_value=self.default_workout_length)
        self.interval_spin_box: QSpinBox = self.add_int_field(label="Interval (seconds)", default_value=self.default_interval_time)
        self.rest_time_spin_box: QSpinBox = self.add_int_field(label="Rest Time (seconds)", default_value=self.default_rest_time)
        self.workout_type_combo_box: QComboBox = self.add_combo_box(label="Workout Type", items=self.workout_types, default_index=2)
        self.nope_list_line_edit: QLineEdit = self.add_line_edit(label="Nope List", default_value=self.default_nope_list, placeholder_text="List exercises to avoid here")

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
    def workout_type(self) -> str:
        return self.workout_type_combo_box.currentText()

    @property
    def nope_list(self) -> list[str]:
        if self.nope_list_line_edit.text():
            return [x.strip() for x in self.nope_list_line_edit.text().split(",")]
        return []