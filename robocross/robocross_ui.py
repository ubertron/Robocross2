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
    default_size = QSize(800, 400)
    minimum_width = 640

    def __init__(self, parent=None):
        super(Robocross, self).__init__(title=VERSIONS[-1].title, parent=parent)
        self.settings = QSettings(DEVELOPER, APP_NAME)
        self.tab_widget = self.add_widget(QTabWidget())
        self.parameters_widget: ParametersWidget = ParametersWidget()
        self.form = self.parameters_widget.form
        self.tab_widget.addTab(self.parameters_widget, 'Create')
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
        self.setMinimumWidth(self.minimum_width)
        self.viewer.stopwatch.play_pause_button.setEnabled(False)
        self.viewer.stopwatch.reset_button.setEnabled(False)
        self.viewer.scroll_widget.setVisible(False)
        self.resize(self.app_size)

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

    def new_workout_clicked(self):
        """Reset all parameters to start a new workout."""
        # Reset form to default values via the actual widgets
        self.form.interval_spin_box.setValue(45)
        self.form.length_spin_box.setValue(10)
        self.form.rest_time_spin_box.setValue(30)
        self.form.nope_list_line_edit.setText("")

        # Check all equipment checkboxes (enable all)
        for checkbox in self.parameters_widget.equipment_check_boxes:
            checkbox.setChecked(True)

        # Clear the workout list
        self.routine = None
        self.workout_list = []

        # Reset viewer
        self.viewer.stopwatch.play_pause_button.setEnabled(False)
        self.viewer.stopwatch.reset_button.setEnabled(False)
        self.viewer.scroll_widget.setVisible(False)
        self.viewer.info = 'create a workout'
        self.viewer.workout_name = "New Workout"

        # Update info
        self.parameters_widget.info = "New workout started. Configure parameters and click Build."
        LOGGER.info("New workout started - parameters reset")

    def build_button_clicked(self):
        """Create the routine."""
        if self.parameters_widget.zero_equipment:
            self.parameters_widget.info = "No equipment selected.\nJust go for a run or something..."
        else:
            self.routine = Routine(
                interval=self.form.interval,
                workout_length=self.form.length,
                rest_time=self.form.rest_time,
                nope_list=self.form.nope_list,
                equipment_filter=self.parameters_widget.equipment_filter,
            )
            if self.workout_list:
                self.viewer.stopwatch.play_pause_button.setEnabled(True)
                self.viewer.stopwatch.reset_button.setEnabled(True)
                self.viewer.scroll_widget.setVisible(True)
                self.viewer.info = 'get ready...'
                self.viewer.workout_name = "New Workout"
                LOGGER.info(self.workout_report)
                self.parameters_widget.info = self.workout_report
            else:
                self.parameters_widget.info = 'No workouts found.\nPlease select more equipment.'

    def save_button_clicked(self):
        """Save the current workout session to a JSON file."""
        if not self.workout_list:
            self.parameters_widget.info = "No workout to save. Build a workout first."
            return

        # Create data directory if it doesn't exist
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Open file dialog to choose save location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Workout Session",
            str(DATA_DIR / f"workout_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"),
            "JSON Files (*.json)"
        )

        if file_path:
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

            with open(file_path, 'w') as f:
                json.dump(session_data, f, indent=4)

            self.parameters_widget.info = f"Workout session saved to:\n{file_path}"
            LOGGER.info(f"Workout session saved to: {file_path}")

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
            try:
                with open(file_path, 'r') as f:
                    session_data = json.load(f)

                # Load the workout list
                workouts_data = session_data.get("workouts", [])
                loaded_workouts = []

                for workout_dict in workouts_data:
                    equipment_list = [Equipment.__members__.get(eq) for eq in workout_dict.get("equipment", [])]
                    target_list = [Target.__members__.get(t) for t in workout_dict.get("target", [])]

                    workout = Workout(
                        name=workout_dict.get("name"),
                        description=workout_dict.get("description"),
                        equipment=equipment_list if equipment_list else [],
                        intensity=Intensity.__members__.get(workout_dict.get("intensity")),
                        aerobic_type=AerobicType.__members__.get(workout_dict.get("aerobic_type")),
                        target=target_list,
                        time=workout_dict.get("time"),
                        sub_workouts=workout_dict.get("sub_workouts")
                    )
                    loaded_workouts.append(workout)

                # Set the workout list
                self.workout_list = loaded_workouts
                self.rest_time = session_data.get("rest_time", 30)

                # Enable the player controls
                self.viewer.stopwatch.play_pause_button.setEnabled(True)
                self.viewer.stopwatch.reset_button.setEnabled(True)
                self.viewer.scroll_widget.setVisible(True)
                self.viewer.info = 'get ready...'

                # Get workout name from filename and set it
                workout_name = Path(file_path).stem
                workout_name_nice = parse_name_nicely(workout_name)
                self.viewer.workout_name = workout_name_nice

                # Build workout items list
                workout_items = []
                for workout in loaded_workouts:
                    if workout.name != REST_PERIOD:
                        workout_name_parsed = parse_name_nicely(workout.name)
                        workout_items.append(f"{workout_name_parsed}  ({time_utils.time_nice(workout.time)})")

                # Calculate total time
                total_time = sum(w.time for w in loaded_workouts)

                # Update info with workout name and items (use <br> for HTML line breaks)
                items_text = '<br>'.join(workout_items)
                self.parameters_widget.info = (
                    f"<b>{workout_name_nice}</b><br><br>"
                    f"Total time: {time_utils.time_nice(total_time)}<br>"
                    f"Rest time: {time_utils.time_nice(self.rest_time)}<br>"
                    f"Exercises: {len(workout_items)}<br><br>"
                    f"<b>Workout Items:</b><br>{items_text}<br><br>"
                    f"Go to Player tab to start!"
                )
                LOGGER.info(f"Workout session loaded: {workout_name_nice} ({len(workout_items)} exercises)")

            except Exception as e:
                self.parameters_widget.info = f"Error loading workout session:\n{str(e)}"
                LOGGER.error(f"Error loading workout session: {e}")

    def resizeEvent(self, event):
        """This method is called whenever the widget is resized."""
        new_size = event.size()
        old_size = event.oldSize()
        LOGGER.debug(f"Widget resized from: {old_size.width()}x{old_size.height()} to: {new_size.width()}x{new_size.height()}")
        self.app_size = new_size
        super().resizeEvent(event)


if __name__ == '__main__':
    import qdarktheme

    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QCoreApplication, Qt
    from PySide6.QtGui import QPixmap

    from core.core_paths import image_path
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    splash_manager = splash_screen_manager.SplashScreenManager(
        splash_image_path=SPLASH_SCREEN, message=VERSIONS[-1].short_title.upper())
    splash_manager.show_splash(pause_duration_ms=5000, fade_duration_ms=1000)
    app.setWindowIcon(QPixmap(ROBOCROSS_LOGO.as_posix()))
    app.setApplicationDisplayName(APP_NAME)
    qdarktheme.setup_theme()
    widget = Robocross()
    widget.show()
    sys.exit(app.exec())
