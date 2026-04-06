"""PySide ui for Robocross2."""
from __future__ import annotations

import getpass
import json
import logging
import re
import sys
import time

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QSettings, QSize
from PySide6.QtGui import QFont, QPixmap, QClipboard
from PySide6.QtWidgets import QTabWidget, QSplashScreen, QFileDialog, QApplication

from core import DEVELOPER, logging_utils, splash_screen_manager, SANS_SERIF_FONT, CODE_FONT
from core.version_info import VersionInfo
from core import time_utils
from core.core_paths import image_path, DATA_DIR
from robocross import APP_NAME, REST_PERIOD
from robocross.parameters_widget import ParametersWidget
from robocross.routine import Routine
from robocross.viewer_v2 import ViewerV2
from robocross.workout import Workout
from robocross.robocross_enums import Equipment, Intensity, AerobicType, Target
from widgets.generic_widget import GenericWidget
from widgets.exercise_editor import ExerciseEditor

LOG_PATH = Path(__file__).parents[1].joinpath("logs/workouts.log")
FILE_HANDLER = logging_utils.FileHandler(path=LOG_PATH, level=logging.DEBUG)
STREAM_HANDLER = logging_utils.StreamHandler(level=logging.INFO)
LOGGER = logging_utils.get_logger(name=__name__, level=logging.INFO, handlers=[FILE_HANDLER, STREAM_HANDLER])
VERSIONS = (
    VersionInfo(name=APP_NAME, version='1.0', codename='Alpha', info='Initial release'),
    VersionInfo(name=APP_NAME, version='2.0', codename='Colt Seavers', info='Revamp'),
    VersionInfo(name=APP_NAME, version='2.0.1', codename='MacGyver', info='Icon buttons, save/load sessions, sub-workouts'),
    VersionInfo(name=APP_NAME, version='2.0.2', codename='Michael Knight', info='Full workout editor with editable table'),
    VersionInfo(name=APP_NAME, version='2.0.3', codename='Mr. Miyagi', info='Combat & flexibility categories, Random/Sequence modes'),
    VersionInfo(name=APP_NAME, version='2.0.4', codename='Stringfellow Hawk', info='Player v2 with workout images'),
    VersionInfo(name=APP_NAME, version='2.0.5', codename='Poncharello', info='Exercise Editor'),
)
SPLASH_SCREEN = image_path("splashscreen_640.png")
ROBOCROSS_LOGO = image_path("robocross.png")


def parse_name_nicely(name: str) -> str:
    """Parse workout name to be human-readable.

    Handles:
    - snake_case -> Snake Case
    - camelCase -> Camel Case
    - PascalCase -> Pascal Case
    - kebab-case -> Kebab Case
    """
    # Replace underscores and hyphens with spaces
    name = name.replace('_', ' ').replace('-', ' ')

    # Insert space before capital letters (for camelCase/PascalCase)
    name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)

    # Capitalize each word
    return ' '.join(word.capitalize() for word in name.split())


