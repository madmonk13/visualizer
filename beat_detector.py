"""
Beat detection module
Analyzes audio for transient changes (beats)
"""

import numpy as np


class BeatDetector:
    def __init__(self):
        self.prev_energy = 0
        self.beat_intensity = 0
    
    def detect_beat(self, frame_idx, frequencies, magnitude):
        """Detect transient changes (beats) in the audio"""
        if frame_idx >= magnitude.shape[1]:
            frame_idx = magnitude.shape[1] - 1
        
        frame_data = magnitude[:, frame_idx]
        
        # Calculate energy in bass/low-mid range
        bass_mask = (frequencies >= 20) & (frequencies <= 250)
        low_mid_mask = (frequencies >= 250) & (frequencies <= 1000)
        
        bass_energy = np.sum(frame_data[bass_mask])
        low_mid_energy = np.sum(frame_data[low_mid_mask])
        total_energy = bass_energy + low_mid_energy
        
        # Detect sudden increase in energy
        energy_change = total_energy - self.prev_energy
        
        # Threshold for beat detection
        max_energy = np.sum(magnitude[:, :]) / magnitude.shape[1]
        threshold = max_energy * 0.3
        
        if energy_change > threshold:
            self.beat_intensity = min(1.0, energy_change / (threshold * 2))
        else:
            self.beat_intensity *= 0.7  # Decay
        
        self.prev_energy = total_energy
        
        return self.beat_intensity