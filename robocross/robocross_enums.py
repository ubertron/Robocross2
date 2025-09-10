from __future__ import annotations

from enum import auto, Enum, unique


@unique
class AerobicType(Enum):
    cardio = auto()
    strength = auto()
    recovery = auto()


@unique
class Equipment(Enum):
    band = auto()
    bench = auto()
    bo_staff = auto()
    dumbbell = auto()
    barbell = auto()
    jump_rope = auto()
    kettle_bell = auto()
    mat = auto()
    medicine_ball = auto()
    swiss_ball = auto()


class Intensity(Enum):
    low = 0
    medium = 1
    high = 2


@unique
class RunMode(Enum):
    paused = auto()
    play = auto()


@unique
class Target(Enum):
    abdominals = auto()
    arms = auto()
    back = auto()
    chest = auto()
    full_body = auto()
    legs = auto()
    lower_body = auto()
    shoulders = auto()
    upper_body = auto()


class WorkoutType(Enum):
    cardio = "Cardio"
    strength = "Strength"
    cardio_strength = "Cardio/Strength"
    random = "Random"
    test = "Test"

    @staticmethod
    def values() -> list[str]:
        return [x.value for x in WorkoutType]

    @staticmethod
    def get_by_value(value: str) -> Enum | None:
        return next((x for x in WorkoutType if x.value == value), None)