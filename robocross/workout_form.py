import logging
import re

from PySide6.QtWidgets import QWidget, QLineEdit, QCheckBox, QComboBox, QSpinBox, QGroupBox, QVBoxLayout, QGridLayout, QHBoxLayout, QLabel, QFormLayout, QMenu, QRadioButton
from PySide6.QtCore import QSettings, Qt

from core import APPLICATION_NAME, DEVELOPER
from core.logging_utils import get_logger
from widgets.form_widget import FormWidget


LOGGER: logging.Logger = get_logger(name=__name__, level=logging.DEBUG)


class WorkoutForm(FormWidget):
    default_workout_length = 30
    default_interval_time = 120
    default_rest_time = 30
    default_selected_categories = ["cardio", "strength"]  # Default categories
    workout_name_key = "workout name"
    length_key = "length"
    interval_key = "interval"
    rest_time_key = "rest time"
    warm_up_key = "warm_up"
    cool_down_key = "cool_down"

    def __init__(self, parent_widget: QWidget):
        super(WorkoutForm, self).__init__(title="Workout Parameters")
        self.parent_widget = parent_widget
        self.settings = QSettings(DEVELOPER, APPLICATION_NAME)

        # Weight tracking for exercise types
        self.category_weight_spinboxes: dict[str, QSpinBox] = {}
        self.category_weight_locks: dict[str, bool] = {}  # True = user modified (locked)

        # Workout Properties group box
        workout_props_group = QGroupBox("Workout Properties")
        workout_props_outer_layout = QVBoxLayout()

        # Top row: Workout Name spanning full width
        workout_name_layout = QFormLayout()
        self.workout_name_line_edit = QLineEdit(placeholderText="Untitled Workout")
        self.workout_name_line_edit.setToolTip("Name for this workout session (used when saving)")
        workout_name_layout.addRow("Workout Name:", self.workout_name_line_edit)
        workout_props_outer_layout.addLayout(workout_name_layout)

        # Bottom section: 2 columns
        workout_props_columns_layout = QHBoxLayout()

        # Left column: Basic workout properties
        left_form_layout = QFormLayout()

        self.workout_cycles_spin_box = QSpinBox()
        self.workout_cycles_spin_box.setMinimum(1)
        self.workout_cycles_spin_box.setMaximum(999)
        self.workout_cycles_spin_box.setToolTip("Number of times to repeat the circuit (total time = circuit length × cycles)")
        left_form_layout.addRow("Workout Cycles:", self.workout_cycles_spin_box)

        self.length_spin_box = QSpinBox()
        self.length_spin_box.setMinimum(0)
        self.length_spin_box.setMaximum(999)
        self.length_spin_box.setToolTip("Total duration of a single circuit in minutes")
        left_form_layout.addRow("Circuit Length (minutes):", self.length_spin_box)

        self.interval_spin_box = QSpinBox()
        self.interval_spin_box.setMinimum(0)
        self.interval_spin_box.setMaximum(999)
        self.interval_spin_box.setToolTip("Duration of each exercise in seconds")
        left_form_layout.addRow("Interval (seconds):", self.interval_spin_box)

        self.rest_time_spin_box = QSpinBox()
        self.rest_time_spin_box.setMinimum(0)
        self.rest_time_spin_box.setMaximum(999)
        self.rest_time_spin_box.setToolTip("Rest duration between exercises in seconds")
        left_form_layout.addRow("Approximate Rest Time (seconds):", self.rest_time_spin_box)

        # Right column: Warm up, Cool down, Workout mode
        right_options_layout = QVBoxLayout()
        right_options_layout.setSpacing(10)

        self.warm_up_checkbox = QCheckBox("Warm up")
        self.warm_up_checkbox.setToolTip("Force first exercise to be cardio")
        right_options_layout.addWidget(self.warm_up_checkbox)

        self.cool_down_checkbox = QCheckBox("Cool down")
        self.cool_down_checkbox.setToolTip("Force last exercise to be flexibility")
        right_options_layout.addWidget(self.cool_down_checkbox)

        # Add spacing before workout mode radio buttons
        right_options_layout.addSpacing(15)

        # Workout mode radio buttons
        mode_label = QLabel("Workout Mode:")
        mode_label.setStyleSheet("font-weight: bold;")
        right_options_layout.addWidget(mode_label)

        self.random_radio = QRadioButton("Random")
        self.random_radio.setToolTip("Use weighted probability to select exercises randomly")
        self.random_radio.setChecked(True)  # Default
        right_options_layout.addWidget(self.random_radio)

        self.sequence_radio = QRadioButton("Sequence")
        self.sequence_radio.setToolTip("Cycle through selected categories in a random repeating pattern")
        right_options_layout.addWidget(self.sequence_radio)

        right_options_layout.addStretch()

        # Add both columns to columns layout
        workout_props_columns_layout.addLayout(left_form_layout)
        workout_props_columns_layout.addSpacing(30)
        workout_props_columns_layout.addLayout(right_options_layout)

        # Add columns layout to outer layout
        workout_props_outer_layout.addLayout(workout_props_columns_layout)

        workout_props_group.setLayout(workout_props_outer_layout)
        self.layout().addRow(workout_props_group)

        # Category and target checkboxes (read from workout data)
        self.category_checkboxes: dict[str, QCheckBox] = {}
        self.target_checkboxes: dict[str, QCheckBox] = {}
        from robocross.workout_data import WorkoutData
        from robocross.robocross_enums import Target
        workout_data = WorkoutData()
        category_tooltips = {
            "cardio": "Include cardiovascular exercises (running, jumping, etc.)",
            "strength": "Include strength training exercises (weights, resistance, etc.)",
            "combat": "Include combat/martial arts exercises",
            "flexibility": "Include stretching and flexibility exercises"
        }

        # Create group box for exercise details with categories and targets
        self.exercise_details_group = QGroupBox("Exercise Details")
        main_layout = QHBoxLayout()  # Main horizontal layout

        # Left side: Categories with weights
        categories_layout = QVBoxLayout()
        categories_label = QLabel("Exercise Types:")
        categories_label.setStyleSheet("font-weight: bold;")
        categories_layout.addWidget(categories_label)

        # Read categories from workout data (top-level keys in JSON)
        categories = sorted(workout_data.categories)
        for category in categories:
            # Create horizontal row: [Checkbox] [Label] [SpinBox]
            row_layout = QHBoxLayout()

            # Checkbox (30px fixed width)
            checkbox = QCheckBox()
            checkbox.setFixedWidth(30)
            checkbox.setToolTip(category_tooltips.get(category, f"Include {category} exercises"))

            # Category label (expanding)
            label = QLabel(category.title())
            label.setMinimumWidth(100)

            # Weight spinbox (80px fixed, 0-100 range, "%" suffix)
            spinbox = QSpinBox()
            spinbox.setRange(0, 100)
            spinbox.setSuffix("%")
            spinbox.setFixedWidth(80)
            spinbox.setToolTip("Percentage weight for this category (total must = 100%)")

            # Add widgets to row
            row_layout.addWidget(checkbox)
            row_layout.addWidget(label)
            row_layout.addWidget(spinbox)
            row_layout.addStretch()

            # Add row to categories layout
            categories_layout.addLayout(row_layout)

            # Store references
            self.category_checkboxes[category] = checkbox
            self.category_weight_spinboxes[category] = spinbox
            self.category_weight_locks[category] = False  # Initialize as unlocked

        categories_layout.addStretch()

        # Right side: Target checkboxes (in 2 columns)
        targets_layout = QVBoxLayout()
        targets_label = QLabel("Exercise Targets:")
        targets_label.setStyleSheet("font-weight: bold;")
        targets_layout.addWidget(targets_label)

        # All checkbox at the top
        self.all_targets_checkbox = QCheckBox("All")
        self.all_targets_checkbox.setChecked(True)  # Default to all targets
        self.all_targets_checkbox.setToolTip("Include all body targets (disables individual target selection)")
        targets_layout.addWidget(self.all_targets_checkbox)

        # Add separator line
        targets_layout.addSpacing(5)

        # Individual target checkboxes in 2-column grid
        targets_grid = QGridLayout()
        targets_grid.setHorizontalSpacing(15)  # More space between columns
        targets_grid.setVerticalSpacing(5)

        targets = sorted([member.name for member in Target])
        for index, target in enumerate(targets):
            checkbox = QCheckBox(target.replace('_', ' ').title())
            checkbox.setToolTip(f"Include exercises targeting {target.replace('_', ' ')}")
            checkbox.setEnabled(False)  # Disabled when "All" is checked
            checkbox.setMinimumWidth(100)  # Give checkboxes more width

            row = index // 2
            col = index % 2
            targets_grid.addWidget(checkbox, row, col)

            self.target_checkboxes[target] = checkbox

        targets_layout.addLayout(targets_grid)
        targets_layout.addStretch()

        # Combine left and right sides
        main_layout.addLayout(categories_layout)
        main_layout.addSpacing(30)  # Add space between columns
        main_layout.addLayout(targets_layout)

        self.exercise_details_group.setLayout(main_layout)
        self.layout().addRow(self.exercise_details_group)

        self.setup_ui()

    @property
    def interval(self) -> int:
        return self.interval_spin_box.value()

    @property
    def rest_time(self) -> int:
        return self.rest_time_spin_box.value()

    @property
    def length(self) -> int:
        return self.length_spin_box.value()

    @property
    def workout_cycles(self) -> int:
        return self.workout_cycles_spin_box.value()

    @property
    def selected_categories(self) -> list[str]:
        """Return list of selected category names."""
        return [category for category, checkbox in self.category_checkboxes.items() if checkbox.isChecked()]

    @property
    def category_weights(self) -> dict[str, int]:
        """Return dictionary mapping category names to weight percentages."""
        weights = {}
        for category, spinbox in self.category_weight_spinboxes.items():
            if self.category_checkboxes[category].isChecked():
                weights[category] = spinbox.value()
        return weights

    @property
    def warm_up(self) -> bool:
        """Return True if warm up is enabled (force first exercise to be cardio)."""
        return self.warm_up_checkbox.isChecked()

    @property
    def cool_down(self) -> bool:
        """Return True if cool down is enabled (force last exercise to be flexibility)."""
        return self.cool_down_checkbox.isChecked()

    @property
    def selected_targets(self) -> list[str]:
        """Return list of selected target names. Empty list means all targets."""
        if self.all_targets_checkbox.isChecked():
            return []  # Empty list means no filtering (all targets)

        # Return list of checked target names
        from robocross.robocross_enums import Target
        return [
            Target[target_name]
            for target_name, checkbox in self.target_checkboxes.items()
            if checkbox.isChecked()
        ]

    @property
    def workout_name(self) -> str:
        """Get workout name."""
        return self.workout_name_line_edit.text()

    @property
    def workout_name_snake_case(self) -> str:
        """Convert workout name to snake_case for filename."""
        name = self.workout_name.lower()
        # Replace non-alphanumeric with underscores
        name = re.sub(r'[^a-z0-9]+', '_', name)
        # Strip leading/trailing underscores
        return name.strip('_')

    @property
    def workout_structure(self) -> str:
        """Return 'Random' or 'Sequence' based on radio button selection."""
        return "Random" if self.random_radio.isChecked() else "Sequence"

    def _save_workout_name_to_settings(self):
        """Save workout name to settings."""
        workout_name = self.workout_name_line_edit.text()
        self.settings.setValue(self.workout_name_key, workout_name)
        LOGGER.debug(f"Saved workout name to settings: {workout_name}")

    def calculate_default_weights(self) -> dict[str, int]:
        """Calculate even distribution among checked categories."""
        checked = [cat for cat, cb in self.category_checkboxes.items() if cb.isChecked()]
        if not checked:
            return {}

        base = 100 // len(checked)
        remainder = 100 % len(checked)

        return {
            cat: base + (1 if i < remainder else 0)
            for i, cat in enumerate(checked)
        }

    def recalculate_weights(self, modified_category: str = None):
        """Recalculate weights to sum to 100, keeping locked values fixed."""

        # 1. Lock the category that was just modified
        if modified_category:
            self.category_weight_locks[modified_category] = True
            self.apply_yellow_background(modified_category)

        # 2. Get checked categories
        checked = [cat for cat, cb in self.category_checkboxes.items() if cb.isChecked()]
        if not checked:
            return

        # 3. Calculate locked sum and identify unlocked categories
        locked_sum = sum(
            self.category_weight_spinboxes[cat].value()
            for cat in checked
            if self.category_weight_locks.get(cat, False)
        )

        unlocked = [cat for cat in checked if not self.category_weight_locks.get(cat, False)]

        # 4. Distribute remaining weight (100 - locked_sum) evenly among unlocked
        remaining = 100 - locked_sum
        if unlocked and remaining >= 0:
            base_weight = remaining // len(unlocked)
            remainder_weight = remaining % len(unlocked)

            for i, category in enumerate(unlocked):
                weight = base_weight + (1 if i < remainder_weight else 0)
                self.category_weight_spinboxes[category].blockSignals(True)
                self.category_weight_spinboxes[category].setValue(weight)
                self.category_weight_spinboxes[category].blockSignals(False)

        # 5. Handle edge case: locked weights exceed 100
        elif remaining < 0 and not unlocked:
            self.handle_overflow(checked)

        # 6. Save to settings
        self.save_weights_to_settings()

    def handle_overflow(self, checked_categories: list[str]):
        """Handle case where locked weights exceed 100% by proportionally reducing them."""
        locked_categories = [
            cat for cat in checked_categories
            if self.category_weight_locks.get(cat, False)
        ]

        if not locked_categories:
            return

        # Get current locked weights
        locked_weights = {
            cat: self.category_weight_spinboxes[cat].value()
            for cat in locked_categories
        }

        total_locked = sum(locked_weights.values())
        if total_locked == 0:
            return

        # Proportionally scale down to 100
        for category, weight in locked_weights.items():
            new_weight = int(round(weight * 100 / total_locked))
            self.category_weight_spinboxes[category].blockSignals(True)
            self.category_weight_spinboxes[category].setValue(new_weight)
            self.category_weight_spinboxes[category].blockSignals(False)

        LOGGER.info("Locked weights exceeded 100%, adjusted proportionally")

    def on_category_toggled(self, category: str):
        """Handle checkbox state change - unlock all and recalculate."""
        # Unlock all categories and recalculate
        for cat in self.category_weight_locks:
            self.category_weight_locks[cat] = False
            self.clear_yellow_background(cat)

        defaults = self.calculate_default_weights()
        for cat, weight in defaults.items():
            self.category_weight_spinboxes[cat].blockSignals(True)
            self.category_weight_spinboxes[cat].setValue(weight)
            self.category_weight_spinboxes[cat].blockSignals(False)

        # Disable spinboxes for unchecked categories
        for cat, checkbox in self.category_checkboxes.items():
            self.category_weight_spinboxes[cat].setEnabled(checkbox.isChecked())

        self.save_weights_to_settings()

    def on_all_targets_toggled(self):
        """Handle 'All' targets checkbox - enable/disable individual target checkboxes."""
        all_checked = self.all_targets_checkbox.isChecked()

        # Enable/disable all individual target checkboxes
        for checkbox in self.target_checkboxes.values():
            checkbox.setEnabled(not all_checked)

        # Save state
        self.settings.setValue("all_targets", all_checked)

    def apply_yellow_background(self, category: str):
        """Apply subtle highlight to locked spinbox."""
        spinbox = self.category_weight_spinboxes[category]
        spinbox.setStyleSheet("""
            QSpinBox {
                background-color: #4A4520;
                border-left: 3px solid #D4A574;
                font-weight: bold;
            }
        """)

    def clear_yellow_background(self, category: str):
        """Remove yellow background from unlocked spinbox."""
        self.category_weight_spinboxes[category].setStyleSheet("")

    def setup_context_menu(self):
        """Add right-click context menu to Exercise Details group box."""
        self.exercise_details_group.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.exercise_details_group.customContextMenuRequested.connect(self.show_reset_menu)

    def show_reset_menu(self, pos):
        """Show context menu with reset option."""
        menu = QMenu(self.exercise_details_group)
        reset_action = menu.addAction("Reset All Weights to Default")

        action = menu.exec(self.exercise_details_group.mapToGlobal(pos))

        if action == reset_action:
            self.reset_all_weights()

    def reset_all_weights(self):
        """Reset all weights to default and unlock all."""
        # Clear all locks
        for category in self.category_weight_locks:
            self.category_weight_locks[category] = False
            self.clear_yellow_background(category)

        # Recalculate default weights
        defaults = self.calculate_default_weights()
        for category, weight in defaults.items():
            self.category_weight_spinboxes[category].blockSignals(True)
            self.category_weight_spinboxes[category].setValue(weight)
            self.category_weight_spinboxes[category].blockSignals(False)

        # Set unchecked categories to 0
        for category, checkbox in self.category_checkboxes.items():
            if not checkbox.isChecked():
                self.category_weight_spinboxes[category].blockSignals(True)
                self.category_weight_spinboxes[category].setValue(0)
                self.category_weight_spinboxes[category].blockSignals(False)

        self.save_weights_to_settings()
        LOGGER.info("Reset all category weights to default")

    def save_weights_to_settings(self):
        """Save weight values and lock states to QSettings."""
        for category, spinbox in self.category_weight_spinboxes.items():
            # Save weight value
            self.settings.setValue(f"category_weight_{category}", spinbox.value())
            # Save lock state
            is_locked = self.category_weight_locks.get(category, False)
            self.settings.setValue(f"category_lock_{category}", is_locked)

    def load_weights_from_settings(self):
        """Load saved weights or use defaults for first run."""
        # Check if any weights are saved
        has_saved_weights = any(
            self.settings.contains(f"category_weight_{cat}")
            for cat in self.category_checkboxes.keys()
        )

        if not has_saved_weights:
            # First run - use defaults
            defaults = self.calculate_default_weights()
            for category, weight in defaults.items():
                self.category_weight_spinboxes[category].setValue(weight)
            # Set unchecked categories to 0
            for category, checkbox in self.category_checkboxes.items():
                if not checkbox.isChecked():
                    self.category_weight_spinboxes[category].setValue(0)
            return

        # Load saved values
        for category, spinbox in self.category_weight_spinboxes.items():
            # Load weight value
            weight = self.settings.value(f"category_weight_{category}", 0, type=int)
            spinbox.setValue(weight)

            # Load lock state
            is_locked = self.settings.value(f"category_lock_{category}", False, type=bool)
            self.category_weight_locks[category] = is_locked
            if is_locked:
                self.apply_yellow_background(category)

        # Disable spinboxes for unchecked categories
        for category, checkbox in self.category_checkboxes.items():
            self.category_weight_spinboxes[category].setEnabled(checkbox.isChecked())

    def setup_ui(self):
        self.workout_name_line_edit.setText(self.settings.value(self.workout_name_key, ""))
        # Save workout name to settings when editing is finished (return pressed or focus lost)
        self.workout_name_line_edit.editingFinished.connect(self._save_workout_name_to_settings)
        self.length_spin_box.setValue(self.settings.value(self.length_key, self.default_workout_length))
        self.interval_spin_box.setValue(self.settings.value(self.interval_key, self.default_interval_time))
        self.rest_time_spin_box.setValue(self.settings.value(self.rest_time_key, self.default_rest_time))
        self.workout_cycles_spin_box.setValue(1)  # Always defaults to 1 (NOT saved to settings)

        # Initialize category checkboxes from settings
        for category, checkbox in self.category_checkboxes.items():
            # Default to checked if in default_selected_categories
            default_checked = category in self.default_selected_categories
            is_checked = self.settings.value(f"category_{category}", default_checked, type=bool)
            checkbox.setChecked(is_checked)

        # Load weight values and lock states from settings
        self.load_weights_from_settings()

        # Load warm up and cool down checkbox states
        self.warm_up_checkbox.setChecked(self.settings.value("warm_up", False, type=bool))
        self.cool_down_checkbox.setChecked(self.settings.value("cool_down", False, type=bool))

        # Connect warm up and cool down signals to save state
        self.warm_up_checkbox.stateChanged.connect(
            lambda: self.settings.setValue("warm_up", self.warm_up_checkbox.isChecked())
        )
        self.cool_down_checkbox.stateChanged.connect(
            lambda: self.settings.setValue("cool_down", self.cool_down_checkbox.isChecked())
        )

        # Load workout structure radio button state
        workout_structure = self.settings.value("workout_structure", "Random", type=str)
        if workout_structure == "Sequence":
            self.sequence_radio.setChecked(True)
        else:
            self.random_radio.setChecked(True)

        # Connect radio button signals to save state
        self.random_radio.toggled.connect(
            lambda checked: self.settings.setValue("workout_structure", "Random") if checked else None
        )
        self.sequence_radio.toggled.connect(
            lambda checked: self.settings.setValue("workout_structure", "Sequence") if checked else None
        )

        # Connect checkbox signals
        for category, checkbox in self.category_checkboxes.items():
            # Save checkbox state and recalculate weights
            checkbox.stateChanged.connect(
                lambda state, cat=category: (
                    self.settings.setValue(f"category_{cat}", self.category_checkboxes[cat].isChecked()),
                    self.on_category_toggled(cat)
                )
            )

        # Connect spinbox signals (lock and recalculate when manually changed)
        for category, spinbox in self.category_weight_spinboxes.items():
            spinbox.valueChanged.connect(
                lambda value, cat=category: self.recalculate_weights(cat)
            )

        # Setup context menu for resetting weights
        self.setup_context_menu()

        # Initialize target checkboxes from settings
        all_targets_checked = self.settings.value("all_targets", True, type=bool)
        self.all_targets_checkbox.setChecked(all_targets_checked)

        for target_name, checkbox in self.target_checkboxes.items():
            # Load individual target checkbox state
            is_checked = self.settings.value(f"target_{target_name}", False, type=bool)
            checkbox.setChecked(is_checked)
            # Enable/disable based on "All" checkbox
            checkbox.setEnabled(not all_targets_checked)

        # Connect "All" checkbox to enable/disable individual targets
        self.all_targets_checkbox.stateChanged.connect(self.on_all_targets_toggled)

        # Connect individual target checkboxes to save state
        for target_name, checkbox in self.target_checkboxes.items():
            checkbox.stateChanged.connect(
                lambda state, tn=target_name: self.settings.setValue(f"target_{tn}", self.target_checkboxes[tn].isChecked())
            )

        # Initialize warm up and cool down checkboxes from settings
        warm_up_enabled = self.settings.value(self.warm_up_key, False, type=bool)
        self.warm_up_checkbox.setChecked(warm_up_enabled)
        cool_down_enabled = self.settings.value(self.cool_down_key, False, type=bool)
        self.cool_down_checkbox.setChecked(cool_down_enabled)

        # Connect signals
        self.workout_name_line_edit.textChanged.connect(self._on_workout_name_changed)
        self.length_spin_box.valueChanged.connect(lambda: self.settings.setValue(self.length_key, self.length))
        self.interval_spin_box.valueChanged.connect(lambda: self.settings.setValue(self.interval_key, self.interval))
        self.rest_time_spin_box.valueChanged.connect(lambda: self.settings.setValue(self.rest_time_key, self.rest_time))
        self.warm_up_checkbox.stateChanged.connect(lambda: self.settings.setValue(self.warm_up_key, self.warm_up))
        self.cool_down_checkbox.stateChanged.connect(lambda: self.settings.setValue(self.cool_down_key, self.cool_down))

    def _on_workout_name_changed(self):
        """Filter workout name input to only allow lowercase letters and underscores."""
        current_text = self.workout_name_line_edit.text()
        cursor_position = self.workout_name_line_edit.cursorPosition()

        # Convert to lowercase and replace invalid characters with underscores
        filtered_text = ""
        for char in current_text:
            if char.islower() or char == '_':
                filtered_text += char
            elif char.isupper():
                filtered_text += char.lower()
            elif char == ' ' or not char.isalnum():
                # Spaces and special characters become underscores
                if filtered_text and filtered_text[-1] != '_':  # Avoid consecutive underscores
                    filtered_text += '_'
            # Numbers are ignored (not added)

        # Update if changed
        if filtered_text != current_text:
            self.workout_name_line_edit.blockSignals(True)
            self.workout_name_line_edit.setText(filtered_text)
            self.workout_name_line_edit.setCursorPosition(min(cursor_position, len(filtered_text)))
            self.workout_name_line_edit.blockSignals(False)

        # Save to settings
        self.settings.setValue(self.workout_name_key, filtered_text)