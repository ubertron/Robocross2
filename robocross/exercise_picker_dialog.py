"""Dialog for picking exercises from a hierarchical tree view."""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt


class ExercisePickerDialog(QDialog):
    """Dialog with tree view for selecting exercises by category."""

    def __init__(self, exercises_by_category: dict, current_exercise: str = None, parent=None):
        """
        Initialize the exercise picker dialog.

        Args:
            exercises_by_category: Dict with 'cardio' and 'strength' keys, each containing list of exercise names
            current_exercise: Currently selected exercise name
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Select Exercise")
        self.selected_exercise = current_exercise
        self.setup_ui(exercises_by_category, current_exercise)

    def setup_ui(self, exercises_by_category: dict, current_exercise: str):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Create tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Exercises")
        self.tree.setAlternatingRowColors(True)
        layout.addWidget(self.tree)

        # Populate tree with categories
        for category_name, exercises in sorted(exercises_by_category.items()):
            # Create category item
            category_item = QTreeWidgetItem(self.tree)
            category_item.setText(0, category_name.title())
            category_item.setFlags(category_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)  # Make non-selectable
            category_item.setExpanded(True)

            # Add exercises under category (sorted alphabetically)
            for exercise_name in sorted(exercises):
                nice_name = exercise_name.replace('_', ' ').title()
                exercise_item = QTreeWidgetItem(category_item)
                exercise_item.setText(0, nice_name)
                exercise_item.setData(0, Qt.ItemDataRole.UserRole, exercise_name)  # Store actual name

                # Highlight current selection
                if exercise_name == current_exercise:
                    self.tree.setCurrentItem(exercise_item)

        # Connect double-click to accept
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)

        # Add buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.resize(400, 500)

    def on_item_double_clicked(self, item, column):
        """Handle double-click on an item."""
        # Only accept if it's an exercise (not a category)
        if item.parent() is not None:
            self.accept()

    def accept(self):
        """Store selected exercise before accepting."""
        current_item = self.tree.currentItem()
        if current_item and current_item.parent() is not None:
            # It's an exercise (has a parent category)
            self.selected_exercise = current_item.data(0, Qt.ItemDataRole.UserRole)
        super().accept()

    @staticmethod
    def get_exercise(exercises_by_category: dict, current_exercise: str = None, parent=None):
        """
        Show dialog and return selected exercise.

        Args:
            exercises_by_category: Dict with 'cardio' and 'strength' keys
            current_exercise: Currently selected exercise
            parent: Parent widget

        Returns:
            tuple: (exercise_name, ok_pressed)
        """
        dialog = ExercisePickerDialog(exercises_by_category, current_exercise, parent)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            return dialog.selected_exercise, True
        return current_exercise, False
