"""Workout data."""
import hashlib
import json

from pathlib import Path
from datetime import datetime
from typing import Sequence

from core.logging_utils import get_logger
from robocross.workout import Workout
from robocross.robocross_enums import Equipment, Intensity, AerobicType, Target
from robocross import DATA_FILE_PATH


DEFAULT_TIME = 120
LOGGER = get_logger(__name__)


WORKOUTS: tuple[Workout] = (
    Workout(name="shuttle runs with medicine ball", description="", equipment=[Equipment.medicine_ball],
            intensity=Intensity.high, aerobic_type=AerobicType.cardio, target=[Target.full_body], time=DEFAULT_TIME),
    Workout(name="spot running", description="", equipment=[],
            intensity=Intensity.high, aerobic_type=AerobicType.cardio, target=[Target.full_body], time=DEFAULT_TIME),
    Workout(name="reverse flies standing", description="", equipment=[Equipment.dumbbell], intensity=Intensity.medium,
            aerobic_type=AerobicType.strength, target=[Target.back], time=DEFAULT_TIME),
    Workout(name="jumping jacks", description="", equipment=[], intensity=Intensity.high,
            aerobic_type=AerobicType.cardio,
            target=[Target.full_body], time=DEFAULT_TIME),
    Workout(name="dumbbell flies", description="lie on bench back-facing, raise dumbbells vertically from the side",
            equipment=[Equipment.bench, Equipment.dumbbell], intensity=Intensity.medium,
            aerobic_type=AerobicType.strength, target=[Target.chest], time=DEFAULT_TIME),
    Workout(name="skipping", description="use jump rope continuously", equipment=[Equipment.jump_rope],
            intensity=Intensity.high, aerobic_type=AerobicType.cardio, target=[Target.full_body], time=DEFAULT_TIME),
    Workout(name="lunges", description="alternate steps forward with weights",
            equipment=[Equipment.dumbbell, Equipment.kettle_bell], intensity=Intensity.medium,
            aerobic_type=AerobicType.strength, target=[Target.legs], time=DEFAULT_TIME),
    Workout(name="three point shoulder raise", description="raise dumbbells to front, rotate to side, then lower",
            equipment=[Equipment.dumbbell], intensity=Intensity.medium, aerobic_type=AerobicType.strength,
            target=[Target.shoulders], time=DEFAULT_TIME),
    Workout(name="three point shoulder raise reversed", description="raise dumbbells to side, rotate to front, then lower",
            equipment=[Equipment.dumbbell], intensity=Intensity.medium, aerobic_type=AerobicType.strength,
            target=[Target.shoulders], time=DEFAULT_TIME),
    Workout(name="crunches", description="lie on back and reach forward, bending at the hip",
            equipment=[Equipment.mat], intensity=Intensity.medium, aerobic_type=AerobicType.strength,
            target=[Target.abdominals], time=DEFAULT_TIME),
    Workout(name="russian twists", description="lie on back with legs raised, plant a weight on alternate sides",
            equipment=[Equipment.mat], intensity=Intensity.medium, aerobic_type=AerobicType.strength,
            target=[Target.abdominals], time=DEFAULT_TIME),
    Workout(name="squats",
            description="start standing holding weights, bend legs to low position keeping back straight",
            equipment=[Equipment.dumbbell], intensity=Intensity.medium, aerobic_type=AerobicType.strength,
            target=[Target.legs], time=DEFAULT_TIME),
    Workout(name="kettle bell swings", description="thrust quads to raise kettle bells to chest height",
            equipment=[Equipment.kettle_bell], intensity=Intensity.high, aerobic_type=AerobicType.strength,
            target=[Target.full_body], time=DEFAULT_TIME),
    Workout(name="curl + press", description="standing curl with shoulder press", equipment=[Equipment.dumbbell],
            intensity=Intensity.medium, aerobic_type=AerobicType.strength, target=[Target.upper_body], time=DEFAULT_TIME),
    Workout(name="dumbbell curls", description="standing curl", equipment=[Equipment.dumbbell],
            intensity=Intensity.medium, aerobic_type=AerobicType.strength, target=[Target.upper_body], time=DEFAULT_TIME),
    Workout(name="tricep kickbacks", description="standing bent at the waist, raise dumbbells to horizontal",
            equipment=[Equipment.dumbbell], intensity=Intensity.medium, aerobic_type=AerobicType.strength,
            target=[Target.arms], time=DEFAULT_TIME),
    Workout(name="oblique twist",
            description="standing bent at the waist with bo staff at shoulder level, twist to alternate sides",
            equipment=[Equipment.bo_staff], intensity=Intensity.medium, aerobic_type=AerobicType.strength,
            target=[Target.abdominals], time=DEFAULT_TIME),
    Workout(name="bicycle crunches", description="lying on back, rotate legs forward in a circular motion",
            equipment=[Equipment.mat], intensity=Intensity.high, aerobic_type=AerobicType.strength,
            target=[Target.abdominals], time=DEFAULT_TIME),
    Workout(name="bench press", description="lying on back, raise weights vertically",
            equipment=[Equipment.bench, Equipment.dumbbell, Equipment.barbell], intensity=Intensity.medium,
            aerobic_type=AerobicType.strength, target=[Target.chest], time=DEFAULT_TIME),
    Workout(name="medicine ball slams", description="raise medicine ball overhead, then slam to ground",
            equipment=[Equipment.medicine_ball], intensity=Intensity.high, aerobic_type=AerobicType.strength,
            target=[Target.full_body], time=DEFAULT_TIME),
    Workout(name="burpees", description="push up, squat thrust, star jump", equipment=[Equipment.mat],
            intensity=Intensity.high, aerobic_type=AerobicType.cardio, target=[Target.full_body], time=DEFAULT_TIME),
    Workout(name="weighted punches", description="continuous punches forward holding weights",
            equipment=[Equipment.dumbbell], intensity=Intensity.high, aerobic_type=AerobicType.cardio,
            target=[Target.arms], time=DEFAULT_TIME),
    Workout(name="plank", description="facing down with elbows on the floor, hold a straight position",
            equipment=[Equipment.mat], intensity=Intensity.low, aerobic_type=AerobicType.strength,
            target=[Target.abdominals], time=DEFAULT_TIME),
    Workout(name="shoulder press", description="standing up, hold dumbbells at shoulder level and raise vertically",
            equipment=[Equipment.dumbbell], intensity=Intensity.high, aerobic_type=AerobicType.strength,
            target=[Target.shoulders, Target.arms], time=DEFAULT_TIME)
)


