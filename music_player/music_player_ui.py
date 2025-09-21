from __future__ import annotations

from functools import partial
from pathlib import Path

import eyed3
from PySide6.QtCore import QUrl, QSettings
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import QComboBox, QPushButton
from music_player import PLAYLIST_DIR, MUSIC_DIR
from music_player.playlist import Playlist

from core import DEVELOPER
from core.core_enums import Alignment, RunState, Position
from core.logging_utils import get_logger
from core.version_info import VersionInfo
from widgets.generic_widget import GenericWidget

TOOL_NAME = "Music Player"
VERSIONS = [
    VersionInfo(name=TOOL_NAME, version="0.1", codename="bugatti", info="first release")
]
DEFAULT_PLAYLIST = 'Maximum Overdrive'
LOGGER = get_logger(name=__name__)


class MusicPlayer(GenericWidget):
    """Widget for playing music."""

    play_pause_text = {
        RunState.paused: 'Play',
        RunState.playing: 'Pause'
    }
    default_volume = 7
    button_width = 80
    volume_button_width = 32
    volume_key = 'volume'
    playlist_key = 'playlist'

    def __init__(self):
        super().__init__(title=VERSIONS[-1].title, alignment=Alignment.horizontal, spacing=8)
        self.settings = QSettings(DEVELOPER, TOOL_NAME)
        self.playlist_combo_box: QComboBox = self.add_widget(QComboBox())
        self.current_track_label = self.add_label()
        self.add_stretch()
        self.play_pause_button = self.add_button(text='', tool_tip='Toggle music play state',
                                                 clicked=self.play_pause_clicked)
        self.next_button = self.add_button(text='Next', tool_tip='Play next track',
                                           clicked=self.next_button_clicked)
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.track_index = -1
        self.run_state = RunState.paused
        self.media_player.mediaStatusChanged.connect(self.handle_media_status_changed)
        self.volume_label = self.add_label(position=Position.left)
        self.volume_down = self.add_button(text='-', clicked=partial(self.volume_changed, -1))
        self.volume_up = self.add_button(text='+', clicked=partial(self.volume_changed, 1))
        self.mute_button: QPushButton = self.add_button('Mute', clicked=partial(self.volume_changed, 0))
        self._setup_ui()

    def _setup_ui(self):
        self.playlist_combo_box.addItems(x.name for x in self.playlists)
        self.playlist_combo_box.setCurrentText(self.settings.value(self.playlist_key, DEFAULT_PLAYLIST))
        self.playlist_combo_box.currentTextChanged.connect(self.playlist_changed)
        self.playlist_changed()
        self.play_pause_button.setFixedWidth(self.button_width)
        self.next_button.setFixedWidth(self.button_width)
        self.volume = self.settings.value(self.volume_key, self.default_volume)
        self.volume_up.setFixedWidth(self.volume_button_width)
        self.volume_down.setFixedWidth(self.volume_button_width)
        self.mute_button.setCheckable(True)
        self.setFixedHeight(self.sizeHint().height())

    @property
    def current_artist(self) -> str | None:
        if self.current_track and self.current_track.suffix == ".mp3":
            metadata = eyed3.load(self.current_track.as_posix())
            return metadata.tag.artist if metadata and metadata.tag.artist else None
        return None

    @property
    def current_playlist(self):
        return Playlist(self.playlist_combo_box.currentText())

    @property
    def current_track(self) -> Path | None:
        return MUSIC_DIR / self.current_playlist.tracks[self.track_index] if len(self.current_playlist.tracks) else None

    @property
    def mute(self) -> bool:
        return not self.mute_button.isChecked()

    @mute.setter
    def mute(self, value: bool):
        self.mute_button.setChecked(value)
        self.volume_changed(delta=0)

    @property
    def playlists(self) -> list[Playlist]:
        return [Playlist(name=x.stem) for x in PLAYLIST_DIR.glob("*.txt")]

    @property
    def run_state(self) -> RunState:
        return self._run_state

    @run_state.setter
    def run_state(self, state: RunState) -> None:
        self._run_state = state
        self.play_pause_button.setText(self.play_pause_text.get(state))
        if state is RunState.playing:
            self.media_player.play()
        else:
            self.media_player.pause()

    @property
    def track_index(self) -> int:
        return self._track_index

    @track_index.setter
    def track_index(self, index: int):
        self._track_index = index
        if self.current_track:
            artist_string = f"{self.current_artist.title()} - " if self.current_artist else ""
            self.current_track_label.setText(f'{artist_string}{self.current_track.stem}')

    @property
    def volume(self) -> int:
        return int(self.volume_label.text().split(" ")[1])

    @volume.setter
    def volume(self, value: int):
        mute_factor = 0.25 if self.mute_button.isChecked() else 1.0
        self.volume_label.setText(f"Volume: {value}")
        self.audio_output.setVolume(value / 10 * mute_factor)
        LOGGER.debug(f"Volume changed to {self.audio_output.volume()}")
        self.settings.setValue(self.volume_key, value)

    def handle_media_status_changed(self, status):
        """Event for media player."""
        if status == QMediaPlayer.EndOfMedia:
            LOGGER.debug("Audio playback has finished.")
            self.next_button_clicked()

    def next_button_clicked(self):
        self.track_index = (self.track_index + 1) % len(self.current_playlist.tracks)
        run_state = self.run_state
        self.media_player.pause()
        self.media_player.setSource(QUrl.fromLocalFile(self.current_track.as_posix()))
        if run_state is RunState.playing:
            self.media_player.play()

    def play(self):
        self.media_player.play()
        self.run_state = RunState.playing

    def play_pause_clicked(self):
        """Event for play_pause_button."""
        self.run_state = RunState.paused if self.run_state == RunState.playing else RunState.playing

    def playlist_changed(self):
        """Event for playlist_combo_box."""
        initial_run_state = self.run_state
        self.run_state = RunState.paused
        self.media_player.stop()
        self.settings.setValue(self.playlist_key, self.current_playlist.name)
        if self.current_playlist.tracks:
            self.track_index = 0
            if self.current_track.exists():
                self.media_player.setSource(QUrl.fromLocalFile(self.current_track.as_posix()))
            else:
                LOGGER.exception(f"Could not find track '{self.current_track}'")
                self.track_index = -1
        self.run_state = initial_run_state

    def volume_changed(self, delta: int):
        """Set the volume."""
        self.volume = self.volume + delta
        self.volume_up.setEnabled(self.volume < 10)
        self.volume_down.setEnabled(self.volume > 0)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = MusicPlayer()
    window.show()
    app.exec()
