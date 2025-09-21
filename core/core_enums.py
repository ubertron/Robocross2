from enum import Enum, auto, unique

class Alignment(Enum):
    horizontal = auto()
    stacked = auto()
    vertical = auto()


class RunState(Enum):
    paused = auto()
    playing = auto()


class Position(Enum):
    bottom = auto()
    center = auto()
    left = auto()
    right = auto()
    top = auto()