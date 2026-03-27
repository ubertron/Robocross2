from pathlib import Path
from core.core_paths import image_path, MEDIA_ROOT
import random

from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False



MOVIES_DIR = MEDIA_ROOT / "movies"
ANIMATIONS_DIR = MEDIA_ROOT / "animations"
IMAGES_DIR = MEDIA_ROOT / "images"


def has_transparent_padding(image_path: Path, min_padding: int = 10) -> bool:
    """
    Check if a PNG image has transparent padding on its edges.

    Args:
        image_path: Path to PNG image
        min_padding: Minimum padding in pixels to detect (default 10)

    Returns:
        True if image has transparent padding >= min_padding on all edges
    """
    if not HAS_PIL or image_path.suffix.lower() != '.png':
        return False

    try:
        img = Image.open(image_path).convert("RGBA")
        width, height = img.size
        pixels = img.load()

        # Check if all edges have at least min_padding transparent pixels
        # Top edge
        top_transparent = 0
        for y in range(height):
            if all(pixels[x, y][3] == 0 for x in range(width)):
                top_transparent += 1
            else:
                break

        # Bottom edge
        bottom_transparent = 0
        for y in range(height - 1, -1, -1):
            if all(pixels[x, y][3] == 0 for x in range(width)):
                bottom_transparent += 1
            else:
                break

        # Left edge
        left_transparent = 0
        for x in range(width):
            if all(pixels[x, y][3] == 0 for y in range(height)):
                left_transparent += 1
            else:
                break

        # Right edge
        right_transparent = 0
        for x in range(width - 1, -1, -1):
            if all(pixels[x, y][3] == 0 for y in range(height)):
                right_transparent += 1
            else:
                break

        # Return True if all edges have at least min_padding transparent pixels
        return (top_transparent >= min_padding and
                bottom_transparent >= min_padding and
                left_transparent >= min_padding and
                right_transparent >= min_padding)

    except Exception:
        return False


def find_workout_media(workout_name: str) -> Path | None:
    """
    Find media file for a workout using priority search.

    Priority:
    1. Movies (.mp4, .mov, .avi)
    2. Animations (.gif)
    3. Images (.png, .jpg, .jpeg)
    4. Default fallback (default_image*.png)

    Args:
        workout_name: Human-readable name (e.g., "Bent Over Rows")

    Returns:
        Path to media file or None
    """
    # Convert to snake_case
    snake_name = workout_name.lower().replace(' ', '_')

    # 1. Search movies (in media/movies directory)
    for ext in ['.mp4', '.mov', '.avi']:
        movie_path = MOVIES_DIR / f"{snake_name}{ext}"
        if movie_path.exists():
            return movie_path

    # 2. Search animations (in media/animations directory)
    gif_path = ANIMATIONS_DIR / f"{snake_name}.gif"
    if gif_path.exists():
        return gif_path

    # 3. Search images (in media/images directory)
    for ext in ['.png', '.jpg', '.jpeg']:
        img_path = IMAGES_DIR / f"{snake_name}{ext}"
        if img_path.exists():
            return img_path

    # 4. Fallback to random default image
    default_images = list(IMAGES_DIR.glob("default_image*.png"))
    if default_images:
        return random.choice(default_images)

    return None


class VideoPlayerWidget(QVideoWidget):
    """Looping video player for exercise demonstrations."""

    def __init__(self, video_path: Path):
        super().__init__()
        self.player = QMediaPlayer()
        self.player.setVideoOutput(self)
        self.player.setSource(QUrl.fromLocalFile(str(video_path)))
        self.player.setLoops(QMediaPlayer.Loops.Infinite)  # Loop forever
        self.player.setAudioOutput(None)  # Muted

        # Maintain aspect ratio
        self.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)

    def start(self):
        """Start video playback."""
        self.player.play()

    def stop(self):
        """Stop video playback."""
        self.player.stop()
