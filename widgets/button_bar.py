from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import QSizePolicy

from widgets.generic_widget import GenericWidget
from core.core_enums import Alignment

class ButtonBar(GenericWidget):
    def __init__(self, parent=None):
        super(ButtonBar, self).__init__(alignment=Alignment.horizontal, margin=0, spacing=0)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum))

    def add_icon_button(self, image: Path, tool_tip: str, clicked: Callable):
        """Add icon button to the layout"""