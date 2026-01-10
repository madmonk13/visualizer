#!/usr/bin/env python3
"""
Psychedelic Music Visualizer - Main Module
Orchestrates all components to render audio-reactive video
"""

import numpy as np
import cv2
from PIL import Image
import subprocess
import os
import tempfile
from tqdm import tqdm
import math
import copy

from config import (
    FREQUENCY_BANDS, COLOR_PALETTES, 
    BASE_ROTATION_SPEED, VOLUME_ROTATION_MULTIPLIER,
    HUE_SHIFT_BASE, TRAIL_FADE_FACTOR, FADE_DURATION_SECONDS
)
from audio_processor import AudioProcessor
from effects import EffectsRenderer
from beat_detector import BeatDetector


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
        
        # Initialize components
        self.audio_processor = AudioProcessor(audio_path, fps=fps, is_preview=self.is_preview)
        self.effects_renderer = EffectsRenderer(self.width, self.height, is_preview=self.is_preview)
        self.beat_detector = BeatDetector()
        
        # Get duration from audio processor
        self.duration = self.audio_processor.duration
        
        # Setup frequency bands with color palette
        self.bands = self._setup_bands()
        
        # Animation state
        self.rotation = 0
        self.cover_rotation = 0
        self.hue_offset = 0
        
        # Text fade tracking
        self.text_fade_history = []
        
        # Trail buffer for afterimage effect
        self.trail_buffer = None
        
        # Load cover image if provided
        self.cover_image = None
        if cover_image_path:
            try:
                self.cover_image = Image.open(cover_image_path).convert('RGB')
                print(f"Loaded cover image: {cover_image_path}")
            except Exception as e:
                print(f"Could not load cover image: {e}")
    
    def _setup_bands(self):
        """Setup frequency bands with color palette applied"""
        bands = copy.deepcopy(FREQUENCY_BANDS)
        
        if self.color_palette in COLOR_PALETTES:
            palette = COLOR_PALETTES[self.color_palette]
            for i, band in enumerate(bands):
                band['hue_offset'] = palette['colors'][i % len(palette['colors'])]
                band['saturation'] = palette['saturation']
                band['brightness'] = palette['brightness']
        else:
            print(f"Warning: Palette '{self.color_palette}' not found, using rainbow")
            for band in bands:
                band['saturation'] = 1.0
                band['brightness'] = 1.0
        
        return bands
    
    @staticmethod
    def _get_x_rotation_matrix(angle, height):
        """Calculate perspective transform matrix for X-axis rotation"""
        distortion = 0.3 * math.sin(angle * 2)
        return (1, 0, 0, distortion, 1, -height * distortion / 2, 0, 0)
    
    @staticmethod
    def _get_y_rotation_matrix(angle, width):
        """Calculate perspective transform matrix for Y-axis rotation"""
        distortion = 0.3 * math.sin(angle * 2)
        return (1, distortion, -width * distortion / 2, 0, 1, 0, 0, 0)
    
    def render_frame(self, frame_idx, total_frames):
        """Render a single frame with all psychedelic effects"""
        # Calculate volume intensity
        band_values = self.audio_processor.get_band_values(frame_idx, self.bands)
        avg_volume = np.mean(band_values) if band_values else 0
        max_possible = np.max(self.audio_processor.magnitude) if np.max(self.audio_processor.magnitude) > 0 else 1
        volume_intensity = avg_volume / max_possible
        
        # Detect beats
        beat_intensity = self.beat_detector.detect_beat(
            frame_idx, 
            self.audio_processor.frequencies, 
            self.audio_processor.magnitude
        )
        
        # Update animation state
        rotation_speed = BASE_ROTATION_SPEED + (volume_intensity * VOLUME_ROTATION_MULTIPLIER)
        self.rotation += rotation_speed
        self.cover_rotation -= rotation_speed * 2
        self.hue_offset = (self.hue_offset + HUE_SHIFT_BASE + volume_intensity) % 360
        
        # Initialize or fade trail buffer
        if self.trail_buffer is None:
            self.trail_buffer = Image.new('RGB', (self.width, self.height), (0, 0, 0))
        else:
            trail_array = np.array(self.trail_buffer)
            trail_array = (trail_array * TRAIL_FADE_FACTOR).astype(np.uint8)
            self.trail_buffer = Image.fromarray(trail_array)
        
        # Start with faded trail
        img = self.trail_buffer.copy()
        
        # Draw starfield (behind everything)
        if not self.disable_starfield:
            self.effects_renderer.update_starfield(volume_intensity, self.starfield_rotation)
            self.effects_renderer.draw_starfield(img, volume_intensity)
        
        # Create separate canvas for waveforms
        waveform_canvas = Image.new('RGB', (self.width, self.height), (0, 0, 0))
        
        # Draw waveforms
        self.effects_renderer.draw_waveforms_with_glow(
            waveform_canvas, frame_idx, self.bands, 
            self.hue_offset, self.audio_processor
        )
        
        # Rotate waveforms based on rotation axis
        if self.waveform_rotation == 'none':
            waveform_rotated = waveform_canvas
        elif self.waveform_rotation == 'z':
            waveform_rotated = waveform_canvas.rotate(
                math.degrees(self.rotation), expand=False, 
                fillcolor=(0, 0, 0), resample=Image.BILINEAR
            )
        elif self.waveform_rotation == 'x':
            waveform_rotated = waveform_canvas.transform(
                (self.width, self.height),
                Image.PERSPECTIVE,
                self._get_x_rotation_matrix(self.rotation, self.height),
                resample=Image.BILINEAR
            )
        elif self.waveform_rotation == 'y':
            waveform_rotated = waveform_canvas.transform(
                (self.width, self.height),
                Image.PERSPECTIVE,
                self._get_y_rotation_matrix(self.rotation, self.width),
                resample=Image.BILINEAR
            )
        else:
            waveform_rotated = waveform_canvas
        
        # Composite rotated waveforms
        img_array = np.array(img)
        waveform_array = np.array(waveform_rotated)
        mask = (waveform_array.sum(axis=2) > 0)
        img_array[mask] = waveform_array[mask]
        img = Image.fromarray(img_array)
        
        # Draw cover/rings on top
        base_size = int(min(self.width, self.height) * 0.525 * self.cover_size)
        self.effects_renderer.draw_cover_and_rings(
            img, self.cover_image, base_size, volume_intensity, 
            beat_intensity, self.rotation, self.hue_offset, self.bands,
            self.cover_shape, self.ring_rotation, 
            self.disable_rings, self.ring_shape
        )
        
        # Draw text overlay
        if self.text_overlay:
            self.effects_renderer.draw_text_overlay(
                img, self.text_overlay, beat_intensity, volume_intensity,
                self.text_fade_history, self.cover_image, base_size
            )
        
        # Update trail buffer
        self.trail_buffer = img.copy()
        
        # Apply fade to black at the end
        fade_frames = int(FADE_DURATION_SECONDS * self.fps)
        frames_from_end = total_frames - frame_idx
        
        if frames_from_end <= fade_frames:
            fade_amount = 1.0 - (frames_from_end / fade_frames)
            img_array = np.array(img)
            img_array = (img_array * (1 - fade_amount)).astype(np.uint8)
            img = Image.fromarray(img_array)
        
        return img
    
    def render(self):
        """Render the complete video with audio"""
        # Calculate frames
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
            img = self.render_frame(frame_idx, total_frames)
            frame_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            out.write(frame_cv)
        
        out.release()
        
        # Merge video with audio
        print("\nAdding audio to video...")
        try:
            if self.preview_seconds:
                subprocess.run([
                    'ffmpeg', '-i', temp_video_path, '-i', self.audio_path,
                    '-t', str(render_duration),
                    '-c:v', 'libx264', '-c:a', 'aac', '-strict', 'experimental',
                    '-shortest', '-y', self.output_path
                ], check=True, capture_output=True)
            else:
                subprocess.run([
                    'ffmpeg', '-i', temp_video_path, '-i', self.audio_path,
                    '-c:v', 'libx264', '-c:a', 'aac', '-strict', 'experimental',
                    '-shortest', '-y', self.output_path
                ], check=True, capture_output=True)
            
            os.remove(temp_video_path)
            print(f"Video with audio saved to: {self.output_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error adding audio: {e}")
            print(f"Video without audio saved to: {temp_video_path}")