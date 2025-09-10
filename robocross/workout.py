from __future__ import annotations

from dataclasses import dataclass

from robocross.robocross_enums import Equipment, Intensity, AerobicType, Target


@dataclass
class Workout:
    name: str
    description: str
    equipment: list[Equipment] | None
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
