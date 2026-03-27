"""Workout data."""
import hashlib
import json

from pathlib import Path
from datetime import datetime
from typing import Sequence

from core.logging_utils import get_logger
from robocross.workout import Workout
from robocross.robocross_enums import Equipment, Intensity, AerobicType, Target
from core.core_paths import DATA_FILE_PATH


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
            target=[Target.core], time=DEFAULT_TIME),
    Workout(name="russian twists", description="lie on back with legs raised, plant a weight on alternate sides",
            equipment=[Equipment.mat], intensity=Intensity.medium, aerobic_type=AerobicType.strength,
            target=[Target.core], time=DEFAULT_TIME),
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
            target=[Target.core], time=DEFAULT_TIME),
    Workout(name="bicycle crunches", description="lying on back, rotate legs forward in a circular motion",
            equipment=[Equipment.mat], intensity=Intensity.high, aerobic_type=AerobicType.strength,
            target=[Target.core], time=DEFAULT_TIME),
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
            target=[Target.core], time=DEFAULT_TIME),
    Workout(name="shoulder press", description="standing up, hold dumbbells at shoulder level and raise vertically",
            equipment=[Equipment.dumbbell], intensity=Intensity.high, aerobic_type=AerobicType.strength,
            target=[Target.shoulders, Target.arms], time=DEFAULT_TIME),

    # Combat workouts (Wado-ryu Karate)
    Workout(name="front kicks", description="mae geri - forward snapping kicks alternating legs",
            equipment=[], intensity=Intensity.high, aerobic_type=AerobicType.combat,
            target=[Target.legs, Target.core], time=DEFAULT_TIME),
    Workout(name="side kicks", description="yoko geri - lateral kicks with hip rotation",
            equipment=[], intensity=Intensity.high, aerobic_type=AerobicType.combat,
            target=[Target.legs, Target.core], time=DEFAULT_TIME),
    Workout(name="roundhouse kicks", description="mawashi geri - circular kicks targeting mid-section",
            equipment=[], intensity=Intensity.high, aerobic_type=AerobicType.combat,
            target=[Target.legs, Target.core], time=DEFAULT_TIME),
    Workout(name="punching combinations", description="tsuki waza - rapid punch sequences with proper form",
            equipment=[], intensity=Intensity.high, aerobic_type=AerobicType.combat,
            target=[Target.arms, Target.shoulders, Target.core], time=DEFAULT_TIME),
    Workout(name="blocking drills", description="uke waza - defensive blocking techniques in sequence",
            equipment=[], intensity=Intensity.medium, aerobic_type=AerobicType.combat,
            target=[Target.arms, Target.core], time=DEFAULT_TIME),
    Workout(name="kata practice", description="traditional karate forms with focus and precision",
            equipment=[], intensity=Intensity.medium, aerobic_type=AerobicType.combat,
            target=[Target.full_body], time=DEFAULT_TIME),
    Workout(name="shadow sparring", description="kumite practice - fighting movements without contact",
            equipment=[], intensity=Intensity.high, aerobic_type=AerobicType.combat,
            target=[Target.full_body], time=DEFAULT_TIME),
    Workout(name="knee strikes", description="hiza geri - powerful knee strikes with hip drive",
            equipment=[], intensity=Intensity.high, aerobic_type=AerobicType.combat,
            target=[Target.legs, Target.core], time=DEFAULT_TIME),
    Workout(name="elbow strikes", description="empi uchi - close range elbow striking techniques",
            equipment=[], intensity=Intensity.high, aerobic_type=AerobicType.combat,
            target=[Target.arms, Target.core], time=DEFAULT_TIME),
    Workout(name="stance training", description="kihon dachi - hold and transition between fighting stances",
            equipment=[], intensity=Intensity.medium, aerobic_type=AerobicType.combat,
            target=[Target.legs, Target.core], time=DEFAULT_TIME),

    # Flexibility workouts (Yoga)
    Workout(name="downward dog", description="adho mukha svanasana - inverted v-shape stretching hamstrings and shoulders",
            equipment=[Equipment.mat], intensity=Intensity.low, aerobic_type=AerobicType.flexibility,
            target=[Target.full_body], time=DEFAULT_TIME),
    Workout(name="warrior pose", description="virabhadrasana - standing lunge position with arms extended",
            equipment=[Equipment.mat], intensity=Intensity.medium, aerobic_type=AerobicType.flexibility,
            target=[Target.legs, Target.core], time=DEFAULT_TIME),
    Workout(name="triangle pose", description="trikonasana - standing side stretch with extended leg",
            equipment=[Equipment.mat], intensity=Intensity.low, aerobic_type=AerobicType.flexibility,
            target=[Target.legs, Target.obliques], time=DEFAULT_TIME),
    Workout(name="child's pose", description="balasana - kneeling rest position with arms extended forward",
            equipment=[Equipment.mat], intensity=Intensity.low, aerobic_type=AerobicType.flexibility,
            target=[Target.back, Target.shoulders], time=DEFAULT_TIME),
    Workout(name="cat-cow stretch", description="chakravakasana - alternating spinal flexion and extension on hands and knees",
            equipment=[Equipment.mat], intensity=Intensity.low, aerobic_type=AerobicType.flexibility,
            target=[Target.back, Target.core], time=DEFAULT_TIME),
    Workout(name="pigeon pose", description="eka pada rajakapotasana - deep hip flexor and glute stretch",
            equipment=[Equipment.mat], intensity=Intensity.low, aerobic_type=AerobicType.flexibility,
            target=[Target.legs, Target.lower_body], time=DEFAULT_TIME),
    Workout(name="seated forward bend", description="paschimottanasana - seated hamstring and back stretch reaching for toes",
            equipment=[Equipment.mat], intensity=Intensity.low, aerobic_type=AerobicType.flexibility,
            target=[Target.back, Target.legs], time=DEFAULT_TIME),
    Workout(name="cobra pose", description="bhujangasana - prone back extension opening chest and shoulders",
            equipment=[Equipment.mat], intensity=Intensity.low, aerobic_type=AerobicType.flexibility,
            target=[Target.back, Target.chest], time=DEFAULT_TIME),
    Workout(name="bridge pose", description="setu bandhasana - supine hip extension strengthening glutes and opening chest",
            equipment=[Equipment.mat], intensity=Intensity.medium, aerobic_type=AerobicType.flexibility,
            target=[Target.legs, Target.core, Target.back], time=DEFAULT_TIME),
    Workout(name="spinal twist", description="ardha matsyendrasana - seated rotation stretching spine and obliques",
            equipment=[Equipment.mat], intensity=Intensity.low, aerobic_type=AerobicType.flexibility,
            target=[Target.back, Target.obliques, Target.core], time=DEFAULT_TIME)
)


