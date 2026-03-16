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
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import QTabWidget, QSplashScreen, QFileDialog

from core import DEVELOPER, logging_utils, splash_screen_manager, SANS_SERIF_FONT, CODE_FONT
from core.version_info import VersionInfo
from core import time_utils
from core.core_paths import image_path, DATA_DIR
from robocross import APP_NAME, REST_PERIOD
from robocross.parameters_widget import ParametersWidget
from robocross.routine import Routine
from robocross.viewer import Viewer
from robocross.workout import Workout
from robocross.robocross_enums import Equipment, Intensity, AerobicType, Target
from widgets.generic_widget import GenericWidget

LOG_PATH = Path(__file__).parents[1].joinpath("logs/workouts.log")
FILE_HANDLER = logging_utils.FileHandler(path=LOG_PATH, level=logging.DEBUG)
STREAM_HANDLER = logging_utils.StreamHandler(level=logging.INFO)
LOGGER = logging_utils.get_logger(name=__name__, level=logging.INFO, handlers=[FILE_HANDLER, STREAM_HANDLER])
VERSIONS = (
    VersionInfo(name=APP_NAME, version='1.0', codename='Alpha', info='Initial release'),
    VersionInfo(name=APP_NAME, version='2.0', codename='Colt Seavers', info='Revamp'),
    VersionInfo(name=APP_NAME, version='2.1', codename='MacGyver', info='Icon buttons, save/load sessions, sub-workouts'),
    VersionInfo(name=APP_NAME, version='2.2', codename='Michael Knight', info='Full workout editor with editable table'),
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
        self.viewer: Viewer = Viewer()
        self.tab_widget.addTab(self.viewer, 'Player')
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
        self.parameters_widget.workout_name_changed.connect(self.on_workout_name_changed)
        self.parameters_widget.editor_table.workout_list_changed.connect(self.on_workout_list_changed)
        self.setMinimumWidth(self.minimum_width)
        self.viewer.stopwatch.play_pause_button.setEnabled(False)
        self.viewer.stopwatch.reset_button.setEnabled(False)
        self.viewer.scroll_widget.setVisible(False)
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
        self.viewer.info_font = QFont(SANS_SERIF_FONT, int(value.width() / 32))
        self.viewer.progress_bar_font = QFont(SANS_SERIF_FONT, int(value.height() / 16))
        self.viewer.progress_bar.setFixedHeight(int(value.height() / 10))
        self.viewer.resize_stopwatch()
        self.viewer.chip_font = QFont(SANS_SERIF_FONT, int(value.height() / 36))
        self.viewer.resize_scroll_widget()

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
        workout_list = routine.get_workout_list(self.form.workout_type) if routine else []
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
                "target": [t.name for t in workout.target],
                "time": workout.time,
                "sub_workouts": workout.sub_workouts
            }
            workouts_data.append(workout_dict)

        session_data = {
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
        self.form.nope_list_line_edit.setText("")
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
        self.viewer.stopwatch.play_pause_button.setEnabled(False)
        self.viewer.stopwatch.reset_button.setEnabled(False)
        self.viewer.scroll_widget.setVisible(False)
        self.viewer.info = 'create a workout'
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
                    nope_list=self.form.nope_list,
                    equipment_filter=self.parameters_widget.equipment_filter,
                )

                if self.workout_list:
                    # Populate editor table
                    self.parameters_widget.set_workout_list(
                        self.workout_list,
                        self.form.rest_time,
                        self.form.workout_name
                    )

                    # Enable viewer
                    self.viewer.stopwatch.play_pause_button.setEnabled(True)
                    self.viewer.stopwatch.reset_button.setEnabled(True)
                    self.viewer.scroll_widget.setVisible(True)
                    self.viewer.info = 'get ready...'
                    self.viewer.workout_name = self.form.workout_name or "New Workout"

                    LOGGER.info(self.workout_report)

                    # Save the built workout to a temp file so it can be auto-loaded
                    self._save_temp_workout()
                else:
                    self.parameters_widget.info = 'No workouts found. Please select more equipment.'
            finally:
                progress.close()

    def add_exercise_button_clicked(self):
        """Add blank exercise row to editor."""
        if self.parameters_widget.editor_table.available_exercises:
            default_workout = self.parameters_widget.editor_table._create_default_workout()
            default_workout.time = self.form.interval  # Use interval as default
            self.parameters_widget.editor_table.add_row(
                default_workout,
                self.form.rest_time
            )
            LOGGER.info("Added new exercise row")

    def on_workout_name_changed(self, workout_name: str):
        """Handle workout name change from parameters widget."""
        # Update viewer with formatted name
        formatted_name = workout_name.replace('_', ' ').title() if workout_name else "Untitled Workout"
        self.viewer.workout_name = formatted_name

    def on_workout_list_changed(self):
        """Handle workout list changes from editor table."""
        # Update the main workout list from editor
        workouts, rest_times = self.parameters_widget.get_workout_list()
        if workouts:
            self.workout_list = workouts
            # Update viewer if needed
            # Note: Viewer updates happen when stopwatch runs, so this mainly keeps data in sync

    def save_button_clicked(self):
        """Save workout session with snake_case filename."""
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

        if file_path:
            workouts_data = []
            for workout in workouts:
                workout_dict = {
                    "name": workout.name,
                    "description": workout.description,
                    "equipment": [eq.name for eq in workout.equipment] if workout.equipment else [],
                    "intensity": workout.intensity.name,
                    "aerobic_type": workout.aerobic_type.name,
                    "target": [t.name for t in workout.target],
                    "time": workout.time,
                    "sub_workouts": workout.sub_workouts
                }
                workouts_data.append(workout_dict)

            # Calculate average rest time for metadata
            avg_rest = sum(rest_times) // len(rest_times) if rest_times else 30

            session_data = {
                "workout_name": workout_name,
                "workouts": workouts_data,
                "rest_time": avg_rest,
                "rest_times": rest_times,  # Save individual rest times
                "saved_at": self.date_time_string
            }

            with open(file_path, 'w') as f:
                json.dump(session_data, f, indent=4)

            LOGGER.info(f"Saved: {file_path}")

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
                    sub_workouts=workout_dict.get("sub_workouts")
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

            # Clear and populate editor table
            self.parameters_widget.editor_table.clear_rows()
            for i, workout in enumerate(loaded_workouts):
                rest = loaded_rest_times[i] if i < len(loaded_rest_times) else default_rest_time
                self.parameters_widget.editor_table.add_row(workout, rest)

            self.workout_list = loaded_workouts
            self.rest_time = default_rest_time

            # Load workout name
            workout_name = session_data.get("workout_name", "")
            if not workout_name:
                workout_name = Path(file_path).stem

            self.form.workout_name_line_edit.setText(workout_name)
            self.parameters_widget.editor_table.workout_name = workout_name
            self.parameters_widget.update_summary()

            # Enable viewer
            self.viewer.stopwatch.play_pause_button.setEnabled(True)
            self.viewer.stopwatch.reset_button.setEnabled(True)
            self.viewer.scroll_widget.setVisible(True)
            self.viewer.info = 'get ready...'
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
