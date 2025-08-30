import os
from pathlib import Path

import qdarktheme

from PySide6.QtWidgets import QApplication, QPushButton
from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QPixmap, QIcon

from core.core_paths import image_path
from widgets.generic_widget import GenericWidget


class Icon(QIcon):
    def __init__(self, icon_path: str):
        super(Icon, self).__init__(QPixmap(icon_path))
        self.path = icon_path


class IconButton(QPushButton):
    checked = Signal(bool)

    def __init__(self, icon_path: Path, tool_tip: str = "", size: int = 40, margin: int = 2):
        """
        Creates a square button using an image file
        :param icon_path:
        :param size:
        :param text: optional text accompaniment
        """
        assert icon_path is not None, "Icon path invalid"
        super(IconButton, self).__init__()
        self.setToolTip(tool_tip if tool_tip else icon_path.stem)
        if icon_path.exists():
            self.setToolTip(tool_tip)
            self.setIcon(QIcon(QPixmap(icon_path)))
            self.setIconSize(QSize(size - 2 * margin, size - 2 * margin))
            self.setFixedSize(QSize(size, size))
        else:
            self.setFixedHeight(size)
            self.setStyleSheet("Text-align:center")


if __name__ == "__main__":
    app = QApplication()
    widget = GenericWidget("Icon Button Test Widget")
    icon_file_path = image_path("open_grey.png")
    icon_button = IconButton(icon_path=icon_file_path, tool_tip="Open Icon Button")
    widget.add_widget(icon_button)
    widget.resize(256, 256)
    widget.setStyleSheet(qdarktheme.load_stylesheet())
    widget.show()
    app.exec()