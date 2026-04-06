"""Scrollable editable table of workout items."""

from PySide6.QtWidgets import QLabel, QSizePolicy, QFrame, QMenu
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
    add_exercise_requested = Signal()  # emitted when user requests to add exercise via context menu

    def __init__(self, available_exercises: list[str], exercises_by_category: dict = None, parent=None):
        super().__init__(alignment=Alignment.vertical, parent=parent)
        self.available_exercises = available_exercises
        self.exercises_by_category = exercises_by_category or {'cardio': [], 'strength': []}
        self.rows: list[WorkoutEditorRow] = []
        self.default_rest_time = 30
        self.workout_name = ""
        self.copied_duration = None  # Stored duration value for copy/paste
        self.copied_rest_time = None  # Stored rest time value for copy/paste
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
        exercise_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        duration_label = header.add_widget(QLabel("Duration"))
        duration_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        duration_label.setStyleSheet("font-weight: bold;")
        duration_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        rest_label = header.add_widget(QLabel("Rest Time"))
        rest_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        rest_label.setStyleSheet("font-weight: bold;")
        rest_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

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
                'total_calories': 0,
                'equipment': []
            }

        # Calculate stats
        total_time = sum(row.workout.time for row in self.rows)
        total_rest = sum(row.rest_seconds for row in self.rows)
        num_exercises = len(self.rows)

        # Collect unique equipment from all workouts
        equipment_set = set()
        for row in self.rows:
            if row.workout.equipment:
                for equip in row.workout.equipment:
                    equipment_set.add(equip)

        # Convert to sorted list of equipment names
        equipment_list = sorted([eq.name.replace('_', ' ').title() for eq in equipment_set])

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
            'total_calories': total_calories,
            'equipment': equipment_list
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
        row.move_up_requested.connect(self.on_move_up)
        row.move_down_requested.connect(self.on_move_down)
        row.data_changed.connect(self.on_data_changed)

        # Connect time copy/paste/apply signals
        row.copy_duration_requested.connect(self.on_copy_duration)
        row.paste_duration_requested.connect(self.on_paste_duration)
        row.apply_duration_to_all_requested.connect(self.on_apply_duration_to_all)
        row.copy_rest_requested.connect(self.on_copy_rest)
        row.paste_rest_requested.connect(self.on_paste_rest)
        row.apply_rest_to_all_requested.connect(self.on_apply_rest_to_all)

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
            self.widget.layout().insertWidget(index + 1, row)  # +1 for header row

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

    def shuffle_rows(self, warm_up: bool = False, cool_down: bool = False, workout_structure: str = "Random"):
        """Randomize the order of workout rows, preserving warm up/cool down if active.

        In Random mode: shuffles exercises randomly
        In Sequence mode: re-randomizes the category pattern while keeping same exercises
        """
        import random

        if len(self.rows) <= 1:
            return  # Nothing to shuffle

        # Determine which rows to shuffle
        first_row = None
        last_row = None
        middle_rows = self.rows[:]

        if warm_up and len(self.rows) > 0:
            first_row = middle_rows.pop(0)  # Preserve first row

        if cool_down and len(middle_rows) > 0:
            last_row = middle_rows.pop()  # Preserve last row

        if workout_structure == "Sequence":
            # Sequence mode: group by category, randomize pattern, re-interleave
            middle_rows = self._shuffle_sequence_mode(middle_rows)
        else:
            # Random mode: shuffle exercises randomly
            if middle_rows:
                random.shuffle(middle_rows)

        # Rebuild the full list
        new_order = []
        if first_row:
            new_order.append(first_row)
        new_order.extend(middle_rows)
        if last_row:
            new_order.append(last_row)

        self.rows = new_order

        # Remove all rows from layout (but keep them in memory)
        for row in self.rows:
            self.widget.layout().removeWidget(row)

        # Re-add rows in new shuffled order
        for i, row in enumerate(self.rows):
            # Insert at position i + 1 (skip header row at position 0)
            self.widget.layout().insertWidget(i + 1, row)

        # Emit signal that workout list changed
        self.workout_list_changed.emit()

    def _shuffle_sequence_mode(self, rows: list):
        """Shuffle rows in sequence mode: re-randomize category pattern while keeping same exercises.

        Args:
            rows: List of WorkoutRow widgets to shuffle

        Returns:
            List of WorkoutRow widgets in new sequence order
        """
        import random
        from collections import defaultdict

        if not rows:
            return rows

        # Group exercises by category
        by_category = defaultdict(list)
        for row in rows:
            # Get the workout from the row
            workout = row.workout
            if workout:
                category = workout.aerobic_type.name
                by_category[category].append(row)

        # Get unique categories and randomize their order
        categories = list(by_category.keys())
        random.shuffle(categories)

        # Rebuild exercise list by cycling through randomized categories
        new_order = []
        max_iterations = len(rows)  # Safety limit
        category_indices = {cat: 0 for cat in categories}

        for _ in range(max_iterations):
            for category in categories:
                if category_indices[category] < len(by_category[category]):
                    new_order.append(by_category[category][category_indices[category]])
                    category_indices[category] += 1

            # Check if all exercises have been added
            if len(new_order) >= len(rows):
                break

        return new_order[:len(rows)]  # Ensure we return exactly the right number

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

    def on_move_up(self, row: WorkoutEditorRow):
        """Move row up one position in the list."""
        if row not in self.rows:
            return

        index = self.rows.index(row)
        if index == 0:
            return  # Already at top

        # Swap with previous row in list
        self.rows[index], self.rows[index - 1] = self.rows[index - 1], self.rows[index]

        # Update layout positions: row is now at index - 1, layout position is (index - 1) + 1 = index
        layout = self.widget.layout()
        layout.removeWidget(row)
        layout.insertWidget(index, row)  # + 1 for header offset

        self.on_data_changed()

    def on_move_down(self, row: WorkoutEditorRow):
        """Move row down one position in the list."""
        if row not in self.rows:
            return

        index = self.rows.index(row)
        if index >= len(self.rows) - 1:
            return  # Already at bottom

        # Swap with next row in list
        self.rows[index], self.rows[index + 1] = self.rows[index + 1], self.rows[index]

        # Update layout positions: row is now at index + 1, layout position is (index + 1) + 1 = index + 2
        layout = self.widget.layout()
        layout.removeWidget(row)
        layout.insertWidget(index + 2, row)  # + 1 for header, + 1 for new position

        self.on_data_changed()

    def reorder_row(self, dragged_row: WorkoutEditorRow, target_index: int):
        """
        Reorder rows via drag and drop.

        Args:
            dragged_row: The row being dragged
            target_index: The index where it should be dropped
        """
        if dragged_row not in self.rows:
            return

        current_index = self.rows.index(dragged_row)
        if current_index == target_index:
            return  # No change

        # Remove from current position
        self.rows.pop(current_index)

        # Adjust target index if dragging down
        if current_index < target_index:
            target_index -= 1

        # Insert at new position
        self.rows.insert(target_index, dragged_row)

        # Update layout
        layout = self.widget.layout()
        layout.removeWidget(dragged_row)
        layout.insertWidget(target_index + 1, dragged_row)  # + 1 for header

        self.on_data_changed()

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

    def contextMenuEvent(self, event):
        """Show context menu when right-clicking in empty space."""
        # Check if the click is on the widget (empty space) and not on a row
        # Get the widget under the cursor
        widget_at_pos = self.widget.childAt(event.pos())

        # If widget_at_pos is None or the widget itself (not a row), show add menu
        if widget_at_pos is None or widget_at_pos == self.widget:
            menu = QMenu(self)
            add_action = menu.addAction("Add Exercise")

            action = menu.exec(event.globalPos())

            if action == add_action:
                self.add_exercise_requested.emit()
        else:
            # Let the event propagate to rows
            super().contextMenuEvent(event)

    def on_copy_duration(self, row: WorkoutEditorRow):
        """Copy duration value from row."""
        self.copied_duration = row.workout.time
        from core import LOGGER
        LOGGER.info(f"Copied duration: {self.copied_duration} seconds")

    def on_paste_duration(self, row: WorkoutEditorRow):
        """Paste duration value to row."""
        if self.copied_duration is not None:
            row.workout.time = self.copied_duration
            row.update_duration_button_text()
            row.data_changed.emit()
            from core import LOGGER
            LOGGER.info(f"Pasted duration: {self.copied_duration} seconds")

    def on_apply_duration_to_all(self, row: WorkoutEditorRow):
        """Apply duration from current row to all other rows."""
        duration = row.workout.time
        for other_row in self.rows:
            if other_row != row:
                other_row.workout.time = duration
                other_row.update_duration_button_text()
        self.on_data_changed()
        from core import LOGGER
        LOGGER.info(f"Applied duration {duration} seconds to all rows")

    def on_copy_rest(self, row: WorkoutEditorRow):
        """Copy rest time value from row."""
        self.copied_rest_time = row.rest_seconds
        from core import LOGGER
        LOGGER.info(f"Copied rest time: {self.copied_rest_time} seconds")

    def on_paste_rest(self, row: WorkoutEditorRow):
        """Paste rest time value to row."""
        if self.copied_rest_time is not None:
            row.rest_seconds = self.copied_rest_time
            row.update_rest_button_text()
            row.data_changed.emit()
            from core import LOGGER
            LOGGER.info(f"Pasted rest time: {self.copied_rest_time} seconds")

    def on_apply_rest_to_all(self, row: WorkoutEditorRow):
        """Apply rest time from current row to all other rows."""
        rest_time = row.rest_seconds
        for other_row in self.rows:
            if other_row != row:
                other_row.rest_seconds = rest_time
                other_row.update_rest_button_text()
        self.on_data_changed()
        from core import LOGGER
        LOGGER.info(f"Applied rest time {rest_time} seconds to all rows")
