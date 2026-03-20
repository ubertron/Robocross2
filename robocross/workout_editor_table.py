"""Scrollable editable table of workout items."""

from PySide6.QtWidgets import QLabel, QSizePolicy, QFrame
from PySide6.QtCore import Signal, Qt

from core.core_enums import Alignment
from core import time_utils
from robocross.workout import Workout
from robocross.workout_editor_row import WorkoutEditorRow
from widgets.generic_widget import GenericWidget
from widgets.scroll_widget import ScrollWidget


class WorkoutEditorTable(ScrollWidget):
    """Scrollable editable table of workout items."""

    # Signals
    workout_list_changed = Signal()  # emitted when workout list is modified

    def __init__(self, available_exercises: list[str], exercises_by_category: dict = None, parent=None):
        super().__init__(alignment=Alignment.vertical, parent=parent)
        self.available_exercises = available_exercises
        self.exercises_by_category = exercises_by_category or {'cardio': [], 'strength': []}
        self.rows: list[WorkoutEditorRow] = []
        self.default_rest_time = 30
        self.workout_name = ""
        self.setup_ui()

    def setup_ui(self):
        """Add header row with column labels."""
        # Reduce spacing between rows
        self.widget.layout().setSpacing(2)
        self.widget.layout().setContentsMargins(0, 0, 0, 0)

        # Header row
        header = self.widget.add_widget(
            GenericWidget(alignment=Alignment.horizontal)
        )

        # Header labels with same proportions as row widgets
        exercise_label = header.add_widget(QLabel("Exercise"))
        exercise_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        exercise_label.setStyleSheet("font-weight: bold;")

        duration_label = header.add_widget(QLabel("Duration"))
        duration_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        duration_label.setStyleSheet("font-weight: bold;")

        rest_label = header.add_widget(QLabel("Rest Time"))
        rest_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        rest_label.setStyleSheet("font-weight: bold;")

        delete_label = header.add_widget(QLabel(""))
        delete_label.setMaximumWidth(40)

        # Add stretch at end to push rows to top
        self.widget.add_stretch()

    def get_summary_data(self) -> dict:
        """Get summary data for the workout."""
        if not self.rows:
            return {
                'workout_name': self.workout_name,
                'total_time': 0,
                'total_rest': 0,
                'num_exercises': 0,
                'total_calories': 0
            }

        # Calculate stats
        total_time = sum(row.workout.time for row in self.rows)
        total_rest = sum(row.rest_seconds for row in self.rows)
        num_exercises = len(self.rows)

        # Calculate total calories
        from robocross.workout_data import WorkoutData
        workout_data = WorkoutData()
        total_calories = 0
        for row in self.rows:
            energy = 0

            # First try to use energy from the workout object itself
            if row.workout.energy is not None:
                energy = row.workout.energy
            else:
                # Fallback: get energy from workout database
                exercise_name = row.workout.name
                if exercise_name in workout_data.data:
                    energy = workout_data.data[exercise_name].get("energy", 0)
                else:
                    # Last resort: estimate based on intensity
                    intensity_energy = {"high": 13, "medium": 9, "low": 6}
                    energy = intensity_energy.get(row.workout.intensity.name, 9)

            # energy is calories per minute, workout time is in seconds
            calories = energy * (row.workout.time / 60.0)
            total_calories += calories

        return {
            'workout_name': self.workout_name,
            'total_time': total_time,
            'total_rest': total_rest,
            'num_exercises': num_exercises,
            'total_calories': total_calories
        }

    def add_row(self, workout: Workout, rest_seconds: int = None,
                index: int = -1):
        """
        Add workout row at specified index.

        Args:
            workout: Workout object for this row
            rest_seconds: Rest time after this workout (uses default if None)
            index: Insert position (-1 = append at end)
        """
        if rest_seconds is None:
            rest_seconds = self.default_rest_time

        row = WorkoutEditorRow(workout, self.available_exercises, rest_seconds, self.exercises_by_category)

        # Connect row signals
        row.delete_requested.connect(self.on_row_delete)
        row.insert_above_requested.connect(self.on_insert_above)
        row.insert_below_requested.connect(self.on_insert_below)
        row.data_changed.connect(self.on_data_changed)

        # Insert at correct position
        if index == -1 or index >= len(self.rows):
            # Append at end
            self.rows.append(row)
            # Insert before stretch (which is last item in layout)
            self.widget.layout().insertWidget(
                self.widget.layout().count() - 1, row
            )
        else:
            # Insert at specific index
            self.rows.insert(index, row)
            self.widget.layout().insertWidget(index + 2, row)  # +2 for summary and header

        # Explicitly show the row
        row.show()

        self.on_data_changed()

    def on_data_changed(self):
        """Handle data change - emit signal."""
        self.workout_list_changed.emit()

    def remove_row(self, row: WorkoutEditorRow):
        """Remove row from table."""
        if row in self.rows:
            self.rows.remove(row)
            self.widget.layout().removeWidget(row)
            row.deleteLater()
            self.on_data_changed()

    def clear_rows(self):
        """Remove all workout rows from table."""
        for row in self.rows[:]:  # Copy list for safe iteration
            self.remove_row(row)

    def set_workout_list(self, workouts: list[Workout], rest_time: int = 30, workout_name: str = ""):
        """
        Populate table with list of workouts.

        Args:
            workouts: List of Workout objects
            rest_time: Default rest time for all workouts
            workout_name: Name of the workout (optional)
        """
        from robocross import REST_PERIOD

        self.clear_rows()
        self.default_rest_time = rest_time
        if workout_name:
            self.workout_name = workout_name

        # Filter out REST_PERIOD items and extract rest times
        for i, workout in enumerate(workouts):
            # Skip REST_PERIOD items - they're handled by rest_time per row
            if workout.name == REST_PERIOD:
                continue

            # Check if next item is a rest period to get specific rest time
            current_rest = rest_time
            if i + 1 < len(workouts) and workouts[i + 1].name == REST_PERIOD:
                current_rest = workouts[i + 1].time

            self.add_row(workout, current_rest)

    def get_workout_list(self) -> tuple[list[Workout], list[int]]:
        """
        Get current workout list and rest times from all rows.

        Returns:
            tuple[list[Workout], list[int]]: (workouts, rest_times)
        """
        workouts = []
        rest_times = []
        for row in self.rows:
            workout, rest = row.get_workout_with_rest()
            workouts.append(workout)
            rest_times.append(rest)
        return workouts, rest_times

    def on_row_delete(self, row: WorkoutEditorRow):
        """Handle delete button/context menu action."""
        self.remove_row(row)

    def on_insert_above(self, row: WorkoutEditorRow):
        """Insert blank row above target row."""
        index = self.rows.index(row)
        default_workout = self._create_default_workout()
        self.add_row(default_workout, self.default_rest_time, index)

    def on_insert_below(self, row: WorkoutEditorRow):
        """Insert blank row below target row."""
        index = self.rows.index(row)
        default_workout = self._create_default_workout()
        self.add_row(default_workout, self.default_rest_time, index + 1)

    def _create_default_workout(self) -> Workout:
        """
        Create default workout for new rows.

        Returns:
            Workout: New workout with default values
        """
        from robocross.robocross_enums import Intensity, AerobicType

        first_exercise = (self.available_exercises[0]
                         if self.available_exercises else "unknown")

        return Workout(
            name=first_exercise,
            description="",
            equipment=[],
            intensity=Intensity.medium,
            aerobic_type=AerobicType.strength,
            target=[],
            time=45,
            sub_workouts=None
        )
