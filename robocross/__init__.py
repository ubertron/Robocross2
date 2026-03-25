from __future__ import annotations
from pathlib import Path

from robocross.robocross_enums import WorkoutType

DATA_FILE_PATH: Path = Path(__file__).parent / "workout_data.json"
REST_PERIOD: str = "rest period"
APP_NAME: str = "Robocross"

# Category color constants (RGB hex values)
CATEGORY_COLORS = {
    'cardio': '#3498DB',      # Energetic blue
    'strength': '#E74C3C',    # Strong red-orange
    'combat': '#8E44AD',      # Aggressive purple
    'flexibility': '#27AE60', # Calm green
    'recovery': '#95A5A6',    # Neutral grey
}
SCROLL_PANEL_WIDTH: int = 320
IMAGE_PADDING: int = 20  # Padding/margin for workout images in pixels
TOOL_TIP_SIZE: int = 32  # Font size for transport button tooltips

def get_category_color(category: str) -> str:
    """Get the color for a given category name."""
    return CATEGORY_COLORS.get(category.lower(), '#95A5A6')

def get_contrast_text_color(bg_color: str) -> str:
    """
    Determine if text should be white or black based on background color luminance.

    Args:
        bg_color: Hex color string (e.g., '#E74C3C')

    Returns:
        '#FFFFFF' for white text or '#000000' for black text
    """
    # Remove '#' if present
    hex_color = bg_color.lstrip('#')

    # Convert to RGB
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    # Calculate relative luminance (ITU-R BT.709)
    luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255

    # Use white text for dark backgrounds, black for light
    return '#FFFFFF' if luminance < 0.5 else '#000000'
