from core.core_paths import image_path
from pathlib import Path
from PIL import Image, ImageColor, ImageDraw


RED = (255, 0, 0)
LIGHT_GREY = (216, 216, 216)


def tint_image(path: Path, output_path: Path, rgb: tuple[int, int, int], factor=0.3):
    try:
        image = Image.open(path.as_posix())
        image = image.convert("RGB")
        rgb_string = ", ".join(str(x) for x in rgb)
        tint_rgb = ImageColor.getrgb(f"rgb({rgb_string})")

        tinted_image = Image.new("RGB", image.size, tint_rgb)
        blended_image = Image.blend(image, tinted_image, factor)
        blended_image.save(output_path.as_posix())
        blended_image.show()
        print(f"Image tinted and saved to {output_path}")

    except FileNotFoundError:
        print(f"Error: Image not found at {path}")
    except Exception as e:
        print(f"An error occurred: {e}")


def fill_background(path: Path, output_path: Path, rgb: tuple[int, int, int]):
    """Fill the background of a transparent image."""
    image = Image.open(path).convert("RGBA")
    background = Image.new("RGBA", image.size, rgb + (255,))
    result = Image.alpha_composite(background, image)
    result.save(output_path)


def fill_foreground(path: Path, output_path: Path, rgb: tuple[int, int, int]) -> None:
    """Fill an image with a specified color, preserving transparency.

    Args:
        path: Path to the image file.
        output_path: Output path.
        rgb: Color to fill with, as an RGBA tuple (e.g., (255, 0, 0, 255) for red).
    """
    img = Image.open(path).convert("RGBA")
    pixels = img.load()
    width, height = img.size
    rgba = (*list(rgb), 255)
    for x in range(width):
        for y in range(height):
            if pixels[x, y][3] > 0:  # Check if pixel is not fully transparent
                pixels[x, y] = rgba
    img.save(output_path)

def resize(path: Path, new_width = 320, text_suffix: str = ""):
    # Open the image
    image = Image.open(path.as_posix())

    # Calculate the aspect ratio
    aspect_ratio = image.height / image.width

    # Calculate the new height based on the aspect ratio
    new_height = int(new_width * aspect_ratio)

    # Resize the image using the calculated dimensions
    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)  # Use a good resampling filter

    # Save the resized image
    resized_image.save(path.with_stem(f"{path.stem}{text_suffix}"))

if __name__ == "__main__":
    from core_paths import image_path, IMAGE_FOLDER
    # my_path = image_path("open.png")
    #tint_image(image_path=my_path, rgb=(255, 0, 0), output_path=IMAGE_FOLDER / "open_red.png", factor=.3)
    #fill_background(image_path=my_path, rgb=(255, 0, 0), output_path=IMAGE_FOLDER / "open_red.png")
    # fill_foreground(path=my_path, rgb=LIGHT_GREY, output_path=IMAGE_FOLDER / "open_grey.png")
    # fill_foreground(path=image_path("new.png"), rgb=LIGHT_GREY, output_path=IMAGE_FOLDER / "new_grey.png")
    # fill_foreground(path=image_path("save.png"), rgb=LIGHT_GREY, output_path=IMAGE_FOLDER / "save_grey.png")
    my_image = image_path('splashscreen.png')
    print(my_image)
    resize(path=my_image, new_width=640, text_suffix="_640")