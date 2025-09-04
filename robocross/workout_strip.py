import logging
import sys

from PySide6.QtCore import QTimer, Qt, QElapsedTimer, QEvent
from PySide6.QtWidgets import QProgressBar, QSizePolicy

from robocross.workout import Workout, AerobicType, Intensity
from robocross import REST_PERIOD
from widgets.grid_widget import GridWidget
from core.logging_utils import get_logger

LOGGER = get_logger(__name__, level=logging.DEBUG)


class WorkoutStrip(GridWidget):
    """Widget to represent a workout."""

    background_in_progress = 'background-color: rgb(128, 128, 128)'
    background_finished = 'background-color: rgb(216, 216, 216)'
    progress_bar_style = 'background-color: rgb(0, 255, 0)'
    text_style = 'color: rgb(16, 16, 16)'

    def __init__(self, workout: Workout):
        self.workout = workout
        super(WorkoutStrip, self).__init__(self.title, margin=1)
        self.background = self.add_label('', row=0, column=0)
        self.background.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        self.progress_label: QLabel = self.add_label('', row=0, column=0)
        self.label = self.add_label(f"{workout.name.title()}", row=0, column=0)
        self.label.setToolTip(workout.description)
        self.timer: QTimer = QTimer()
        self.time: float = 0.0
        self.progress: float = 0.0
        self.sample_size: float = 1.0
        self.setup_ui()

    def setup_ui(self):
        """Setup ui."""
        # self.background.setStyleSheet(self.background_in_progress)
        self.label.setStyleSheet(self.text_style)
        self.progress_label.setAlignment(Qt.AlignLeft)
        self.progress_label.setStyleSheet(self.progress_bar_style)
        self.timer.timeout.connect(self.update_progress)
        self.timer.setInterval(self.sample_size * 1000)
        self.reset()

    def resizeEvent(self, event):
        new_size = event.size()
        self.progress_label.setFixedWidth(int(new_size.width() * self.progress))
        super().resizeEvent(event)

    @property
    def title(self) -> str:
        return f"Workout: {self.workout.name.title()}"

    def reset(self):
        self.background.setStyleSheet(self.background_in_progress)
        self.time = 0.0
        self.progress = 0.0
        self.progress_label.setVisible(True)
        self.progress_label.setFixedWidth(0)

    def start(self):
        self.timer.start()

    def pause(self):
        self.timer.stop()

    def update_progress(self):
        self.time += self.sample_size
        self.progress = min(1.0, self.time / self.workout.time)
        if self.progress == 1.0:
            self.timer.stop()
            self.progress_label.setVisible(False)
            self.background.setStyleSheet(self.background_finished)
        else:
            self.progress_label.setFixedWidth(self.size().width() * self.progress)



class TestWorkoutStrip(WorkoutStrip):
    party_time = Workout(
        name="Party time",
        description="Party time",
        equipment=[],
        intensity=Intensity.high,
        aerobic_type=AerobicType.recovery,
        target=[],
        time=12,
        )
    def __init__(self):
        super(TestWorkoutStrip, self).__init__(workout=self.party_time)

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication, QProgressBar

    app = QApplication(sys.argv)
    widget = TestWorkoutStrip()
    widget.show()
    widget.start()
    widget.resize(320, 20)
    app.exec()
