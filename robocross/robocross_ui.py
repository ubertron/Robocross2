"""PySide ui for Robocross2."""
from __future__ import annotations

import getpass
import logging
import sys
import time

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QSettings, QSize
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import QTabWidget, QSplashScreen

from core import DEVELOPER, logging_utils, splash_screen_manager, SANS_SERIF_FONT, CODE_FONT
from core.version_info import VersionInfo
from core import time_utils
from core.core_paths import image_path
from robocross import APP_NAME, REST_PERIOD
from robocross.parameters_widget import ParametersWidget
from robocross.routine import Routine
from robocross.viewer import Viewer
from robocross.workout import Workout
from robocross.robocross_enums import Equipment
from widgets.generic_widget import GenericWidget

LOG_PATH = Path(__file__).parents[1].joinpath("logs/workouts.log")
FILE_HANDLER = logging_utils.FileHandler(path=LOG_PATH, level=logging.DEBUG)
STREAM_HANDLER = logging_utils.StreamHandler(level=logging.INFO)
LOGGER = logging_utils.get_logger(name=__name__, level=logging.INFO, handlers=[FILE_HANDLER, STREAM_HANDLER])
VERSIONS = (
    VersionInfo(name=APP_NAME, version='1.0', codename='Alpha', info='Initial release'),
    VersionInfo(name=APP_NAME, version='2.0', codename='Colt Seavers', info='Revamp'),
)
SPLASH_SCREEN = image_path("splashscreen_640.png")
ROBOCROSS_LOGO = image_path("robocross.png")


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
        self.parameters_widget.build_button_clicked.connect(self.build_button_clicked)
        self.parameters_widget.print_button_clicked.connect(self.print_button_clicked)
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
                LOGGER.info(self.workout_report)
                self.parameters_widget.info = self.workout_report
            else:
                self.parameters_widget.info = 'No workouts found.\nPlease select more equipment.'

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
