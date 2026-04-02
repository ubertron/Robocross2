# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Robocross2 is a PySide6-based workout planning and player application that generates randomized or structured fitness routines from an exercise database. The app features a workout editor, a visual player with media support, and an exercise editor for managing the workout database.

## Development Commands

### Running the Application
```bash
# Activate virtual environment
source .venv/bin/activate

# Run the main application
python robocross/robocross_ui.py
```

### Dependencies
```bash
# Install dependencies
pip install -r requirements.txt
```

Core dependencies: PySide6, Pillow, eyeD3, pyqtdarktheme

## Architecture

### Application Structure

The application follows a three-tab architecture:

1. **Editor Tab** (`ParametersWidget`) - Workout configuration and exercise list editing
2. **Player Tab** (`ViewerV2`) - Visual workout player with timer, media display, and progress tracking
3. **Exercise Tab** (`ExerciseEditor`) - Exercise database management

### Core Data Model

**Workout** (`robocross/workout.py`)
- Dataclass representing a single exercise with properties: name, description, equipment, intensity, aerobic_type (category), target areas, time, optional sub_workouts, and energy (calories/min)

**Routine** (`robocross/routine.py`)
- Builds workout lists from the exercise database
- Supports two workout structures: "Random" (picks random exercises from selected categories) or "Sequence" (cycles through categories in order)
- Calculates intervals, rest periods, and workout counts based on workout length

**WorkoutData** (`robocross/workout_data.py`)
- Manages the exercise database from `robocross/workout_data.json`
- Provides filtering by equipment and categories
- The JSON file has hierarchical structure: `{category: {exercise_name: {properties}}}`
- Categories (AerobicType): cardio, strength, combat, flexibility, recovery

### Key Design Patterns

**Session Persistence**
- Workouts auto-save to `data/_last_workout_temp.json` on build
- Auto-loads the last workout on startup via QSettings (`last_workout_path_key`)
- Manual save/load via JSON files in `data/` directory

**Circuit Cycles**
- `workout_cycles` property allows repeating a circuit multiple times
- The player expands the base workout list by cycles before display
- Dot indicators show progress through all cycles

**Widget Architecture**
- `GenericWidget` (`widgets/generic_widget.py`) is the base class for all custom widgets
- Provides consistent margin/spacing and layout management (horizontal/vertical via Alignment enum)
- `FormWidget`, `ButtonBar`, `ImageLabel`, `Stopwatch` all extend this base

**Media System** (`robocross/media_loader.py`)
- Media files stored in `media/images/`, `media/animations/`, `media/movies/`
- Naming convention: `{exercise_name_with_underscores}.{ext}`
- Falls back to default images if exercise-specific media not found
- Supports images, GIFs, and videos (via `VideoPlayerWidget`)

### Critical Files

**Data File** (`robocross/workout_data.json`)
- Main exercise database
- Backup stored at `robocross/workout_data_backup.json`
- To regenerate from Python constants: run `python robocross/workout_data.py`

**Paths** (`core/core_paths.py`)
- Centralized path configuration
- `DATA_FILE_PATH` points to workout_data.json
- `image_path()` searches recursively for icons/images

**Enums** (`robocross/robocross_enums.py`)
- `Equipment`: mat, dumbbell, barbell, medicine_ball, etc.
- `Intensity`: low, medium, high
- `AerobicType`: cardio, strength, combat, flexibility, recovery
- `Target`: full_body, upper_body, legs, core, arms, shoulders, etc.
- `RunMode`: playing, paused

### Player Implementation (ViewerV2)

**State Management**
- `_base_workout_list`: Original circuit without cycle expansion
- `workout_list`: Full expanded list (base × cycles)
- `current_index`: Position in expanded workout list
- `_current_circuit`: Which cycle iteration (1-based)

**Visual Components**
- Workout name label at top
- Dot indicators (`DotContainer`) showing exercise progress
- Large exercise title with category-colored background
- Media display (image/video/animation)
- Stopwatch with play/pause/reset controls
- Music player integration
- Next exercise preview

**Notifications**
- Uses macOS `say` command via `Speaker` class for voice announcements
- Volume configurable via settings (`narration_volume` 0-10)

## Code Conventions

### Naming
- Exercise names in data: lowercase with spaces (`"front kicks"`)
- File names: snake_case
- Classes: PascalCase
- Properties/methods: snake_case

### File Structure
- `/robocross/` - Main application logic
- `/widgets/` - Reusable UI components
- `/core/` - Shared utilities (logging, paths, enums, time formatting)
- `/music_player/` - Audio playback components
- `/data/` - Saved workout sessions (JSON)
- `/media/` - Exercise images, animations, videos
- `/images/` - App icons and UI assets

### Logging
- File logs to `logs/workouts.log`
- Uses custom `logging_utils` with FileHandler and StreamHandler
- Log level: DEBUG for file, INFO for console

### Settings Persistence
- Uses `QSettings(DEVELOPER, APP_NAME)` for user preferences
- Stores: app size, last workout path, narration volume
- Auto-saves workout name to settings on save/build

## Working with Exercises

### Adding a New Exercise
1. Use Exercise Editor tab (third tab)
2. Set name (lowercase with spaces), category, description
3. Select equipment and target areas
4. Set intensity and energy (cal/min)
5. Optionally enable sub-workouts for composite exercises
6. Optionally load custom media
7. Save - file automatically copied to `media/images/{exercise_name}.{ext}`

### Media Lookup Order
1. `media/images/{exercise_name_with_underscores}.{png,jpg,jpeg,gif}`
2. `media/animations/{exercise_name_with_underscores}.{gif}`
3. `media/movies/{exercise_name_with_underscores}.{mp4,mov,avi}`
4. Falls back to default images (default_image_01.png, default_image_02.png, default_image_03.png)

## Important Notes

- **Python Version**: Uses Python 3.9+ (tested with 3.9.13)
- **Platform**: Developed for macOS (uses `say` command for voice)
- **Theme**: Dark theme via `qdarktheme`
- **Splash Screen**: 5-second delay on startup (`splash_screen_manager`)
- **Version System**: Managed via `VersionInfo` dataclass with codenames
- **Rest Periods**: Special workout items with name `"rest period"` inserted between exercises
- **Category Colors**: Defined in `robocross/__init__.py` as `CATEGORY_COLORS` dict (hex RGB)
