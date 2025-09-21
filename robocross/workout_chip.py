import logging
import sys

from PySide6.QtCore import QTimer, Qt, QElapsedTimer, QEvent, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QProgressBar, QSizePolicy

from robocross import SANS_SERIF_FONT
from robocross.workout import Workout
from robocross.robocross_enums import Intensity, AerobicType
from robocross import REST_PERIOD
from widgets.grid_widget import GridWidget
from core.logging_utils import get_logger

LOGGER = get_logger(__name__, level=logging.DEBUG)


class WorkoutChip(GridWidget):
    """Widget to represent a workout."""

    background_not_started = 'background-color: rgb(128, 128, 128)'
    background_in_progress = 'background-color: rgb(255, 255, 255)'
    background_finished = 'background-color: rgb(216, 216, 216)'
    progress_bar_style = 'background-color: rgb(0, 255, 0)'
    padding = 4
    text_style = 'color: rgb(16, 16, 16)'
    default_font = QFont(SANS_SERIF_FONT, 16)
    time_reached: Signal = Signal()

    def __init__(self, workout: Workout, period: int = 100, show_progress: bool = True):
        super(WorkoutChip, self).__init__(workout.name, margin=1)
        self.period = period
        self.background = self.add_label('', row=0, column=0)
        self.background.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        self.progress_label: QLabel = self.add_label('', row=0, column=0)
        self.label = self.add_label(text="", row=0, column=0, alignment=Qt.AlignmentFlag.AlignLeft)
        self.label.setFont(self.default_font)
        self.label.setContentsMargins(self.padding, self.padding, self.padding, self.padding)
        self.timer: QTimer = QTimer()
        self.workout = workout
        self.time: float = 0.0
        self.progress: float = 0.0
        self.running: bool = False
        self.show_progress: bool = show_progress
        self.progress_visible = show_progress
        self.setup_ui()

    def setup_ui(self):
        """Setup ui."""
        self.label.setStyleSheet(self.text_style)
        self.progress_label.setAlignment(Qt.AlignLeft)
        self.progress_label.setStyleSheet(self.progress_bar_style)
        self.timer.timeout.connect(self.update_progress)
        self.timer.setInterval(self.period)
        self.reset()

    @property
    def title(self) -> str:
        return f"Workout: {self.workout.name.title()}"

    def reset(self):
        self.background.setStyleSheet(self.background_not_started)
        self.time = 0.0
        self.progress = 0.0
        self.progress_visible = self.show_progress
        self.progress_label.setFixedWidth(0)

    def start(self):
        self.timer.start()
        self.running = True
        self.background.setStyleSheet(self.background_in_progress)

    def pause(self):
        self.timer.stop()

    def update_progress(self):
        self.time += self.period / 1000.0
        self.progress = min(1.0, self.time / self.workout.time)
        if self.progress == 1.0:
            self.timer.stop()
            self.progress_visible = False
            self.background.setStyleSheet(self.background_finished)
            self.time_reached.emit()
        else:
            new_width  = int(self.size().width() * self.progress)
            self.progress_label.setFixedWidth(new_width)

    @property
    def progress_visible(self):
        return self.progress_label.isVisible()

    @progress_visible.setter
    def progress_visible(self, value):
        self.progress_label.setVisible(value)

    @property
    def workout(self):
        return self._workout

    @workout.setter
    def workout(self, workout: Workout):
        self._workout = workout
        self.setWindowTitle(workout.name)
        self.label.setText(workout.name.title())
        self.label.setToolTip(workout.description)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    _workout = Workout.default()
    widget = WorkoutChip(workout=Workout.default(), period=100)
    widget.show()
    LOGGER.info(f"Start size is {widget.size().width()}")
    widget.start()
    widget.resize(400, 20)
    app.exec()
