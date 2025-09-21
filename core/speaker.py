"""Text to speech mac-only"""
from __future__ import annotations

import logging
import os
import random

from enum import Enum, unique, auto
from pathlib import Path
from typing import Optional
from subprocess import Popen
from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QWidget

from core.logging_utils import get_logger
LOGGER = get_logger(name=__name__, level=logging.DEBUG)


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


class Speaker(QObject):
    speaking_finished = Signal()

    def __init__(self, voice: Optional[Voice] = None, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self.voice: str = voice.name.replace("_", "-") if voice else random.choice(Voice.names())

    def speak(self, text: str):
        """Text to speech.

        add '[[slnc 500]]' to text string to include a pause of 500 ms
        """
        process = Popen(['say', '-v', self.voice, text])
        process.wait()
        self.speaking_finished.emit()

    def save(self, text: str, file_path: Optional[Path] = None):
        if not file_path:
            file_path = Path(f'{text}.aiff')
        file_path.parent.mkdir(parents=True, exist_ok=True)
        Popen(['say', '-o', file_path.absolute(), '-v', self.voice, text])
        return file_path.resolve()


if __name__ == "__main__":
    line = "This is a sentence."
    _voice = Speaker(voice=Voice.Samantha)
    _voice.speaking_finished.connect(lambda: print("Finished speaking"))
    _voice.speak(text=line)
    result = _voice.save(text=line, file_path=Path("test.aiff"))
    print(result)
