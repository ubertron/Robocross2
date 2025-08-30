from enum import Enum, auto, unique

class Alignment(Enum):
    horizontal = auto()
    vertical = auto()

class Position(Enum):
    bottom = auto()
    center = auto()
    left = auto()
    right = auto()
    top = auto()
