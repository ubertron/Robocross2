"""PySide ui for Robocross2."""
from __future__ import annotations

import getpass
import logging
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QSettings, QSize
from PySide6.QtWidgets import QTabWidget

from core import DEVELOPER, logging_utils
from core.version_info import VersionInfo
from robocross import APP_NAME, REST_PERIOD
from robocross.parameters_widget import ParametersWidget
from robocross.routine import Routine
from robocross.viewer import Viewer
from robocross.workout import Workout
from robocross.robocross_enums import Equipment
from widgets.generic_widget import GenericWidget

log_path = Path(__file__).parents[1].joinpath("logs/workouts.log")
file_handler = logging_utils.FileHandler(path=log_path, level=logging.DEBUG)
stream_handler = logging_utils.StreamHandler(level=logging.INFO)
LOGGER = logging_utils.get_logger(name=__name__, level=logging.INFO, handlers=[file_handler, stream_handler])
VERSIONS = (
    VersionInfo(name=APP_NAME, version='1.0', codename='Alpha', info='Initial release'),
    VersionInfo(name=APP_NAME, version='2.0', codename='Colt Seavers', info='Revamp'),
)

class RoboCrossUI(GenericWidget):
    app_size_key = "app_size"
    default_size = QSize(800, 400)
    minimum_width = 640

    def __init__(self, parent=None):
        super(RoboCrossUI, self).__init__(title=VERSIONS[-1].title, parent=parent)
        self.settings = QSettings(DEVELOPER, APP_NAME)
        self.tab_widget = self.add_widget(QTabWidget())
        self.parameters_widget: ParametersWidget = ParametersWidget()
        self.form = self.parameters_widget.form
        self.tab_widget.addTab(self.parameters_widget, 'Create')
        self.viewer: Viewer = Viewer()
        self.tab_widget.addTab(self.viewer, 'Workout')
        self.routine = None
        self.info = ""
        self.workout_list = []
        self.parameters_widget.info = "Build your workout..."
        self.app_size = self.settings.value(self.app_size_key, self.default_size)
        self.setup_ui()

    def setup_ui(self):
        self.parameters_widget.build_button_clicked.connect(self.build_button_clicked)
        self.parameters_widget.print_button_clicked.connect(self.print_button_clicked)
        self.setMinimumWidth(self.minimum_width)
        self.viewer.stopwatch.play_pause_btn.setEnabled(False)
        self.resize(self.app_size)

    @property
    def app_size(self) -> QSize:
        return self._app_size

    @app_size.setter
    def app_size(self, value: QSize):
        self._app_size = value
        self.settings.setValue(self.app_size_key, value)

    @property
    def date_time_string(self) -> str:
        return datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    @property
    def equipment(self) -> list[Equipment]:
        equipment = list({x.name.replace('_', ' ') for y in self.workout_list for x in y.equipment})
        equipment.sort(key=lambda x: x.lower())
        return equipment

    @property
    def info(self) -> str:
        return self._info

    @info.setter
    def info(self, info: str) -> None:
        self._info = info

    @property
    def routine(self) -> Routine | None:
        return self._routine

    @routine.setter
    def routine(self, routine: Routine | None):
        self._routine = routine
        workout_list = routine.get_workout_list(self.form.workout_type) if routine else []
        self.workout_list = workout_list
        self.viewer.info = "get ready..."

    @property
    def user(self) -> str:
        return getpass.getuser()

    @property
    def workout_list(self):
        return self._workout_list

    @workout_list.setter
    def workout_list(self, workout_list: list[Workout]):
        self._workout_list = workout_list
        self.viewer.workout_list = workout_list
        self.parameters_widget.info = self.workout_report

    @property
    def workout_report(self) -> str:
        report = '\n'.join(f"• {x.name}" for x in self.workout_list if x.name != REST_PERIOD)
        equipment = ', '.join(self.equipment)
        return f"Workout items:\n{report}\n\nEquipment: {equipment}"

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
                self.viewer.stopwatch.play_pause_btn.setEnabled(True)
                LOGGER.info(self.workout_report)
            else:
                self.parameters_widget.info = "No workouts found.\nPlease select more equipment."

    def print_button_clicked(self):
        """Event for print button."""
        LOGGER.info(self.workout_report)

    def resizeEvent(self, event):
        """This method is called whenever the widget is resized."""
        new_size = event.size()
        old_size = event.oldSize()
        LOGGER.debug(f"Widget resized from: {old_size.width()}x{old_size.height()} to: {new_size.width()}x{new_size.height()}")
        self.app_size = new_size
        super().resizeEvent(event)


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QCoreApplication, Qt
    from PySide6.QtGui import QPixmap

    from core.core_paths import image_path

    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setWindowIcon(QPixmap(image_path("robocross.png").as_posix()))
    app.setApplicationDisplayName(APP_NAME)
    widget = RoboCrossUI()
    widget.show()
    sys.exit(app.exec())
