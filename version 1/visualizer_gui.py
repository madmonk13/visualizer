#!/usr/bin/env python3
"""
Music Visualizer GUI - macOS Desktop App
Provides live preview and interactive controls for the music visualizer
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import subprocess
import os
import sys

# Import the visualizer class
from visualizer import MusicVisualizer

class VisualizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Visualizer Studio")
        self.root.geometry("1200x800")
        
        # State
        self.audio_path = None
        self.cover_path = None
        self.visualizer = None
        self.preview_thread = None
        self.is_rendering = False
        self.cancel_render_flag = False
        self.preview_image = None
        
        # Create UI
        self.create_ui()
        
    def create_ui(self):
        """Create the main UI layout"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Left panel - Controls
        self.create_controls_panel(main_frame)
        
        # Right panel - Preview
        self.create_preview_panel(main_frame)
        
    def create_controls_panel(self, parent):
        """Create the left control panel with scrolling"""
        # Container for canvas and scrollbar
        scroll_container = ttk.Frame(parent)
        scroll_container.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        scroll_container.columnconfigure(0, weight=1)
        scroll_container.rowconfigure(0, weight=1)
        
        # Create a canvas with scrollbar for controls
        canvas = tk.Canvas(scroll_container, width=280, highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        
        # Create the actual controls frame inside the canvas
        controls_frame = ttk.Frame(canvas, padding="5")
        
        # Add controls frame to canvas
        canvas_window = canvas.create_window((0, 0), window=controls_frame, anchor="nw")
        
        # Configure canvas scrolling
        def configure_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Make sure canvas window is wide enough
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())
        
        def configure_canvas(event=None):
            canvas.itemconfig(canvas_window, width=event.width)
        
        controls_frame.bind("<Configure>", configure_scroll_region)
        canvas.bind("<Configure>", configure_canvas)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Store canvas reference for mousewheel binding
        self.controls_canvas = canvas
        
        # Enable mousewheel scrolling on macOS
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta)), "units")
        
        def bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        def unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind("<Enter>", bind_mousewheel)
        canvas.bind("<Leave>", unbind_mousewheel)
        
        # Grid the canvas and scrollbar
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # File Selection Section
        file_section = ttk.LabelFrame(controls_frame, text="Files", padding="10")
        file_section.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Audio file
        ttk.Label(file_section, text="Audio:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.audio_label = ttk.Label(file_section, text="No file selected", foreground="gray")
        self.audio_label.grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Button(file_section, text="Select Audio...", command=self.select_audio).grid(row=2, column=0, sticky=tk.W, pady=5)
        
        # Cover image
        ttk.Label(file_section, text="Cover Image (Optional):").grid(row=3, column=0, sticky=tk.W, pady=(10, 2))
        self.cover_label = ttk.Label(file_section, text="No cover selected", foreground="gray")
        self.cover_label.grid(row=4, column=0, sticky=tk.W, pady=2)
        
        cover_btn_frame = ttk.Frame(file_section)
        cover_btn_frame.grid(row=5, column=0, sticky=tk.W, pady=5)
        ttk.Button(cover_btn_frame, text="Select Cover...", command=self.select_cover).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(cover_btn_frame, text="Clear", command=self.clear_cover).pack(side=tk.LEFT)
        
        # Visual Settings Section
        visual_section = ttk.LabelFrame(controls_frame, text="Visual Settings", padding="10")
        visual_section.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Color Palette
        ttk.Label(visual_section, text="Color Palette:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.palette_var = tk.StringVar(value="rainbow")
        palette_combo = ttk.Combobox(visual_section, textvariable=self.palette_var, state="readonly", width=18)
        palette_combo['values'] = ('rainbow', 'spring', 'summer', 'autumn', 'winter', 'ice', 'fire', 'water', 'earth')
        palette_combo.grid(row=1, column=0, sticky=tk.W, pady=2)
        palette_combo.bind('<<ComboboxSelected>>', lambda e: self.update_preview())
        
        # Cover Shape
        ttk.Label(visual_section, text="Cover Shape:").grid(row=2, column=0, sticky=tk.W, pady=(10, 2))
        self.cover_shape_var = tk.StringVar(value="square")
        shape_frame = ttk.Frame(visual_section)
        shape_frame.grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Radiobutton(shape_frame, text="Square", variable=self.cover_shape_var, value="square", 
                       command=self.update_preview).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(shape_frame, text="Round", variable=self.cover_shape_var, value="round",
                       command=self.update_preview).pack(side=tk.LEFT)
        
        # Cover Size
        ttk.Label(visual_section, text="Cover Size:").grid(row=4, column=0, sticky=tk.W, pady=(10, 2))
        self.cover_size_var = tk.DoubleVar(value=1.0)
        cover_size_frame = ttk.Frame(visual_section)
        cover_size_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=2)
        cover_size_slider = ttk.Scale(cover_size_frame, from_=0.5, to=2.0, variable=self.cover_size_var, 
                                     orient=tk.HORIZONTAL, command=lambda v: self.update_preview())
        cover_size_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.cover_size_label = ttk.Label(cover_size_frame, text="1.0x", width=5)
        self.cover_size_label.pack(side=tk.LEFT)
        self.cover_size_var.trace_add('write', lambda *args: self.cover_size_label.config(text=f"{self.cover_size_var.get():.1f}x"))
        
        # Rotation Settings Section
        rotation_section = ttk.LabelFrame(controls_frame, text="Rotation Effects", padding="10")
        rotation_section.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Waveform Rotation
        ttk.Label(rotation_section, text="Waveform Rotation:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.waveform_rot_var = tk.StringVar(value="z")
        wf_rot_combo = ttk.Combobox(rotation_section, textvariable=self.waveform_rot_var, state="readonly", width=18)
        wf_rot_combo['values'] = ('none - No Rotation', 'z - Standard Spin', 'x - Horizontal Flip', 'y - Vertical Tilt')
        wf_rot_combo.current(1)
        wf_rot_combo.grid(row=1, column=0, sticky=tk.W, pady=2)
        wf_rot_combo.bind('<<ComboboxSelected>>', lambda e: self.update_preview())
        
        # Ring Rotation
        ttk.Label(rotation_section, text="Ring Rotation:").grid(row=2, column=0, sticky=tk.W, pady=(10, 2))
        self.ring_rot_var = tk.StringVar(value="z")
        ring_rot_combo = ttk.Combobox(rotation_section, textvariable=self.ring_rot_var, state="readonly", width=18)
        ring_rot_combo['values'] = ('none - No Rotation', 'z - No Rotation', 'x - Horizontal Squeeze', 'y - Vertical Squeeze')
        ring_rot_combo.current(0)
        ring_rot_combo.grid(row=3, column=0, sticky=tk.W, pady=2)
        ring_rot_combo.bind('<<ComboboxSelected>>', lambda e: self.update_preview())
        
        # Ring Shape
        ttk.Label(rotation_section, text="Ring Shape:").grid(row=4, column=0, sticky=tk.W, pady=(10, 2))
        self.ring_shape_var = tk.StringVar(value="circle")
        ring_shape_frame = ttk.Frame(rotation_section)
        ring_shape_frame.grid(row=5, column=0, sticky=tk.W, pady=2)
        ttk.Radiobutton(ring_shape_frame, text="Circle", variable=self.ring_shape_var, value="circle", 
                       command=self.update_preview).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(ring_shape_frame, text="Square", variable=self.ring_shape_var, value="square",
                       command=self.update_preview).pack(side=tk.LEFT)
        
        # Starfield Rotation
        ttk.Label(rotation_section, text="Starfield Rotation:").grid(row=6, column=0, sticky=tk.W, pady=(10, 2))
        self.starfield_rot_var = tk.StringVar(value="none")
        star_rot_combo = ttk.Combobox(rotation_section, textvariable=self.starfield_rot_var, state="readonly", width=18)
        star_rot_combo['values'] = ('none - Outward Only', 'cw - Clockwise Spiral', 'ccw - Counter-Clockwise')
        star_rot_combo.current(0)
        star_rot_combo.grid(row=7, column=0, sticky=tk.W, pady=2)
        star_rot_combo.bind('<<ComboboxSelected>>', lambda e: self.update_preview())
        
        # Effects Toggles
        effects_section = ttk.LabelFrame(controls_frame, text="Effects", padding="10")
        effects_section.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.rings_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(effects_section, text="Show Rings", variable=self.rings_enabled_var,
                       command=self.update_preview).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.starfield_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(effects_section, text="Show Starfield", variable=self.starfield_enabled_var,
                       command=self.update_preview).grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # Text Overlay Section
        text_section = ttk.LabelFrame(controls_frame, text="Text Overlay", padding="10")
        text_section.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(text_section, text="Text (Optional):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.text_var = tk.StringVar()
        text_entry = ttk.Entry(text_section, textvariable=self.text_var, width=25)
        text_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        text_entry.bind('<KeyRelease>', lambda e: self.update_preview())
        
        # Output Settings Section
        output_section = ttk.LabelFrame(controls_frame, text="Output Settings", padding="10")
        output_section.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Resolution
        ttk.Label(output_section, text="Resolution:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.resolution_var = tk.StringVar(value="1280x720")
        res_combo = ttk.Combobox(output_section, textvariable=self.resolution_var, state="readonly", width=18)
        res_combo['values'] = ('1280x720 - HD', '1920x1080 - Full HD', '1080x1920 - Phone Vertical', '1920x1080 - Phone Horizontal')
        res_combo.current(0)
        res_combo.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # FPS
        ttk.Label(output_section, text="Frame Rate:").grid(row=2, column=0, sticky=tk.W, pady=(10, 2))
        self.fps_var = tk.IntVar(value=30)
        fps_combo = ttk.Combobox(output_section, textvariable=self.fps_var, state="readonly", width=18)
        fps_combo['values'] = ('15', '30', '60')
        fps_combo.current(1)
        fps_combo.grid(row=3, column=0, sticky=tk.W, pady=2)
        
        # Action Buttons
        button_frame = ttk.Frame(controls_frame)
        button_frame.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.preview_btn = ttk.Button(button_frame, text="Update Preview", command=self.update_preview)
        self.preview_btn.pack(fill=tk.X, pady=(0, 5))
        
        self.render_btn = ttk.Button(button_frame, text="Render Full Video", command=self.render_video, style="Accent.TButton")
        self.render_btn.pack(fill=tk.X, pady=(0, 5))
        
        # Progress bar (hidden by default)
        self.progress_frame = ttk.Frame(button_frame)
        self.progress_label = ttk.Label(self.progress_frame, text="", font=('TkDefaultFont', 9))
        self.progress_label.pack(fill=tk.X, pady=(0, 2))
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate', maximum=100)
        self.progress_bar.pack(fill=tk.X)
        
        self.cancel_btn = ttk.Button(button_frame, text="Cancel Render", command=self.cancel_render)
        self.cancel_btn.pack(fill=tk.X, pady=(5, 0))
        
    def create_preview_panel(self, parent):
        """Create the right preview panel"""
        preview_frame = ttk.LabelFrame(parent, text="Live Preview", padding="10")
        preview_frame.grid(row=0, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        # Canvas for preview
        self.preview_canvas = tk.Canvas(preview_frame, bg='black', highlightthickness=0)
        self.preview_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Info label
        self.info_label = ttk.Label(preview_frame, text="Select an audio file to begin", foreground="gray")
        self.info_label.grid(row=1, column=0, pady=(10, 0))
        
    def select_audio(self):
        """Open file dialog to select audio"""
        filename = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[
                ("Audio files", "*.mp3 *.wav *.m4a *.flac *.ogg"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.audio_path = filename
            self.audio_label.config(text=os.path.basename(filename), foreground="black")
            self.update_preview()
    
    def select_cover(self):
        """Open file dialog to select cover image"""
        filename = filedialog.askopenfilename(
            title="Select Cover Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.cover_path = filename
            self.cover_label.config(text=os.path.basename(filename), foreground="black")
            self.update_preview()
    
    def clear_cover(self):
        """Clear the cover image"""
        self.cover_path = None
        self.cover_label.config(text="No cover selected", foreground="gray")
        self.update_preview()
    
    def get_rotation_value(self, combo_value):
        """Extract rotation axis from combo box value"""
        return combo_value.split(' - ')[0]
    
    def update_preview(self):
        """Generate and display preview frame"""
        if not self.audio_path:
            return
        
        if self.preview_thread and self.preview_thread.is_alive():
            return  # Already generating preview
        
        self.info_label.config(text="Generating preview...")
        self.preview_btn.config(state='disabled')
        
        # Start preview generation in background thread
        self.preview_thread = threading.Thread(target=self._generate_preview, daemon=True)
        self.preview_thread.start()
    
    def _generate_preview(self):
        """Background thread to generate preview"""
        try:
            # Parse resolution
            res_str = self.resolution_var.get().split(' - ')[0]
            width, height = map(int, res_str.split('x'))
            
            # Create visualizer with preview settings
            visualizer = MusicVisualizer(
                audio_path=self.audio_path,
                cover_image_path=self.cover_path,
                fps=15,  # Low FPS for preview
                resolution=(width // 2, height // 2),  # Half resolution for speed
                text_overlay=self.text_var.get() or None,
                color_palette=self.palette_var.get(),
                waveform_rotation=self.get_rotation_value(self.waveform_rot_var.get()),
                ring_rotation=self.get_rotation_value(self.ring_rot_var.get()),
                starfield_rotation=self.get_rotation_value(self.starfield_rot_var.get()),
                preview_seconds=None,  # Just render one frame
                cover_shape=self.cover_shape_var.get(),
                cover_size=self.cover_size_var.get(),
                disable_rings=not self.rings_enabled_var.get(),
                disable_starfield=not self.starfield_enabled_var.get(),
                ring_shape=self.ring_shape_var.get()
            )
            
            # Render a frame from middle of song (most interesting)
            frame_idx = min(len(visualizer.times) // 2, len(visualizer.times) - 1)
            total_frames = len(visualizer.times)
            
            preview_img = visualizer.render_frame(frame_idx, total_frames)
            
            # Store for display in main thread
            self.preview_image = preview_img
            
            # Update UI in main thread
            self.root.after(0, self._display_preview)
            
        except Exception as error:
            error_msg = str(error)
            self.root.after(0, lambda msg=error_msg: self._preview_error(msg))
    
    def _display_preview(self):
        """Display the generated preview (called from main thread)"""
        if not self.preview_image:
            return
        
        # Resize to fit canvas
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()
        
        if canvas_width < 100:  # Canvas not yet sized
            canvas_width = 700
            canvas_height = 500
        
        # Calculate scaling to fit
        img_width, img_height = self.preview_image.size
        scale = min(canvas_width / img_width, canvas_height / img_height)
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # Resize preview
        display_img = self.preview_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(display_img)
        
        # Display on canvas
        self.preview_canvas.delete("all")
        x = (canvas_width - new_width) // 2
        y = (canvas_height - new_height) // 2
        self.preview_canvas.create_image(x, y, anchor=tk.NW, image=photo)
        self.preview_canvas.image = photo  # Keep reference
        
        self.info_label.config(text="Preview updated - Ready to render")
        self.preview_btn.config(state='normal')
    
    def _preview_error(self, error_msg):
        """Handle preview generation error"""
        self.info_label.config(text=f"Error: {error_msg}")
        self.preview_btn.config(state='normal')
        messagebox.showerror("Preview Error", f"Could not generate preview:\n{error_msg}")
    
    def render_video(self):
        """Render the full video"""
        if not self.audio_path:
            messagebox.showwarning("No Audio", "Please select an audio file first.")
            return
        
        if self.is_rendering:
            messagebox.showinfo("Rendering", "A video is already being rendered.")
            return
        
        # Ask for output location
        output_path = filedialog.asksaveasfilename(
            title="Save Video As",
            defaultextension=".mp4",
            filetypes=[("MP4 Video", "*.mp4"), ("All files", "*.*")]
        )
        
        if not output_path:
            return
        
        # Confirm before long render
        duration_estimate = "several minutes"
        if messagebox.askyesno("Confirm Render", 
                              f"This will render the full video, which may take {duration_estimate}.\n\nContinue?"):
            self.is_rendering = True
            self.cancel_render_flag = False
            self.render_btn.config(state='disabled')
            self.preview_btn.config(state='disabled')
            
            # Show progress UI
            self.progress_frame.pack(fill=tk.X, pady=(5, 0))
            self.cancel_btn.pack(fill=tk.X, pady=(5, 0))
            self.progress_bar['value'] = 0
            self.progress_label.config(text="Starting render...")
            self.info_label.config(text="Rendering full video... Please wait")
            
            # Start render in background
            render_thread = threading.Thread(
                target=self._render_video_background,
                args=(output_path,),
                daemon=True
            )
            render_thread.start()
    
    def cancel_render(self):
        """Cancel the current render"""
        if messagebox.askyesno("Cancel Render", "Are you sure you want to cancel the current render?"):
            self.cancel_render_flag = True
            self.progress_label.config(text="Cancelling...")
    
    def update_render_progress(self, current_frame, total_frames):
        """Update progress bar from render thread"""
        if self.cancel_render_flag:
            return False  # Signal to stop rendering
        
        progress = int((current_frame / total_frames) * 100)
        elapsed_time = current_frame / total_frames  # Rough estimate
        
        self.root.after(0, lambda: self.progress_bar.config(value=progress))
        self.root.after(0, lambda: self.progress_label.config(
            text=f"Rendering frame {current_frame}/{total_frames} ({progress}%)"
        ))
        
        return True  # Continue rendering
    
    def _render_video_background(self, output_path):
        """Background thread for rendering"""
        import tempfile
        
        try:
            # Parse resolution
            res_str = self.resolution_var.get().split(' - ')[0]
            width, height = map(int, res_str.split('x'))
            
            # Create visualizer
            visualizer = MusicVisualizer(
                audio_path=self.audio_path,
                output_path=output_path,
                cover_image_path=self.cover_path,
                fps=self.fps_var.get(),
                resolution=(width, height),
                text_overlay=self.text_var.get() or None,
                color_palette=self.palette_var.get(),
                waveform_rotation=self.get_rotation_value(self.waveform_rot_var.get()),
                ring_rotation=self.get_rotation_value(self.ring_rot_var.get()),
                starfield_rotation=self.get_rotation_value(self.starfield_rot_var.get()),
                preview_seconds=None,
                cover_shape=self.cover_shape_var.get(),
                cover_size=self.cover_size_var.get(),
                disable_rings=not self.rings_enabled_var.get(),
                disable_starfield=not self.starfield_enabled_var.get(),
                ring_shape=self.ring_shape_var.get()
            )
            
            # Calculate frames
            render_duration = visualizer.duration
            total_frames = int(render_duration * visualizer.fps)
            
            # Create temporary video without audio
            temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            temp_video_path = temp_video.name
            temp_video.close()
            
            # Setup video writer
            import cv2
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(temp_video_path, fourcc, visualizer.fps, 
                                 (visualizer.width, visualizer.height))
            
            # Render frames with progress updates
            for frame_idx in range(total_frames):
                # Check for cancellation
                if not self.update_render_progress(frame_idx + 1, total_frames):
                    out.release()
                    os.remove(temp_video_path)
                    self.root.after(0, self._render_cancelled)
                    return
                
                # Render frame
                img = visualizer.render_frame(frame_idx, total_frames)
                
                # Convert PIL to OpenCV format
                import numpy as np
                frame_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                
                # Write frame
                out.write(frame_cv)
            
            out.release()
            
            # Update progress for audio merge
            self.root.after(0, lambda: self.progress_label.config(text="Adding audio to video..."))
            
            # Merge video with audio using ffmpeg
            subprocess.run([
                'ffmpeg', '-i', temp_video_path, '-i', self.audio_path,
                '-c:v', 'libx264', '-c:a', 'aac', '-strict', 'experimental',
                '-shortest', '-y', output_path
            ], check=True, capture_output=True)
            
            # Clean up temp file
            os.remove(temp_video_path)
            
            # Success
            self.root.after(0, lambda: self._render_complete(output_path))
            
        except Exception as error:
            error_msg = str(error)
            self.root.after(0, lambda msg=error_msg: self._render_error(msg))
    
    def _render_complete(self, output_path):
        """Handle successful render"""
        self.is_rendering = False
        self.render_btn.config(state='normal')
        self.preview_btn.config(state='normal')
        self.info_label.config(text="Render complete!")
        
        # Hide progress UI
        self.progress_frame.pack_forget()
        self.cancel_btn.pack_forget()
        
        result = messagebox.askyesno("Render Complete", 
                                     f"Video saved to:\n{output_path}\n\nOpen in Finder?")
        if result:
            subprocess.run(['open', '-R', output_path])
    
    def _render_cancelled(self):
        """Handle cancelled render"""
        self.is_rendering = False
        self.cancel_render_flag = False
        self.render_btn.config(state='normal')
        self.preview_btn.config(state='normal')
        self.info_label.config(text="Render cancelled")
        
        # Hide progress UI
        self.progress_frame.pack_forget()
        self.cancel_btn.pack_forget()
        
        messagebox.showinfo("Cancelled", "Render was cancelled.")
    
    def _render_error(self, error_msg):
        """Handle render error"""
        self.is_rendering = False
        self.render_btn.config(state='normal')
        self.preview_btn.config(state='normal')
        self.info_label.config(text="Render failed")
        
        # Hide progress UI
        self.progress_frame.pack_forget()
        self.cancel_btn.pack_forget()
        
        messagebox.showerror("Render Error", f"Could not render video:\n{error_msg}")

def main():
    root = tk.Tk()
    
    # Set macOS style
    style = ttk.Style()
    style.theme_use('aqua')  # macOS native theme
    
    # Create app
    app = VisualizerGUI(root)
    
    # Run
    root.mainloop()

if __name__ == '__main__':
    main()