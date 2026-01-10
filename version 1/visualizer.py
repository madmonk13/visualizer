#!/usr/bin/env python3
"""
Psychedelic Music Visualizer
Renders audio-reactive video with 4 frequency bands and rotating kaleidoscope effects
Uses scipy instead of librosa to avoid dependency issues
"""

import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter
import argparse
from tqdm import tqdm
import math
from scipy.io import wavfile
from scipy import signal
import subprocess
import os
import tempfile

class MusicVisualizer:
    def __init__(self, audio_path, output_path='output.mp4', cover_image_path=None, 
                 fps=30, resolution=(1280, 720), text_overlay=None, color_palette='rainbow',
                 waveform_rotation='z', ring_rotation='z', starfield_rotation='none', 
                 preview_seconds=None, cover_shape='square', cover_size=1.0, 
                 disable_rings=False, disable_starfield=False, ring_shape='circle'):
        self.audio_path = audio_path
        self.output_path = output_path
        self.cover_image_path = cover_image_path
        self.fps = fps
        self.width, self.height = resolution
        self.text_overlay = text_overlay
        self.color_palette = color_palette
        self.waveform_rotation = waveform_rotation
        self.ring_rotation = ring_rotation
        self.starfield_rotation = starfield_rotation
        self.preview_seconds = preview_seconds
        self.is_preview = preview_seconds is not None
        self.cover_shape = cover_shape
        self.cover_size = cover_size
        self.disable_rings = disable_rings
        self.disable_starfield = disable_starfield
        self.ring_shape = ring_shape
        
        # Convert audio to WAV if needed
        print("Loading audio...")
        wav_path = self._convert_to_wav(audio_path)
        
        # Load audio
        self.sr, audio_data = wavfile.read(wav_path)
        
        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1)
        
        # Normalize
        self.y = audio_data.astype(np.float32) / np.max(np.abs(audio_data))
        self.duration = len(self.y) / self.sr
        
        # Clean up temporary WAV
        if wav_path != audio_path:
            os.remove(wav_path)
        
        # Frequency bands (Hz) - custom spacing
        self.bands = [
            {'name': 'Sub-Bass', 'min': 20, 'max': 40, 'hue_offset': 0},
            {'name': 'Bass', 'min': 40, 'max': 80, 'hue_offset': 45},
            {'name': 'Low-Bass', 'min': 80, 'max': 100, 'hue_offset': 90},
            {'name': 'Low-Mid', 'min': 100, 'max': 200, 'hue_offset': 135},
            {'name': 'Mid', 'min': 200, 'max': 400, 'hue_offset': 180},
            {'name': 'Upper-Mid', 'min': 400, 'max': 600, 'hue_offset': 225},
            {'name': 'High-Mid', 'min': 600, 'max': 800, 'hue_offset': 270},
            {'name': 'Presence', 'min': 800, 'max': 1000, 'hue_offset': 315}
        ]
        
        # Color palettes - easy to add more!
        self.palettes = {
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
        
        # Apply color palette to bands
        if self.color_palette in self.palettes:
            palette = self.palettes[self.color_palette]
            for i, band in enumerate(self.bands):
                band['hue_offset'] = palette['colors'][i % len(palette['colors'])]
                band['saturation'] = palette['saturation']
                band['brightness'] = palette['brightness']
        else:
            # Default rainbow if palette not found
            print(f"Warning: Palette '{self.color_palette}' not found, using rainbow")
            for band in self.bands:
                band['saturation'] = 1.0
                band['brightness'] = 1.0
        
        # Animation state
        self.rotation = 0
        self.cover_rotation = 0
        self.hue_offset = 0
        
        # Beat detection
        self.prev_energy = 0
        self.beat_intensity = 0
        
        # Text fade tracking
        self.text_fade_history = []
        
        # Trail buffer for afterimage effect
        self.trail_buffer = None
        
        # Starfield
        self.stars = []
        self.init_starfield()
        
        # Trail buffer for psychedelic effect
        self.trail_buffer = None
        
        # Load cover image if provided
        self.cover_image = None
        if cover_image_path:
            try:
                self.cover_image = Image.open(cover_image_path).convert('RGB')
                print(f"Loaded cover image: {cover_image_path}")
            except Exception as e:
                print(f"Could not load cover image: {e}")
        
        # Calculate STFT for the entire audio
        print("Analyzing audio frequencies...")
        hop_length = self.sr // self.fps
        
        # Use smaller FFT in preview mode for speed
        if self.is_preview:
            nperseg = 1024
        else:
            nperseg = 2048
        
        self.frequencies, self.times, self.stft = signal.stft(
            self.y, 
            fs=self.sr, 
            nperseg=nperseg, 
            noverlap=nperseg - hop_length
        )
        self.magnitude = np.abs(self.stft)
        
        print(f"Audio loaded: {self.duration:.2f}s at {self.sr}Hz")
        
    def _convert_to_wav(self, audio_path):
        """Convert audio file to WAV using ffmpeg if needed"""
        if audio_path.lower().endswith('.wav'):
            return audio_path
        
        wav_path = audio_path.rsplit('.', 1)[0] + '_temp.wav'
        
        try:
            subprocess.run([
                'ffmpeg', '-i', audio_path, '-ar', '44100', '-ac', '1', 
                '-y', wav_path
            ], check=True, capture_output=True)
            return wav_path
        except subprocess.CalledProcessError:
            raise Exception("FFmpeg is required to process MP3 files. Install with: brew install ffmpeg")
        except FileNotFoundError:
            raise Exception("FFmpeg not found. Install with: brew install ffmpeg")
    
    def hsv_to_rgb(self, h, s, v):
        """Convert HSV to RGB (0-255 range) with enhanced vibrancy"""
        h = h % 360
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c
        
        if h < 60:
            r, g, b = c, x, 0
        elif h < 120:
            r, g, b = x, c, 0
        elif h < 180:
            r, g, b = 0, c, x
        elif h < 240:
            r, g, b = 0, x, c
        elif h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        
        # Boost saturation and brightness for more vibrant colors
        r = int(min(255, (r + m) * 255 * 1.2))
        g = int(min(255, (g + m) * 255 * 1.2))
        b = int(min(255, (b + m) * 255 * 1.2))
        
        return (r, g, b)
    
    def get_band_values(self, frame_idx):
        """Extract frequency band values for a specific frame"""
        if frame_idx >= self.magnitude.shape[1]:
            frame_idx = self.magnitude.shape[1] - 1
        
        frame_data = self.magnitude[:, frame_idx]
        band_values = []
        
        for band in self.bands:
            # Find frequency indices for this band
            mask = (self.frequencies >= band['min']) & (self.frequencies <= band['max'])
            band_data = frame_data[mask]
            
            if len(band_data) > 0:
                avg_value = np.mean(band_data)
                band_values.append(avg_value)
            else:
                band_values.append(0)
        
        return band_values
    
    def detect_beat(self, frame_idx):
        """Detect transient changes (beats) in the audio"""
        if frame_idx >= self.magnitude.shape[1]:
            frame_idx = self.magnitude.shape[1] - 1
        
        # Calculate energy in bass/low-mid range (where beats are strongest)
        frame_data = self.magnitude[:, frame_idx]
        bass_mask = (self.frequencies >= 20) & (self.frequencies <= 250)
        low_mid_mask = (self.frequencies >= 250) & (self.frequencies <= 1000)
        
        bass_energy = np.sum(frame_data[bass_mask])
        low_mid_energy = np.sum(frame_data[low_mid_mask])
        total_energy = bass_energy + low_mid_energy
        
        # Detect sudden increase in energy (beat)
        energy_change = total_energy - self.prev_energy
        
        # Threshold for beat detection - normalized by max magnitude
        max_energy = np.sum(self.magnitude[:, :]) / self.magnitude.shape[1]
        threshold = max_energy * 0.3
        
        if energy_change > threshold:
            self.beat_intensity = min(1.0, energy_change / (threshold * 2))
        else:
            self.beat_intensity *= 0.7  # Decay
        
        self.prev_energy = total_energy
        
        return self.beat_intensity
    
    def _get_x_rotation_matrix(self, angle):
        """Calculate perspective transform matrix for X-axis rotation"""
        # Simplified 3D rotation around X-axis projected to 2D
        distortion = 0.3 * math.sin(angle * 2)
        return (
            1, 0, 0,
            distortion, 1, -self.height * distortion / 2,
            0, 0
        )
    
    def _get_y_rotation_matrix(self, angle):
        """Calculate perspective transform matrix for Y-axis rotation"""
        # Simplified 3D rotation around Y-axis projected to 2D
        distortion = 0.3 * math.sin(angle * 2)
        return (
            1, distortion, -self.width * distortion / 2,
            0, 1, 0,
            0, 0
        )
    
    def init_starfield(self):
        """Initialize starfield particles"""
        # Fewer stars in preview mode
        num_stars = 100 if self.is_preview else 200
        for _ in range(num_stars):
            self.stars.append({
                'x': np.random.rand() * self.width,
                'y': np.random.rand() * self.height,
                'z': np.random.rand() * 2,  # Depth
                'size': np.random.randint(1, 4)
            })
    
    def update_starfield(self, volume_intensity):
        """Update starfield positions based on volume and rotation settings"""
        # Base speed varies dramatically with volume (0.5 to 6)
        speed = 0.5 + volume_intensity * 5.5
        
        center_x, center_y = self.width / 2, self.height / 2
        
        for star in self.stars:
            # Apply rotation if enabled
            if self.starfield_rotation == 'cw':
                # Clockwise rotation
                angle = math.atan2(star['y'] - center_y, star['x'] - center_x)
                angle -= speed * 0.01 * star['z']
                distance = math.sqrt((star['x'] - center_x)**2 + (star['y'] - center_y)**2)
                star['x'] = center_x + distance * math.cos(angle)
                star['y'] = center_y + distance * math.sin(angle)
            elif self.starfield_rotation == 'ccw':
                # Counter-clockwise rotation
                angle = math.atan2(star['y'] - center_y, star['x'] - center_x)
                angle += speed * 0.01 * star['z']
                distance = math.sqrt((star['x'] - center_x)**2 + (star['y'] - center_y)**2)
                star['x'] = center_x + distance * math.cos(angle)
                star['y'] = center_y + distance * math.sin(angle)
            
            # Move stars outward from center (always happens regardless of rotation)
            dx = star['x'] - center_x
            dy = star['y'] - center_y
            
            # Normalize and scale by speed and depth
            distance = math.sqrt(dx*dx + dy*dy)
            if distance > 0:
                star['x'] += (dx / distance) * speed * star['z']
                star['y'] += (dy / distance) * speed * star['z']
            
            # Wrap around edges - reset to center
            if (star['x'] < 0 or star['x'] > self.width or 
                star['y'] < 0 or star['y'] > self.height):
                star['x'] = center_x + np.random.randn() * 50
                star['y'] = center_y + np.random.randn() * 50
                star['z'] = np.random.rand() * 2
    
    def draw_starfield(self, img, volume_intensity):
        """Draw the starfield with white stars"""
        star_layer = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(star_layer)
        
        for star in self.stars:
            # White stars with brightness varying by depth
            brightness = int(150 + star['z'] * 50)
            star_color = (255, 255, 255)  # Pure white
            
            x, y = int(star['x']), int(star['y'])
            size = star['size']
            
            # Draw star with glow
            for glow in range(3, 0, -1):
                glow_alpha = int(brightness * 0.3 * (1 - glow / 3))
                draw.ellipse([x - size - glow, y - size - glow, 
                             x + size + glow, y + size + glow],
                            fill=(*star_color, glow_alpha))
            
            # Draw core
            draw.ellipse([x - size, y - size, x + size, y + size],
                        fill=(*star_color, brightness))
        
        # Composite stars onto image
        img.paste(star_layer, (0, 0), star_layer)
    
    def get_band_waveform(self, frame_idx, band_idx, points=150):
        """Get waveform data for a specific frequency band"""
        if frame_idx >= self.magnitude.shape[1]:
            frame_idx = self.magnitude.shape[1] - 1
        
        band = self.bands[band_idx]
        frame_data = self.magnitude[:, frame_idx]
        
        # Find frequency indices for this band
        mask = (self.frequencies >= band['min']) & (self.frequencies <= band['max'])
        band_data = frame_data[mask]
        
        if len(band_data) == 0:
            return np.zeros(points)
        
        # Resample to desired number of points
        indices = np.linspace(0, len(band_data) - 1, points).astype(int)
        waveform = band_data[indices]
        
        # Normalize to 0-1 range
        max_val = np.max(self.magnitude) if np.max(self.magnitude) > 0 else 1
        waveform = waveform / max_val
        
        return waveform

### END OF PART 1 - Continue with part 2 ###

### PART 2 - Continue from part 1 ###
    
    def draw_waveforms_with_glow(self, img, frame_idx):
        """Draw the frequency band waveforms with glow effects"""
        band_height = self.height // len(self.bands)
        
        # Create a layer for waveforms - RGB not RGBA so no transparency issues
        waveform_layer = Image.new('RGB', (self.width, self.height), (0, 0, 0))
        waveform_draw = ImageDraw.Draw(waveform_layer)
        
        # Fewer points in preview mode
        waveform_points = 100 if self.is_preview else 150
        
        for band_idx, band in enumerate(self.bands):
            waveform = self.get_band_waveform(frame_idx, band_idx, points=waveform_points)
            center_y = (band_idx + 0.5) * band_height
            
            base_hue = (self.hue_offset + band['hue_offset']) % 360
            
            # Calculate sensitivity multiplier - higher frequencies get more sensitivity
            # Ranges from 1.0 for lowest band to 3.0 for highest band
            sensitivity = 1.0 + (band_idx / (len(self.bands) - 1)) * 2.0
            
            # Draw two layers with mirroring for psychedelic effect
            for layer in range(2):
                layer_hue = (base_hue + layer * 40) % 360
                
                # Use palette saturation and brightness
                sat = band.get('saturation', 1.0)
                bright = band.get('brightness', 1.0)
                color = self.hsv_to_rgb(layer_hue, sat, bright)
                
                phase_offset = layer * 0.3
                
                # Create waveform points with increased amplitude range
                points_upper = []
                points_lower = []
                
                for i, value in enumerate(waveform):
                    x = int((i / len(waveform)) * self.width)
                    t = i / len(waveform)
                    
                    # Apply sensitivity multiplier to amplitude
                    amplitude = value * (band_height * 0.65) * sensitivity
                    wave1 = math.sin((t * math.pi * 4) + phase_offset) * amplitude
                    wave2 = math.sin((t * math.pi * 8) + (phase_offset * 2)) * (amplitude * 0.3)
                    wave3 = math.cos((t * math.pi * 2) + (self.hue_offset * 0.02)) * (amplitude * 0.2)
                    
                    y_upper = int(center_y + wave1 + wave2 + wave3)
                    y_lower = int(center_y - (wave1 + wave2 + wave3))
                    
                    points_upper.append((x, y_upper))
                    points_lower.append((x, y_lower))
                
                # Draw gradient-filled area between waveforms first
                if layer == 0 and len(points_upper) > 1:
                    fill_points = points_upper + points_lower[::-1]
                    # Bright vibrant fill
                    waveform_draw.polygon(fill_points, fill=color)
                
                # Draw glow halo
                if len(points_upper) > 1:
                    # Fewer glow layers in preview mode
                    glow_layers = 6 if self.is_preview else 12
                    
                    for thickness in range(glow_layers, 0, -1):
                        # Calculate glow color that fades to black
                        glow_intensity = (1 - thickness / glow_layers) * 0.5
                        glow_r = int(color[0] * glow_intensity)
                        glow_g = int(color[1] * glow_intensity)
                        glow_b = int(color[2] * glow_intensity)
                        glow_color = (glow_r, glow_g, glow_b)
                        
                        waveform_draw.line(points_upper, fill=glow_color, width=thickness + 8)
                        waveform_draw.line(points_lower, fill=glow_color, width=thickness + 8)
                    
                    # Draw main solid bright lines on top
                    waveform_draw.line(points_upper, fill=color, width=6 - layer)
                    waveform_draw.line(points_lower, fill=color, width=6 - layer)
                
                # Draw particles on peaks
                for i in range(0, len(waveform), 15):
                    if waveform[i] > 0.7:
                        x = int((i / len(waveform)) * self.width)
                        particle_hue = (base_hue + i * 2) % 360
                        particle_color = self.hsv_to_rgb(particle_hue, 1.0, 1.0)
                        
                        # Draw particle glow
                        for radius in range(10, 2, -1):
                            glow_intensity = (1 - radius / 10) * 0.5
                            glow_r = int(particle_color[0] * glow_intensity)
                            glow_g = int(particle_color[1] * glow_intensity)
                            glow_b = int(particle_color[2] * glow_intensity)
                            waveform_draw.ellipse(
                                [x-radius, center_y-radius, x+radius, center_y+radius],
                                fill=(glow_r, glow_g, glow_b)
                            )
                        
                        # Draw bright center
                        waveform_draw.ellipse(
                            [x-3, center_y-3, x+3, center_y+3],
                            fill=particle_color
                        )
        
        # Apply slight blur for glow effect but keep waveforms visible
        blur_radius = 1 if self.is_preview else 2
        waveform_layer = waveform_layer.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        
        # Paste waveforms onto the main image
        img.paste(waveform_layer, (0, 0), None)
    
    def draw_cover_kaleidoscope(self, img, frame_idx, volume_intensity, beat_intensity):
        """Draw the stationary kaleidoscope cover art with psychedelic effects"""
        center_x, center_y = self.width // 2, self.height // 2
        base_size = int(min(self.width, self.height) * 0.525 * self.cover_size)  # Apply size multiplier
        
        if self.cover_image:
            # Get band values for fragment animation
            band_values = self.get_band_values(frame_idx)
            max_band = max(band_values) if band_values else 0
            normalized_bands = [v / max_band if max_band > 0 else 0 for v in band_values]
            
            if self.cover_shape == 'square':
                # Square cover - no kaleidoscope fragments
                cover_width = int(base_size * 1.2)
                cover_height = int(base_size * 1.2)
                
                # Resize cover to fit
                cover_resized = self.cover_image.resize((cover_width, cover_height))
                
                # Paste directly onto image
                img.paste(cover_resized, (center_x - cover_width // 2, center_y - cover_height // 2))
                
            else:  # round
                # Create circular mask for round cover
                center_size = int(base_size * 0.6 * (1 + volume_intensity * 0.3 + beat_intensity * 0.5))
                center_cover = self.cover_image.resize((center_size * 2, center_size * 2))
                
                mask = Image.new('L', (center_size * 2, center_size * 2), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse([0, 0, center_size * 2, center_size * 2], fill=255)
                
                img.paste(center_cover, (center_x - center_size, center_y - center_size), mask)
        
        # Draw glowing rings (unless disabled)
        if not self.disable_rings:
            ring_layer = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
            
            # Apply rotation to ring layer if specified
            if self.ring_rotation != 'z':
                ring_canvas = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
                ring_draw = ImageDraw.Draw(ring_canvas)
            else:
                ring_draw = ImageDraw.Draw(ring_layer)
            
            for r in range(3):
                # Size variation based on beat and volume
                base_ring_size = base_size * (0.4 + r * 0.2)
                beat_expansion = beat_intensity * 80
                volume_expansion = volume_intensity * 0.5 * base_ring_size
                ring_size = int(base_ring_size + beat_expansion + volume_expansion)
                
                ring_hue = (self.hue_offset + r * 60) % 360
                
                # Use palette settings if available
                if self.bands:
                    sat = self.bands[0].get('saturation', 1.0)
                    bright = self.bands[0].get('brightness', 0.9)
                else:
                    sat = 1.0
                    bright = 0.9
                
                ring_color = self.hsv_to_rgb(ring_hue, sat, bright)
                line_width = int(3 + volume_intensity * 4 + beat_intensity * 6)
                
                # Apply perspective distortion for X/Y rotation
                if self.ring_rotation == 'none':
                    # No rotation/distortion
                    shape_width = ring_size
                    shape_height = ring_size
                elif self.ring_rotation == 'x':
                    distortion = 0.6 + 0.4 * math.cos(self.rotation * 2)
                    shape_height = int(ring_size * distortion)
                    shape_width = ring_size
                elif self.ring_rotation == 'y':
                    distortion = 0.6 + 0.4 * math.cos(self.rotation * 2)
                    shape_width = int(ring_size * distortion)
                    shape_height = ring_size
                else:  # 'z' - no distortion, just pulsing
                    shape_width = ring_size
                    shape_height = ring_size
                
                # Draw glow based on shape
                for glow in range(8, 0, -1):
                    alpha = int((200 + beat_intensity * 55) * (1 - glow / 8))
                    glow_color = (*ring_color, alpha)
                    
                    if self.ring_shape == 'square':
                        # Square glow
                        ring_draw.rectangle(
                            [center_x - shape_width - glow*2, center_y - shape_height - glow*2,
                             center_x + shape_width + glow*2, center_y + shape_height + glow*2],
                            outline=glow_color, width=line_width + glow
                        )
                    else:
                        # Circle glow
                        ring_draw.ellipse(
                            [center_x - shape_width - glow*2, center_y - shape_height - glow*2,
                             center_x + shape_width + glow*2, center_y + shape_height + glow*2],
                            outline=glow_color, width=line_width + glow
                        )
                
                # Main ring/square
                if self.ring_shape == 'square':
                    ring_draw.rectangle(
                        [center_x - shape_width, center_y - shape_height,
                         center_x + shape_width, center_y + shape_height],
                        outline=(*ring_color, 255), width=line_width
                    )
                else:
                    ring_draw.ellipse(
                        [center_x - shape_width, center_y - shape_height,
                         center_x + shape_width, center_y + shape_height],
                        outline=(*ring_color, 255), width=line_width
                    )
            
            if self.ring_rotation != 'z':
                ring_layer = ring_canvas
            
            img.paste(ring_layer, (0, 0), ring_layer)
    
    def draw_text_overlay(self, img, beat_intensity, volume_intensity):
        """Draw white text below the cover image with music-reactive fading"""
        if not self.text_overlay:
            return
        
        # Add current volume to history
        self.text_fade_history.append(volume_intensity)
        
        # Keep only last 60 frames (2 seconds at 30fps)
        if len(self.text_fade_history) > 60:
            self.text_fade_history.pop(0)
        
        # Calculate fade based on average recent volume
        avg_recent_volume = np.mean(self.text_fade_history) if self.text_fade_history else 0
        
        # Map volume to fade: 0.3-1.0 opacity range
        # Lower volumes = more transparent, higher = more opaque
        base_alpha = 0.3 + (avg_recent_volume * 0.7)
        
        # Add beat boost for extra pop
        beat_boost = beat_intensity * 0.2
        alpha = min(1.0, base_alpha + beat_boost)
        
        # Create text layer
        text_layer = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_layer)
        
        # Try to load a nice sans-serif font
        try:
            from PIL import ImageFont
            font_size = int(self.height * 0.08)
            for font_name in ['Helvetica', 'Arial', 'DejaVuSans', 'FreeSans']:
                try:
                    font = ImageFont.truetype(font_name, font_size)
                    break
                except:
                    continue
            else:
                font = ImageFont.load_default()
        except:
            font = None
        
        # Get text size
        if font:
            bbox = draw.textbbox((0, 0), self.text_overlay, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width = len(self.text_overlay) * 10
            text_height = 20
        
        # Position text below cover image (center bottom area)
        x = (self.width - text_width) // 2
        
        # If cover exists, position below it, otherwise center vertically
        if self.cover_image:
            base_size = int(min(self.width, self.height) * 0.525)
            cover_bottom = (self.height // 2) + base_size
            y = cover_bottom + 40  # 40px below cover
        else:
            y = int(self.height * 0.7)
        
        # Draw text shadow for better visibility
        shadow_offset = 3
        shadow_alpha = int(alpha * 180)
        if font:
            draw.text((x + shadow_offset, y + shadow_offset), self.text_overlay, 
                     font=font, fill=(0, 0, 0, shadow_alpha))
        else:
            draw.text((x + shadow_offset, y + shadow_offset), self.text_overlay, 
                     fill=(0, 0, 0, shadow_alpha))
        
        # Draw main white text
        text_alpha = int(alpha * 255)
        if font:
            draw.text((x, y), self.text_overlay, font=font, fill=(255, 255, 255, text_alpha))
        else:
            draw.text((x, y), self.text_overlay, fill=(255, 255, 255, text_alpha))
        
        # Composite onto image
        img.paste(text_layer, (0, 0), text_layer)

### END OF PART 2 - Continue with part 3 ###


### PART 3 - Continue from part 2 ###
    
    def render_frame(self, frame_idx, total_frames):
        """Render a single frame with all psychedelic effects"""
        # Calculate volume intensity
        band_values = self.get_band_values(frame_idx)
        avg_volume = np.mean(band_values) if band_values else 0
        max_possible = np.max(self.magnitude) if np.max(self.magnitude) > 0 else 1
        volume_intensity = avg_volume / max_possible
        
        # Detect beats
        beat_intensity = self.detect_beat(frame_idx)
        
        # Update animation state
        rotation_speed = 0.001 + (volume_intensity * 0.015)
        self.rotation += rotation_speed
        self.cover_rotation -= rotation_speed * 2
        self.hue_offset = (self.hue_offset + 0.5 + volume_intensity) % 360
        
        # Initialize or fade trail buffer
        if self.trail_buffer is None:
            self.trail_buffer = Image.new('RGB', (self.width, self.height), (0, 0, 0))
        else:
            # Apply fade to trail buffer for afterimage effect
            trail_array = np.array(self.trail_buffer)
            trail_array = (trail_array * 0.85).astype(np.uint8)  # 85% retention = subtle trails
            self.trail_buffer = Image.fromarray(trail_array)
        
        # Start with faded trail
        img = self.trail_buffer.copy()
        
        # Draw starfield (behind everything) - unless disabled
        if not self.disable_starfield:
            self.update_starfield(volume_intensity)
            self.draw_starfield(img, volume_intensity)
        
        # Create a separate canvas for waveforms that will be rotated
        waveform_canvas = Image.new('RGB', (self.width, self.height), (0, 0, 0))
        
        # Draw waveforms on separate canvas
        self.draw_waveforms_with_glow(waveform_canvas, frame_idx)
        
        # Rotate the waveform canvas based on rotation axis
        if self.waveform_rotation == 'none':
            # No rotation
            waveform_rotated = waveform_canvas
        elif self.waveform_rotation == 'z':
            # Z-axis rotation (standard 2D rotation)
            waveform_rotated = waveform_canvas.rotate(math.degrees(self.rotation), expand=False, 
                                                       fillcolor=(0, 0, 0), resample=Image.BILINEAR)
        elif self.waveform_rotation == 'x':
            # X-axis rotation (flip/perspective effect)
            waveform_rotated = waveform_canvas.transform(
                (self.width, self.height),
                Image.PERSPECTIVE,
                self._get_x_rotation_matrix(self.rotation),
                resample=Image.BILINEAR
            )
        elif self.waveform_rotation == 'y':
            # Y-axis rotation (tilt/perspective effect)
            waveform_rotated = waveform_canvas.transform(
                (self.width, self.height),
                Image.PERSPECTIVE,
                self._get_y_rotation_matrix(self.rotation),
                resample=Image.BILINEAR
            )
        else:
            waveform_rotated = waveform_canvas
        
        # Composite rotated waveforms onto main image (with starfield and trails)
        img_array = np.array(img)
        waveform_array = np.array(waveform_rotated)
        
        # Blend where waveforms are not black
        mask = (waveform_array.sum(axis=2) > 0)
        img_array[mask] = waveform_array[mask]
        img = Image.fromarray(img_array)
        
        # Draw cover/rings on top (stationary, not rotated)
        # Rings are always drawn, cover kaleidoscope only if image exists
        self.draw_cover_kaleidoscope(img, frame_idx, volume_intensity, beat_intensity)
        
        # Draw text overlay on top of everything
        if self.text_overlay:
            self.draw_text_overlay(img, beat_intensity, volume_intensity)
        
        # Update trail buffer with current frame
        self.trail_buffer = img.copy()
        
        # Apply fade to black at the end (last 2 seconds)
        fade_duration = 2.0  # seconds
        fade_frames = int(fade_duration * self.fps)
        frames_from_end = total_frames - frame_idx
        
        if frames_from_end <= fade_frames:
            # Calculate fade amount (0 = fully visible, 1 = completely black)
            fade_amount = 1.0 - (frames_from_end / fade_frames)
            
            # Apply fade
            img_array = np.array(img)
            img_array = (img_array * (1 - fade_amount)).astype(np.uint8)
            img = Image.fromarray(img_array)
        
        return img
    
    def render(self):
        """Render the complete video with audio"""
        # Calculate frames - limit to preview duration if specified
        if self.preview_seconds:
            render_duration = min(self.preview_seconds, self.duration)
            total_frames = int(render_duration * self.fps)
            print(f"⚡ PREVIEW MODE: Rendering first {render_duration:.1f}s")
        else:
            render_duration = self.duration
            total_frames = int(render_duration * self.fps)
        
        # Create temporary video without audio
        temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_video_path = temp_video.name
        temp_video.close()
        
        # Setup video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_video_path, fourcc, self.fps, 
                             (self.width, self.height))
        
        print(f"Rendering {total_frames} frames at {self.fps} fps...")
        
        for frame_idx in tqdm(range(total_frames)):
            # Render frame with fade info
            img = self.render_frame(frame_idx, total_frames)
            
            # Convert PIL to OpenCV format
            frame_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            
            # Write frame
            out.write(frame_cv)
        
        out.release()
        
        # Merge video with audio using ffmpeg
        print("\nAdding audio to video...")
        try:
            # If preview mode, cut audio to match video length
            if self.preview_seconds:
                subprocess.run([
                    'ffmpeg', '-i', temp_video_path, '-i', self.audio_path,
                    '-t', str(render_duration),  # Limit audio duration
                    '-c:v', 'libx264', '-c:a', 'aac', '-strict', 'experimental',
                    '-shortest', '-y', self.output_path
                ], check=True, capture_output=True)
            else:
                subprocess.run([
                    'ffmpeg', '-i', temp_video_path, '-i', self.audio_path,
                    '-c:v', 'libx264', '-c:a', 'aac', '-strict', 'experimental',
                    '-shortest', '-y', self.output_path
                ], check=True, capture_output=True)
            
            # Clean up temp file
            os.remove(temp_video_path)
            
            print(f"Video with audio saved to: {self.output_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error adding audio: {e}")
            print(f"Video without audio saved to: {temp_video_path}")

def main():
    parser = argparse.ArgumentParser(
        description='Generate psychedelic music visualization with rotating waveforms, starfield, and reactive effects',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Basic usage:
    python visualizer.py song.mp3
  
  With cover image and text:
    python visualizer.py song.mp3 -c cover.jpg -t "Song Title"
  
  Autumn palette at 60fps:
    python visualizer.py song.mp3 -p autumn --fps 60
  
  Phone vertical format:
    python visualizer.py song.mp3 --phone-vertical
  
  3D waveform rotation with spiral starfield:
    python visualizer.py song.mp3 --waveform-rotation x --starfield-rotation cw
  
  Breathing rings effect:
    python visualizer.py song.mp3 --ring-rotation x
  
  Square rings:
    python visualizer.py song.mp3 --ring-shape square
  
  Quick 30-second preview (10-15x faster):
    python visualizer.py song.mp3 --preview 30 -c cover.jpg -t "Test"
  
  Preview with different settings:
    python visualizer.py song.mp3 --preview 60 -p autumn
  
  Full custom:
    python visualizer.py song.mp3 -c cover.jpg -t "Artist - Song" -p winter \\
      --waveform-rotation y --starfield-rotation ccw -o output.mp4 --fps 30

Workflow:
  1. Create a quick preview to test appearance:
     python visualizer.py song.mp3 --preview 30 -p summer -c cover.jpg
  
  2. Once satisfied, render full video:
     python visualizer.py song.mp3 -p summer -c cover.jpg --fps 60

Color Palettes:
  rainbow - Full spectrum colors (default)
  spring  - Greens, blues, and pinks
  summer  - Oranges, yellows, and blues
  autumn  - Reds, oranges, and golds
  winter  - Blues and cool tones
  ice     - Shades of blue and white
  fire    - Reds, oranges, and yellows
  water   - Blues, greens, and sea greens
  earth   - Earth tones - browns, tans, greens

Rotation Options:
  Waveform Rotation (--waveform-rotation):
    none - No rotation (stationary)
    z - Standard 2D spin (default)
    x - Horizontal flip/tilt (3D perspective)
    y - Vertical tilt (3D perspective)
  
  Ring Rotation (--ring-rotation):
    none - No rotation, just pulsing
    z - No rotation, just pulsing (default)
    x - Horizontal squeeze/stretch
    y - Vertical squeeze/stretch
  
  Starfield Rotation (--starfield-rotation):
    none - Outward only (default)
    cw   - Clockwise spiral
    ccw  - Counter-clockwise spiral

Features:
  - 8 frequency bands with exponential sensitivity
  - Beat-reactive center rings
  - Volume-reactive starfield
  - Rotating waveforms with afterimage trails
  - Fade to black ending
  - Music-synced text fading
  - Multiple rotation axes for 3D effects
  - Square or circle ring shapes
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
                       help='Frames per second (default: 30, recommended: 30 or 60)')
    
    parser.add_argument('--resolution', 
                       help='Custom resolution as WIDTHxHEIGHT (e.g., 1920x1080)')
    
    parser.add_argument('--phone-vertical', action='store_true',
                       help='Use phone vertical resolution (1080x1920)')
    
    parser.add_argument('--phone-horizontal', action='store_true',
                       help='Use phone horizontal resolution (1920x1080)')
    
    parser.add_argument('--waveform-rotation', default='z',
                       choices=['none', 'x', 'y', 'z'],
                       help='Waveform rotation axis: none=no rotation, x=horizontal flip, y=vertical tilt, z=standard spin (default: z)')
    
    parser.add_argument('--ring-rotation', default='z',
                       choices=['none', 'x', 'y', 'z'],
                       help='Ring rotation axis: none=no rotation, x=horizontal squeeze, y=vertical squeeze, z=no rotation (default: z)')
    
    parser.add_argument('--ring-shape', default='circle',
                       choices=['circle', 'square'],
                       help='Ring shape: circle or square (default: circle)')
    
    parser.add_argument('--starfield-rotation', default='none',
                       choices=['none', 'cw', 'ccw'],
                       help='Starfield rotation: none=outward only, cw=clockwise spiral, ccw=counter-clockwise spiral (default: none)')
    
    parser.add_argument('--preview', type=int, metavar='SECONDS',
                       help='Preview mode: render only first N seconds at lower quality for fast iteration')
    
    parser.add_argument('--cover-shape', default='square',
                       choices=['square', 'round'],
                       help='Cover art shape: square or round (default: square)')
    
    parser.add_argument('--cover-size', type=float, default=1.0,
                       help='Cover art size multiplier (default: 1.0, try 0.5-2.0)')
    
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
        width, height = 1280, 720  # Default HD
    
    # Apply preview mode optimizations
    preview_fps = args.fps
    if args.preview:
        # Reduce resolution by half
        width = width // 2
        height = height // 2
        # Reduce FPS to 15 if using default
        if args.fps == 30:
            preview_fps = 15
        print(f"⚡ PREVIEW MODE:")
        print(f"   Duration: First {args.preview} seconds")
        print(f"   Resolution: {width}x{height} (half of normal)")
        print(f"   FPS: {preview_fps}")
        print(f"   Simplified effects")
        print(f"   Expected speedup: ~10-15x faster")
        print()
    
    print(f"Configuration:")
    print(f"  Audio: {args.audio}")
    print(f"  Resolution: {width}x{height}")
    print(f"  FPS: {preview_fps}")
    print(f"  Palette: {args.palette}")
    print(f"  Waveform Rotation: {args.waveform_rotation}-axis")
    print(f"  Ring Rotation: {args.ring_rotation}-axis")
    print(f"  Ring Shape: {args.ring_shape}")
    print(f"  Starfield Rotation: {args.starfield_rotation}")
    if args.preview:
        print(f"  Preview: {args.preview} seconds")
    if args.cover:
        print(f"  Cover: {args.cover}")
        print(f"  Cover Shape: {args.cover_shape}")
        print(f"  Cover Size: {args.cover_size}x")
    if args.disable_rings:
        print(f"  Rings: Disabled")
    if args.disable_starfield:
        print(f"  Starfield: Disabled")
    if args.text:
        print(f"  Text: {args.text}")
    print(f"  Output: {args.output}")
    print()
    
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

### END OF PART 3 - This is the final part ###