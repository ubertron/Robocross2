import json
import math
import random
from typing import Sequence
from robocross.workout_data import WorkoutData
from robocross import DATA_FILE_PATH
from robocross.workout import Workout, AerobicType


NOPE_LIST = tuple(["burpees"])
WORKOUT_DATA: WorkoutData = WorkoutData()

class Routine:
    def __init__(self, interval: int = 120, workout_length: int = 35, rest_time: int = 30, nope_list: list = NOPE_LIST):
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

    @property
    def workout_count(self) -> int:
        """Number of workout items."""
        return math.floor(self.workout_length * 60 / (self.interval + self.minimum_rest_time))

    @property
    def rest_time(self) -> int:
        workout_count = self.workout_count
        remaining_time = self.workout_length * 60 - workout_count * (self.interval + self.minimum_rest_time)
        return math.floor(self.minimum_rest_time + remaining_time / workout_count)

    def cardio_strength_mix(self) -> list[Workout]:
        """Build a workout based on alternating cardio and strength AerobicType values."""
        workout_items = []
        for i in range(self.workout_count):
            item_list = WORKOUT_DATA.cardio_workout_items if i % 2 == 0 else WORKOUT_DATA.strength_workout_items
            workout_items.append(random.choice(item_list))
        return workout_items

    def cardio_workout(self) -> list[Workout]:
        return [random.choice(WORKOUT_DATA.cardio_workout_items) for _ in range(self.workout_count)]

    def strength_workout(self) -> list[Workout]:
        return [random.choice(WORKOUT_DATA.strength_workout_items) for _ in range(self.workout_count)]

    def random_workout(self) -> list[Workout]:
        return [random.choice(WORKOUT_DATA.workouts) for _ in range(self.workout_count)]



if __name__ == "__main__":
    routine = Routine(workout_length=20)
    for index, item in enumerate(routine.random_workout()):
        print(f"{index + 1}:\t{item.name}")
