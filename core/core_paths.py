from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]
IMAGE_FOLDER = PROJECT_ROOT / "images"
DATA_DIR = PROJECT_ROOT / "data"
MEDIA_ROOT = Path(__file__).parents[1] / "media"
DATA_FILE_PATH: Path = Path(__file__).parents[1] / "robocross" / "workout_data.json"

def image_path(file_name: str) -> Path or None:
    """Searches image directory for path"""
    return next((x for x in IMAGE_FOLDER.rglob(file_name)), None)



if __name__ == "__main__":
    print(image_path(file_name="open.png"))