def generate_hash(text: str) -> str:
    time_stamp = datetime.now().strftime("%Y_%m_%d_%H-%M-%S")
    data = f"{text}_{time_stamp}"
    full_sha256_hash = hashlib.sha256(data.encode('utf-8')).hexdigest()
    short_hash = full_sha256_hash[:8]  # Take the first 8 characters
    return short_hash


def convert_to_data_file():

    # print(DATA_FILE_PATH)
    # Energy mapping based on intensity (calories per minute)
    energy_by_intensity = {
        Intensity.high: 13,
        Intensity.medium: 9,
        Intensity.low: 6
    }

    # Create hierarchical structure grouped by aerobic_type (category)
    data_dict = {}
    for workout in WORKOUTS:
        category = workout.aerobic_type.name
        if category not in data_dict:
            data_dict[category] = {}

        data_dict[category][workout.name] = {
            "description": workout.description,
            "equipment": [x.name for x in list(workout.equipment)] if workout.equipment else [],
            "intensity": workout.intensity.name,
            "target": [x.name for x in list(workout.target)],
            "time": workout.time,
            "energy": energy_by_intensity.get(workout.intensity, 9)  # Add calorie burn rate
        }
    with DATA_FILE_PATH.open("w") as f:
        json.dump(data_dict, f, indent=4)


