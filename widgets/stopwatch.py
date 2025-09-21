import logging
import sys
import threading
import queue
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
)
from PySide6.QtCore import QTimer, QTime, Qt, Signal
from PySide6.QtGui import QFont

from collections import OrderedDict
from core.speaker import Speaker, Voice
from core.logging_utils import get_logger
from robocross import CODE_FONT
from robocross.robocross_enums import RunMode
from widgets.generic_widget import GenericWidget


LOGGER: logging.Logger = get_logger(name=__name__, level=logging.INFO)


class Stopwatch(GenericWidget):
    time_reached = Signal(str, str)  # emit time + message
    play_pause_clicked = Signal(RunMode)
    reset_clicked = Signal()
    default_time_font = QFont(CODE_FONT, 48)

    def __init__(self, period: int):
        super().__init__(title="Stopwatch")
        self.targets: OrderedDict[str, str] = {}  # time -> spoken message
        self.completed_targets = []
        self.period: int = period  # evaluation time for stopwatch
        button_bar = self.add_button_bar(spacing=4)
        self.play_pause_button = button_bar.add_button("Play")
        self.reset_button = button_bar.add_button("Reset")
        self.time_label = self.add_label("00:00:00")
        self.time_font = self.default_time_font
        self.elapsed = QTime(0, 0, 0)
        self.running = False
        self.play_pause_button.clicked.connect(self.play_pause_button_clicked)
        self.reset_button.clicked.connect(self.reset_button_clicked)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.speaker: Speaker = Speaker(Voice.Samantha)
        self.time_reached.connect(self._speak)

    @property
    def current_time(self) -> str:
        """Return the current stopwatch time as a string (hh:mm:ss)."""
        return self.elapsed.toString("hh:mm:ss")

    @property
    def time_font(self) -> QFont:
        return self.time_label.font()

    @time_font.setter
    def time_font(self, font: QFont) -> None:
        self.time_label.setFont(font)

    def set_targets(self, target_dict: OrderedDict[str, str]):
        """
        Schedule notifications with spoken messages.
        Example:
            stopwatch.notify_at({
                "00:00:05": "Five seconds have passed",
                "00:00:10": "Ten seconds reached"
            })
        """
        self.targets = {}
        self.targets.update(target_dict)

    def play_pause_button_clicked(self):
        if not self.running:
            self.timer.start(self.period)
            self.play_pause_button.setText("Pause")
            self.running = True
            run_mode = RunMode.play
        else:
            self.timer.stop()
            self.play_pause_button.setText("Play")
            self.running = False
            run_mode = RunMode.paused
        self.play_pause_clicked.emit(run_mode)

    def reset_button_clicked(self):
        self.reset_clicked.emit()
        self.timer.stop()
        self.elapsed = QTime(0, 0, 0)
        self.time_label.setText("00:00:00")
        self.play_pause_button.setText("Play")
        self.running = False
        self.completed_targets = []

    def update_time(self):
        self.elapsed = self.elapsed.addMSecs(self.period)
        now_str = self.elapsed.toString("hh:mm:ss")
        self.time_label.setText(now_str)

        if now_str in self.targets and now_str not in self.completed_targets:
            message = self.targets[now_str]
            self.time_reached.emit(now_str, message)
            self.completed_targets.append(now_str)

    def _speak(self, t: str, message: str):
        """Queue text to be spoken in the background."""
        if LOGGER.level == logging.DEBUG:
            self.speaker.speak(message)
        LOGGER.debug(f"🗣 {t} → {message}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    stopwatch = Stopwatch(period=100)
    stopwatch.resize(250, 150)
    stopwatch.show()

    # Example: repeat notifications
    stopwatch.set_targets({
        "00:00:05": "Five seconds have passed",
        "00:00:10": "Ten seconds reached"
    })

    sys.exit(app.exec())
