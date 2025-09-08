from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto, unique

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
class AerobicType(Enum):
    cardio = auto()
    strength = auto()
    recovery = auto()

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

@dataclass
class Workout:
    name: str
    description: str
    equipment: list[Equipment]
    intensity: Intensity
    aerobic_type: AerobicType
    target: list[Target]
    time: int

    def __repr__(self):
        return f'{self.name} - time: {self.time} seconds'

    @staticmethod
    def default() -> Workout:
        return Workout(name="default workout",
                       description="default workout",
                       equipment=[Equipment.mat, Equipment.medicine_ball],
                       intensity=Intensity.low,
                       aerobic_type=AerobicType.recovery,
                       target=Target.full_body,
                       time=8)