class WorkoutData:
    def __init__(self, nope_list: Sequence[str] = (), equipment_filter: Sequence[Equipment] = (),
                 selected_categories: Sequence[str] = None):
        """Initialize the workout data.
        Args:
            nope_list (Sequence): The list of workout items to omit.
            equipment_filter (Sequence[Equipment]): The list of equipment items to omit.
            selected_categories (Sequence[str]): The list of category names to include (e.g., ['cardio', 'strength']).
                                                 If None, all categories are included.
            """
        with DATA_FILE_PATH.open("r") as f:
            loaded_data = json.load(f)

        # Detect if data is hierarchical (category->exercises) or flat (exercise->data)
        # Hierarchical: first value is a dict of dicts
        # Flat: first value is a dict with 'aerobic_type' key
        first_value = next(iter(loaded_data.values()))
        is_hierarchical = isinstance(first_value, dict) and 'aerobic_type' not in first_value

        if is_hierarchical:
            # Hierarchical structure: {category: {exercise: data}}
            self.hierarchical_data = loaded_data
            # Flatten for backward compatibility
            self.data = {}
            for category_name, exercises in self.hierarchical_data.items():
                for exercise_name, exercise_data in exercises.items():
                    exercise_data_with_category = exercise_data.copy()
                    exercise_data_with_category['aerobic_type'] = category_name
                    self.data[exercise_name] = exercise_data_with_category
        else:
            # Flat structure: {exercise: data} where data includes aerobic_type
            self.data = loaded_data
            # Build hierarchical structure for categories property
            self.hierarchical_data = {}
            for exercise_name, exercise_data in self.data.items():
                category = exercise_data.get('aerobic_type', 'unknown')
                if category not in self.hierarchical_data:
                    self.hierarchical_data[category] = {}
                self.hierarchical_data[category][exercise_name] = exercise_data

        self.nope_list = nope_list
        self.equipment_filter = equipment_filter
        self.selected_categories = selected_categories

    @property
    def filtered_data(self) -> dict:
        """Data with items removed."""
        filtered = {}
        for name, value in self.data.items():
            if name not in self.nope_list:
                # Filter by category if selected_categories is specified
                if self.selected_categories is not None:
                    category = value.get("aerobic_type")
                    if category not in self.selected_categories:
                        continue

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
            sub_workouts = value.get("sub_workouts")
            workouts.append(
                Workout(
                    name=name,
                    description=value.get("description"),
                    equipment=equipment_list if equipment_list else [],
                    intensity=Intensity.__members__.get(value.get("intensity")),
                    aerobic_type=AerobicType.__members__.get(value.get("aerobic_type")),
                    target=target_list,
                    time=DEFAULT_TIME,
                    sub_workouts=sub_workouts,
                )
            )
        return workouts

    @property
    def cardio_workout_items(self) -> list[Workout]:
        return [x for x in self.workouts if x.aerobic_type is AerobicType.cardio if x.name]

    @property
    def strength_workout_items(self) -> list[Workout]:
        return [x for x in self.workouts if x.aerobic_type is AerobicType.strength]

    @property
    def combat_workout_items(self) -> list[Workout]:
        return [x for x in self.workouts if x.aerobic_type is AerobicType.combat]

    @property
    def flexibility_workout_items(self) -> list[Workout]:
        return [x for x in self.workouts if x.aerobic_type is AerobicType.flexibility]

    @property
    def categories(self) -> list[str]:
        """Return list of available category names."""
        return list(self.hierarchical_data.keys())

    def get_workouts_by_category(self, category: str) -> list[Workout]:
        """Get workouts for a specific category."""
        return [x for x in self.workouts if x.aerobic_type.name == category]


if __name__ == "__main__":
    convert_to_data_file()
    equipment_filter = [Equipment.mat, Equipment.kettle_bell, Equipment.dumbbell]
    for x in WorkoutData(nope_list=["oblique twist"], equipment_filter=equipment_filter).strength_workout_items:
        print(x.name, x.equipment)
