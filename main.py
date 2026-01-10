#!/usr/bin/env python3
"""
Psychedelic Music Visualizer - Command Line Interface
Main entry point for the application
"""

import argparse
from visualizer import MusicVisualizer


def main():
    parser = argparse.ArgumentParser(
        description='Generate psychedelic music visualization with rotating waveforms, starfield, and reactive effects',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Basic usage:
    python main.py song.mp3
  
  With cover image and text:
    python main.py song.mp3 -c cover.jpg -t "Song Title"
  
  Autumn palette at 60fps:
    python main.py song.mp3 -p autumn --fps 60
  
  Quick 30-second preview (10-15x faster):
    python main.py song.mp3 --preview 30 -c cover.jpg -t "Test"

Color Palettes:
  rainbow, spring, summer, autumn, winter, ice, fire, water, earth

Rotation Options:
  Waveform: none, z (2D spin), x (horizontal flip), y (vertical tilt)
  Ring: none, z, x (horizontal squeeze), y (vertical squeeze)
  Starfield: none (outward only), cw (clockwise), ccw (counter-clockwise)
        """)
    
    parser.add_argument('audio', help='Path to audio file (mp3, wav, etc.)')
    
    parser.add_argument('-o', '--output', default='visualization.mp4', 
                       help='Output video path (default: visualization.mp4)')
    
    parser.add_argument('-c', '--cover', 
                       help='Path to cover image (optional)')
    
    parser.add_argument('-t', '--text', 
                       help='Text overlay to display below cover (optional)')
    
    parser.add_argument('-p', '--palette', default='rainbow',
                       choices=['rainbow', 'spring', 'summer', 'autumn', 'winter',
                                'ice', 'fire', 'water', 'earth'],
                       help='Color palette for waveforms (default: rainbow)')
    
    parser.add_argument('--fps', type=int, default=30, 
                       help='Frames per second (default: 30)')
    
    parser.add_argument('--resolution', 
                       help='Custom resolution as WIDTHxHEIGHT (e.g., 1920x1080)')
    
    parser.add_argument('--phone-vertical', action='store_true',
                       help='Use phone vertical resolution (1080x1920)')
    
    parser.add_argument('--phone-horizontal', action='store_true',
                       help='Use phone horizontal resolution (1920x1080)')
    
    parser.add_argument('--waveform-rotation', default='z',
                       choices=['none', 'x', 'y', 'z'],
                       help='Waveform rotation axis (default: z)')
    
    parser.add_argument('--ring-rotation', default='z',
                       choices=['none', 'x', 'y', 'z'],
                       help='Ring rotation axis (default: z)')
    
    parser.add_argument('--ring-shape', default='circle',
                       choices=['circle', 'square'],
                       help='Ring shape (default: circle)')
    
    parser.add_argument('--starfield-rotation', default='none',
                       choices=['none', 'cw', 'ccw'],
                       help='Starfield rotation (default: none)')
    
    parser.add_argument('--preview', type=int, metavar='SECONDS',
                       help='Preview mode: render only first N seconds')
    
    parser.add_argument('--cover-shape', default='square',
                       choices=['square', 'round'],
                       help='Cover art shape (default: square)')
    
    parser.add_argument('--cover-size', type=float, default=1.0,
                       help='Cover art size multiplier (default: 1.0)')
    
    parser.add_argument('--disable-rings', action='store_true',
                       help='Disable rings around cover art')
    
    parser.add_argument('--disable-starfield', action='store_true',
                       help='Disable starfield background')
    
    args = parser.parse_args()
    
    # Determine resolution
    if args.phone_vertical:
        width, height = 1080, 1920
    elif args.phone_horizontal:
        width, height = 1920, 1080
    elif args.resolution:
        width, height = map(int, args.resolution.split('x'))
    else:
        width, height = 1280, 720
    
    # Apply preview mode optimizations
    preview_fps = args.fps
    if args.preview:
        width = width // 2
        height = height // 2
        if args.fps == 30:
            preview_fps = 15
        print(f"⚡ PREVIEW MODE:")
        print(f"   Duration: First {args.preview} seconds")
        print(f"   Resolution: {width}x{height} (half)")
        print(f"   FPS: {preview_fps}")
        print(f"   Expected speedup: ~10-15x faster\n")
    
    print(f"Configuration:")
    print(f"  Audio: {args.audio}")
    print(f"  Resolution: {width}x{height}")
    print(f"  FPS: {preview_fps}")
    print(f"  Palette: {args.palette}")
    print(f"  Waveform Rotation: {args.waveform_rotation}")
    print(f"  Ring Rotation: {args.ring_rotation}")
    print(f"  Ring Shape: {args.ring_shape}")
    print(f"  Starfield Rotation: {args.starfield_rotation}")
    if args.preview:
        print(f"  Preview: {args.preview} seconds")
    if args.cover:
        print(f"  Cover: {args.cover} ({args.cover_shape}, {args.cover_size}x)")
    if args.disable_rings:
        print(f"  Rings: Disabled")
    if args.disable_starfield:
        print(f"  Starfield: Disabled")
    if args.text:
        print(f"  Text: {args.text}")
    print(f"  Output: {args.output}\n")
    
    # Create and render
    visualizer = MusicVisualizer(
        audio_path=args.audio,
        output_path=args.output,
        cover_image_path=args.cover,
        fps=preview_fps,
        resolution=(width, height),
        text_overlay=args.text,
        color_palette=args.palette,
        waveform_rotation=args.waveform_rotation,
        ring_rotation=args.ring_rotation,
        starfield_rotation=args.starfield_rotation,
        preview_seconds=args.preview,
        cover_shape=args.cover_shape,
        cover_size=args.cover_size,
        disable_rings=args.disable_rings,
        disable_starfield=args.disable_starfield,
        ring_shape=args.ring_shape
    )
    
    visualizer.render()


if __name__ == '__main__':
    main()