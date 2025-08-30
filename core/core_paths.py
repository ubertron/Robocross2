from pathlib import Path

IMAGE_FOLDER = Path(__file__).parents[1] / "images"

def image_path(file_name: str) -> Path or None:
    """Searches image directory for path"""
    return next((x for x in IMAGE_FOLDER.rglob(file_name)), None)



if __name__ == "__main__":
    print(image_path(file_name="open.png"))