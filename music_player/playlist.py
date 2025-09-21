"""Utils to create playlists."""
import logging
import random
import subprocess

from pathlib import Path
from core.logging_utils import get_logger
from music_player import PLAYLIST_DIR, MUSIC_DIR

LOGGER: logging.Logger = get_logger(name=__name__)

class Playlist:
    def __init__(self, name: str):
        self.name = name
        if self.path.exists():
            self.load()
        else:
            self.tracks = []

    @property
    def path(self) -> Path:
        return PLAYLIST_DIR.joinpath(self.name).with_suffix('.txt')

    @property
    def tracks(self) -> list[Path]:
        """Absolute paths of the tracks."""
        return self._tracks

    @tracks.setter
    def tracks(self, value: list[Path]):
        self._tracks = value

    def load(self) -> None:
        if self.path.exists():
            with self.path.open('r') as file:
                self.tracks = [MUSIC_DIR / Path(x) for x in file.read().splitlines()]

    def build_from_artists(self, artists: list[str], count: int):
        all_tracks = []
        for artist in artists:
            if MUSIC_DIR.joinpath(artist).exists():
                all_tracks.extend(MUSIC_DIR.joinpath(artist).rglob("*.mp3"))
                all_tracks.extend(MUSIC_DIR.joinpath(artist).rglob("*.m4a"))
        if len(all_tracks) >= count:
            self.tracks = random.sample(all_tracks, count)
            for x in self.tracks:
                print(x.relative_to(MUSIC_DIR))
        else:
            raise RuntimeError('Not enough tracks found')

    def git_add(self):
        return subprocess.check_output(['git', 'add', self.path])

    def save(self):
        """Tracks are saved with relative paths."""
        with self.path.open('w') as file:
            file.write('\n'.join(x.relative_to(MUSIC_DIR).as_posix() for x in self.tracks))
        self.git_add()


def create_single_artist_playlist(artist: str, count: int = 10):
    """Create a random playlist featuring a single artist."""
    playlist = Playlist(name=artist)
    playlist.build_from_artists(artists=[artist], count=count)
    playlist.save()


if __name__ == "__main__":
    # playlist = Playlist(name='maximum overdrive')
    # LOGGER.info('\n'.join(x.as_posix() for x in playlist.tracks))
    # hyperdrive = Playlist(name='Hyperdrive')
    # artists = ('Friendly Fires', 'Molchat Doma', 'Pendulum', 'White Lies')
    # hyperdrive.build_from_artists(artists=artists, count=10)
    # hyperdrive.save()
    # maiden_playlist = Playlist(name='Iron Maiden')
    # maiden_playlist.build_from_artists(artists=["Iron Maiden"], count=10)
    # maiden_playlist.save()
    # beastie_boys = Playlist(name='Intergalactic')
    # beastie_boys.build_from_artists(artists=['Beastie Boys'], count=20)
    # beastie_boys.save()
    create_single_artist_playlist(artist='Drab Majesty')
