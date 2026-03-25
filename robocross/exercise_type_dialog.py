"""Modal dialog for selecting exercise type when adding new exercises."""

import random
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from robocross import get_category_color, get_contrast_text_color


class ExerciseTypeDialog(QDialog):
    """Dialog for selecting exercise type/category."""

    category_selected = Signal(str)  # Emits the selected category name

    def __init__(self, categories: list[str], parent=None):
        """
        Initialize the exercise type selection dialog.

        Args:
            categories: List of category names (e.g., ['cardio', 'strength', ...])
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Select Exercise Type")
        self.setModal(True)
        self.selected_category = None

        # Setup UI
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title label
        title = QLabel("Choose an exercise type:")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Add spacing
        layout.addSpacing(10)

        # Create button for each category
        for category in categories:
            button = self._create_category_button(category)
            layout.addWidget(button)

        # Add spacing
        layout.addSpacing(10)

        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedHeight(40)
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)

        self.setLayout(layout)

        # Set minimum width
        self.setMinimumWidth(300)

    def _create_category_button(self, category: str) -> QPushButton:
        """
        Create a styled button for a category.

        Args:
            category: Category name (e.g., 'cardio', 'strength')

        Returns:
            Configured QPushButton
        """
        # Get category colors
        bg_color = get_category_color(category)
        text_color = get_contrast_text_color(bg_color)

        # Format button text (capitalize)
        button_text = category.capitalize()

        # Create button
        button = QPushButton(button_text)
        button.setFixedHeight(60)

        # Style with category color
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                font-size: 16pt;
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 5px;
                padding: 10px;
            }}
            QPushButton:hover {{
                border: 3px solid white;
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(bg_color)};
            }}
        """)

        # Connect to handler
        button.clicked.connect(lambda: self._on_category_selected(category))

        return button

    def _darken_color(self, hex_color: str, factor: float = 0.8) -> str:
        """Darken a hex color by a factor."""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)

        return f'#{r:02x}{g:02x}{b:02x}'

    def _on_category_selected(self, category: str):
        """Handle category button click."""
        self.selected_category = category
        self.category_selected.emit(category)
        self.accept()

    def get_selected_category(self) -> str | None:
        """
        Get the selected category after dialog closes.

        Returns:
            Category name or None if cancelled
        """
        return self.selected_category