def generate_hash(text: str) -> str:
    time_stamp = datetime.now().strftime("%Y_%m_%d_%H-%M-%S")
    data = f"{text}_{time_stamp}"
    full_sha256_hash = hashlib.sha256(data.encode('utf-8')).hexdigest()
    short_hash = full_sha256_hash[:8]  # Take the first 8 characters
    return short_hash


def convert_to_data_file():

    # print(DATA_FILE_PATH)
    data_dict = {}
    for workout in WORKOUTS:
        data_dict[workout.name] = {
            "description": workout.description,
            "equipment": [x.name for x in list(workout.equipment)] if workout.equipment else [],
            "intensity": workout.intensity.name,
            "aerobic_type": workout.aerobic_type.name,
            "target": [x.name for x in list(workout.target)],
            "time": workout.time,
        }
    with DATA_FILE_PATH.open("w") as f:
        json.dump(data_dict, f, indent=4)


class WorkoutData:
    def __init__(self, nope_list: Sequence[str] = (), equipment_filter: Sequence[Equipment] = ()):
        """Initialize the workout data.
        Args:
            nope_list (Sequence): The list of workout items to omit.
            equipment_filter (Sequence[Equipment]): The list of equipment items to omit.
            """
        with DATA_FILE_PATH.open("r") as f:
            self.data = json.load(f)
        self.nope_list = nope_list
        self.equipment_filter = equipment_filter

    @property
    def filtered_data(self) -> dict:
        """Data with items removed."""
        filtered = {}
        for name, value in self.data.items():
            if name not in self.nope_list:
                equipment_list = [Equipment.__members__.get(x) for x in value.get("equipment")]
                if bool(set(equipment_list).intersection(set(self.equipment_filter))) is False:
                    filtered[name] = value
        return filtered

    @property
    def workouts(self) -> list[Workout]:
        workouts = []
        for name, value in self.filtered_data.items():
            equipment_list = [Equipment.__members__.get(x) for x in value.get("equipment")]
            target_list = [Target.__members__.get(x) for x in value.get("target")]
            workouts.append(
                Workout(
                    name=name,
                    description=value.get("description"),
                    equipment=equipment_list if equipment_list else [],
                    intensity=Intensity.__members__.get(value.get("intensity")),
                    aerobic_type=AerobicType.__members__.get(value.get("aerobic_type")),
                    target=target_list,
                    time=DEFAULT_TIME,
                )
            )
        return workouts

    @property
    def cardio_workout_items(self) -> list[Workout]:
        return [x for x in self.workouts if x.aerobic_type is AerobicType.cardio if x.name]

    @property
    def strength_workout_items(self) -> list[Workout]:
        return [x for x in self.workouts if x.aerobic_type is AerobicType.strength]


if __name__ == "__main__":
    convert_to_data_file()
    equipment_filter = [Equipment.mat, Equipment.kettle_bell, Equipment.dumbbell]
    for x in WorkoutData(nope_list=["oblique twist"], equipment_filter=equipment_filter).strength_workout_items:
        print(x.name, x.equipment)
