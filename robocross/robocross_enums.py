from __future__ import annotations

from enum import auto, Enum, unique

@unique
class RunMode(Enum):
    paused = auto()
    play = auto()


class WorkoutType(Enum):
    cardio = "Cardio"
    strength = "strength"
    cardio_strength = "Cardio/Strength"
    random = "Random"
    test = "Test"

    @staticmethod
    def values() -> list[str]:
        return [x.value for x in WorkoutType]

    @staticmethod
    def get_by_value(value: str) -> Enum | None:
        return next((x for x in WorkoutType if x.value == value), None)
