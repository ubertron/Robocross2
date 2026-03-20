"""Single editable row in the workout editor table."""

from PySide6.QtWidgets import QComboBox, QPushButton, QMenu, QSizePolicy
from PySide6.QtCore import Signal, Qt

from core.core_enums import Alignment
from robocross.workout import Workout
from widgets.generic_widget import GenericWidget


class WorkoutEditorRow(GenericWidget):
    """Single editable workout row with exercise selector, duration, rest time, and delete button."""

    # Signals
    delete_requested = Signal(object)  # emits self when delete clicked
    insert_above_requested = Signal(object)  # emits self when insert above requested
    insert_below_requested = Signal(object)  # emits self when insert below requested
    data_changed = Signal()  # emitted when any field changes

    def __init__(self, workout: Workout, available_exercises: list[str],
                 rest_seconds: int = 30, exercises_by_category: dict = None, parent=None):
        super().__init__(alignment=Alignment.horizontal, parent=parent)
        self.workout = workout
        self.available_exercises = available_exercises
        self.exercises_by_category = exercises_by_category or {'cardio': [], 'strength': []}
        self.rest_seconds = rest_seconds
        self.setup_ui()

    def setup_ui(self):
        """Create row widgets: exercise button, duration button, rest button, delete button."""
        # Set layout alignment to center vertically
        self.layout().setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Add spacing between buttons
        self.layout().setSpacing(4)

        # Fixed height for all widgets to ensure alignment
        widget_height = 30

        # Exercise button (40% width) - opens picker dialog
        self.exercise_button = self.add_widget(QPushButton())
        self.update_exercise_button_text()
        self.exercise_button.clicked.connect(self.on_exercise_button_clicked)
        self.exercise_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.exercise_button.setFixedHeight(widget_height)

        # Duration button (25% width)
        self.duration_button = self.add_widget(QPushButton())
        self.update_duration_button_text()
        self.duration_button.clicked.connect(self.on_duration_clicked)
        self.duration_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.duration_button.setFixedHeight(widget_height)

        # Rest button (25% width)
        self.rest_button = self.add_widget(QPushButton())
        self.update_rest_button_text()
        self.rest_button.clicked.connect(self.on_rest_clicked)
        self.rest_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.rest_button.setFixedHeight(widget_height)

        # Delete button (10% width)
        self.delete_button = self.add_widget(QPushButton("X"))
        self.delete_button.clicked.connect(
            lambda: self.delete_requested.emit(self)
        )
        self.delete_button.setMaximumWidth(40)
        self.delete_button.setFixedHeight(widget_height)
        self.delete_button.setStyleSheet("color: red; font-weight: bold;")

    def update_exercise_button_text(self):
        """Update exercise button text with nicely formatted name."""
        nice_name = self.workout.name.replace('_', ' ').title()
        self.exercise_button.setText(nice_name)
        self.update_exercise_button_color()

    def update_exercise_button_color(self):
        """Update exercise button background color based on category."""
        from robocross import get_category_color, get_contrast_text_color

        category = self.workout.aerobic_type.name
        bg_color = get_category_color(category)
        text_color = get_contrast_text_color(bg_color)

        self.exercise_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid #555;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {bg_color};
                border: 2px solid #000;
            }}
        """)

    def update_duration_button_text(self):
        """Update duration button text to show human-readable time."""
        from core.time_utils import time_nice
        self.duration_button.setText(time_nice(self.workout.time))

    def update_rest_button_text(self):
        """Update rest button text to show human-readable time."""
        from core.time_utils import time_nice
        self.rest_button.setText(time_nice(self.rest_seconds))

    def on_duration_clicked(self):
        """Open duration dialog to edit exercise duration."""
        from robocross.duration_dialog import DurationDialog
        new_seconds, ok = DurationDialog.get_duration(
            self, self.workout.time
        )
        if ok:
            self.workout.time = new_seconds
            self.update_duration_button_text()
            self.data_changed.emit()

    def on_rest_clicked(self):
        """Open duration dialog to edit rest time."""
        from robocross.duration_dialog import DurationDialog
        new_seconds, ok = DurationDialog.get_duration(
            self, self.rest_seconds
        )
        if ok:
            self.rest_seconds = new_seconds
            self.update_rest_button_text()
            self.data_changed.emit()

    def on_exercise_button_clicked(self):
        """Open exercise picker dialog when button is clicked."""
        from robocross.exercise_picker_dialog import ExercisePickerDialog

        exercise_name, ok = ExercisePickerDialog.get_exercise(
            self.exercises_by_category,
            self.workout.name,
            self
        )

        if ok and exercise_name:
            # Update workout with selected exercise
            from robocross.workout_data import WorkoutData
            workout_data = WorkoutData()
            new_workout = next(
                (w for w in workout_data.workouts if w.name == exercise_name),
                None
            )
            if new_workout:
                # Preserve time but update other workout fields
                old_time = self.workout.time
                self.workout = new_workout
                self.workout.time = old_time
                self.update_exercise_button_text()
                self.data_changed.emit()

    def contextMenuEvent(self, event):
        """Show right-click context menu with Insert Above/Below/Delete options."""
        menu = QMenu(self)
        insert_above = menu.addAction("Insert Above")
        insert_below = menu.addAction("Insert Below")
        menu.addSeparator()
        delete_action = menu.addAction("Delete")

        action = menu.exec(event.globalPos())

        if action == insert_above:
            self.insert_above_requested.emit(self)
        elif action == insert_below:
            self.insert_below_requested.emit(self)
        elif action == delete_action:
            self.delete_requested.emit(self)

    def get_workout_with_rest(self) -> tuple[Workout, int]:
        """
        Get workout and rest time from this row.

        Returns:
            tuple[Workout, int]: (workout object, rest time in seconds)
        """
        return self.workout, self.rest_seconds
