# Psychedelic Music Visualizer

A powerful Python-based music visualizer that creates stunning audio-reactive videos with rotating waveforms, beat-reactive effects, and customizable visual styles.

![Features](https://img.shields.io/badge/features-8_frequency_bands-brightgreen) ![Python](https://img.shields.io/badge/python-3.8+-blue) ![License](https://img.shields.io/badge/license-MIT-orange)

## Features

- 🎵 **8 Frequency Bands** - Custom frequency ranges with exponential sensitivity for higher frequencies
- 🌈 **Multiple Color Palettes** - Rainbow, Spring, Summer, Autumn, and Winter themes
- ⭐ **Volume-Reactive Starfield** - Stars move faster during louder sections
- 🔄 **3D Rotation Effects** - Rotate waveforms and rings on X, Y, or Z axes
- 💫 **Beat Detection** - Rings expand dramatically on beats and transients
- 👻 **Afterimage Trails** - Smooth motion trails create flowing, psychedelic effects
- 🖼️ **Cover Art Support** - Optional kaleidoscope effect with album artwork
- 📱 **Phone Resolutions** - Presets for vertical and horizontal phone videos
- 🎬 **Fade to Black** - Professional ending with 2-second fade out
- 📝 **Text Overlay** - Music-reactive text fading with volume

## Demo

Create visualizations like this:

```bash
python visualizer.py song.mp3 -c cover.jpg -t "Artist - Song Title" -p autumn
```

## Installation

### Prerequisites

- Python 3.8 or higher
- FFmpeg (for audio processing)

### Install FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

### Install Python Dependencies

```bash
pip install numpy scipy opencv-python pillow tqdm
```

Or use the requirements file:

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
numpy>=1.20.0
scipy>=1.7.0
opencv-python>=4.5.0
pillow>=9.0.0
tqdm>=4.60.0
```

## Usage

### Basic Usage

```bash
# Simplest form - just audio
python visualizer.py song.mp3

# With cover image
python visualizer.py song.mp3 -c cover.jpg

# With cover and text
python visualizer.py song.mp3 -c cover.jpg -t "Song Title"
```

### Color Palettes

```bash
# Use a seasonal palette
python visualizer.py song.mp3 -p autumn
python visualizer.py song.mp3 -p winter
python visualizer.py song.mp3 -p spring
python visualizer.py song.mp3 -p summer

# Default rainbow
python visualizer.py song.mp3 -p rainbow
```

### Resolution Options

```bash
# Vertical phone video (Instagram Stories, TikTok, Reels)
python visualizer.py song.mp3 --phone-vertical

# Horizontal phone video
python visualizer.py song.mp3 --phone-horizontal

# Custom resolution
python visualizer.py song.mp3 --resolution 1920x1080

# 4K resolution
python visualizer.py song.mp3 --resolution 3840x2160
```

### Rotation Effects

```bash
# 3D waveform flip effect
python visualizer.py song.mp3 --waveform-rotation x

# Waveform tilt effect
python visualizer.py song.mp3 --waveform-rotation y

# Breathing rings (horizontal squeeze)
python visualizer.py song.mp3 --ring-rotation x

# Breathing rings (vertical squeeze)
python visualizer.py song.mp3 --ring-rotation y

# Spiral starfield (clockwise)
python visualizer.py song.mp3 --starfield-rotation cw

# Spiral starfield (counter-clockwise)
python visualizer.py song.mp3 --starfield-rotation ccw
```

### Advanced Examples

```bash
# Full social media ready video
python visualizer.py song.mp3 \
  -c cover.jpg \
  -t "Artist - Song Title" \
  -p summer \
  --phone-vertical \
  --fps 60 \
  -o instagram.mp4

# Psychedelic 3D effect
python visualizer.py song.mp3 \
  --waveform-rotation x \
  --ring-rotation y \
  --starfield-rotation cw \
  -p rainbow

# Minimal aesthetic (no cover)
python visualizer.py song.mp3 \
  -p winter \
  --ring-rotation z \
  --fps 30

# Maximum quality 4K render
python visualizer.py song.mp3 \
  -c cover.jpg \
  -t "Song Name" \
  --resolution 3840x2160 \
  --fps 60 \
  -p autumn \
  -o output_4k.mp4
```

## Command Line Options

### Required Arguments

- `audio` - Path to audio file (mp3, wav, etc.)

### Optional Arguments

| Option | Description | Default |
|--------|-------------|---------|
| `-o`, `--output` | Output video path | `visualization.mp4` |
| `-c`, `--cover` | Path to cover image | None |
| `-t`, `--text` | Text overlay below cover | None |
| `-p`, `--palette` | Color palette (rainbow/spring/summer/autumn/winter) | `rainbow` |
| `--fps` | Frames per second | `30` |
| `--resolution` | Custom resolution (WIDTHxHEIGHT) | `1280x720` |
| `--phone-vertical` | Use 1080x1920 resolution | Off |
| `--phone-horizontal` | Use 1920x1080 resolution | Off |
| `--waveform-rotation` | Waveform rotation axis (x/y/z) | `z` |
| `--ring-rotation` | Ring rotation axis (x/y/z) | `z` |
| `--starfield-rotation` | Starfield rotation (none/cw/ccw) | `none` |

## How It Works

### Audio Processing

1. Audio is loaded and converted to mono WAV format
2. STFT (Short-Time Fourier Transform) analyzes frequency content
3. Audio is split into 8 frequency bands:
   - 20-40 Hz (Sub-Bass)
   - 40-80 Hz (Bass)
   - 80-100 Hz (Low-Bass)
   - 100-200 Hz (Low-Mid)
   - 200-400 Hz (Mid)
   - 400-600 Hz (Upper-Mid)
   - 600-800 Hz (High-Mid)
   - 800-1000 Hz (Presence)

### Visual Layers (Bottom to Top)

1. **Starfield** - 200 white stars moving outward from center
2. **Waveforms** - 8 colored waveforms with trails and glow
3. **Cover/Rings** - Kaleidoscope cover art and beat-reactive rings
4. **Text** - White text that fades with volume

### Beat Detection

The visualizer detects beats by analyzing sudden increases in bass/low-mid energy. When a beat is detected:
- Center rings expand dramatically
- Text brightness increases
- Ring glow intensifies

## Adding Custom Color Palettes

Edit the `self.palettes` dictionary in the code:

```python
'your_palette_name': {
    'name': 'Display Name',
    'colors': [0, 45, 90, 135, 180, 225, 270, 315],  # 8 hue values (0-360)
    'saturation': 1.0,  # 0.0 to 1.0
    'brightness': 1.0   # 0.0 to 1.0
}
```

Then use it with:
```bash
python visualizer.py song.mp3 -p your_palette_name
```

## Performance Tips

- **Lower resolution** renders faster: `--resolution 854x480`
- **30 fps** is sufficient for most uses; 60 fps doubles render time
- **Shorter videos** render proportionally faster
- **Close other applications** to free up memory
- Rendering is CPU-intensive and can take several minutes for a 3-minute song at 1080p

### Approximate Render Times (3-minute song, 1080p, 30fps)

- Modern laptop (M1/M2): ~5-8 minutes
- Desktop (i7/Ryzen 7): ~8-12 minutes
- Older laptop: ~15-20 minutes

## Troubleshooting

### "FFmpeg not found"
Install FFmpeg as described in the Installation section.

### "Error loading file"
Ensure your audio file is a valid MP3 or WAV file.

### "Black video output"
This was a bug in earlier versions. Make sure you're using the latest version of the code.

### Video has no audio
The script automatically merges audio with the rendered video. If audio is missing, check that FFmpeg is properly installed.

### Out of memory
Try reducing resolution or fps, or close other applications.

## Examples Output

### Rainbow Palette
- Full spectrum colors
- High energy, festival vibe
- Works well with electronic music

### Autumn Palette
- Warm reds, oranges, golds
- Cozy, intimate feel
- Great for acoustic, folk, indie

### Winter Palette
- Cool blues and cyans
- Calm, ethereal atmosphere
- Perfect for ambient, chill music

### Spring Palette
- Fresh greens, blues, pinks
- Bright and lively
- Ideal for upbeat, happy songs

### Summer Palette
- Bright oranges, yellows, blues
- Vibrant and energetic
- Best for pop, dance music

## Credits

Created with Python, NumPy, SciPy, OpenCV, and PIL.

## License

MIT License - Feel free to use and modify for your projects!

## Support

For issues or questions, check that:
1. All dependencies are installed
2. FFmpeg is accessible from command line
3. Audio file is valid
4. You have enough disk space for output

Run `python visualizer.py --help` for detailed usage information.