class Robocross(GenericWidget):
    app_size_key = "app_size"
    last_workout_path_key = "last_workout_path"
    default_size = QSize(800, 400)
    minimum_width = 640

    def __init__(self, parent=None):
        super(Robocross, self).__init__(title=VERSIONS[-1].title, parent=parent)
        self.settings = QSettings(DEVELOPER, APP_NAME)
        self.tab_widget = self.add_widget(QTabWidget())
        self.parameters_widget: ParametersWidget = ParametersWidget()
        self.form = self.parameters_widget.form
        self.tab_widget.addTab(self.parameters_widget, 'Editor')
        self.viewer: ViewerV2 = ViewerV2()
        self.tab_widget.addTab(self.viewer, 'Player')
        self.exercise_editor = ExerciseEditor()
        self.tab_widget.addTab(self.exercise_editor, 'Exercise')
        self.rest_time = 0
        self.routine = None
        self.info = ""
        self.workout_list = []
        self.parameters_widget.info = "Build your workout..."
        self.app_size = self.settings.value(self.app_size_key, self.default_size)
        self.setup_ui()

    def setup_ui(self):
        self.parameters_widget.new_workout_clicked.connect(self.new_workout_clicked)
        self.parameters_widget.load_button_clicked.connect(self.load_button_clicked)
        self.parameters_widget.save_button_clicked.connect(self.save_button_clicked)
        self.parameters_widget.build_button_clicked.connect(self.build_button_clicked)
        self.parameters_widget.add_exercise_clicked.connect(self.add_exercise_button_clicked)
        self.parameters_widget.copy_to_clipboard_clicked.connect(self.copy_to_clipboard_button_clicked)
        self.parameters_widget.workout_name_changed.connect(self.on_workout_name_changed)
        self.parameters_widget.workout_cycles_changed.connect(self.on_workout_cycles_changed)
        self.parameters_widget.editor_table.workout_list_changed.connect(self.on_workout_list_changed)
        self.parameters_widget.editor_table.add_exercise_requested.connect(self.add_exercise_button_clicked)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.setMinimumWidth(self.minimum_width)
        # ViewerV2 doesn't have separate play/pause buttons on stopwatch - they're in the timer row
        # ViewerV2 doesn't have scroll_widget
        self.resize(self.app_size)

        # Auto-load the last workout if available
        self._auto_load_last_workout()

    @property
    def app_size(self) -> QSize:
        return self._app_size

    @app_size.setter
    def app_size(self, value: QSize):
        self._app_size = value
        self.settings.setValue(self.app_size_key, value)
        # ViewerV2 uses fixed font sizes in its setup_ui() method
        # Dynamic font resizing is not implemented in v2

    @property
    def date_time_string(self) -> str:
        return datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    @property
    def equipment(self) -> list[Equipment]:
        equipment = list({x.name.replace('_', ' ') for y in self.workout_list \
                          for x in y.equipment if x is not None})
        equipment.sort(key=lambda x: x.lower())
        return equipment

    @property
    def info(self) -> str:
        return self._info

    @info.setter
    def info(self, info: str) -> None:
        self._info = info

    @property
    def rest_time(self) -> int:
        return self._rest_time

    @rest_time.setter
    def rest_time(self, rest_time: int) -> None:
        self._rest_time = rest_time

    @property
    def routine(self) -> Routine | None:
        return self._routine

    @routine.setter
    def routine(self, routine: Routine | None):
        self._routine = routine
        workout_list = routine.get_workout_list() if routine else []
        self.workout_list = workout_list
        if routine:
            self.rest_time = routine.rest_time
        self.viewer.info = 'create a workout'

    @property
    def user(self) -> str:
        return getpass.getuser()

    @property
    def workout_list(self) -> list[Workout]:
        return self._workout_list

    @workout_list.setter
    def workout_list(self, workout_list: list[Workout]):
        self._workout_list = workout_list
        self.viewer.workout_list = workout_list

    @property
    def workout_report(self) -> str:
        report = '\n'.join(f"{x.name.title()}  ({time_utils.time_nice(self.form.interval)})" for x in self.workout_list if x.name != REST_PERIOD)
        equipment = ', '.join(self.equipment)
        return (
            f"Workout time: {time_utils.time_nice(self.form.length * 60)}\n"
            f"Rest time: {time_utils.time_nice(self.rest_time)}\n"
            f"Equipment: {equipment}\n\n"
            f"Workout items:\n{report}"
        )

    def _auto_load_last_workout(self):
        """Auto-load the last opened workout on startup."""
        last_workout_path = self.settings.value(self.last_workout_path_key)
        LOGGER.info(f"Attempting auto-load. Last workout path from settings: {last_workout_path}")

        if last_workout_path:
            workout_path = Path(last_workout_path)
            if workout_path.exists():
                LOGGER.info(f"Auto-loading last workout: {workout_path}")
                self._load_workout_from_file(str(workout_path), show_info=True)
            else:
                LOGGER.warning(f"Last workout path not found: {workout_path}")
        else:
            LOGGER.info("No last workout path found in settings")

    def _save_temp_workout(self):
        """Save the current workout to a temporary file for auto-loading."""
        if not self.workout_list:
            return

        # Create data directory if it doesn't exist
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Use a fixed temp file name
        temp_file_path = DATA_DIR / "_last_workout_temp.json"

        # Save the actual workout list
        workouts_data = []
        for workout in self.workout_list:
            workout_dict = {
                "name": workout.name,
                "description": workout.description,
                "equipment": [eq.name for eq in workout.equipment] if workout.equipment else [],
                "intensity": workout.intensity.name,
                "aerobic_type": workout.aerobic_type.name,
                "target": [t.name for t in workout.target if t is not None],
                "time": workout.time,
                "sub_workouts": workout.sub_workouts
            }
            workouts_data.append(workout_dict)

        session_data = {
            "workout_name": self.form.workout_name,  # NEW: Save workout name for auto-load
            "workout_cycles": self.form.workout_cycles,  # NEW: Save circuit cycles
            "workouts": workouts_data,
            "rest_time": self.rest_time,
            "saved_at": self.date_time_string
        }

        with open(temp_file_path, 'w') as f:
            json.dump(session_data, f, indent=4)

        # Save this as the last opened workout
        self.settings.setValue(self.last_workout_path_key, str(temp_file_path))
        LOGGER.debug(f"Temp workout saved to: {temp_file_path}")

    def new_workout_clicked(self):
        """Reset all parameters to start a new workout."""
        # Reset form to default values via the actual widgets
        self.form.interval_spin_box.setValue(45)
        self.form.length_spin_box.setValue(10)
        self.form.rest_time_spin_box.setValue(30)
        self.form.workout_name_line_edit.setText("")

        # Check all equipment checkboxes (enable all)
        for checkbox in self.parameters_widget.equipment_check_boxes:
            checkbox.setChecked(True)

        # Clear editor table
        self.parameters_widget.editor_table.clear_rows()
        self.parameters_widget.editor_table.workout_name = ""
        self.parameters_widget.update_summary()

        # Clear the workout list
        self.routine = None
        self.workout_list = []

        # Reset viewer
        # ViewerV2 doesn't have stopwatch play/pause buttons or scroll_widget
        self.viewer.workout_name = "Untitled Workout"

        # Update info
        self.parameters_widget.info = "New workout started. Configure parameters and click Build."
        LOGGER.info("New workout started - parameters reset")

    def build_button_clicked(self):
        """Create the routine and populate editor table."""
        from PySide6.QtWidgets import QProgressDialog
        from PySide6.QtCore import Qt

        if self.parameters_widget.zero_equipment:
            self.parameters_widget.info = "No equipment selected."
        else:
            # Show progress dialog
            progress = QProgressDialog("Building workout...", None, 0, 0, self)
            progress.setWindowTitle("Please Wait")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            progress.setCancelButton(None)
            progress.setValue(0)
            progress.show()

            # Process events to show the dialog
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()

            try:
                self.routine = Routine(
                    interval=self.form.interval,
                    workout_length=self.form.length,
                    rest_time=self.form.rest_time,
                    equipment_filter=self.parameters_widget.equipment_filter,
                    selected_categories=self.form.selected_categories,
                    workout_structure=self.form.workout_structure,
                    category_weights=self.form.category_weights,
                    warm_up=self.form.warm_up,
                    cool_down=self.form.cool_down,
                    target_filter=self.form.selected_targets,
                )

                # Validate that the combination yields results
                if not self.workout_list:
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.warning(
                        self,
                        "No Workouts Found",
                        "The current combination of Exercise Types and Exercise Targets doesn't yield any valid workouts.\n\n"
                        "Please try:\n"
                        "• Selecting different exercise types\n"
                        "• Choosing different exercise targets\n"
                        "• Checking 'All' in Exercise Targets\n"
                        "• Adjusting equipment filters"
                    )
                    progress.close()
                    return

                if self.workout_list:
                    # Populate editor table
                    self.parameters_widget.set_workout_list(
                        self.workout_list,
                        self.form.rest_time,
                        self.form.workout_name
                    )

                    # ViewerV2 doesn't have stopwatch buttons or scroll_widget
                    # Display is automatically updated by update_display() call in workout_list setter

                    self.viewer.workout_name = self.form.workout_name or "New Workout"
                    self.viewer.workout_cycles = self.form.workout_cycles  # NEW: Set circuit cycles on viewer

                    LOGGER.info(self.workout_report)

                    # Save the built workout to a temp file so it can be auto-loaded
                    self._save_temp_workout()
                else:
                    self.parameters_widget.info = 'No workouts found. Please select more equipment.'
            finally:
                progress.close()

    def add_exercise_button_clicked(self):
        """Show exercise type dialog and add random exercise from selected category."""
        from robocross.exercise_type_dialog import ExerciseTypeDialog
        from robocross.workout_data import WorkoutData
        from dataclasses import replace
        import random

        # Get available categories
        workout_data = WorkoutData()
        categories = workout_data.categories

        # Show dialog
        dialog = ExerciseTypeDialog(categories, parent=self)
        result = dialog.exec()

        if result == ExerciseTypeDialog.DialogCode.Accepted:
            selected_category = dialog.get_selected_category()
            if selected_category:
                # Get workouts for this category
                category_workouts = workout_data.get_workouts_by_category(selected_category)

                if category_workouts:
                    # Pick random workout from category
                    random_workout = random.choice(category_workouts)

                    # Create a copy with updated time (don't modify original)
                    workout_copy = replace(random_workout, time=self.form.interval)

                    # Add to editor table
                    self.parameters_widget.editor_table.add_row(
                        workout_copy,
                        self.form.rest_time
                    )
                    LOGGER.info(f"Added random {selected_category} exercise: {random_workout.name}")
                else:
                    LOGGER.warning(f"No exercises found for category: {selected_category}")
        else:
            LOGGER.info("Add exercise cancelled")

    def on_workout_name_changed(self, workout_name: str):
        """Handle workout name change from parameters widget."""
        # Update viewer with formatted name
        formatted_name = workout_name.replace('_', ' ').title() if workout_name else "Untitled Workout"
        self.viewer.workout_name = formatted_name

    def on_workout_cycles_changed(self, cycles: int):
        """Handle workout cycles change from parameters widget."""
        # Update viewer with new cycles count and rebuild workout list
        self.viewer.workout_cycles = cycles
        # Rebuild the workout list with new cycle count (if we have exercises)
        if self.parameters_widget.editor_table.rows:
            self.on_workout_list_changed()

    def on_tab_changed(self, index: int):
        """Handle tab changes - update viewer workout name when switching to Player tab."""
        # Index 1 is the Player tab
        if index == 1:
            # Update viewer workout name from editor table
            workout_name = self.parameters_widget.editor_table.workout_name
            if workout_name:
                formatted_name = workout_name.replace('_', ' ').title()
                self.viewer.workout_name = formatted_name
            else:
                self.viewer.workout_name = "Untitled Workout"

    def on_workout_list_changed(self):
        """Handle workout list changes from editor table."""
        # Update the main workout list from editor
        workouts, rest_times = self.parameters_widget.get_workout_list()
        LOGGER.info(f"on_workout_list_changed triggered: {len(workouts)} workouts from editor, {len(self.parameters_widget.editor_table.rows)} rows in table")
        if workouts:
            # Reconstruct workout list with REST_PERIOD items
            full_workout_list = []
            for i, workout in enumerate(workouts):
                full_workout_list.append(workout)
                # Add rest period after each exercise
                if i < len(rest_times):
                    rest_period = Workout(
                        name=REST_PERIOD,
                        description="Take a break",
                        equipment=[],
                        intensity=Intensity.low,
                        aerobic_type=AerobicType.recovery,
                        target=[],
                        time=rest_times[i],
                    )
                    full_workout_list.append(rest_period)

            # Sync workout cycles BEFORE setting workout_list (so list is expanded correctly)
            self.viewer.workout_cycles = self.form.workout_cycles
            self.workout_list = full_workout_list
            # Update viewer workout name from editor table
            self.viewer.workout_name = self.parameters_widget.editor_table.workout_name or "Untitled Workout"
            # Note: Viewer updates happen when stopwatch runs, so this mainly keeps data in sync

    def save_button_clicked(self):
        """Save workout session with snake_case filename."""
        # Save workout name to settings before proceeding
        self.form._save_workout_name_to_settings()

        workouts, rest_times = self.parameters_widget.get_workout_list()

        if not workouts:
            LOGGER.warning("No workout to save")
            return

        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Generate default filename from workout name
        workout_name = self.form.workout_name
        if workout_name:
            default_filename = f"{self.form.workout_name_snake_case}.json"
        else:
            default_filename = f"workout_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Workout Session",
            str(DATA_DIR / default_filename),
            "JSON Files (*.json)"
        )

        if not file_path:
            LOGGER.info("Save cancelled by user")
            self.parameters_widget.info = "Save cancelled"
            return

        if file_path:
            workouts_data = []
            for workout in workouts:
                workout_dict = {
                    "name": workout.name,
                    "description": workout.description,
                    "equipment": [eq.name for eq in workout.equipment if eq is not None] if workout.equipment else [],
                    "intensity": workout.intensity.name,
                    "aerobic_type": workout.aerobic_type.name,
                    "target": [t.name for t in workout.target if t is not None] if workout.target else [],
                    "time": workout.time,
                    "sub_workouts": workout.sub_workouts
                }
                workouts_data.append(workout_dict)

            # Calculate average rest time for metadata
            avg_rest = sum(rest_times) // len(rest_times) if rest_times else 30

            session_data = {
                "workout_name": workout_name,
                "workout_cycles": self.form.workout_cycles,  # NEW: Circuit cycles
                "workouts": workouts_data,
                "rest_time": avg_rest,
                "rest_times": rest_times,  # Save individual rest times
                "saved_at": self.date_time_string
            }

            with open(file_path, 'w') as f:
                json.dump(session_data, f, indent=4)

            # Update last workout path so this file auto-loads on next startup
            self.settings.setValue(self.last_workout_path_key, file_path)

            LOGGER.info(f"Saved: {file_path}")
            filename = Path(file_path).name
            self.parameters_widget.info = f"Workout saved to {filename}"

    def _load_workout_from_file(self, file_path: str, show_info: bool = True):
        """Load workout and populate editor table."""
        LOGGER.info(f"Loading: {file_path}")
        try:
            with open(file_path, 'r') as f:
                session_data = json.load(f)

            workouts_data = session_data.get("workouts", [])
            loaded_workouts = []
            loaded_rest_times = []
            default_rest_time = session_data.get("rest_time", 30)
            loaded_cycles = session_data.get("workout_cycles", 1)  # NEW: Load circuit cycles

            # Parse workouts and extract rest times
            i = 0
            while i < len(workouts_data):
                workout_dict = workouts_data[i]

                # Skip rest period items (they're stored as separate entries in old format)
                if workout_dict.get("name") == REST_PERIOD:
                    i += 1
                    continue

                # Create workout object
                equipment_list = [Equipment.__members__.get(eq)
                                for eq in workout_dict.get("equipment", [])]
                target_list = [Target.__members__.get(t)
                              for t in workout_dict.get("target", [])]

                workout = Workout(
                    name=workout_dict.get("name"),
                    description=workout_dict.get("description"),
                    equipment=equipment_list if equipment_list else [],
                    intensity=Intensity.__members__.get(
                        workout_dict.get("intensity")),
                    aerobic_type=AerobicType.__members__.get(
                        workout_dict.get("aerobic_type")),
                    target=target_list,
                    time=workout_dict.get("time"),
                    sub_workouts=workout_dict.get("sub_workouts"),
                    energy=workout_dict.get("energy")  # Include calorie burn rate
                )
                loaded_workouts.append(workout)

                # Check if next item is a rest period
                rest_time = default_rest_time
                if i + 1 < len(workouts_data):
                    next_workout = workouts_data[i + 1]
                    if next_workout.get("name") == REST_PERIOD:
                        rest_time = next_workout.get("time", default_rest_time)
                        i += 1  # Skip the rest period item

                loaded_rest_times.append(rest_time)
                i += 1

            # Use rest_times from new format if available
            rest_times = session_data.get("rest_times")
            if rest_times:
                loaded_rest_times = rest_times

            # Load workout name FIRST
            workout_name = session_data.get("workout_name", "")
            if not workout_name:
                workout_name = Path(file_path).stem

            LOGGER.info(f"Loading workout: {workout_name}, cycles: {loaded_cycles}, workouts: {len(loaded_workouts)}")

            # Set cycles on form and viewer BEFORE populating editor
            self.form.workout_name_line_edit.setText(workout_name)
            self.form.workout_cycles_spin_box.setValue(loaded_cycles)
            self.viewer.workout_cycles = loaded_cycles  # Set BEFORE workout_list is updated

            # Auto-calculate circuit length based on workout + rest durations
            total_workout_time = sum(workout.time for workout in loaded_workouts)
            total_rest_time = sum(loaded_rest_times)
            total_circuit_time = total_workout_time + total_rest_time
            estimated_circuit_minutes = int(round(total_circuit_time / 60))
            self.form.length_spin_box.setValue(estimated_circuit_minutes)
            LOGGER.info(f"Auto-calculated circuit length: {estimated_circuit_minutes} minutes (work: {total_workout_time}s, rest: {total_rest_time}s, total: {total_circuit_time}s)")

            # Clear and populate editor table
            LOGGER.info(f"Clearing editor table and adding {len(loaded_workouts)} rows...")
            self.parameters_widget.editor_table.clear_rows()
            for i, workout in enumerate(loaded_workouts):
                rest = loaded_rest_times[i] if i < len(loaded_rest_times) else default_rest_time
                self.parameters_widget.editor_table.add_row(workout, rest)

            # Force layout update
            self.parameters_widget.editor_table.widget.updateGeometry()
            self.parameters_widget.editor_table.updateGeometry()
            LOGGER.info(f"Successfully added {len(loaded_workouts)} rows to editor table")

            # Note: workout_list is automatically updated via on_workout_list_changed signal
            self.rest_time = default_rest_time

            self.parameters_widget.editor_table.workout_name = workout_name
            self.parameters_widget.update_summary()

            # ViewerV2 doesn't have stopwatch buttons, scroll_widget, or info label
            # Display is automatically updated by update_display() call in workout_list setter

            self.viewer.workout_name = parse_name_nicely(workout_name)

            LOGGER.info(f"Loaded: {workout_name} ({len(loaded_workouts)} items)")
            self.settings.setValue(self.last_workout_path_key, file_path)

        except Exception as e:
            LOGGER.error(f"Load error: {e}")

    def load_button_clicked(self):
        """Load a workout session from a JSON file."""
        # Create data directory if it doesn't exist
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Open file dialog to choose file to load
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Workout Session",
            str(DATA_DIR),
            "JSON Files (*.json)"
        )

        if file_path:
            self._load_workout_from_file(file_path, show_info=True)

    def copy_to_clipboard_button_clicked(self):
        """Export workout data to clipboard as TSV for spreadsheet paste."""
        # Get workout data from editor
        workouts, rest_times = self.parameters_widget.get_workout_list()

        # Validation: Check if workout is empty
        if not workouts:
            LOGGER.warning("No exercises in workout - cannot copy to clipboard")
            self.parameters_widget.info = "No exercises to export. Add exercises first."
            return

        # Get workout cycles from form
        workout_cycles = self.form.workout_cycles

        # Build exercise list (repeat for cycles if > 1)
        full_workout_list = []
        full_rest_list = []

        for cycle in range(workout_cycles):
            for i, workout in enumerate(workouts):
                full_workout_list.append(workout)
                if i < len(rest_times):
                    full_rest_list.append(rest_times[i])

        # Generate TSV data
        tsv_lines = []

        # Date header (merged effect: first column has date, others empty)
        import platform
        if platform.system() == "Windows":
            date_format = "%#d %B %Y"  # Windows uses %#d
        else:
            date_format = "%-d %B %Y"  # Unix uses %-d
        current_date = datetime.now().strftime(date_format)
        tsv_lines.append(f"{current_date}\t\t")

        # Column headers
        tsv_lines.append("Item\tDuration\tCalories")

        # Calculate start row for exercises (row 3 in spreadsheet)
        data_start_row = 3

        # Exercise rows
        total_rest_seconds = 0
        total_rest_calories = 0

        from robocross.workout_data import WorkoutData
        workout_data = WorkoutData()

        for i, workout in enumerate(full_workout_list):
            # Get exercise name (formatted nicely)
            exercise_name = workout.name.replace('_', ' ').title()

            # Format duration as H:MM:SS
            duration_str = self.format_time_hms(workout.time)

            # Calculate calories
            energy = 0
            if workout.energy is not None:
                energy = workout.energy
            elif workout.name in workout_data.data:
                energy = workout_data.data[workout.name].get("energy", 0)
            else:
                # Fallback based on intensity
                intensity_energy = {"high": 13, "medium": 9, "low": 6}
                energy = intensity_energy.get(workout.intensity.name, 9)

            calories = int(energy * (workout.time / 60.0))

            # Add exercise row
            tsv_lines.append(f"{exercise_name}\t{duration_str}\t{calories}")

            # Accumulate rest time if available
            if i < len(full_rest_list):
                rest_seconds = full_rest_list[i]
                total_rest_seconds += rest_seconds
                # Calculate rest calories (assume low intensity = 6 cal/min)
                total_rest_calories += int(6 * (rest_seconds / 60.0))

        # Total rest time row
        if total_rest_seconds > 0:
            rest_duration_str = self.format_time_hms(total_rest_seconds)
            tsv_lines.append(f"Total rest time\t{rest_duration_str}\t{total_rest_calories}")

        # Calculate row numbers for SUM formulas
        data_end_row = data_start_row + len(full_workout_list) - 1
        if total_rest_seconds > 0:
            data_end_row += 1  # Include rest row in sum

        # Total row with formulas
        duration_formula = f"=SUM(B{data_start_row}:B{data_end_row})"
        calories_formula = f"=SUM(C{data_start_row}:C{data_end_row})"
        tsv_lines.append(f"Total\t{duration_formula}\t{calories_formula}")

        # Join all lines with newlines
        tsv_data = "\n".join(tsv_lines)

        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(tsv_data)

        # Log success
        exercise_count = len(full_workout_list)
        LOGGER.info(f"Copied {exercise_count} exercises to clipboard as TSV")
        self.parameters_widget.info = f"Copied {exercise_count} exercises to clipboard"

    def format_time_hms(self, seconds: int) -> str:
        """
        Format seconds as H:MM:SS for spreadsheet.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted string like "0:01:00" for 60 seconds
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:02d}"

    def resizeEvent(self, event):
        """This method is called whenever the widget is resized."""
        new_size = event.size()
        old_size = event.oldSize()
        LOGGER.debug(f"Widget resized from: {old_size.width()}x{old_size.height()} to: {new_size.width()}x{new_size.height()}")
        self.app_size = new_size
        super().resizeEvent(event)


if __name__ == '__main__':
    import qdarktheme
    import os
    from contextlib import contextmanager

    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QCoreApplication, Qt, QLoggingCategory
    from PySide6.QtGui import QPixmap

    from core.core_paths import image_path

    # Suppress Qt multimedia FFmpeg logging noise
    QLoggingCategory.setFilterRules("qt.multimedia*=false")
    os.environ['QT_LOGGING_RULES'] = 'qt.multimedia*=false'

    @contextmanager
    def suppress_stderr():
        """Temporarily suppress stderr output."""
        null_fd = os.open(os.devnull, os.O_RDWR)
        save_stderr = os.dup(2)
        os.dup2(null_fd, 2)
        try:
            yield
        finally:
            os.dup2(save_stderr, 2)
            os.close(null_fd)
            os.close(save_stderr)

    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    splash_manager = splash_screen_manager.SplashScreenManager(
        splash_image_path=SPLASH_SCREEN, message=VERSIONS[-1].short_title.upper())
    splash_manager.show_splash(pause_duration_ms=5000, fade_duration_ms=1000)
    app.setWindowIcon(QPixmap(ROBOCROSS_LOGO.as_posix()))
    app.setApplicationDisplayName(APP_NAME)
    qdarktheme.setup_theme()

    # Create widget with FFmpeg logging suppressed
    with suppress_stderr():
        widget = Robocross()

    widget.show()
    sys.exit(app.exec())
