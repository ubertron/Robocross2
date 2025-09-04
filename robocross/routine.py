import logging
import math
import random

from core.logging_utils import get_logger
from robocross.workout_data import WorkoutData
from robocross import REST_PERIOD, WorkoutType
from robocross.workout import Workout, AerobicType, Intensity


LOGGER = get_logger(name=__name__, level=logging.DEBUG)


class Routine:
    def __init__(self, interval: int = 120, workout_length: int = 35, rest_time: int = 30, nope_list: list = ()):
        """
        Workout Routine
        :param interval: seconds
        :param workout_length: minutes
        :param rest_time: seconds
        """
        self.interval = interval
        self.workout_length = workout_length
        self.minimum_rest_time = rest_time
        self.nope_list = nope_list
        self.workout_data: WorkoutData = WorkoutData(filter_list=self.nope_list)

    def __repr__(self) -> str:
        return f"Routine | interval: {self.interval}, workout_length: {self.workout_length}, rest_time: {self.rest_time}"

    @property
    def workout_count(self) -> int:
        """Number of workout items."""
        return math.floor(self.workout_length * 60 / (self.interval + self.minimum_rest_time))

    @property
    def rest_time(self) -> int:
        workout_count = self.workout_count
        remaining_time = self.workout_length * 60 - workout_count * (self.interval + self.minimum_rest_time)
        return math.floor(self.minimum_rest_time + remaining_time / workout_count)

    @property
    def cardio_strength_mix(self) -> list[Workout]:
        """Build a workout based on alternating cardio and strength AerobicType values."""
        workout_items = []
        for i in range(self.workout_count):
            item_list = self.workout_data.cardio_workout_items if i % 2 == 0 else self.workout_data.strength_workout_items
            workout_items.append(random.choice(item_list))
        return self.build_routine(workout_items)

    @property
    def cardio_workout(self) -> list[Workout]:
        return self.build_routine(
            [random.choice(self.workout_data.cardio_workout_items) for _ in range(self.workout_count)])

    @property
    def strength_workout(self) -> list[Workout]:
        return self.build_routine(
            [random.choice(self.workout_data.strength_workout_items) for _ in range(self.workout_count)])

    @property
    def random_workout(self) -> list[Workout]:
        return self.build_routine([random.choice(self.workout_data.workouts) for _ in range(self.workout_count)])

    @property
    def test_workout(self) -> list[Workout]:
        return [
            Workout(name="test item 1", description="description 1", equipment=[], intensity=Intensity.low,
                    aerobic_type=AerobicType.recovery, target=[], time=8),
            Workout(name="test item 2", description="description 2", equipment=[], intensity=Intensity.low,
                    aerobic_type=AerobicType.recovery, target=[], time=8),
        ]

    def build_routine(self, workouts: list[Workout]):
        workout_list = []
        rest_period = Workout(
            name=REST_PERIOD,
            description="Take a break",
            equipment=[],
            intensity=Intensity.low,
            aerobic_type=AerobicType.recovery,
            target=[],
            time=self.rest_time,
        )
        for workout in workouts:
            workout.time = self.interval
            workout_list.append(workout)
            workout_list.append(rest_period)
        return workout_list

    def get_workout_list(self, workout_type: WorkoutType) -> list[Workout]:
        """Get workout list by workout type."""
        workout_list = {
            WorkoutType.cardio: self.cardio_workout,
            WorkoutType.strength: self.strength_workout,
            WorkoutType.cardio_strength: self.cardio_strength_mix,
            WorkoutType.random: self.random_workout,
            WorkoutType.test: self.test_workout,
        }[workout_type] if workout_type else []
        return workout_list


if __name__ == "__main__":
    routine = Routine(workout_length=20)
    for index, item in enumerate(routine.random_workout):
        LOGGER.debug(f"{index + 1}:\t{item}")
