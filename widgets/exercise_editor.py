import json
import shutil
from pathlib import Path
from functools import partial

from PySide6.QtWidgets import QCheckBox, QTextEdit, QLineEdit, QFileDialog, QMessageBox
from PySide6.QtCore import Qt

from widgets.generic_widget import GenericWidget
from widgets.button_bar import ButtonBar
from core.core_paths import image_path, MEDIA_ROOT, DATA_FILE_PATH
from widgets.form_widget import FormWidget
from core.core_enums import Alignment
from widgets.image_label import ImageLabel
from robocross import WORKOUT_CATEGORIES
from robocross.robocross_enums import Equipment, Target
from robocross.exercise_picker_dialog import ExercisePickerDialog


DEFAULT_IMAGE_1 = MEDIA_ROOT / "images" / "default_image_01.png"
DEFAULT_IMAGE_2 = MEDIA_ROOT / "images" / "default_image_02.png"
DEFAULT_IMAGE_3 = MEDIA_ROOT / "images" / "default_image_03.png"
BACKUP_DATA_FILE = DATA_FILE_PATH.parent / "workout_data_backup.json"


class ExerciseEditor(GenericWidget):
    def __init__(self):
        super().__init__(title="Exercise Editor")

        # Current state
        self.current_category = None
        self.current_exercise_name = None
        self.current_media_path = DEFAULT_IMAGE_1

        # Button bar
        button_bar: ButtonBar = self.add_widget(ButtonBar())
        button_bar.add_icon_button(icon_path=image_path("new.png"), tool_tip="Add a new exercise", clicked=self._new_button_clicked)
        button_bar.add_icon_button(icon_path=image_path("save.png"), tool_tip="Save exercise", clicked=self._save_button_clicked)
        button_bar.add_icon_button(icon_path=image_path("open.png"), tool_tip="Open exercise", clicked=self._open_button_clicked)
        button_bar.add_icon_button(icon_path=image_path("delete.png"), tool_tip="Delete exercise", clicked=self._delete_button_clicked)
        button_bar.add_icon_button(icon_path=image_path("restore.png"), tool_tip="Restore default exercises", clicked=self._restore_button_clicked)
        button_bar.add_stretch()

        # Main content area
        content_widget = self.add_widget(GenericWidget(alignment=Alignment.horizontal))

        # Left side - Form and checkboxes
        left_panel = content_widget.add_widget(GenericWidget())

        # Form section
        self.form: FormWidget = left_panel.add_widget(FormWidget())
        self.exercise_name_field = self.form.add_line_edit(label="Exercise Name", placeholder_text="lowercase and spaces only")
        self.category_combo_box = self.form.add_combo_box(label="Category", items=WORKOUT_CATEGORIES)

        # Description field (text edit)
        self.description_field = QTextEdit()
        self.description_field.setPlaceholderText("lowercase letters, punctuation, and spaces")
        self.description_field.setMaximumHeight(80)
        self.form.add_row(label="Description", widget=self.description_field)

        # Intensity and Energy
        self.intensity_combo = self.form.add_combo_box(label="Intensity", items=["low", "medium", "high"], default_index=1)
        self.energy_field = self.form.add_float_field(label="Energy (cal/min)", default_value=10.0)

        # Equipment checkboxes (outside form)
        equipment_widget = left_panel.add_widget(GenericWidget())
        self.equipment_checkboxes = {}
        equipment_label = equipment_widget.add_label("Equipment:")
        for eq in Equipment:
            cb = QCheckBox(eq.name.replace('_', ' ').title())
            self.equipment_checkboxes[eq.name] = equipment_widget.add_widget(cb)

        # Target checkboxes (outside form)
        target_widget = left_panel.add_widget(GenericWidget())
        self.target_checkboxes = {}
        target_label = target_widget.add_label("Target:")
        for tgt in Target:
            cb = QCheckBox(tgt.name.replace('_', ' ').title())
            self.target_checkboxes[tgt.name] = target_widget.add_widget(cb)

        # Sub-workouts section (outside form)
        subworkouts_widget = left_panel.add_widget(GenericWidget())
        self.subworkouts_checkbox = QCheckBox("Enable Sub-workouts")
        self.subworkouts_checkbox.toggled.connect(self._on_subworkouts_toggled)
        subworkouts_widget.add_widget(self.subworkouts_checkbox)

        self.subworkout_fields = []
        for i in range(4):
            field = subworkouts_widget.add_widget(QLineEdit())
            field.setPlaceholderText(f"Sub-workout {i+1} name...")
            field.setVisible(False)
            self.subworkout_fields.append(field)

        # Right side - Media
        media_loader = content_widget.add_widget(GenericWidget())
        self.image_label: ImageLabel = media_loader.add_widget(ImageLabel(path=DEFAULT_IMAGE_1))
        self.thumbnail_widget: ButtonBar = media_loader.add_widget(ButtonBar(size=64))
        self._setup_thumbnails()

    def _setup_thumbnails(self, exercise_name: str = None):
        """Setup thumbnail buttons including exercise-specific media if it exists."""
        # Clear existing thumbnails
        while self.thumbnail_widget.layout().count():
            item = self.thumbnail_widget.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Always add browse button
        self.thumbnail_widget.add_icon_button(
            icon_path=image_path("open.png"),
            tool_tip="Load media",
            clicked=self._load_media_button_clicked
        )

        # Add exercise-specific media thumbnail if it exists
        if exercise_name:
            filename_base = exercise_name.replace(' ', '_')
            for ext in ['.png', '.jpg', '.jpeg', '.gif']:
                exercise_media_path = MEDIA_ROOT / "images" / f"{filename_base}{ext}"
                if exercise_media_path.exists():
                    self.thumbnail_widget.add_icon_button(
                        icon_path=exercise_media_path,
                        tool_tip=f"{exercise_name} image",
                        clicked=partial(self._thumbnail_clicked, exercise_media_path)
                    )
                    break

        # Always add default image thumbnails
        self.thumbnail_widget.add_icon_button(
            icon_path=DEFAULT_IMAGE_1,
            clicked=partial(self._thumbnail_clicked, DEFAULT_IMAGE_1)
        )
        self.thumbnail_widget.add_icon_button(
            icon_path=DEFAULT_IMAGE_2,
            clicked=partial(self._thumbnail_clicked, DEFAULT_IMAGE_2)
        )
        self.thumbnail_widget.add_icon_button(
            icon_path=DEFAULT_IMAGE_3,
            clicked=partial(self._thumbnail_clicked, DEFAULT_IMAGE_3)
        )

    def _thumbnail_clicked(self, image_path: Path):
        """Handle thumbnail button click."""
        self.current_media_path = image_path
        self.image_label.path = image_path

    def _on_subworkouts_toggled(self, checked: bool):
        """Toggle sub-workout fields visibility."""
        for field in self.subworkout_fields:
            field.setVisible(checked)

    def _load_media_button_clicked(self):
        """Open file dialog to select media."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Exercise Media",
            str(MEDIA_ROOT),
            "Media Files (*.png *.jpg *.jpeg *.gif *.mp4 *.mov *.avi);;All Files (*)"
        )
        if file_path:
            self.current_media_path = Path(file_path)
            self.image_label.path = self.current_media_path

    def _new_button_clicked(self):
        """Create new exercise."""
        self.current_category = None
        self.current_exercise_name = None
        self._clear_form()

    def _open_button_clicked(self):
        """Open exercise picker dialog."""
        # Load all exercises
        with DATA_FILE_PATH.open("r") as f:
            data = json.load(f)

        exercises_by_category = {cat: list(exercises.keys()) for cat, exercises in data.items()}

        dialog = ExercisePickerDialog(exercises_by_category, self.current_exercise_name, self)
        if dialog.exec():
            exercise_name = dialog.selected_exercise
            if exercise_name:
                # Find which category it belongs to
                for category, exercises in data.items():
                    if exercise_name in exercises:
                        self._load_exercise(category, exercise_name, exercises[exercise_name])
                        break

    def _save_button_clicked(self):
        """Save current exercise."""
        # Validate
        exercise_name = self.exercise_name_field.text().strip()
        if not exercise_name:
            QMessageBox.warning(self, "Validation Error", "Exercise name cannot be empty")
            return

        category = self.category_combo_box.currentText()

        # Get form data
        exercise_data = {
            "description": self.description_field.toPlainText().strip(),
            "equipment": [name for name, cb in self.equipment_checkboxes.items() if cb.isChecked()],
            "intensity": self.intensity_combo.currentText(),
            "target": [name for name, cb in self.target_checkboxes.items() if cb.isChecked()],
            "energy": self.energy_field.value()
        }

        # Add sub-workouts if enabled
        if self.subworkouts_checkbox.isChecked():
            sub_workouts = [f.text().strip() for f in self.subworkout_fields if f.text().strip()]
            if sub_workouts:
                exercise_data["sub_workouts"] = sub_workouts

        # Validate required fields
        if not exercise_data["description"]:
            QMessageBox.warning(self, "Validation Error", "Description cannot be empty")
            return
        if not exercise_data["target"]:
            QMessageBox.warning(self, "Validation Error", "At least one target area must be selected")
            return

        # Load current data
        with DATA_FILE_PATH.open("r") as f:
            data = json.load(f)

        # If category changed, delete from old category
        if self.current_category and self.current_category != category and self.current_exercise_name:
            if self.current_category in data and self.current_exercise_name in data[self.current_category]:
                del data[self.current_category][self.current_exercise_name]

        # Ensure category exists
        if category not in data:
            data[category] = {}

        # Save exercise
        data[category][exercise_name] = exercise_data

        # Write back to file
        with DATA_FILE_PATH.open("w") as f:
            json.dump(data, f, indent=4)

        # Save media (copy to exercise-specific filename)
        self._save_media(exercise_name)

        self.current_category = category
        self.current_exercise_name = exercise_name

        # Refresh thumbnails to include newly saved exercise media
        self._setup_thumbnails(exercise_name)

        QMessageBox.information(self, "Success", f"Exercise '{exercise_name}' saved successfully")

    def _delete_button_clicked(self):
        """Delete current exercise."""
        if not self.current_exercise_name or not self.current_category:
            QMessageBox.warning(self, "No Exercise", "No exercise selected to delete")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete exercise '{self.current_exercise_name}' from category '{self.current_category}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Load data
            with DATA_FILE_PATH.open("r") as f:
                data = json.load(f)

            # Delete exercise
            if self.current_category in data and self.current_exercise_name in data[self.current_category]:
                del data[self.current_category][self.current_exercise_name]

                # Write back
                with DATA_FILE_PATH.open("w") as f:
                    json.dump(data, f, indent=4)

                QMessageBox.information(self, "Success", f"Exercise '{self.current_exercise_name}' deleted")
                self._clear_form()

    def _restore_button_clicked(self):
        """Restore exercises from backup."""
        if not BACKUP_DATA_FILE.exists():
            QMessageBox.warning(self, "No Backup", "No backup file found")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Restore",
            "Restore workout data from backup?\n\nThis will overwrite all current exercise data.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            shutil.copy2(BACKUP_DATA_FILE, DATA_FILE_PATH)
            QMessageBox.information(self, "Success", "Workout data restored from backup")
            self._clear_form()

    def _load_exercise(self, category: str, exercise_name: str, exercise_data: dict):
        """Load exercise data into form."""
        self.current_category = category
        self.current_exercise_name = exercise_name

        # Set form fields
        self.exercise_name_field.setText(exercise_name)
        self.category_combo_box.setCurrentText(category)
        self.description_field.setPlainText(exercise_data.get("description", ""))

        # Set equipment checkboxes
        equipment_list = exercise_data.get("equipment", [])
        for name, cb in self.equipment_checkboxes.items():
            cb.setChecked(name in equipment_list)

        # Set target checkboxes
        target_list = exercise_data.get("target", [])
        for name, cb in self.target_checkboxes.items():
            cb.setChecked(name in target_list)

        # Set intensity and energy
        self.intensity_combo.setCurrentText(exercise_data.get("intensity", "medium"))
        self.energy_field.setValue(exercise_data.get("energy", 10.0))

        # Set sub-workouts
        sub_workouts = exercise_data.get("sub_workouts", [])
        if sub_workouts:
            self.subworkouts_checkbox.setChecked(True)
            for i, sub_workout in enumerate(sub_workouts):
                if i < len(self.subworkout_fields):
                    self.subworkout_fields[i].setText(sub_workout)
        else:
            self.subworkouts_checkbox.setChecked(False)

        # Setup thumbnails (including exercise-specific if it exists)
        self._setup_thumbnails(exercise_name)

        # Load media
        self._load_media_for_exercise(exercise_name)

    def _load_media_for_exercise(self, exercise_name: str):
        """Load media for exercise."""
        # Convert exercise name to filename (replace spaces with underscores)
        filename_base = exercise_name.replace(' ', '_')

        # Check for exercise-specific media files
        for ext in ['.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mov', '.avi']:
            media_path = MEDIA_ROOT / "images" / f"{filename_base}{ext}"
            if media_path.exists():
                self.current_media_path = media_path
                self.image_label.path = media_path
                return

            media_path = MEDIA_ROOT / "animations" / f"{filename_base}{ext}"
            if media_path.exists():
                self.current_media_path = media_path
                self.image_label.path = media_path
                return

            media_path = MEDIA_ROOT / "movies" / f"{filename_base}{ext}"
            if media_path.exists():
                self.current_media_path = media_path
                self.image_label.path = media_path
                return

        # Check for generic "media" file as fallback
        for ext in ['.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mov', '.avi']:
            media_path = MEDIA_ROOT / "images" / f"media{ext}"
            if media_path.exists():
                self.current_media_path = media_path
                self.image_label.path = media_path
                return

            media_path = MEDIA_ROOT / "animations" / f"media{ext}"
            if media_path.exists():
                self.current_media_path = media_path
                self.image_label.path = media_path
                return

            media_path = MEDIA_ROOT / "movies" / f"media{ext}"
            if media_path.exists():
                self.current_media_path = media_path
                self.image_label.path = media_path
                return

        # Final fallback to first default image
        self.current_media_path = DEFAULT_IMAGE_1
        self.image_label.path = DEFAULT_IMAGE_1

    def _save_media(self, exercise_name: str):
        """Save media file for exercise."""
        if not self.current_media_path.exists():
            return

        # Convert exercise name to filename (replace spaces with underscores)
        filename_base = exercise_name.replace(' ', '_')

        suffix = self.current_media_path.suffix.lower()

        # Determine destination directory
        if suffix in ['.mp4', '.mov', '.avi']:
            dest_dir = MEDIA_ROOT / "movies"
        elif suffix == '.gif':
            dest_dir = MEDIA_ROOT / "animations"
        else:
            dest_dir = MEDIA_ROOT / "images"

        dest_path = dest_dir / f"{filename_base}{suffix}"

        # Copy file
        shutil.copy2(self.current_media_path, dest_path)

    def _clear_form(self):
        """Clear all form fields."""
        self.current_category = None
        self.current_exercise_name = None

        self.exercise_name_field.clear()
        self.category_combo_box.setCurrentIndex(0)
        self.description_field.clear()

        # Clear checkboxes
        for cb in self.equipment_checkboxes.values():
            cb.setChecked(False)
        for cb in self.target_checkboxes.values():
            cb.setChecked(False)

        # Reset defaults
        self.intensity_combo.setCurrentIndex(1)  # medium
        self.energy_field.setValue(10.0)

        # Clear sub-workouts
        self.subworkouts_checkbox.setChecked(False)
        for field in self.subworkout_fields:
            field.clear()

        # Reset thumbnails to defaults only (no exercise-specific)
        self._setup_thumbnails()

        # Reset media
        self.current_media_path = DEFAULT_IMAGE_1
        self.image_label.path = DEFAULT_IMAGE_1


