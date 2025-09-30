"""Class to handle the splash screen."""

from pathlib import Path

from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import QTimer, QPropertyAnimation, QEasingCurve, Qt

from core import SANS_SERIF_FONT


class SplashScreenManager:
    def __init__(self, splash_image_path: Path, message: str):
        # Create a QPixmap from the image file
        pixmap = QPixmap(splash_image_path.as_posix())
        self.message = message

        # Create the splash screen
        self.splash = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
        self.splash.setFont(QFont(SANS_SERIF_FONT, 24))

        # This will hold the QPropertyAnimation to prevent it from being garbage collected
        self.animation = None

    def show_splash(self, pause_duration_ms=3000, fade_duration_ms=1000):
        # Show the splash screen
        self.splash.show()
        self.splash.showMessage(self.message, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft, Qt.GlobalColor.white)

        # Use a single-shot timer to pause before starting the fade-out
        QTimer.singleShot(pause_duration_ms, lambda: self.start_fade_out(fade_duration_ms))

        # Process events to ensure the splash screen paints immediately
        QApplication.processEvents()

    def start_fade_out(self, duration_ms):
        # Create a QPropertyAnimation for the window's opacity
        self.animation = QPropertyAnimation(self.splash, b"windowOpacity")
        self.animation.setDuration(duration_ms)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.setEasingCurve(QEasingCurve.OutQuad) # Optional: Adds a smooth curve to the fade

        # Connect the finished signal to close the splash screen
        self.animation.finished.connect(self.splash.close)

        # Start the animation
        self.animation.start()