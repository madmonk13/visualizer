"""
Configuration module for music visualizer
Contains color palettes, frequency bands, and default settings
"""

# Frequency bands configuration (Hz)
FREQUENCY_BANDS = [
    {'name': 'Sub-Bass', 'min': 20, 'max': 40, 'hue_offset': 0},
    {'name': 'Bass', 'min': 40, 'max': 80, 'hue_offset': 45},
    {'name': 'Low-Bass', 'min': 80, 'max': 100, 'hue_offset': 90},
    {'name': 'Low-Mid', 'min': 100, 'max': 200, 'hue_offset': 135},
    {'name': 'Mid', 'min': 200, 'max': 400, 'hue_offset': 180},
    {'name': 'Upper-Mid', 'min': 400, 'max': 600, 'hue_offset': 225},
    {'name': 'High-Mid', 'min': 600, 'max': 800, 'hue_offset': 270},
    {'name': 'Presence', 'min': 800, 'max': 1000, 'hue_offset': 315}
]

# Color palettes
COLOR_PALETTES = {
    'rainbow': {
        'name': 'Rainbow',
        'colors': [0, 45, 90, 135, 180, 225, 270, 315],
        'saturation': 1.0,
        'brightness': 1.0
    },
    'spring': {
        'name': 'Spring',
        'colors': [80, 100, 120, 140, 280, 300, 320, 340],
        'saturation': 0.8,
        'brightness': 0.95
    },
    'summer': {
        'name': 'Summer',
        'colors': [30, 45, 60, 180, 200, 220, 240, 260],
        'saturation': 1.0,
        'brightness': 1.0
    },
    'autumn': {
        'name': 'Autumn',
        'colors': [0, 15, 30, 35, 40, 25, 20, 10],
        'saturation': 0.9,
        'brightness': 0.85
    },
    'winter': {
        'name': 'Winter',
        'colors': [180, 200, 220, 240, 260, 200, 190, 210],
        'saturation': 0.7,
        'brightness': 0.9
    },
    'ice': {
        'name': 'Ice',
        'colors': [180, 190, 200, 210, 220, 200, 195, 205],
        'saturation': 0.5,
        'brightness': 1.0
    },
    'fire': {
        'name': 'Fire',
        'colors': [0, 10, 20, 30, 40, 25, 15, 35],
        'saturation': 1.0,
        'brightness': 0.95
    },
    'water': {
        'name': 'Water',
        'colors': [160, 170, 180, 190, 150, 165, 175, 185],
        'saturation': 0.8,
        'brightness': 0.9
    },
    'earth': {
        'name': 'Earth',
        'colors': [25, 30, 35, 40, 45, 50, 55, 60],
        'saturation': 0.6,
        'brightness': 0.7
    }
}

# Default settings
DEFAULT_FPS = 30
DEFAULT_RESOLUTION = (1280, 720)
PHONE_VERTICAL_RESOLUTION = (1080, 1920)
PHONE_HORIZONTAL_RESOLUTION = (1920, 1080)

# Preview mode optimizations
PREVIEW_FPS_REDUCTION = 15
PREVIEW_RESOLUTION_DIVISOR = 2
PREVIEW_NPERSEG = 1024
FULL_NPERSEG = 2048

# Animation parameters
BASE_ROTATION_SPEED = 0.001
VOLUME_ROTATION_MULTIPLIER = 0.015
HUE_SHIFT_BASE = 0.5
TRAIL_FADE_FACTOR = 0.85
FADE_DURATION_SECONDS = 2.0

# Starfield parameters
STARFIELD_STARS_FULL = 200
STARFIELD_STARS_PREVIEW = 100
STARFIELD_BASE_SPEED = 0.5
STARFIELD_VOLUME_MULTIPLIER = 5.5

# Beat detection parameters
BEAT_BASS_MIN = 20
BEAT_BASS_MAX = 250
BEAT_LOW_MID_MIN = 250
BEAT_LOW_MID_MAX = 1000
BEAT_THRESHOLD_MULTIPLIER = 0.3
BEAT_DECAY_FACTOR = 0.7