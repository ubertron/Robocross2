import logging
import sys

from PySide6.QtCore import QTimer, Qt, QElapsedTimer, QEvent, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QProgressBar, QSizePolicy

from core import SANS_SERIF_FONT
from robocross.workout import Workout
from robocross.robocross_enums import Intensity, AerobicType
from robocross import REST_PERIOD
from widgets.grid_widget import GridWidget
from core.logging_utils import get_logger

LOGGER = get_logger(__name__, level=logging.DEBUG)


class WorkoutChip(GridWidget):
    """Widget to represent a workout."""

    padding = 5  # Match editor button padding
    fixed_height = 30  # Match editor button height
    time_reached: Signal = Signal()

    def __init__(self, workout: Workout, period: int = 100, show_progress: bool = True):
        super(WorkoutChip, self).__init__(workout.name, margin=1)
        self.period = period
        self.background = self.add_label('', row=0, column=0)
        self.background.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        self.background.setFixedHeight(self.fixed_height)
        self.progress_label: QLabel = self.add_label('', row=0, column=0)
        self.label = self.add_label(text="", row=0, column=0, alignment=Qt.AlignmentFlag.AlignCenter)
        self.label.setContentsMargins(self.padding, self.padding, self.padding, self.padding)
        self.setFixedHeight(self.fixed_height)
        self.timer: QTimer = QTimer()
        self.workout = workout
        self.time: float = 0.0
        self.progress: float = 0.0
        self.running: bool = False
        self.show_progress: bool = show_progress
        self.progress_visible = show_progress
        self._category_colors = self._get_category_colors()
        self.setup_ui()

    def _get_category_colors(self) -> dict:
        """Get colors for different states based on workout category."""
        from robocross import get_category_color, get_contrast_text_color

        base_color = get_category_color(self.workout.aerobic_type.name)
        text_color = get_contrast_text_color(base_color)

        # Darken color for not-started state (60% brightness)
        not_started_color = self._adjust_brightness(base_color, 0.6)
        # Lighten color for finished state (130% brightness)
        finished_color = self._adjust_brightness(base_color, 1.3)

        return {
            'not_started_bg': not_started_color,
            'in_progress_bg': base_color,
            'finished_bg': finished_color,
            'text': text_color
        }

    def _adjust_brightness(self, hex_color: str, factor: float) -> str:
        """Adjust brightness of hex color by factor (0.0 to 2.0)."""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Apply factor and clamp to 0-255
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))

        return f'#{r:02x}{g:02x}{b:02x}'

    def setup_ui(self):
        """Setup ui."""
        self.progress_label.setAlignment(Qt.AlignLeft)
        # Progress overlay will show bright color (set in start())
        self.progress_label.setFixedHeight(self.fixed_height)  # Match background height
        self.progress_label.setContentsMargins(0, 0, 0, 0)  # No margins for perfect alignment
        self.timer.timeout.connect(self.update_progress)
        self.timer.setInterval(self.period)
        self.reset()

    @property
    def title(self) -> str:
        return f"Workout: {self.workout.name.title()}"

    def reset(self):
        # Background is dark (not_started), progress will reveal bright color
        bg_color = self._category_colors['not_started_bg']
        text_color = self._category_colors['text']
        self.background.setStyleSheet(f'background-color: {bg_color}; border: 1px solid #555;')
        self.label.setStyleSheet(f'color: {text_color}; font-weight: normal;')
        self.time = 0.0
        self.progress = 0.0
        self.progress_visible = self.show_progress
        self.progress_label.setFixedWidth(0)

    def start(self):
        self.timer.start()
        self.running = True
        # Background stays dark, progress overlay will be bright color
        bg_color = self._category_colors['not_started_bg']  # Keep dark background
        progress_color = self._category_colors['in_progress_bg']  # Bright overlay
        text_color = self._category_colors['text']
        self.background.setStyleSheet(f'background-color: {bg_color}; border: 1px solid #555;')
        self.progress_label.setStyleSheet(f'background-color: {progress_color};')  # Bright progress overlay
        self.label.setStyleSheet(f'color: {text_color}; font-weight: normal;')

    def pause(self):
        self.timer.stop()

    def update_progress(self):
        self.time += self.period / 1000.0
        self.progress = min(1.0, self.time / self.workout.time)
        if self.progress == 1.0:
            self.timer.stop()
            self.progress_visible = False
            # Show full bright finished color
            bg_color = self._category_colors['finished_bg']
            text_color = self._category_colors['text']
            self.background.setStyleSheet(f'background-color: {bg_color}; border: 1px solid #555;')
            self.label.setStyleSheet(f'color: {text_color}; font-weight: normal;')
            self.time_reached.emit()
        else:
            # Grow bright progress overlay from left to right
            new_width = int(self.size().width() * self.progress)
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
        # Format name: replace underscores with spaces and title case
        formatted_name = workout.name.replace('_', ' ').title()
        self.label.setText(formatted_name)
        self.label.setToolTip(workout.description)
        # Regenerate colors for new workout category
        if hasattr(self, '_category_colors'):
            self._category_colors = self._get_category_colors()

    def update_display_name(self, display_name: str):
        """Update the displayed name while keeping the same workout for progress tracking.

        This is used for sub-workouts where the display changes but the progress
        calculation stays based on the full workout duration.
        """
        # Format name: replace underscores with spaces and title case
        formatted_name = display_name.replace('_', ' ').title()
        self.label.setText(formatted_name)


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
