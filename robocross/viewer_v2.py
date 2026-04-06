from __future__ import annotations

import logging
import random
from collections import OrderedDict
from datetime import timedelta
from pathlib import Path
import tempfile

from PySide6.QtCore import Qt, QSize, QSettings
from PySide6.QtGui import QFont, QMovie, QIcon, QPixmap
from PySide6.QtWidgets import QSizePolicy, QLabel, QPushButton

from functools import partial
from core.core_enums import Alignment
from core import logging_utils, DEVELOPER
from core.speaker import Speaker, Voice
from core import SANS_SERIF_FONT
from core.core_paths import image_path
from core.image_utils import fill_foreground
from music_player.music_player_ui import MusicPlayer
from robocross import REST_PERIOD, APP_NAME
from robocross.robocross_enums import AerobicType, RunMode, Intensity
from robocross.workout import Workout
from robocross.workout_chip import WorkoutChip
from robocross.workout_dot import DotContainer
from robocross.media_loader import find_workout_media, VideoPlayerWidget
from widgets.generic_widget import GenericWidget
from widgets.stopwatch import Stopwatch
from widgets.image_label import ImageLabel

# Setup debug logging to file
LOG_PATH = Path(__file__).parents[1].joinpath("logs/workouts.log")
FILE_HANDLER = logging_utils.FileHandler(path=LOG_PATH, level=logging.DEBUG)
STREAM_HANDLER = logging_utils.StreamHandler(level=logging.INFO)
LOGGER = logging_utils.get_logger(name=__name__, level=logging.DEBUG, handlers=[FILE_HANDLER, STREAM_HANDLER])


