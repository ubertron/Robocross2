from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import QWidget, QHBoxLayout

from robocross.workout import Workout
from robocross import REST_PERIOD


class WorkoutDot(QWidget):
    """Circular dot representing a single workout in the progress row."""

    def __init__(self, workout: Workout, dot_size: int = 20):
        super().__init__()
        self.workout = workout
        self.dot_size = dot_size
        self.state = 'not_started'  # 'not_started', 'in_progress', 'finished'
        self._category_colors = self._get_category_colors()
        self.setFixedSize(dot_size, dot_size)
        self.setToolTip(workout.name.replace('_', ' ').title())

    def _get_category_colors(self) -> dict:
        """Get colors for different states based on workout category."""
        from robocross import get_category_color

        base_color = get_category_color(self.workout.aerobic_type.name)

        # Darken color for not-started state (60% brightness)
        not_started_color = self._adjust_brightness(base_color, 0.6)
        # Lighten color for finished state (130% brightness)
        finished_color = self._adjust_brightness(base_color, 1.3)

        return {
            'not_started_bg': not_started_color,
            'in_progress_bg': base_color,
            'finished_bg': finished_color
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

    def paintEvent(self, event):
        """Custom paint event to draw the circular dot."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Determine color based on state
        if self.state == 'not_started':
            color = self._category_colors['not_started_bg']
        elif self.state == 'in_progress':
            color = self._category_colors['in_progress_bg']
        else:  # finished
            color = self._category_colors['finished_bg']

        # Draw white border first if in progress (underneath)
        if self.state == 'in_progress':
            painter.setBrush(Qt.GlobalColor.white)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(0, 0, self.dot_size, self.dot_size)

        # Draw filled circle on top (smaller if in progress to show white ring)
        painter.setBrush(QColor(color))
        painter.setPen(Qt.PenStyle.NoPen)
        if self.state == 'in_progress':
            # Draw smaller circle to show white border
            painter.drawEllipse(3, 3, self.dot_size - 6, self.dot_size - 6)
        else:
            painter.drawEllipse(0, 0, self.dot_size, self.dot_size)


class DotContainer(QWidget):
    """Container that spaces dots to fill available width."""

    def __init__(self, workouts: list[Workout]):
        super().__init__()
        self.dots = []
        layout = QHBoxLayout()
        layout.setSpacing(0)  # We'll handle spacing manually
        layout.setContentsMargins(0, 0, 0, 0)

        for workout in workouts:
            if workout.name != REST_PERIOD:
                dot = WorkoutDot(workout)
                self.dots.append(dot)
                layout.addWidget(dot)

        layout.addStretch()  # Push dots to fill width
        self.setLayout(layout)

    def resizeEvent(self, event):
        """Calculate spacing to distribute dots across width on resize."""
        if self.dots:
            total_width = self.width()
            dot_width = self.dots[0].dot_size
            num_dots = len(self.dots)
            available_space = total_width - (num_dots * dot_width)
            spacing = max(5, available_space // (num_dots + 1))
            self.layout().setSpacing(spacing)

        super().resizeEvent(event)
