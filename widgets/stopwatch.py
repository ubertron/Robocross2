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
from core.mac_voice import MacVoice, Voice
from core.logging_utils import get_logger
from robocross.robocross_enums import RunMode
from widgets.generic_widget import GenericWidget


LOGGER: logging.Logger = get_logger(name=__name__, level=logging.INFO)


class Stopwatch(GenericWidget):
    time_reached = Signal(str, str)  # emit time + message
    play_pause_clicked = Signal(RunMode)
    reset_clicked = Signal()

    def __init__(self):
        super().__init__(title="Stopwatch")

        # Buttons
        button_bar = self.add_button_bar()
        self.play_pause_btn = button_bar.add_button("Play")
        self.reset_btn = button_bar.add_button("Reset")

        # Time label
        self.time_label = self.add_label("00:00:00")
        font = QFont("Courier New", 32)
        self.time_label.setFont(font)

        # Stopwatch state
        self.elapsed = QTime(0, 0, 0)
        self.running = False
        self.targets: OrderedDict[str, str] = {}  # time -> spoken message

        # Connections
        self.play_pause_btn.clicked.connect(self.play_pause_button_clicked)
        self.reset_btn.clicked.connect(self.reset_button_clicked)

        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.speaker: MacVoice = MacVoice(Voice.Samantha)
        self.time_reached.connect(self._speak)

    @property
    def current_time(self) -> str:
        """Return the current stopwatch time as a string (hh:mm:ss)."""
        return self.elapsed.toString("hh:mm:ss")

    def set_notifications(self, schedule: OrderedDict[str, str]):
        """
        Schedule notifications with spoken messages.
        Example:
            stopwatch.notify_at({
                "00:00:05": "Five seconds have passed",
                "00:00:10": "Ten seconds reached"
            })
        """
        self.targets = {}
        self.targets.update(schedule)

    def play_pause_button_clicked(self):
        if not self.running:
            self.timer.start(1000)
            self.play_pause_btn.setText("Pause")
            self.running = True
            run_mode = RunMode.play
        else:
            self.timer.stop()
            self.play_pause_btn.setText("Play")
            self.running = False
            run_mode = RunMode.paused
        self.play_pause_clicked.emit(run_mode)

    def reset_button_clicked(self):
        self.reset_clicked.emit()
        self.timer.stop()
        self.elapsed = QTime(0, 0, 0)
        self.time_label.setText("00:00:00")
        self.play_pause_btn.setText("Play")
        self.running = False

    def update_time(self):
        self.elapsed = self.elapsed.addSecs(1)
        now_str = self.elapsed.toString("hh:mm:ss")
        self.time_label.setText(now_str)

        if now_str in self.targets:
            message = self.targets[now_str]
            self.time_reached.emit(now_str, message)

    def _speak(self, t: str, message: str):
        """Queue text to be spoken in the background."""
        if LOGGER.level == logging.DEBUG:
            self.speaker.speak(message)
        LOGGER.debug(f"🗣 {t} → {message}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    stopwatch = Stopwatch()
    stopwatch.resize(250, 150)
    stopwatch.show()

    # Example: repeat notifications
    stopwatch.set_notifications({
        "00:00:05": "Five seconds have passed",
        "00:00:10": "Ten seconds reached"
    })

    sys.exit(app.exec())
