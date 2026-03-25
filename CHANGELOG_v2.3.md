# Robocross v2.3 "Mr. Miyagi" - Release Notes

## 🥋 New Features

### Combat Category (10 exercises)
- **Junzuki** - Alternating front punch walking forward
- **Gyakuzuki** - Walk forward, punching with back hand
- **Mae Geri** - Front kick
- **Yoko Geri** - Side kick
- **Mawashi Geri** - Roundhouse kick
- **Sokuto Geri** - Blade kick
- **Jodan Uke** - High block
- **Soto Uke** - Middle block
- **Weighted Punches** (moved from Cardio)
- **Cross Punches** (moved from Cardio)

### Flexibility Category (10 exercises)
- **Downward Dog** - Inverted V position with hands and feet on ground
- **Child's Pose** - Kneeling with forehead on ground, arms extended
- **Cobra Stretch** - Lying face down, push upper body up
- **Forward Fold** - Standing, bend forward reaching for toes
- **Seated Forward Bend** - Sitting with legs extended, reach forward
- **Butterfly Stretch** - Soles of feet together, press knees down
- **Cat Cow Stretch** - On hands and knees, alternate arching/rounding
- **Pigeon Pose** - One leg forward bent, other extended back
- **Quadriceps Stretch** - Pull foot to buttocks to stretch thigh
- **Hamstring Stretch** - Extend leg forward on heel, lean forward

## 🎨 Modern Workout Player (v2)

### Visual Progress Tracking
- **Dot Indicators**: Real-time progress visualization with color-coded dots
  - Each dot represents one exercise in your circuit
  - Colors match exercise categories (cardio, strength, combat, flexibility)
  - Three states: not started (dim), in progress (bright with white ring), finished (extra bright)
- **Circuit Counter**: Shows current circuit number for multi-circuit workouts

### Rich Media Display
- **Video Support**: Looping demonstration videos (.mp4, .mov, .avi)
- **Animated GIFs**: Animated exercise guides
- **Smart Images**: Static images with automatic category color tinting for monochrome diagrams
- **Auto-Fallback**: Default images shown when no media available

### Enhanced Playback Controls
- **Transport Buttons**: Play/pause, skip forward/back through exercises
- **Next Exercise Preview**: Red bar shows upcoming exercise
- **Category Color Coding**: Duration and description text matches exercise category
- **Voice Announcements**: Speaks exercise names and circuit numbers

## 🔄 Workflow Improvements

### Category Selection System
- **Replaced**: Single "Workout Type" dropdown
- **Added**: Four category checkboxes (Cardio, Strength, Combat, Flexibility)
- Select any combination of categories for your workout

### Workout Structure Modes

#### Random Mode
- Picks exercises randomly from ANY selected category
- Creates varied, unpredictable workouts
- Example: Cardio → Combat → Flexibility → Cardio → Strength

#### Sequence Mode
- Generates a random sequence order (e.g., Combat → Flexibility → Strength → Cardio)
- Cycles through selected categories in that order
- Creates structured, balanced progression
- Example with 3 categories: C → F → S → C → F → S → C → F → S

### Removed Features
- ❌ "Nope List" field (no more exercises for cowards!)
- ❌ Old "Workout Type" dropdown

## 📊 Exercise Database

### Total Exercises: 96
- **Cardio**: 17 exercises
- **Strength**: 59 exercises
- **Combat**: 10 exercises
- **Flexibility**: 10 exercises

## 🛠 Technical Changes

### Data Structure
- Restructured `workout_data.json` to hierarchical format:
  ```json
  {
    "cardio": { "exercise_name": {...} },
    "strength": { "exercise_name": {...} },
    "combat": { "exercise_name": {...} },
    "flexibility": { "exercise_name": {...} }
  }
  ```

### Updated Components
- `WorkoutData` class: Category-based filtering and loading
- `Routine` class: Random and Sequence build algorithms
- `WorkoutForm`: Dynamic category checkboxes
- `ExercisePickerDialog`: Shows all 4 categories
- `ParametersWidget`: Dynamic category organization
- `AerobicType` enum: Added Combat and Flexibility types

### New UI Components

#### Workout Player v2 (`viewer_v2.py`)
- Modern visual workout player with enhanced media support
- Dot-based progress indicators showing workout position
- Circuit counter for multi-circuit workouts
- Full media display (videos, GIFs, images)
- Automatic color-coding by exercise category
- Transport controls (play/pause, forward/back, reset)
- Next exercise preview bar

#### Media System (`media_loader.py`)
- Priority-based media file discovery:
  1. Videos (.mp4, .mov, .avi)
  2. Animations (.gif)
  3. Images (.png, .jpg, .jpeg)
  4. Fallback to random default image
- `VideoPlayerWidget`: Looping video player for exercise demonstrations
- `has_transparent_padding()`: Smart image padding detection
- Automatic monochrome image tinting to match category colors

#### Progress Visualization (`workout_dot.py`)
- `WorkoutDot`: Circular progress indicators with three states:
  - Not started (darkened category color)
  - In progress (full category color with white border)
  - Finished (brightened category color)
- `DotContainer`: Auto-spacing container that distributes dots across available width
- Category-colored dots that update in real-time during workouts

#### Exercise Type Dialog (`exercise_type_dialog.py`)
- Modal dialog for selecting exercise category when adding new workouts
- Color-coded category buttons matching workout color scheme
- Hover effects and visual feedback

#### Supporting Components
- `ImageLabel` (`widgets/image_label.py`): Resizable image widget with aspect ratio preservation
- `view_debug_log.py`: Real-time log viewer utility for workout debugging (monitors last 50 lines)

## 🎯 Usage Examples

### Build a Martial Arts Flexibility Workout
1. Check: Combat ✓, Flexibility ✓
2. Select: Sequence mode
3. Click: Build
4. Result: Alternating kicks/punches/blocks with stretches

### Build a Full-Body Random Workout
1. Check: All categories ✓
2. Select: Random mode
3. Click: Build
4. Result: Completely varied exercise selection

### Build a Combat Endurance Circuit
1. Check: Combat ✓, Cardio ✓
2. Select: Sequence mode
3. Click: Build
4. Result: Martial arts techniques alternating with cardio bursts

## 🔧 Migration Notes

- Old workout files still load correctly
- Default selection: Cardio + Strength (maintains existing behavior)
- Exercise picker now shows all 4 categories in tree view
- Saved workouts preserve category information

---

**Version**: 2.3
**Codename**: Mr. Miyagi
**Release Date**: 2026-03-17