class ViewerV2(GenericWidget):
    """Modern visual workout player with dot indicators and media display."""

    end_notification: str = "end of workout"
    period = 50  # evaluation time for timers

    def __init__(self):
        super(ViewerV2, self).__init__(title="Workout Player v2", margin=0, spacing=5)

        # Settings
        self.settings = QSettings(DEVELOPER, APP_NAME)
        self.narration_volume_key = "narration_volume"
        self.default_narration_volume = 7

        # State management (reused from v1)
        self._workout_list = []
        self._base_workout_list = []
        self.current_index = 0
        self._workout_cycles = 1
        self._current_circuit = 1
        self.run_mode = RunMode.paused
        self.started = False
        self.notification_dict = OrderedDict()
        self.sub_workout_times = {}
        self._rest_time = 0

        # Voice for announcements (with volume)
        narration_volume = self.settings.value(self.narration_volume_key, self.default_narration_volume, type=int)
        self.mac_voice = Speaker(
            voice=random.choice([Voice.Samantha, Voice.Daniel]),
            volume=narration_volume / 10.0
        )

        # Cache for tinted reset icon
        self._tinted_reset_icon_path = None

        # Build UI
        self.setup_ui()
        self.setup_connections()

    def _create_tinted_image(self, source_path: Path, rgb: tuple[int, int, int], cache_name: str = None) -> Path:
        """
        Create a tinted version of an image (cached in temp directory).

        Args:
            source_path: Path to the source image
            rgb: RGB tuple for tint color (e.g., (255, 255, 255) for white)
            cache_name: Optional cache name (defaults to source filename + color)

        Returns:
            Path to tinted image in temp directory
        """
        if not cache_name:
            color_hex = f"{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
            cache_name = f"{source_path.stem}_{color_hex}"

        cache_key = f"_tinted_{cache_name}"
        cached_path = getattr(self, cache_key, None)

        if cached_path and Path(cached_path).exists():
            return Path(cached_path)

        # Create tinted version
        temp_dir = Path(tempfile.gettempdir())
        tinted_path = temp_dir / f"{cache_name}.png"

        # Use fill_foreground to tint the image
        fill_foreground(source_path, tinted_path, rgb)

        setattr(self, cache_key, tinted_path)
        return tinted_path

    def _is_monochrome_transparent(self, image_path: Path) -> bool:
        """
        Check if a PNG image is monochrome with transparent background.

        Args:
            image_path: Path to PNG image

        Returns:
            True if image is monochrome with transparency
        """
        try:
            from PIL import Image
            img = Image.open(image_path).convert("RGBA")
            pixels = img.load()
            width, height = img.size

            # Sample pixels to check for monochrome (same R=G=B values for non-transparent pixels)
            colors_found = set()
            has_transparency = False

            for x in range(0, width, max(1, width // 20)):  # Sample every ~5%
                for y in range(0, height, max(1, height // 20)):
                    r, g, b, a = pixels[x, y]
                    if a == 0:
                        has_transparency = True
                    elif a > 0:
                        # Check if pixel is greyscale (R=G=B)
                        if r == g == b:
                            colors_found.add(r)
                        else:
                            return False  # Found a colored pixel, not monochrome

            # Monochrome if we found greyscale values and has transparency
            return has_transparency and len(colors_found) > 0

        except Exception:
            return False

    def setup_ui(self):
        """Setup the UI components."""
        # Music player (reuse from v1)
        self.music_player: MusicPlayer = self.add_widget(MusicPlayer())
        self.music_player.play_pause_button.setVisible(False)
        self.music_player.next_button.setVisible(False)
        self.music_player.mute_button.setVisible(False)

        # Narration volume controls
        narration_widget = self.add_widget(GenericWidget(alignment=Alignment.horizontal))
        narration_widget.setFixedHeight(40)
        narration_widget.add_label("Narration Volume:")
        self.narration_volume_label = narration_widget.add_label("")
        narration_widget.add_stretch()
        self.narration_volume_down = narration_widget.add_button(
            text='-',
            clicked=partial(self._narration_volume_changed, -1)
        )
        self.narration_volume_down.setFixedWidth(32)
        self.narration_volume_up = narration_widget.add_button(
            text='+',
            clicked=partial(self._narration_volume_changed, 1)
        )
        self.narration_volume_up.setFixedWidth(32)
        self.narration_mute_button = narration_widget.add_button(
            text='Mute',
            clicked=partial(self._narration_volume_changed, 0)
        )
        self.narration_mute_button.setCheckable(True)
        self._update_narration_volume_display()

        # Title
        self.title_label = self.add_label("")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 36pt; font-weight: bold;")
        self.title_label.setContentsMargins(10, 0, 10, 5)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.title_label.setVisible(True)

        # Progress row (horizontal)
        progress_row = self.add_widget(GenericWidget(alignment=Alignment.horizontal))
        progress_row.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        # Circuit counter (conditional visibility)
        self.circuit_counter_label = progress_row.add_label("")
        self.circuit_counter_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.circuit_counter_label.setStyleSheet("font-size: 24pt; font-weight: bold;")
        self.circuit_counter_label.setContentsMargins(10, 5, 10, 5)
        self.circuit_counter_label.setVisible(False)

        # Dot container (will be populated when workout_list is set)
        self.dot_container = progress_row.add_widget(DotContainer([]))
        self.dot_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # Timer row (horizontal) - pause, reset, and stopwatch
        timer_row = self.add_widget(GenericWidget(alignment=Alignment.horizontal))
        timer_row.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        # Transport buttons (white tinted icons where available)
        white = (255, 255, 255)

        # Import constants
        from robocross import TOOL_TIP_SIZE

        # Back button (emoji symbol - no icon file)
        self.back_button = timer_row.add_widget(QPushButton("⏮"))
        self.back_button.setFixedSize(80, 80)
        self.back_button.setStyleSheet(f"font-size: 36pt; color: white; border: none;")
        self.back_button.setToolTip(f"<span style='font-size: {TOOL_TIP_SIZE}pt;'>Previous workout</span>")

        # Play/Pause button (white tinted icons)
        play_icon_path = self._create_tinted_image(image_path("play.png"), white, "play_white")
        pause_icon_path = self._create_tinted_image(image_path("pause.png"), white, "pause_white")
        self.play_icon_white = QIcon(QPixmap(str(play_icon_path)))
        self.pause_icon_white = QIcon(QPixmap(str(pause_icon_path)))
        self.pause_button = timer_row.add_widget(QPushButton())
        self.pause_button.setIcon(self.play_icon_white)
        self.pause_button.setIconSize(QSize(50, 50))
        self.pause_button.setFixedSize(80, 80)
        self.pause_button.setStyleSheet("border: none;")
        self.pause_button.setToolTip(f"<span style='font-size: {TOOL_TIP_SIZE}pt;'>Play workout</span>")

        # Forward button (emoji symbol - no icon file)
        self.forward_button = timer_row.add_widget(QPushButton("⏭"))
        self.forward_button.setFixedSize(80, 80)
        self.forward_button.setStyleSheet(f"font-size: 36pt; color: white; border: none;")
        self.forward_button.setToolTip(f"<span style='font-size: {TOOL_TIP_SIZE}pt;'>Next workout</span>")

        # Reset button (white tinted icon)
        reset_icon_path = self._create_tinted_image(image_path("reset.png"), white, "reset_white")
        self.reset_button = timer_row.add_widget(QPushButton())
        self.reset_button.setIcon(QIcon(QPixmap(str(reset_icon_path))))
        self.reset_button.setIconSize(QSize(50, 50))
        self.reset_button.setFixedSize(80, 80)
        self.reset_button.setStyleSheet("border: none;")
        self.reset_button.setToolTip(f"<span style='font-size: {TOOL_TIP_SIZE}pt;'>Reset workout</span>")

        # Stopwatch (reuse from v1) - hide its internal play/pause/reset buttons
        self.stopwatch = Stopwatch(period=self.period)
        self.stopwatch.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.stopwatch.play_pause_button.setVisible(False)
        self.stopwatch.reset_button.setVisible(False)
        timer_row.add_widget(self.stopwatch)

        # Current exercise chip (full width)
        self.current_exercise_chip = self.add_widget(WorkoutChip(self.rest_workout, show_progress=True))
        self.current_exercise_chip.setFixedHeight(70)
        self.current_exercise_chip.background.setFixedHeight(70)
        self.current_exercise_chip.progress_label.setFixedHeight(70)  # Match background height
        self.current_exercise_chip.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chip_font = QFont(SANS_SERIF_FONT, 36)
        chip_font.setBold(True)
        self.current_exercise_chip.label.setFont(chip_font)

        # Content pane (horizontal split)
        content_pane = self.add_widget(GenericWidget(alignment=Alignment.horizontal))
        content_pane.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Left: text section (vertically centered)
        text_section = content_pane.add_widget(GenericWidget())
        text_section.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        text_section.setMaximumWidth(500)

        # Add top stretch to center content vertically
        text_section.add_stretch()

        self.duration_label = text_section.add_label("")
        self.duration_label.setStyleSheet("font-size: 32pt; font-weight: bold;")
        self.duration_label.setContentsMargins(20, 10, 20, 10)
        self.duration_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        self.description_label = text_section.add_label("")
        self.description_label.setStyleSheet("font-size: 24pt; font-weight: bold;")
        self.description_label.setWordWrap(True)
        self.description_label.setContentsMargins(20, 10, 20, 10)
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # Add bottom stretch to center content vertically
        text_section.add_stretch()

        # Right: media section (placeholder, will be replaced per workout)
        self.media_container = content_pane.add_widget(GenericWidget())
        self.media_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Initial placeholder
        self._current_media_widget = QLabel("No media available")
        self._current_media_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._current_media_widget.setStyleSheet("font-size: 18pt; color: #666;")
        self.media_container.add_widget(self._current_media_widget)

        # Bottom: next exercise bar
        self.next_exercise_bar = self.add_label("")
        self.next_exercise_bar.setStyleSheet("background-color: #C0392B; font-size: 18pt; padding: 10px; color: white;")
        self.next_exercise_bar.setContentsMargins(0, 0, 0, 0)
        self.next_exercise_bar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

    def setup_connections(self):
        """Setup signal/slot connections."""
        self.stopwatch.time_reached.connect(self.advance_workout)
        self.back_button.clicked.connect(self.go_back)
        self.pause_button.clicked.connect(self.toggle_run_mode)
        self.forward_button.clicked.connect(self.go_forward)
        self.reset_button.clicked.connect(self.stopwatch_reset)
        self.current_exercise_chip.time_reached.connect(self.rest_strip_time_reached)
        self.mac_voice.speaking_finished.connect(self.speaking_finished)

    # ========== Properties (reused from v1) ==========

    @property
    def app_size(self) -> QSize | None:
        try:
            return self.parent().parent().parent().app_size
        except AttributeError:
            return None

    @property
    def workout_name(self) -> str:
        return self.title_label.text()

    @workout_name.setter
    def workout_name(self, value: str):
        # Format: replace underscores with spaces and title case
        formatted_name = value.replace('_', ' ').title()
        self.title_label.setText(formatted_name)
        self.title_label.setVisible(True)

    @property
    def workout_cycles(self) -> int:
        return self._workout_cycles

    @workout_cycles.setter
    def workout_cycles(self, value: int):
        self._workout_cycles = value
        self.update_circuit_counter()

    @property
    def current_circuit(self) -> int:
        return self._current_circuit

    @current_circuit.setter
    def current_circuit(self, value: int):
        self._current_circuit = value
        self.update_circuit_counter()

    @property
    def current_workout(self) -> Workout | None:
        if self.workout_list and self.current_index < len(self.workout_list):
            return self.workout_list[self.current_index]
        return None

    @property
    def next_index(self) -> int | None:
        return self.current_index + 1 if self.current_index < len(self.workout_list) - 1 else None

    @property
    def next_workout(self) -> Workout | None:
        return self.workout_list[self.next_index] if self.next_index else None

    @property
    def next_exercise(self) -> Workout | None:
        """Get the next non-rest workout, skipping REST_PERIOD items."""
        idx = self.current_index + 1
        while idx < len(self.workout_list):
            workout = self.workout_list[idx]
            if workout.name != REST_PERIOD:
                return workout
            idx += 1
        return None

    @property
    def rest_workout(self) -> Workout:
        return Workout(
            name=REST_PERIOD,
            description="Time to take a break",
            equipment=[],
            intensity=Intensity.low,
            aerobic_type=AerobicType.recovery,
            target=[],
            time=0,
        )

    @property
    def rest_time(self) -> int:
        return self._rest_time

    @rest_time.setter
    def rest_time(self, value: int):
        self._rest_time = value
        self.current_exercise_chip.workout.time = value

    @property
    def workout_list(self) -> list[Workout]:
        return self._workout_list

    @workout_list.setter
    def workout_list(self, workout_list: list[Workout]):
        """Set workout list and rebuild dot container."""
        # Store the base circuit (single iteration)
        self._base_workout_list = workout_list

        # Expand by repeating circuit workout_cycles times
        expanded_list = []
        for circuit_num in range(self.workout_cycles):
            expanded_list.extend(workout_list)

        self._workout_list = expanded_list

        # Rebuild dot container with base circuit
        # Remove old dot container
        progress_row = self.dot_container.parent()
        progress_row.layout().removeWidget(self.dot_container)
        self.dot_container.deleteLater()

        # Create new dot container with base circuit workouts
        self.dot_container = DotContainer(self._base_workout_list)
        self.dot_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        progress_row.layout().addWidget(self.dot_container)

        # Build notification_dict for the EXPANDED list (all cycles)
        self.notification_dict = OrderedDict()
        self.sub_workout_times = {}
        ref_time = timedelta(hours=0, minutes=0, seconds=0)

        for idx, workout in enumerate(expanded_list):
            time_string = self.delta_to_string(time_delta=ref_time)

            if workout.has_sub_workouts:
                # Add announcement for each sub-workout
                for i, sub_workout_name in enumerate(workout.sub_workouts):
                    sub_time_string = self.delta_to_string(
                        time_delta=ref_time + timedelta(seconds=i * workout.sub_workout_duration)
                    )
                    self.notification_dict[sub_time_string] = sub_workout_name
                    # Only add to sub_workout_times if it's NOT the first sub-workout
                    if i > 0:
                        self.sub_workout_times[sub_time_string] = (idx, sub_workout_name)
            else:
                # Regular workout - single announcement
                self.notification_dict[time_string] = workout.name

            ref_time += timedelta(seconds=workout.time)

        self.notification_dict[self.delta_to_string(time_delta=ref_time)] = self.end_notification

        # Send the times to the stopwatch
        LOGGER.debug("📋 Setting stopwatch targets:")
        for time, message in self.notification_dict.items():
            LOGGER.debug(f"   {time} → {message}")
        self.stopwatch.set_targets(self.notification_dict)
        LOGGER.debug(f"   Total targets: {len(self.notification_dict)}")

        # Initialize display to show first workout (only if we have workouts)
        if self._workout_list:
            LOGGER.debug("🎬 Initializing display with first workout")
            self.update_display()

    @property
    def workout_length(self) -> float:
        final_time = list(self.stopwatch.targets.keys())[-1]
        hours, minutes, seconds = final_time.split(":")
        return int(hours) * 60 + int(minutes) + int(seconds) / 60

    @property
    def workout_length_nice(self) -> str:
        final_time = list(self.stopwatch.targets.keys())[-1]
        hours, minutes, seconds = [int(x) for x in final_time.split(":")]
        hours_string = f"{hours} hour, " if hours > 0 else ""
        minutes_string = f"{minutes} minute, " if minutes else ""
        seconds_string = f"{seconds} second" if seconds else ""
        string = f"{hours_string}{minutes_string}{seconds_string}".rstrip()
        return string[:-1] if string.endswith(",") else string

    @staticmethod
    def delta_to_string(time_delta: timedelta) -> str:
        total_seconds = time_delta.total_seconds()
        hours = int(total_seconds // 3600)
        remaining_seconds_after_hours = total_seconds % 3600
        minutes = int(remaining_seconds_after_hours // 60)
        seconds = int(remaining_seconds_after_hours % 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    # ========== Display Update Methods ==========

    def update_display(self):
        """Update all UI elements for current workout."""
        LOGGER.debug(f"🖼 update_display called. current_index={self.current_index}")
        if not self.current_workout:
            LOGGER.warning("   ⚠ No current workout, returning")
            return
        LOGGER.debug(f"   Updating display for: {self.current_workout.name}")

        # Update circuit counter
        if self.workout_cycles > 1:
            self.circuit_counter_label.setText(f"Circuit {self.current_circuit} of {self.workout_cycles}")
            self.circuit_counter_label.setVisible(True)
        else:
            self.circuit_counter_label.setVisible(False)

        # Update dots
        # Count non-REST exercises up to current_index to find which dot to highlight
        if self.dot_container.dots:
            non_rest_count = 0
            for i in range(min(self.current_index + 1, len(self.workout_list))):
                if self.workout_list[i].name != REST_PERIOD:
                    non_rest_count += 1

            # Map to base circuit position (for multi-circuit workouts)
            base_circuit_length = len(self._base_workout_list)
            current_base_index = (non_rest_count - 1) % base_circuit_length if non_rest_count > 0 else 0

            LOGGER.debug(f"   Dot update: current_index={self.current_index}, non_rest_count={non_rest_count}, current_base_index={current_base_index}")

            for i, dot in enumerate(self.dot_container.dots):
                if i < current_base_index:
                    dot.state = 'finished'
                elif i == current_base_index:
                    dot.state = 'in_progress'
                else:
                    dot.state = 'not_started'
                dot.update()  # Trigger repaint

        # Update current exercise chip
        self.current_exercise_chip.workout = self.current_workout

        # For workouts with sub-workouts, determine which sub-workout to display
        if self.current_workout.has_sub_workouts:
            # Get elapsed time from stopwatch (QTime to total seconds)
            elapsed_qtime = self.stopwatch.elapsed
            current_time_seconds = (elapsed_qtime.hour() * 3600 +
                                   elapsed_qtime.minute() * 60 +
                                   elapsed_qtime.second())

            # Calculate when this workout started
            workout_start_time_seconds = 0
            for i in range(self.current_index):
                workout_start_time_seconds += self.workout_list[i].time

            elapsed_in_workout = current_time_seconds - workout_start_time_seconds

            # Determine which sub-workout we're in
            sub_index = int(elapsed_in_workout // self.current_workout.sub_workout_duration)
            sub_index = max(0, min(sub_index, len(self.current_workout.sub_workouts) - 1))

            sub_workout_name = self.current_workout.sub_workouts[sub_index]
            self.current_exercise_chip.update_display_name(sub_workout_name)

        # Chip colors are managed by WorkoutChip.reset() and .start() methods
        # Update text section with workout color
        from robocross import get_category_color
        current_color = get_category_color(self.current_workout.aerobic_type.name)
        self.duration_label.setText(f"Duration: {self.current_workout.time_nice}")
        self.duration_label.setStyleSheet(f"font-size: 32pt; font-weight: bold; color: {current_color};")
        description = self.current_workout.description or "(no details)"
        self.description_label.setText(description.capitalize())
        self.description_label.setStyleSheet(f"font-size: 24pt; font-weight: bold; color: {current_color};")

        # Update media section
        self.load_media(self.current_workout.name)

        # Update next exercise bar (skip rest periods, show next actual exercise)
        next_ex = self.next_exercise
        if next_ex:
            next_name = next_ex.name.replace('_', ' ').title()
            next_color = get_category_color(next_ex.aerobic_type.name)
            self.next_exercise_bar.setText(f"Coming up next: {next_name}")
            self.next_exercise_bar.setStyleSheet(
                f"background-color: {next_color}; font-size: 18pt; padding: 10px; color: white;"
            )
        else:
            # End of workout - use same grey as rest period
            rest_color = get_category_color(AerobicType.recovery.name)
            self.next_exercise_bar.setText("End of workout")
            self.next_exercise_bar.setStyleSheet(
                f"background-color: {rest_color}; font-size: 18pt; padding: 10px; color: white;"
            )

    def load_media(self, workout_name: str):
        """Load and display media for current workout."""
        # Remove current media widget
        if self._current_media_widget:
            self.media_container.layout().removeWidget(self._current_media_widget)
            self._current_media_widget.deleteLater()

        # Find media file
        media_path = find_workout_media(workout_name)

        if not media_path:
            # No media found - show placeholder
            self._current_media_widget = QLabel("No media available")
            self._current_media_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._current_media_widget.setStyleSheet("font-size: 18pt; color: #666; border: none;")
        elif media_path.suffix in ['.mp4', '.mov', '.avi']:
            # Video
            self._current_media_widget = VideoPlayerWidget(media_path)
            self._current_media_widget.setStyleSheet("border: none;")
            self._current_media_widget.start()
        elif media_path.suffix == '.gif':
            # Animated GIF
            self._current_media_widget = QLabel()
            movie = QMovie(str(media_path))
            self._current_media_widget.setMovie(movie)
            self._current_media_widget.setScaledContents(False)
            self._current_media_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._current_media_widget.setStyleSheet("border: none;")
            movie.start()
        else:
            # Static image (PNG/JPG)
            # Check if PNG is monochrome with transparency - if so, tint to workout color
            final_image_path = media_path

            if media_path.suffix.lower() == '.png' and self._is_monochrome_transparent(media_path):
                # Tint to current workout color
                from robocross import get_category_color
                workout_color_hex = get_category_color(self.current_workout.aerobic_type.name)

                # Convert hex to RGB
                hex_color = workout_color_hex.lstrip('#')
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)

                # Create tinted version
                cache_name = f"{media_path.stem}_{workout_color_hex.replace('#', '')}"
                final_image_path = self._create_tinted_image(media_path, (r, g, b), cache_name)

            self._current_media_widget = ImageLabel(final_image_path)

            # Check if image needs padding/margin
            from robocross import IMAGE_PADDING
            from robocross.media_loader import has_transparent_padding

            if has_transparent_padding(final_image_path, min_padding=IMAGE_PADDING):
                # Image has padding, no margin needed
                self._current_media_widget.setStyleSheet("border: none;")
            else:
                # Image doesn't have padding, add margin
                self._current_media_widget.setContentsMargins(IMAGE_PADDING, IMAGE_PADDING, IMAGE_PADDING, IMAGE_PADDING)
                self._current_media_widget.setStyleSheet("border: none;")

        # Add to media container
        self.media_container.layout().addWidget(self._current_media_widget)
        self._current_media_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def update_circuit_counter(self):
        """Update circuit counter display based on current circuit and total cycles."""
        if self.workout_cycles > 1:
            self.circuit_counter_label.setText(f"Circuit {self.current_circuit} of {self.workout_cycles}")
            self.circuit_counter_label.setVisible(True)
        else:
            self.circuit_counter_label.setVisible(False)

    # ========== Workout Control Methods (reused from v1) ==========

    def advance_workout(self, *args):
        """Workout item or sub-workout segment finished."""
        time_str = args[0]
        LOGGER.debug(f"⏭ advance_workout called! time_str={time_str}, current_index={self.current_index}")
        LOGGER.debug(f"   Current workout: {self.current_workout.name if self.current_workout else 'None'}")

        self.started = True

        # Check if this is a sub-workout transition
        if time_str in self.sub_workout_times:
            workout_idx, sub_workout_name = self.sub_workout_times[time_str]
            LOGGER.debug(f"   Sub-workout transition: {sub_workout_name} at index {workout_idx}")
            if workout_idx == self.current_index:
                # Sub-workout transition: announce and update display
                self.speak(text=f"Starting {sub_workout_name}")
                self.current_exercise_chip.update_display_name(sub_workout_name)
            return  # Don't advance to next workout

        # Full workout transition
        LOGGER.debug(f"   Full workout transition. time_str={time_str}")
        if time_str != "00:00:00":
            self.current_index += 1
            LOGGER.debug(f"   Incremented current_index to {self.current_index}")

        # Check if we're transitioning to a new circuit
        base_circuit_length = len(self._base_workout_list)
        if base_circuit_length > 0 and self.current_index > 0:
            # Calculate which circuit we're in (1-based)
            new_circuit = (self.current_index // base_circuit_length) + 1

            # If we just started a new circuit, announce it
            if new_circuit != self.current_circuit and new_circuit <= self.workout_cycles:
                self.current_circuit = new_circuit
                self.speak(text=f"Starting circuit {self.current_circuit}")

        LOGGER.debug(f"time reached: {args}")

        # Skip re-announcing at the very beginning (00:00:00 and index 0)
        # The manual play button click already announced the first workout
        if time_str == "00:00:00" and self.current_index == 0:
            LOGGER.debug("   Skipping duplicate announcement at 00:00:00")
            return

        if self.current_index == len(self.workout_list):
            # Workout complete
            self.mac_voice.speak(text="workout complete")
            self.stopwatch.reset_button_clicked()
            self.stopwatch_reset()
            self.description_label.setText(f"{self.workout_length_nice} workout complete")
            self.music_player.media_player.stop()
        else:
            # Update dots for current workout
            # Count non-REST exercises up to current_index
            if self.dot_container.dots:
                non_rest_count = 0
                for i in range(min(self.current_index + 1, len(self.workout_list))):
                    if self.workout_list[i].name != REST_PERIOD:
                        non_rest_count += 1

                # Map to base circuit position
                base_circuit_length = len(self._base_workout_list)
                current_base_index = (non_rest_count - 1) % base_circuit_length if non_rest_count > 0 else 0

                for i, dot in enumerate(self.dot_container.dots):
                    if i < current_base_index:
                        dot.state = 'finished'
                    elif i == current_base_index:
                        dot.state = 'in_progress'
                    else:
                        dot.state = 'not_started'
                    dot.update()

            self.current_exercise_chip.reset()
            self.play_workout()

    def pause_workout(self):
        """Pause the workout."""
        LOGGER.debug(f"⏸ pause_workout called for: {self.current_workout.name if self.current_workout else 'None'}")
        if not self.current_workout:
            LOGGER.warning("   ⚠ No current workout to pause")
            return

        self.speak(text=f"Pausing {self.current_workout.name}")
        self.description_label.setText(
            f"<span style='color: #95A5A6; font-weight: bold; font-size: 24pt;'>PAUSED</span><br /><br />"
            f"{self.current_workout.description.capitalize() if self.current_workout.description else '(no details)'}"
        )
        LOGGER.debug("   Stopping exercise chip timer")
        self.current_exercise_chip.timer.stop()
        LOGGER.debug("   Pausing stopwatch")
        self.stopwatch.pause()
        LOGGER.debug("   Pausing music player")
        self.music_player.media_player.pause()

    def play_workout(self):
        """Play the workout."""
        LOGGER.debug(f"▶ play_workout called for: {self.current_workout.name if self.current_workout else 'None'}")
        if not self.current_workout:
            LOGGER.warning("   ⚠ No current workout to play")
            return

        LOGGER.debug("   Starting music player")
        self.music_player.play()
        self.current_exercise_chip.workout = self.current_workout
        self.current_exercise_chip.setVisible(True)
        LOGGER.debug(f"   Starting exercise chip timer for {self.current_workout.time}s")
        self.current_exercise_chip.start()

        # Start the stopwatch timer
        LOGGER.debug("   Starting stopwatch timer")
        self.stopwatch.play()
        LOGGER.debug(f"   Stopwatch running={self.stopwatch.running}, period={self.stopwatch.period}ms")

        if self.current_workout.name == REST_PERIOD:
            # Rest period handling
            from robocross import get_category_color

            if self.next_workout is None:
                next_string = "End of workout coming up"
                workout = self.current_workout
                workout.name = "Stretching"
                workout.description = "Time to stretch it out..."
                self.current_exercise_chip.workout = workout
            else:
                next_string = f"Coming up: [[slnc 500]]{self.next_workout.name.title()}"

            speech = f"Rest time {self.current_workout.time} seconds.[[slnc 500]]{next_string}"
            self.speak(text=speech)

            # Use grey color for rest period text
            rest_color = get_category_color(AerobicType.recovery.name)
            self.duration_label.setText(f"Duration: {self.current_workout.time_nice}")
            self.duration_label.setStyleSheet(f"font-size: 32pt; font-weight: bold; color: {rest_color};")
            self.description_label.setText(next_string.replace('[[slnc 500]]', ''))
            self.description_label.setStyleSheet(f"font-size: 24pt; font-weight: bold; color: {rest_color};")
            self.current_exercise_chip.setVisible(True)
        else:
            # Regular workout
            if self.started:
                if self.current_workout.has_sub_workouts:
                    # Announce first sub-workout
                    first_sub = self.current_workout.sub_workouts[0]
                    speech = f"Starting {first_sub}"
                    self.speak(text=speech)
                    # update_display will handle setting the chip display name
                else:
                    # Regular workout announcement
                    speech = f"Starting {self.current_workout.name}"
                    self.speak(text=speech)

            # Update display for current workout (handles sub-workout names automatically)
            self.update_display()

    def rest_strip_time_reached(self):
        """Event for rest strip."""
        self.current_exercise_chip.reset()

    def speak(self, text: str):
        """Speak text using voice synthesis."""
        self.music_player.mute = True
        self.mac_voice.speak(text)

    def speaking_finished(self):
        """Resume music after speaking."""
        self.music_player.mute = False

    def stopwatch_reset(self):
        """Stopwatch reset event."""
        # Reset all dots
        for dot in self.dot_container.dots:
            dot.state = 'not_started'
            dot.update()

        self.current_exercise_chip.workout = self.workout_list[0]
        self.current_exercise_chip.reset()
        self.current_exercise_chip.timer.stop()
        self.current_index = 0
        self.current_circuit = 1
        self.started = False
        self.run_mode = RunMode.paused

        # Update pause button to show play icon
        from robocross import TOOL_TIP_SIZE
        self.pause_button.setIcon(self.play_icon_white)
        self.pause_button.setToolTip(f"<span style='font-size: {TOOL_TIP_SIZE}pt;'>Play workout</span>")

        # Update display for first workout
        if self.workout_list:
            self.update_display()

    def toggle_run_mode(self):
        """Toggle run mode."""
        from robocross import TOOL_TIP_SIZE
        LOGGER.debug(f"🔄 toggle_run_mode called. Current run_mode: {self.run_mode}")
        self.run_mode = RunMode.play if self.run_mode is RunMode.paused else RunMode.paused
        self.started = True
        if self.run_mode is RunMode.paused:
            self.pause_button.setIcon(self.play_icon_white)
            self.pause_button.setToolTip(f"<span style='font-size: {TOOL_TIP_SIZE}pt;'>Play workout</span>")
            LOGGER.debug("   → Switching to PAUSE mode")
            self.pause_workout()
        else:
            self.pause_button.setIcon(self.pause_icon_white)
            self.pause_button.setToolTip(f"<span style='font-size: {TOOL_TIP_SIZE}pt;'>Pause workout</span>")
            LOGGER.debug("   → Switching to PLAY mode")
            self.play_workout()

    def _narration_volume_changed(self, delta: int):
        """Handle narration volume change."""
        if delta == 0:  # Mute toggle
            current_volume = self.settings.value(self.narration_volume_key, self.default_narration_volume, type=int)
            mute_factor = 0.25 if self.narration_mute_button.isChecked() else 1.0
            self.mac_voice.volume = (current_volume / 10.0) * mute_factor
        else:
            current_volume = self.settings.value(self.narration_volume_key, self.default_narration_volume, type=int)
            new_volume = max(0, min(10, current_volume + delta))
            self.settings.setValue(self.narration_volume_key, new_volume)
            mute_factor = 0.25 if self.narration_mute_button.isChecked() else 1.0
            self.mac_voice.volume = (new_volume / 10.0) * mute_factor
        self._update_narration_volume_display()

    def _update_narration_volume_display(self):
        """Update narration volume label."""
        volume = self.settings.value(self.narration_volume_key, self.default_narration_volume, type=int)
        self.narration_volume_label.setText(f"{volume}")

    def go_back(self):
        """Go back to previous workout (skip rest periods)."""
        if self.current_index > 0:
            # Pause if playing
            if self.run_mode is RunMode.play:
                self.toggle_run_mode()

            # Go back to previous non-REST workout
            self.current_index -= 1
            while self.current_index > 0 and self.workout_list[self.current_index].name == REST_PERIOD:
                self.current_index -= 1

            # Update circuit if needed
            base_circuit_length = len(self._base_workout_list)
            if base_circuit_length > 0:
                new_circuit = (self.current_index // base_circuit_length) + 1
                if new_circuit != self.current_circuit:
                    self.current_circuit = new_circuit

            # Update display and reset chip timer
            self.update_display()
            self.current_exercise_chip.reset()

    def go_forward(self):
        """Go forward to next workout (skip rest periods)."""
        if self.current_index < len(self.workout_list) - 1:
            # Pause if playing
            if self.run_mode is RunMode.play:
                self.toggle_run_mode()

            # Go forward to next non-REST workout
            self.current_index += 1
            while self.current_index < len(self.workout_list) - 1 and self.workout_list[self.current_index].name == REST_PERIOD:
                self.current_index += 1

            # Update circuit if needed
            base_circuit_length = len(self._base_workout_list)
            if base_circuit_length > 0:
                new_circuit = (self.current_index // base_circuit_length) + 1
                if new_circuit != self.current_circuit:
                    self.current_circuit = new_circuit

            # Update display and reset chip timer
            self.update_display()
            self.current_exercise_chip.reset()
