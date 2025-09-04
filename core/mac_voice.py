"""Text to speech mac-only"""

import logging
import os
import random

from enum import Enum, unique, auto
from pathlib import Path
from typing import Optional

from core.logging_utils import get_logger
GERGER = get_logger(name=__name__, level=logging.DEBUG)


class Voice(Enum):
    Alex = auto()
    Alice = auto()
    Alva = auto()
    Amelie = auto()
    Anna = auto()
    Carmit = auto()
    Damayanti = auto()
    Daniel = auto()
    Diego = auto()
    Ellen = auto()
    Fiona = auto()
    Fred = auto()
    Ioana = auto()
    Joana = auto()
    Kanya = auto()
    Karen = auto()
    Kyoko = auto()
    Laura = auto()
    Lekha = auto()
    Luciana = auto()
    Mariska = auto()
    Mei_Jia = auto()
    Melina = auto()
    Milena = auto()
    Moira = auto()
    Monica = auto()
    Nora = auto()
    Paulina = auto()
    Samantha = auto()
    Sara = auto()
    Satu = auto()
    Sin_ji = auto()
    Tessa = auto()
    Thomas = auto()
    Ting_Ting = auto()
    Veena = auto()
    Victoria = auto()
    Xander = auto()
    Yelda = auto()
    Yuna = auto()
    Zosia = auto()
    Zuzana = auto()

    @staticmethod
    def names() -> list[str]:
        return [x.name.replace("_", "-") for x in list(Voice)]

    @property
    def count(self):
        return len(self.names())


class MacVoice:
    def __init__(self, voice: Optional[Voice] = None):
        self.voice: str = voice.name.replace("_", "-") if voice else random.choice(Voice.names())

    def speak(self, line: str):
        """Text to speech"""
        os.system(f'say -v {self.voice} "{line}"')

    def save(self, line: str, file_path: Optional[Path] = None):
        if not file_path:
            file_path = Path(f'{line}.aiff')
        file_path.parent.mkdir(parents=True, exist_ok=True)
        os.system(f'say -o "{file_path.absolute()}" -v {self.voice} "{line}"')
        return file_path.resolve()


if __name__ == "__main__":
    _voice = MacVoice(voice=Voice.Samantha)
    _voice.say("This is a sentence.")
