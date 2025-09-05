from __future__ import annotations

import logging
from collections import OrderedDict
from datetime import timedelta

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QSizePolicy, QLabel

from core import logging_utils
from core.core_enums import Alignment
from core.mac_voice import MacVoice, Voice
from robocross.robocross_enums import RunMode
from robocross.workout import Workout
from robocross.workout_strip import WorkoutStrip
from widgets.generic_widget import GenericWidget
from widgets.scroll_widget import ScrollWidget
from widgets.stopwatch import Stopwatch

LOGGER = logging_utils.get_logger(name=__name__, level=logging.DEBUG)


class Viewer(GenericWidget):
    """Widget to run workouts"""

    end_notification: str = "end of workout"
    scroll_panel_width: int = 240
    period = 50  # evaluation time for timers

    def __init__(self):
        super(Viewer, self).__init__(title="Workout Viewer", margin=0, spacing=0)
        self.stopwatch: Stopwatch = self.add_widget(Stopwatch(period=self.period))
        self.workout_pane: GenericWidget = GenericWidget(margin=0, spacing=0)
        content_pane = self.add_widget(GenericWidget(alignment=Alignment.horizontal, margin=0, spacing=0))
        scroll_widget: ScrollWidget = content_pane.add_widget(ScrollWidget())
        scroll_widget.widget.add_widget(self.workout_pane)
        scroll_widget.setFixedWidth(self.scroll_panel_width)
        self.info_label: QLabel = content_pane.add_label()
        self.info_label.setStyleSheet("font-size: 24px;")
        self.info_label.setWordWrap(True)
        self.workout_list = []
        self.notification_dict = OrderedDict()
        self.rest_time = 0
        self.current_index = 0
        self.mac_voice = MacVoice(voice=Voice.Samantha)
        self.setup_ui()

    @property
    def current_index(self) -> int:
        return self._current_index

    @current_index.setter
    def current_index(self, value: int):
        self._current_index = value

    @property
    def current_workout(self) -> Workout:
        return self.workout_list[self.current_index]

    @property
    def info(self):
        return self.info_label.text()

    @info.setter
    def info(self, value: str):
        self.info_label.setText(value)

    @property
    def rest_time(self) -> int:
        return self._rest_time

    @rest_time.setter
    def rest_time(self, value: int):
        self._rest_time = value

    @property
    def workout_list(self) -> list[Workout] | None :
        return self._workout_list

    @workout_list.setter
    def workout_list(self, workout_list: list[Workout]):
        self._workout_list = workout_list
        self.workout_pane.clear_layout()

        # create the workout strips
        for workout in workout_list:
            workout_strip = WorkoutStrip(workout=workout, period=self.period)
            workout_strip.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
            self.workout_pane.add_widget(workout_strip)
        self.workout_pane.add_stretch()
        self.notification_dict = OrderedDict()
        ref_time = timedelta(hours=0, minutes=0, seconds=0)

        # get the times for all the workout items
        for x in self.workout_strips:
            time_string = self.delta_to_string(time_delta=ref_time)
            self.notification_dict[time_string] = x.workout.name
            ref_time += timedelta(seconds=x.workout.time)
        self.notification_dict[self.delta_to_string(time_delta=ref_time)] = self.end_notification

        # send the times to the stopwatch
        self.stopwatch.set_targets(self.notification_dict)

    @property
    def workout_strips(self) -> list[WorkoutStrip]:
        return self.workout_pane.widgets

    @property
    def workout_length(self) -> str:
        final_time = list(self.stopwatch.targets.keys())[-1]
        hours, minutes, seconds = final_time.split(":")
        total_minutes = int(hours) * 60 + int(minutes) + int(seconds) / 60
        return f"{total_minutes: .2f}"


    @staticmethod
    def delta_to_string(time_delta: timedelta) -> str:
        total_seconds = time_delta.total_seconds()
        hours = int(total_seconds // 3600)
        remaining_seconds_after_hours = total_seconds % 3600
        minutes = int(remaining_seconds_after_hours // 60)
        seconds = int(remaining_seconds_after_hours % 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def advance_workout(self, *args):
        """Workout item finished."""
        if args[0] != "00:00:00":
            self.current_index += 1
        print(f"time reached: {args}")
        if self.current_index == len(self.workout_list):
            self.mac_voice.speak(line="workout complete")
            self.stopwatch.reset_button_clicked()
            self.stopwatch_reset()
            self.info = f"{self.workout_length} Minute Workout Complete"
        else:
            self.workout_strips[self.current_index].start()
            self.continue_workout(run_mode=RunMode.play)

    def setup_ui(self):
        self.stopwatch.time_reached.connect(self.advance_workout)
        self.stopwatch.play_pause_clicked.connect(self.continue_workout)
        self.stopwatch.reset_clicked.connect(self.stopwatch_reset)

    def continue_workout(self, run_mode: RunMode):
        """Stopwatch started event."""
        if run_mode is RunMode.play:
            speech = f"Starting {self.current_workout.name}"
            self.workout_strips[self.current_index].start()
            self.mac_voice.speak(line=speech)
            description = self.current_workout.description if self.current_workout.description else "(no details)"
            self.info = (
                f"<b>{self.current_workout.name.title()}</b><br />"
                f"Duration: {self.current_workout.time} seconds<br />{description.capitalize()}"
            )
        else:
            speech = f"Pausing {self.current_workout.name}"
            self.mac_voice.speak(line=speech)
            self.info = "Paused"

    def stopwatch_reset(self):
        """Stopwatch reset event."""
        for x in self.workout_strips:
            x.reset()
            x.timer.stop()
        self.current_index = 0
