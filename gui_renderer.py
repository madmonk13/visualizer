"""
GUI Renderer
Handles preview generation and full video rendering in background threads
"""

import threading
import subprocess
import os
import tempfile
import cv2
import numpy as np
from visualizer import MusicVisualizer
from gui_config import *


class RenderManager:
    def __init__(self, root, controls_panel, preview_panel):
        self.root = root
        self.controls = controls_panel
        self.preview = preview_panel
        
        self.preview_thread = None
        self.render_thread = None
        self.is_rendering = False
        self.cancel_render_flag = False
    
    def generate_preview(self):
        """Start preview generation in background thread"""
        if not self.controls.audio_path:
            return
        
        if self.preview_thread and self.preview_thread.is_alive():
            return  # Already generating
        
        self.preview.set_info(MSG_GENERATING_PREVIEW)
        self.controls.preview_btn.config(state='disabled')
        
        self.preview_thread = threading.Thread(target=self._generate_preview_background, 
                                              daemon=True)
        self.preview_thread.start()
    
    def _generate_preview_background(self):
        """Background thread to generate preview"""
        try:
            settings = self.controls.get_settings()
            width, height = settings['resolution']
            
            # Create visualizer with preview settings
            visualizer = MusicVisualizer(
                audio_path=settings['audio_path'],
                cover_image_path=settings['cover_image_path'],
                fps=PREVIEW_FPS,
                resolution=(width // PREVIEW_RESOLUTION_DIVISOR, 
                           height // PREVIEW_RESOLUTION_DIVISOR),
                text_overlay=settings['text_overlay'],
                color_palette=settings['color_palette'],
                waveform_rotation=settings['waveform_rotation'],
                ring_rotation=settings['ring_rotation'],
                starfield_rotation=settings['starfield_rotation'],
                preview_seconds=None,
                cover_shape=settings['cover_shape'],
                cover_size=settings['cover_size'],
                disable_rings=settings['disable_rings'],
                disable_starfield=settings['disable_starfield'],
                ring_shape=settings['ring_shape']
            )
            
            # Render a frame from middle of song
            frame_idx = min(len(visualizer.audio_processor.times) // 2, 
                           len(visualizer.audio_processor.times) - 1)
            total_frames = len(visualizer.audio_processor.times)
            
            preview_img = visualizer.render_frame(frame_idx, total_frames)
            
            # Update UI in main thread
            self.root.after(0, lambda: self._display_preview(preview_img))
            
        except Exception as error:
            error_msg = str(error)
            self.root.after(0, lambda: self._preview_error(error_msg))
    
    def _display_preview(self, img):
        """Display the generated preview (called from main thread)"""
        self.preview.display_image(img)
        self.preview.set_info(MSG_PREVIEW_UPDATED)
        self.controls.preview_btn.config(state='normal')
    
    def _preview_error(self, error_msg):
        """Handle preview generation error"""
        self.preview.set_info(f"Error: {error_msg}")
        self.controls.preview_btn.config(state='normal')
        from tkinter import messagebox
        messagebox.showerror("Preview Error", f"Could not generate preview:\n{error_msg}")
    
    def start_render(self, output_path):
        """Start full video render"""
        if self.is_rendering:
            return False
        
        self.is_rendering = True
        self.cancel_render_flag = False
        self.controls.render_btn.config(state='disabled')
        self.controls.preview_btn.config(state='disabled')
        
        # Show progress UI
        self.controls.progress_frame.pack(fill='x', pady=(5, 0))
        self.controls.cancel_btn.pack(fill='x', pady=(5, 0))
        self.controls.progress_bar['value'] = 0
        self.controls.progress_label.config(text=MSG_STARTING_RENDER)
        self.preview.set_info(MSG_RENDERING)
        
        # Start render thread
        self.render_thread = threading.Thread(
            target=self._render_video_background,
            args=(output_path,),
            daemon=True
        )
        self.render_thread.start()
        return True
    
    def cancel_render(self):
        """Cancel the current render"""
        from tkinter import messagebox
        if messagebox.askyesno("Cancel Render", 
                              "Are you sure you want to cancel the current render?"):
            self.cancel_render_flag = True
            self.controls.progress_label.config(text=MSG_CANCELLING)
    
    def update_progress(self, current_frame, total_frames):
        """Update progress bar from render thread"""
        if self.cancel_render_flag:
            return False
        
        progress = int((current_frame / total_frames) * 100)
        
        self.root.after(0, lambda: self.controls.progress_bar.config(value=progress))
        self.root.after(0, lambda: self.controls.progress_label.config(
            text=f"Rendering frame {current_frame}/{total_frames} ({progress}%)"
        ))
        
        return True
    
    def _render_video_background(self, output_path):
        """Background thread for rendering"""
        try:
            settings = self.controls.get_settings()
            
            # Create visualizer
            visualizer = MusicVisualizer(
                audio_path=settings['audio_path'],
                output_path=output_path,
                cover_image_path=settings['cover_image_path'],
                fps=settings['fps'],
                resolution=settings['resolution'],
                text_overlay=settings['text_overlay'],
                color_palette=settings['color_palette'],
                waveform_rotation=settings['waveform_rotation'],
                ring_rotation=settings['ring_rotation'],
                starfield_rotation=settings['starfield_rotation'],
                preview_seconds=None,
                cover_shape=settings['cover_shape'],
                cover_size=settings['cover_size'],
                disable_rings=settings['disable_rings'],
                disable_starfield=settings['disable_starfield'],
                ring_shape=settings['ring_shape']
            )
            
            # Calculate frames
            render_duration = visualizer.duration
            total_frames = int(render_duration * visualizer.fps)
            
            # Create temporary video
            temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            temp_video_path = temp_video.name
            temp_video.close()
            
            # Setup video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(temp_video_path, fourcc, visualizer.fps,
                                 (visualizer.width, visualizer.height))
            
            # Render frames
            for frame_idx in range(total_frames):
                if not self.update_progress(frame_idx + 1, total_frames):
                    out.release()
                    os.remove(temp_video_path)
                    self.root.after(0, self._render_cancelled)
                    return
                
                img = visualizer.render_frame(frame_idx, total_frames)
                frame_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                out.write(frame_cv)
            
            out.release()
            
            # Add audio
            self.root.after(0, lambda: self.controls.progress_label.config(
                text=MSG_ADDING_AUDIO))
            
            subprocess.run([
                'ffmpeg', '-i', temp_video_path, '-i', settings['audio_path'],
                '-c:v', 'libx264', '-c:a', 'aac', '-strict', 'experimental',
                '-shortest', '-y', output_path
            ], check=True, capture_output=True)
            
            os.remove(temp_video_path)
            
            self.root.after(0, lambda: self._render_complete(output_path))
            
        except Exception as error:
            error_msg = str(error)
            self.root.after(0, lambda: self._render_error(error_msg))
    
    def _render_complete(self, output_path):
        """Handle successful render"""
        self.is_rendering = False
        self.controls.render_btn.config(state='normal')
        self.controls.preview_btn.config(state='normal')
        self.preview.set_info(MSG_RENDER_COMPLETE)
        
        # Hide progress UI
        self.controls.progress_frame.pack_forget()
        self.controls.cancel_btn.pack_forget()
        
        from tkinter import messagebox
        result = messagebox.askyesno("Render Complete",
                                     f"Video saved to:\n{output_path}\n\nOpen in Finder?")
        if result:
            subprocess.run(['open', '-R', output_path])
    
    def _render_cancelled(self):
        """Handle cancelled render"""
        self.is_rendering = False
        self.cancel_render_flag = False
        self.controls.render_btn.config(state='normal')
        self.controls.preview_btn.config(state='normal')
        self.preview.set_info(MSG_RENDER_CANCELLED)
        
        # Hide progress UI
        self.controls.progress_frame.pack_forget()
        self.controls.cancel_btn.pack_forget()
        
        from tkinter import messagebox
        messagebox.showinfo("Cancelled", "Render was cancelled.")
    
    def _render_error(self, error_msg):
        """Handle render error"""
        self.is_rendering = False
        self.controls.render_btn.config(state='normal')
        self.controls.preview_btn.config(state='normal')
        self.preview.set_info(MSG_RENDER_FAILED)
        
        # Hide progress UI
        self.controls.progress_frame.pack_forget()
        self.controls.cancel_btn.pack_forget()
        
        from tkinter import messagebox
        messagebox.showerror("Render Error", f"Could not render video:\n{error_msg}")