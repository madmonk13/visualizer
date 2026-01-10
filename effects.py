"""
Visual effects module
Handles rendering of waveforms, starfield, rings, and cover art
"""

import numpy as np
import math
from PIL import Image, ImageDraw, ImageFilter


class EffectsRenderer:
    def __init__(self, width, height, is_preview=False):
        self.width = width
        self.height = height
        self.is_preview = is_preview
        
        # Initialize starfield
        self.stars = []
        self._init_starfield()
    
    def _init_starfield(self):
        """Initialize starfield particles"""
        num_stars = 100 if self.is_preview else 200
        for _ in range(num_stars):
            self.stars.append({
                'x': np.random.rand() * self.width,
                'y': np.random.rand() * self.height,
                'z': np.random.rand() * 2,  # Depth
                'size': np.random.randint(1, 4)
            })
    
    @staticmethod
    def hsv_to_rgb(h, s, v):
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
    
    def update_starfield(self, volume_intensity, rotation_mode='none'):
        """Update starfield positions based on volume and rotation settings"""
        speed = 0.5 + volume_intensity * 5.5
        center_x, center_y = self.width / 2, self.height / 2
        
        for star in self.stars:
            # Apply rotation if enabled
            if rotation_mode == 'cw':
                angle = math.atan2(star['y'] - center_y, star['x'] - center_x)
                angle -= speed * 0.01 * star['z']
                distance = math.sqrt((star['x'] - center_x)**2 + (star['y'] - center_y)**2)
                star['x'] = center_x + distance * math.cos(angle)
                star['y'] = center_y + distance * math.sin(angle)
            elif rotation_mode == 'ccw':
                angle = math.atan2(star['y'] - center_y, star['x'] - center_x)
                angle += speed * 0.01 * star['z']
                distance = math.sqrt((star['x'] - center_x)**2 + (star['y'] - center_y)**2)
                star['x'] = center_x + distance * math.cos(angle)
                star['y'] = center_y + distance * math.sin(angle)
            
            # Move stars outward from center
            dx = star['x'] - center_x
            dy = star['y'] - center_y
            
            distance = math.sqrt(dx*dx + dy*dy)
            if distance > 0:
                star['x'] += (dx / distance) * speed * star['z']
                star['y'] += (dy / distance) * speed * star['z']
            
            # Wrap around edges
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
            brightness = int(150 + star['z'] * 50)
            star_color = (255, 255, 255)
            
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
        
        img.paste(star_layer, (0, 0), star_layer)
    
    def draw_waveforms_with_glow(self, img, frame_idx, bands, hue_offset, audio_processor):
        """Draw the frequency band waveforms with glow effects"""
        band_height = self.height // len(bands)
        
        waveform_layer = Image.new('RGB', (self.width, self.height), (0, 0, 0))
        waveform_draw = ImageDraw.Draw(waveform_layer)
        
        waveform_points = 100 if self.is_preview else 150
        
        for band_idx, band in enumerate(bands):
            waveform = audio_processor.get_band_waveform(frame_idx, band_idx, bands, points=waveform_points)
            center_y = (band_idx + 0.5) * band_height
            
            base_hue = (hue_offset + band['hue_offset']) % 360
            sensitivity = 1.0 + (band_idx / (len(bands) - 1)) * 2.0
            
            # Draw two layers with mirroring
            for layer in range(2):
                layer_hue = (base_hue + layer * 40) % 360
                sat = band.get('saturation', 1.0)
                bright = band.get('brightness', 1.0)
                color = self.hsv_to_rgb(layer_hue, sat, bright)
                
                phase_offset = layer * 0.3
                
                points_upper = []
                points_lower = []
                
                for i, value in enumerate(waveform):
                    x = int((i / len(waveform)) * self.width)
                    t = i / len(waveform)
                    
                    amplitude = value * (band_height * 0.65) * sensitivity
                    wave1 = math.sin((t * math.pi * 4) + phase_offset) * amplitude
                    wave2 = math.sin((t * math.pi * 8) + (phase_offset * 2)) * (amplitude * 0.3)
                    wave3 = math.cos((t * math.pi * 2) + (hue_offset * 0.02)) * (amplitude * 0.2)
                    
                    y_upper = int(center_y + wave1 + wave2 + wave3)
                    y_lower = int(center_y - (wave1 + wave2 + wave3))
                    
                    points_upper.append((x, y_upper))
                    points_lower.append((x, y_lower))
                
                # Draw filled area
                if layer == 0 and len(points_upper) > 1:
                    fill_points = points_upper + points_lower[::-1]
                    waveform_draw.polygon(fill_points, fill=color)
                
                # Draw glow halo
                if len(points_upper) > 1:
                    glow_layers = 6 if self.is_preview else 12
                    
                    for thickness in range(glow_layers, 0, -1):
                        glow_intensity = (1 - thickness / glow_layers) * 0.5
                        glow_r = int(color[0] * glow_intensity)
                        glow_g = int(color[1] * glow_intensity)
                        glow_b = int(color[2] * glow_intensity)
                        glow_color = (glow_r, glow_g, glow_b)
                        
                        waveform_draw.line(points_upper, fill=glow_color, width=thickness + 8)
                        waveform_draw.line(points_lower, fill=glow_color, width=thickness + 8)
                    
                    waveform_draw.line(points_upper, fill=color, width=6 - layer)
                    waveform_draw.line(points_lower, fill=color, width=6 - layer)
                
                # Draw particles on peaks
                for i in range(0, len(waveform), 15):
                    if waveform[i] > 0.7:
                        x = int((i / len(waveform)) * self.width)
                        particle_hue = (base_hue + i * 2) % 360
                        particle_color = self.hsv_to_rgb(particle_hue, 1.0, 1.0)
                        
                        for radius in range(10, 2, -1):
                            glow_intensity = (1 - radius / 10) * 0.5
                            glow_r = int(particle_color[0] * glow_intensity)
                            glow_g = int(particle_color[1] * glow_intensity)
                            glow_b = int(particle_color[2] * glow_intensity)
                            waveform_draw.ellipse(
                                [x-radius, center_y-radius, x+radius, center_y+radius],
                                fill=(glow_r, glow_g, glow_b)
                            )
                        
                        waveform_draw.ellipse(
                            [x-3, center_y-3, x+3, center_y+3],
                            fill=particle_color
                        )
        
        blur_radius = 1 if self.is_preview else 2
        waveform_layer = waveform_layer.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        
        img.paste(waveform_layer, (0, 0), None)
    
    def draw_cover_and_rings(self, img, cover_image, base_size, volume_intensity, 
                            beat_intensity, rotation, hue_offset, bands, 
                            cover_shape='square', ring_rotation='z', 
                            disable_rings=False, ring_shape='circle'):
        """Draw cover art and reactive rings"""
        center_x, center_y = self.width // 2, self.height // 2
        
        # Draw cover
        if cover_image:
            if cover_shape == 'square':
                cover_width = int(base_size * 1.2)
                cover_height = int(base_size * 1.2)
                cover_resized = cover_image.resize((cover_width, cover_height))
                img.paste(cover_resized, (center_x - cover_width // 2, center_y - cover_height // 2))
            else:  # round
                center_size = int(base_size * 0.6 * (1 + volume_intensity * 0.3 + beat_intensity * 0.5))
                center_cover = cover_image.resize((center_size * 2, center_size * 2))
                
                mask = Image.new('L', (center_size * 2, center_size * 2), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse([0, 0, center_size * 2, center_size * 2], fill=255)
                
                img.paste(center_cover, (center_x - center_size, center_y - center_size), mask)
        
        # Draw rings
        if not disable_rings:
            ring_layer = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
            ring_draw = ImageDraw.Draw(ring_layer)
            
            for r in range(3):
                base_ring_size = base_size * (0.4 + r * 0.2)
                beat_expansion = beat_intensity * 80
                volume_expansion = volume_intensity * 0.5 * base_ring_size
                ring_size = int(base_ring_size + beat_expansion + volume_expansion)
                
                ring_hue = (hue_offset + r * 60) % 360
                sat = bands[0].get('saturation', 1.0) if bands else 1.0
                bright = bands[0].get('brightness', 0.9) if bands else 0.9
                
                ring_color = self.hsv_to_rgb(ring_hue, sat, bright)
                line_width = int(3 + volume_intensity * 4 + beat_intensity * 6)
                
                # Apply perspective distortion
                if ring_rotation == 'x':
                    distortion = 0.6 + 0.4 * math.cos(rotation * 2)
                    shape_height = int(ring_size * distortion)
                    shape_width = ring_size
                elif ring_rotation == 'y':
                    distortion = 0.6 + 0.4 * math.cos(rotation * 2)
                    shape_width = int(ring_size * distortion)
                    shape_height = ring_size
                else:
                    shape_width = ring_size
                    shape_height = ring_size
                
                # Draw glow
                for glow in range(8, 0, -1):
                    alpha = int((200 + beat_intensity * 55) * (1 - glow / 8))
                    glow_color = (*ring_color, alpha)
                    
                    if ring_shape == 'square':
                        ring_draw.rectangle(
                            [center_x - shape_width - glow*2, center_y - shape_height - glow*2,
                             center_x + shape_width + glow*2, center_y + shape_height + glow*2],
                            outline=glow_color, width=line_width + glow
                        )
                    else:
                        ring_draw.ellipse(
                            [center_x - shape_width - glow*2, center_y - shape_height - glow*2,
                             center_x + shape_width + glow*2, center_y + shape_height + glow*2],
                            outline=glow_color, width=line_width + glow
                        )
                
                # Main ring
                if ring_shape == 'square':
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
            
            img.paste(ring_layer, (0, 0), ring_layer)
    
    def draw_text_overlay(self, img, text, beat_intensity, volume_intensity, 
                         text_fade_history, cover_image, base_size):
        """Draw white text below the cover image with music-reactive fading"""
        if not text:
            return
        
        text_fade_history.append(volume_intensity)
        if len(text_fade_history) > 60:
            text_fade_history.pop(0)
        
        avg_recent_volume = np.mean(text_fade_history) if text_fade_history else 0
        base_alpha = 0.3 + (avg_recent_volume * 0.7)
        beat_boost = beat_intensity * 0.2
        alpha = min(1.0, base_alpha + beat_boost)
        
        text_layer = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_layer)
        
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
        
        if font:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width = len(text) * 10
            text_height = 20
        
        x = (self.width - text_width) // 2
        
        if cover_image:
            cover_bottom = (self.height // 2) + base_size
            y = cover_bottom + 40
        else:
            y = int(self.height * 0.7)
        
        shadow_offset = 3
        shadow_alpha = int(alpha * 180)
        if font:
            draw.text((x + shadow_offset, y + shadow_offset), text, 
                     font=font, fill=(0, 0, 0, shadow_alpha))
        else:
            draw.text((x + shadow_offset, y + shadow_offset), text, 
                     fill=(0, 0, 0, shadow_alpha))
        
        text_alpha = int(alpha * 255)
        if font:
            draw.text((x, y), text, font=font, fill=(255, 255, 255, text_alpha))
        else:
            draw.text((x, y), text, fill=(255, 255, 255, text_alpha))
        
        img.paste(text_layer, (0, 0), text_layer)