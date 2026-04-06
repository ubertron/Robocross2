import logging
import math
import random

from core.logging_utils import get_logger
from robocross.workout_data import WorkoutData
from robocross import REST_PERIOD, WorkoutType
from robocross.workout import Workout
from robocross.robocross_enums import Equipment, Intensity, AerobicType

LOGGER = get_logger(name=__name__, level=logging.DEBUG)


class Routine:
    def __init__(self, interval: int = 120, workout_length: int = 35, rest_time: int = 30, nope_list: list = (),
                 equipment_filter: list[Equipment] = (), selected_categories: list[str] = None,
                 workout_structure: str = "Random", category_weights: dict[str, int] = None,
                 warm_up: bool = False, cool_down: bool = False, target_filter: list = None):
        """
        Workout Routine
        :param interval: seconds
        :param workout_length: minutes
        :param rest_time: seconds
        :param selected_categories: list of category names (e.g., ['cardio', 'strength', 'combat', 'flexibility'])
        :param workout_structure: 'Random' or 'Sequence'
        :param category_weights: dict mapping category name to weight percentage (0-100), if None uses equal weighting
        :param warm_up: if True, force first exercise to be cardio
        :param cool_down: if True, force last exercise to be flexibility
        :param target_filter: list of Target enums to filter exercises by body targets (e.g., [Target.legs, Target.core])
        """
        self.interval = interval
        self.workout_length = workout_length
        self.minimum_rest_time = rest_time
        self.nope_list = nope_list
        self.equipment_filter = equipment_filter
        self.selected_categories = selected_categories if selected_categories else ['cardio', 'strength']
        self.workout_structure = workout_structure
        self.category_weights = category_weights or self._default_weights()
        self.warm_up = warm_up
        self.cool_down = cool_down
        self.target_filter = target_filter if target_filter else []
        self.workout_data: WorkoutData = WorkoutData(
            nope_list=self.nope_list,
            equipment_filter=self.equipment_filter,
            selected_categories=self.selected_categories,
            target_filter=self.target_filter
        )

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

    def _default_weights(self) -> dict[str, int]:
        """Default equal weights for selected categories."""
        if not self.selected_categories:
            return {}
        base = 100 // len(self.selected_categories)
        remainder = 100 % len(self.selected_categories)
        return {
            cat: base + (1 if i < remainder else 0)
            for i, cat in enumerate(self.selected_categories)
        }

    def weighted_random_choice(self, workouts_by_category: dict) -> Workout:
        """Select workout using probability weights."""
        # Build weighted list (category repeated by weight value)
        weighted_categories = []
        for category, weight in self.category_weights.items():
            if category in workouts_by_category and workouts_by_category[category]:
                weighted_categories.extend([category] * weight)

        if not weighted_categories:
            # Fallback to uniform selection
            all_workouts = [w for workouts in workouts_by_category.values() for w in workouts]
            return random.choice(all_workouts) if all_workouts else None

        # Select category by weight, then random workout from that category
        category = random.choice(weighted_categories)
        return random.choice(workouts_by_category[category])

    @property
    def cardio_strength_mix(self) -> list[Workout]:
        """Build a workout based on alternating cardio and strength AerobicType values."""
        workout_items = []
        for i in range(self.workout_count):
            item_list = self.workout_data.cardio_workout_items if i % 2 == 0 else self.workout_data.strength_workout_items
            if not item_list:
                return []
            workout_items.append(random.choice(item_list))
        return self.build_routine(workout_items) if workout_items else None

    @property
    def cardio_workout(self) -> list[Workout]:
        if self.workout_data.cardio_workout_items:
            return self.build_routine(
                [random.choice(self.workout_data.cardio_workout_items) for _ in range(self.workout_count)])
        return []

    @property
    def strength_workout(self) -> list[Workout]:
        if self.workout_data.strength_workout_items:
            return self.build_routine(
                [random.choice(self.workout_data.strength_workout_items) for _ in range(self.workout_count)])
        return []

    @property
    def random_workout(self) -> list[Workout]:
        """Build workout with weighted probability selection."""
        if not self.workout_data.workouts:
            return []

        # Group workouts by category
        by_category = {
            cat: self.workout_data.get_workouts_by_category(cat)
            for cat in self.selected_categories
        }
        by_category = {k: v for k, v in by_category.items() if v}

        # Build workout using weighted selection
        workout_items = [
            self.weighted_random_choice(by_category)
            for _ in range(self.workout_count)
        ]
        workout_items = [w for w in workout_items if w]  # Filter None

        # Apply warm up (force first exercise to be cardio)
        if self.warm_up and workout_items:
            cardio_workouts = self.workout_data.get_all_workouts_by_category('cardio')
            if cardio_workouts:
                workout_items[0] = random.choice(cardio_workouts)
                LOGGER.info("Warm up: First exercise set to cardio")

        # Apply cool down (force last exercise to be flexibility)
        if self.cool_down and workout_items:
            flexibility_workouts = self.workout_data.get_all_workouts_by_category('flexibility')
            if flexibility_workouts:
                workout_items[-1] = random.choice(flexibility_workouts)
                LOGGER.info("Cool down: Last exercise set to flexibility")

        return self.build_routine(workout_items) if workout_items else []

    @property
    def sequence_workout(self) -> list[Workout]:
        """Build workout cycling through categories in a random repeating pattern (ignores weighting)."""
        if not self.selected_categories:
            return []

        # Create simple repeating cycle (ignore weighting)
        category_cycle = self.selected_categories.copy()
        random.shuffle(category_cycle)  # Randomize the order once

        LOGGER.info(f"Category sequence: {' → '.join(category_cycle)} (repeating)")

        workout_items = []
        for i in range(self.workout_count):
            category = category_cycle[i % len(category_cycle)]
            category_workouts = self.workout_data.get_workouts_by_category(category)
            if category_workouts:
                workout_items.append(random.choice(category_workouts))

        # Apply warm up (force first exercise to be cardio)
        if self.warm_up and workout_items:
            cardio_workouts = self.workout_data.get_all_workouts_by_category('cardio')
            if cardio_workouts:
                workout_items[0] = random.choice(cardio_workouts)
                LOGGER.info("Warm up: First exercise set to cardio")

        # Apply cool down (force last exercise to be flexibility)
        if self.cool_down and workout_items:
            flexibility_workouts = self.workout_data.get_all_workouts_by_category('flexibility')
            if flexibility_workouts:
                workout_items[-1] = random.choice(flexibility_workouts)
                LOGGER.info("Cool down: Last exercise set to flexibility")

        return self.build_routine(workout_items) if workout_items else []

    @property
    def test_workout(self) -> list[Workout]:
        return [
            Workout(name="test item 1", description="description 1", equipment=[Equipment.barbell, Equipment.dumbbell], intensity=Intensity.low,
                    aerobic_type=AerobicType.recovery, target=[], time=5),
            Workout(name=REST_PERIOD, description="rest time 1", equipment=[], intensity=Intensity.low,
                    aerobic_type=AerobicType.recovery, target=[], time=5),
            Workout(name="test item 2", description="description 2", equipment=[Equipment.barbell, Equipment.mat], intensity=Intensity.low,
                    aerobic_type=AerobicType.recovery, target=[], time=5),
            Workout(name=REST_PERIOD, description="rest time 2", equipment=[], intensity=Intensity.low,
                    aerobic_type=AerobicType.recovery, target=[], time=5),
        ]

    def build_routine(self, workouts: list[Workout]):
        if workouts:
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
        return []

    def get_workout_list(self, workout_type: WorkoutType = None) -> list[Workout]:
        """Get workout list by workout structure (Random or Sequence)."""
        if workout_type:
            # Legacy support for old workout_type parameter
            workout_list = {
                WorkoutType.cardio: self.cardio_workout,
                WorkoutType.strength: self.strength_workout,
                WorkoutType.cardio_strength: self.cardio_strength_mix,
                WorkoutType.random: self.random_workout,
                WorkoutType.test: self.test_workout,
            }[workout_type]
            return workout_list

        # New workflow_structure based routing
        if self.workout_structure == "Random":
            return self.random_workout
        elif self.workout_structure == "Sequence":
            return self.sequence_workout
        else:
            LOGGER.warning(f"Unknown workout structure: {self.workout_structure}")
            return []


if __name__ == "__main__":
    routine = Routine(workout_length=20)
    for index, item in enumerate(routine.random_workout):
        LOGGER.debug(f"{index + 1}:\t{item}")
