from __future__ import annotations

import logging
from collections import OrderedDict
from datetime import timedelta
from pathlib import Path
import random

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QSizePolicy, QLabel, QSplitter

from core.logging_utils import FileHandler, get_logger, StreamHandler
from core.core_enums import Alignment
from core.mac_voice import MacVoice, Voice
from robocross import REST_PERIOD, workout_strip
from robocross.robocross_enums import AerobicType, RunMode, Intensity
from robocross.workout import Workout
from robocross.workout_strip import WorkoutStrip
from widgets.generic_widget import GenericWidget
from widgets.scroll_widget import ScrollWidget
from widgets.stopwatch import Stopwatch

LOGGER = get_logger(name=__name__)

class Viewer(GenericWidget):
    """Widget to run workouts"""

    end_notification: str = "end of workout"
    scroll_panel_width: int = 240
    period = 50  # evaluation time for timers
    typeface = "Futura"
    default_info_font = QFont(typeface, 32)
    default_workout_strip_font = QFont(typeface, 28)
    default_stopwatch_height = 40

    def __init__(self):
        super(Viewer, self).__init__(title="Workout Viewer", margin=0, spacing=0)
        self.workout_pane: GenericWidget = GenericWidget(margin=0, spacing=0)
        splitter: QSplitter = self.add_widget(QSplitter(Qt.Horizontal))
        splitter.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        scroll_widget = ScrollWidget()
        scroll_widget.widget.add_widget(self.workout_pane)
        content_pane = GenericWidget(alignment=Alignment.vertical, margin=0, spacing=0)
        self.stopwatch: Stopwatch = content_pane.add_widget(Stopwatch(period=self.period))
        self.stopwatch.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.workout_strip: WorkoutStrip = content_pane.add_widget(WorkoutStrip(self.rest_workout))
        self.workout_strip_font = self.default_workout_strip_font
        self.info_label = content_pane.add_label()
        self.info_label.setContentsMargins(20, 20, 20, 20)
        splitter.addWidget(scroll_widget)
        splitter.addWidget(content_pane)
        splitter.setSizes([125, 250])
        self.info_font = self.default_info_font
        self.info_label.setWordWrap(True)
        self.workout_list = []
        self.notification_dict = OrderedDict()
        self.current_index = 0
        self.rest_time = 0
        self.started = False
        self.stopwatch_started = self.default_stopwatch_height
        self.mac_voice = MacVoice(voice=random.choice([Voice.Samantha, Voice.Daniel]))
        self.run_mode = RunMode.paused
        self._setup_ui()

    def _setup_ui(self):
        self.stopwatch.time_reached.connect(self.advance_workout)
        self.stopwatch.play_pause_clicked.connect(self.toggle_run_mode)
        self.stopwatch.reset_clicked.connect(self.stopwatch_reset)
        # self.workout_strip.setFixedHeight(sel)
        self.workout_strip.time_reached.connect(self.rest_strip_time_reached)
        self.workout_strip.setVisible(False)

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
    def current_workout_strip(self) -> WorkoutStrip:
        return self.workout_strips[self.current_index]

    @property
    def info(self):
        return self.info_label.text()

    @info.setter
    def info(self, value: str):
        self.info_label.setText(value)

    @property
    def info_font(self) -> QFont:
        return self._info_font

    @info_font.setter
    def info_font(self, font: QFont):
        self._info_font = font
        self.info_label.setFont(font)

    @property
    def next_index(self) -> int | None:
        return self.current_index + 1 if self.current_index < len(self.workout_list) - 1 else None

    @property
    def next_workout(self) -> Workout | None:
        return self.workout_list[self.next_index] if self.next_index else None

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
        self.workout_strip.workout.time = value

    @property
    def stopwatch_height(self) -> int:
        return self._stopwatch_height

    @stopwatch_height.setter
    def stopwatch_height(self, height: int):
        self._stopwatch_height = height
        self.stopwatch.setFixedHeight(height)

    @property
    def workout_list(self) -> list[Workout] | None :
        return self._workout_list

    @workout_list.setter
    def workout_list(self, workout_list: list[Workout]):
        self._workout_list = workout_list
        self.workout_pane.clear_layout()

        # create the workout strips
        for workout in workout_list:
            strip = WorkoutStrip(workout=workout, period=self.period)
            strip.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
            strip.setHidden(workout.name == REST_PERIOD)
            self.workout_pane.add_widget(strip)
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
    def workout_strip_font(self) ->QFont:
        return self._workout_strip_font

    @workout_strip_font.setter
    def workout_strip_font(self, font: QFont):
        self._workout_strip_font = font
        self.workout_strip.label.setFont(font)


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
        string =  f"{hours_string}{minutes_string}{seconds_string}".rstrip()
        return string[:-1] if string.endswith(",") else string


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
        self.started = True
        if args[0] != "00:00:00":
            self.current_index += 1
        LOGGER.debug(f"time reached: {args}")
        if self.current_index == len(self.workout_list):
            self.mac_voice.speak(line="workout complete")
            self.stopwatch.reset_button_clicked()
            self.stopwatch_reset()
            self.info = f"{self.workout_length_nice} workout complete"
        else:
            self.workout_strips[self.current_index].start()
            self.workout_strip.reset()
            self.play_workout()

    def pause_workout(self):
        """Pause the workout."""
        speech = f"Pausing {self.current_workout.name}"
        self.mac_voice.speak(line=speech)
        self.info = "Paused"
        self.workout_strip.timer.stop()
        self.current_workout_strip.timer.stop()

    def play_workout(self):
        """Play the workout."""
        self.workout_strip.workout = self.current_workout
        self.workout_strip.setVisible(True)
        self.workout_strip.start()
        if self.current_workout.name == REST_PERIOD:
            if self.next_workout is None:
                next_string = "End of workout coming up"
                workout = self.current_workout
                workout.name = "Stretching"
                workout.description = "Time to stretch it out..."
                self.workout_strip.workout = workout
            else:
                next_string = f"Coming up: [[slnc 500]]{self.next_workout.name.title()}"
            speech = f"Rest time {self.current_workout.time} seconds.[[slnc 500]]{next_string}"
            self.mac_voice.speak(line=speech)
            self.info = (
                f"<span style='font-style:italic'>Duration: {self.current_workout.time} seconds</span><br /><br />"
                f"{next_string.replace('[[slnc 500]]', '')}"
            )
            self.workout_strip.setVisible(True)
        else:
            if self.started:  # necessary to distinguish time reached trigger from play/pause trigger
                speech = f"Starting {self.current_workout.name}"
                self.mac_voice.speak(line=speech)
            self.workout_strips[self.current_index].start()
            description = f"{self.current_workout.description}." if self.current_workout.description else "(no details)"
            self.info = (
                f"<span style='font-style:italic'>Duration: {self.current_workout.time} seconds</span><br /><br />"
                f"{description.capitalize()}"
            )

    def rest_strip_time_reached(self):
        """Event for rest strip."""
        self.workout_strip.reset()

    def stopwatch_reset(self):
        """Stopwatch reset event."""
        for x in self.workout_strips:
            x.reset()
            x.timer.stop()
        self.workout_strip.workout = self.workout_list[0]
        self.workout_strip.reset()
        self.workout_strip.timer.stop()
        self.current_index = 0
        self.started = False
        self.run_mode = RunMode.paused

    def toggle_run_mode(self):
        """Toggle run mode."""
        self.run_mode = RunMode.play if self.run_mode is RunMode.paused else RunMode.paused
        if self.run_mode is RunMode.paused:
            self.pause_workout()
        else:
            self.play_workout()


if __name__ == "__main__":
    statement = "asdfasdf,"
    print(statement[:-1] if statement.endswith(",") else statement)