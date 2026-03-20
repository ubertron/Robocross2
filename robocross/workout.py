from __future__ import annotations

from dataclasses import dataclass

from robocross.robocross_enums import Equipment, Intensity, AerobicType, Target
from core import time_utils


@dataclass
class Workout:
    name: str
    description: str
    equipment: list[Equipment] | None
    intensity: Intensity
    aerobic_type: AerobicType
    target: list[Target]
    time: int
    sub_workouts: list[str] | None = None
    energy: int | None = None  # Calories per minute

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
                       time=83)

    @property
    def time_nice(self) -> str:
        return time_utils.time_nice(self.time)

    @property
    def has_sub_workouts(self) -> bool:
        """Check if this workout has sub-workouts."""
        return self.sub_workouts is not None and len(self.sub_workouts) > 0

    @property
    def sub_workout_duration(self) -> int:
        """Get duration per sub-workout in seconds."""
        if not self.has_sub_workouts:
            return self.time
        return self.time // len(self.sub_workouts)


if __name__ == "__main__":
    workout = Workout.default()
    print(workout.time_nice)