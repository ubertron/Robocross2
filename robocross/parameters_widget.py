import logging

from functools import partial

from PySide6.QtWidgets import QCheckBox, QWidget, QLabel, QSizePolicy, QFrame
from PySide6.QtCore import Signal, Qt, QSettings

from core import DEVELOPER
from core.core_enums import Alignment
from core.core_paths import image_path
from robocross.robocross_enums import Equipment
from robocross.workout_form import WorkoutForm
from robocross.workout_editor_table import WorkoutEditorTable
from robocross.workout_data import WorkoutData
from robocross.workout import Workout
from widgets.generic_widget import GenericWidget
from widgets.scroll_widget import ScrollWidget


class ParametersWidget(GenericWidget):
    """Widget storing the workout parameters."""

    new_workout_clicked = Signal()
    load_button_clicked = Signal()
    save_button_clicked = Signal()
    build_button_clicked = Signal()
    add_exercise_clicked = Signal()
    workout_name_changed = Signal(str)  # Emits the workout name
    title = "Robocross Parameters Widget"

    def __init__(self):
        super().__init__(title=self.title)
        self.settings = QSettings(DEVELOPER, self.title)
        self.button_bar = self.add_button_bar()
        self.button_bar.add_icon_button(icon_path=image_path("new.png"), tool_tip="New workout - reset all parameters",
                                        clicked=self.new_workout_clicked.emit)
        self.button_bar.add_icon_button(icon_path=image_path("open.png"), tool_tip="Load saved workout session",
                                        clicked=self.load_button_clicked.emit)
        self.button_bar.add_icon_button(icon_path=image_path("save.png"), tool_tip="Save workout session",
                                        clicked=self.save_button_clicked.emit)
        self.button_bar.add_icon_button(icon_path=image_path("build.png"), tool_tip="Build the workout based on the info",
                                        clicked=self.build_button_clicked.emit)
        self.button_bar.add_icon_button(icon_path=image_path("add.png"), tool_tip="Manually add exercise to workout",
                                        clicked=self.add_exercise_clicked.emit)
        self.button_bar.add_stretch()
        content_pane = self.add_widget(GenericWidget(alignment=Alignment.horizontal))
        self.form: WorkoutForm = content_pane.add_widget(WorkoutForm(parent_widget=self))
        equipment_widget = content_pane.add_widget(GenericWidget())
        equipment_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        equipment_widget.add_label("Equipment List")
        self.equipment_check_boxes = [equipment_widget.add_widget(QCheckBox(x)) for x in self.equipment_names]

        # Summary section (outside scroll area)
        self.summary_frame = self.add_widget(QFrame())
        self.summary_frame.setFrameShape(QFrame.Shape.Box)
        self.summary_frame.setStyleSheet("QFrame { border: 2px solid #555; padding: 5px; margin: 2px; }")

        from PySide6.QtWidgets import QVBoxLayout
        summary_layout = QVBoxLayout()
        summary_layout.setSpacing(2)
        summary_layout.setContentsMargins(5, 5, 5, 5)
        self.summary_frame.setLayout(summary_layout)

        # Workout name title (compact, no borders)
        self.summary_title = QLabel("")
        self.summary_title.setStyleSheet("font-size: 16px; font-weight: bold; border: none; background: transparent;")
        self.summary_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.summary_title.setFrameShape(QFrame.Shape.NoFrame)
        summary_layout.addWidget(self.summary_title)

        # Stats label (compact, no borders)
        self.summary_stats = QLabel("")
        self.summary_stats.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.summary_stats.setStyleSheet("font-size: 12px; border: none; background: transparent;")
        self.summary_stats.setFrameShape(QFrame.Shape.NoFrame)
        summary_layout.addWidget(self.summary_stats)

        # Editor table (in scroll area)
        workout_data = WorkoutData()
        available_exercises = [w.name for w in workout_data.workouts]

        # Organize exercises by category
        exercises_by_category = {'cardio': [], 'strength': []}
        for workout in workout_data.workouts:
            if workout.aerobic_type.name == 'cardio':
                exercises_by_category['cardio'].append(workout.name)
            elif workout.aerobic_type.name == 'strength':
                exercises_by_category['strength'].append(workout.name)

        self.editor_table = self.add_widget(WorkoutEditorTable(available_exercises, exercises_by_category))

        # Connect table changes to update summary
        self.editor_table.workout_list_changed.connect(self.update_summary)

        # Connect workout name field to update summary on Return key
        self.form.workout_name_line_edit.returnPressed.connect(self.on_workout_name_changed)

        self.setup_ui()

        # Initial summary update
        self.update_summary()

    @property
    def equipment_names(self):
        names = [member.name.title().replace('_', ' ') for member in Equipment]
        names.sort()
        return names

    @property
    def equipment_filter(self) -> list[Equipment]:
        """List of equipment being used."""
        return [Equipment.__members__.get(x.text().lower().replace(' ', '_')) \
                for x in self.equipment_check_boxes if not x.isChecked()]

    @property
    def zero_equipment(self) -> bool:
        """Return true if no equipment selected."""
        return len(self.equipment_filter) == len(Equipment)

    @property
    def info(self) -> str:
        """Info text for logging."""
        return getattr(self, '_info_text', '')

    @info.setter
    def info(self, value: str):
        """Log info text instead of displaying."""
        self._info_text = value
        if value:
            from core.logging_utils import get_logger
            LOGGER = get_logger(name=__name__, level=logging.INFO)
            LOGGER.info(f"ParametersWidget: {value}")

    def check_state_changed(self, *args):
        """Event for check box changed."""
        check_box = next(x for x in args if type(x) is QCheckBox)
        self.settings.setValue(check_box.text(), check_box.isChecked())

    def setup_ui(self):
        for checkbox in self.equipment_check_boxes:
            checkbox.setChecked(self.settings.value(checkbox.text(), True))
            checkbox.checkStateChanged.connect(partial(self.check_state_changed, checkbox))

    def set_workout_list(self, workouts: list[Workout], rest_time: int = 30, workout_name: str = ""):
        """Populate editor table with workout list."""
        self.editor_table.set_workout_list(workouts, rest_time, workout_name)

    def get_workout_list(self) -> tuple[list[Workout], list[int]]:
        """Get workout list and rest times from editor table."""
        return self.editor_table.get_workout_list()

    def on_workout_name_changed(self):
        """Handle workout name change from form field."""
        # Update the editor table's workout name
        self.editor_table.workout_name = self.form.workout_name
        # Update the summary display
        self.update_summary()
        # Emit signal so viewer can update
        self.workout_name_changed.emit(self.form.workout_name)

    def update_summary(self):
        """Update summary panel with current workout stats."""
        summary_data = self.editor_table.get_summary_data()

        # Format workout name nicely (capitalize, underscores to spaces)
        raw_name = summary_data['workout_name']
        if raw_name:
            # Convert snake_case to Title Case
            workout_name = raw_name.replace('_', ' ').title()
        else:
            workout_name = "Untitled Workout"
        self.summary_title.setText(workout_name)

        if summary_data['num_exercises'] == 0:
            self.summary_stats.setText("No exercises added yet")
        else:
            from core import time_utils
            total_time = summary_data['total_time'] + summary_data['total_rest']
            stats_text = (
                f"Workout time: {time_utils.time_nice(summary_data['total_time'])}\n"
                f"Rest time: {time_utils.time_nice(summary_data['total_rest'])}\n"
                f"Total time: {time_utils.time_nice(total_time)}\n"
                f"Exercises: {summary_data['num_exercises']}\n"
                f"Total calories: {int(summary_data['total_calories'])}"
            )
            self.summary_stats.setText(stats_text)
