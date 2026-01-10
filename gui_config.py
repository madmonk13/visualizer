"""
GUI Configuration
Constants and settings for the GUI application
"""

# Window settings
WINDOW_TITLE = "Music Visualizer Studio"
WINDOW_SIZE = "1200x800"
CANVAS_MIN_WIDTH = 100
CANVAS_DEFAULT_WIDTH = 700
CANVAS_DEFAULT_HEIGHT = 500

# Control panel settings
CONTROLS_CANVAS_WIDTH = 280
CONTROLS_PADDING = "5"
MAIN_PADDING = "10"

# Color palettes available in dropdown
PALETTE_OPTIONS = (
    'rainbow', 'spring', 'summer', 'autumn', 
    'winter', 'ice', 'fire', 'water', 'earth'
)

# Rotation options for dropdowns
WAVEFORM_ROTATION_OPTIONS = (
    'none - No Rotation',
    'z - Standard Spin',
    'x - Horizontal Flip',
    'y - Vertical Tilt'
)

RING_ROTATION_OPTIONS = (
    'none - No Rotation',
    'z - No Rotation',
    'x - Horizontal Squeeze',
    'y - Vertical Squeeze'
)

STARFIELD_ROTATION_OPTIONS = (
    'none - Outward Only',
    'cw - Clockwise Spiral',
    'ccw - Counter-Clockwise'
)

# Resolution presets
RESOLUTION_OPTIONS = (
    '1280x720 - HD',
    '1920x1080 - Full HD',
    '1080x1920 - Phone Vertical',
    '1920x1080 - Phone Horizontal'
)

# FPS options
FPS_OPTIONS = ('15', '30', '60')

# File dialog filters
AUDIO_FILETYPES = [
    ("Audio files", "*.mp3 *.wav *.m4a *.flac *.ogg"),
    ("All files", "*.*")
]

IMAGE_FILETYPES = [
    ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"),
    ("All files", "*.*")
]

VIDEO_FILETYPES = [
    ("MP4 Video", "*.mp4"),
    ("All files", "*.*")
]

# Preview settings
PREVIEW_FPS = 15
PREVIEW_RESOLUTION_DIVISOR = 2

# Default values
DEFAULT_PALETTE = "rainbow"
DEFAULT_COVER_SHAPE = "square"
DEFAULT_COVER_SIZE = 1.0
DEFAULT_WAVEFORM_ROTATION = "z"
DEFAULT_RING_ROTATION = "z"
DEFAULT_RING_SHAPE = "circle"
DEFAULT_STARFIELD_ROTATION = "none"
DEFAULT_RESOLUTION = "1280x720"
DEFAULT_FPS = 30

# Cover size slider
COVER_SIZE_MIN = 0.5
COVER_SIZE_MAX = 2.0

# UI Messages
MSG_NO_FILE_SELECTED = "No file selected"
MSG_NO_COVER_SELECTED = "No cover selected"
MSG_SELECT_AUDIO_FIRST = "Select an audio file to begin"
MSG_GENERATING_PREVIEW = "Generating preview..."
MSG_PREVIEW_UPDATED = "Preview updated - Ready to render"
MSG_RENDERING = "Rendering full video... Please wait"
MSG_STARTING_RENDER = "Starting render..."
MSG_ADDING_AUDIO = "Adding audio to video..."
MSG_RENDER_COMPLETE = "Render complete!"
MSG_RENDER_CANCELLED = "Render cancelled"
MSG_RENDER_FAILED = "Render failed"
MSG_CANCELLING = "Cancelling..."