"""
Audio processing module
Handles audio loading, conversion, and frequency analysis
"""

import numpy as np
import subprocess
import os
from scipy.io import wavfile
from scipy import signal


class AudioProcessor:
    def __init__(self, audio_path, sample_rate=44100, fps=30, is_preview=False):
        self.audio_path = audio_path
        self.target_sr = sample_rate
        self.fps = fps
        self.is_preview = is_preview
        
        # Load and process audio
        self.sr, self.y, self.duration = self._load_audio()
        
        # Calculate STFT
        self.frequencies, self.times, self.stft, self.magnitude = self._calculate_stft()
    
    def _load_audio(self):
        """Load audio file and convert to normalized mono"""
        print("Loading audio...")
        wav_path = self._convert_to_wav(self.audio_path)
        
        # Load audio
        sr, audio_data = wavfile.read(wav_path)
        
        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1)
        
        # Normalize
        y = audio_data.astype(np.float32) / np.max(np.abs(audio_data))
        duration = len(y) / sr
        
        # Clean up temporary WAV
        if wav_path != self.audio_path:
            os.remove(wav_path)
        
        print(f"Audio loaded: {duration:.2f}s at {sr}Hz")
        return sr, y, duration
    
    def _convert_to_wav(self, audio_path):
        """Convert audio file to WAV using ffmpeg if needed"""
        if audio_path.lower().endswith('.wav'):
            return audio_path
        
        wav_path = audio_path.rsplit('.', 1)[0] + '_temp.wav'
        
        try:
            subprocess.run([
                'ffmpeg', '-i', audio_path, '-ar', str(self.target_sr), '-ac', '1', 
                '-y', wav_path
            ], check=True, capture_output=True)
            return wav_path
        except subprocess.CalledProcessError:
            raise Exception("FFmpeg is required to process audio files. Install with: brew install ffmpeg")
        except FileNotFoundError:
            raise Exception("FFmpeg not found. Install with: brew install ffmpeg")
    
    def _calculate_stft(self):
        """Calculate Short-Time Fourier Transform for frequency analysis"""
        print("Analyzing audio frequencies...")
        hop_length = self.sr // self.fps
        
        # Use smaller FFT in preview mode for speed
        nperseg = 1024 if self.is_preview else 2048
        
        frequencies, times, stft = signal.stft(
            self.y, 
            fs=self.sr, 
            nperseg=nperseg, 
            noverlap=nperseg - hop_length
        )
        magnitude = np.abs(stft)
        
        return frequencies, times, stft, magnitude
    
    def get_band_values(self, frame_idx, bands):
        """Extract frequency band values for a specific frame"""
        if frame_idx >= self.magnitude.shape[1]:
            frame_idx = self.magnitude.shape[1] - 1
        
        frame_data = self.magnitude[:, frame_idx]
        band_values = []
        
        for band in bands:
            # Find frequency indices for this band
            mask = (self.frequencies >= band['min']) & (self.frequencies <= band['max'])
            band_data = frame_data[mask]
            
            if len(band_data) > 0:
                avg_value = np.mean(band_data)
                band_values.append(avg_value)
            else:
                band_values.append(0)
        
        return band_values
    
    def get_band_waveform(self, frame_idx, band_idx, bands, points=150):
        """Get waveform data for a specific frequency band"""
        if frame_idx >= self.magnitude.shape[1]:
            frame_idx = self.magnitude.shape[1] - 1
        
        band = bands[band_idx]
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