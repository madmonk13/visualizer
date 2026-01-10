"""
GUI Controls Panel
Creates and manages the left control panel with all settings
"""

import tkinter as tk
from tkinter import ttk
from gui_config import *


class ControlsPanel:
    def __init__(self, parent, callback_handler):
        self.parent = parent
        self.callback = callback_handler
        
        # Create variables for all controls
        self._create_variables()
        
        # Build the controls panel
        self.frame = self._create_scrollable_frame()
        self._build_controls()
    
    def _create_variables(self):
        """Initialize all tkinter variables"""
        # File paths (not tk variables)
        self.audio_path = None
        self.cover_path = None
        
        # Visual settings
        self.palette_var = tk.StringVar(value=DEFAULT_PALETTE)
        self.cover_shape_var = tk.StringVar(value=DEFAULT_COVER_SHAPE)
        self.cover_size_var = tk.DoubleVar(value=DEFAULT_COVER_SIZE)
        
        # Rotation settings
        self.waveform_rot_var = tk.StringVar(value=DEFAULT_WAVEFORM_ROTATION)
        self.ring_rot_var = tk.StringVar(value=DEFAULT_RING_ROTATION)
        self.ring_shape_var = tk.StringVar(value=DEFAULT_RING_SHAPE)
        self.starfield_rot_var = tk.StringVar(value=DEFAULT_STARFIELD_ROTATION)
        
        # Effects toggles
        self.rings_enabled_var = tk.BooleanVar(value=True)
        self.starfield_enabled_var = tk.BooleanVar(value=True)
        
        # Text and output
        self.text_var = tk.StringVar()
        self.resolution_var = tk.StringVar(value=DEFAULT_RESOLUTION)
        self.fps_var = tk.IntVar(value=DEFAULT_FPS)
    
    def _create_scrollable_frame(self):
        """Create scrollable container for controls"""
        scroll_container = ttk.Frame(self.parent)
        scroll_container.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        scroll_container.columnconfigure(0, weight=1)
        scroll_container.rowconfigure(0, weight=1)
        
        # Canvas and scrollbar
        canvas = tk.Canvas(scroll_container, width=CONTROLS_CANVAS_WIDTH, highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        
        # Controls frame
        controls_frame = ttk.Frame(canvas, padding=CONTROLS_PADDING)
        
        # Configure canvas
        canvas_window = canvas.create_window((0, 0), window=controls_frame, anchor="nw")
        
        def configure_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())
        
        def configure_canvas(event=None):
            canvas.itemconfig(canvas_window, width=event.width)
        
        controls_frame.bind("<Configure>", configure_scroll_region)
        canvas.bind("<Configure>", configure_canvas)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mousewheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta)), "units")
        
        def bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        def unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind("<Enter>", bind_mousewheel)
        canvas.bind("<Leave>", unbind_mousewheel)
        
        # Grid canvas and scrollbar
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        return controls_frame
    
    def _build_controls(self):
        """Build all control sections"""
        row = 0
        
        # File selection
        self._create_file_section(self.frame, row)
        row += 1
        
        # Visual settings
        self._create_visual_section(self.frame, row)
        row += 1
        
        # Rotation effects
        self._create_rotation_section(self.frame, row)
        row += 1
        
        # Effects toggles
        self._create_effects_section(self.frame, row)
        row += 1
        
        # Text overlay
        self._create_text_section(self.frame, row)
        row += 1
        
        # Output settings
        self._create_output_section(self.frame, row)
        row += 1
        
        # Action buttons and progress
        self._create_action_section(self.frame, row)
    
    def _create_file_section(self, parent, row):
        """Create file selection section"""
        section = ttk.LabelFrame(parent, text="Files", padding="10")
        section.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Audio file
        ttk.Label(section, text="Audio:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.audio_label = ttk.Label(section, text=MSG_NO_FILE_SELECTED, foreground="gray")
        self.audio_label.grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Button(section, text="Select Audio...", 
                  command=self.callback.select_audio).grid(row=2, column=0, sticky=tk.W, pady=5)
        
        # Cover image
        ttk.Label(section, text="Cover Image (Optional):").grid(row=3, column=0, sticky=tk.W, pady=(10, 2))
        self.cover_label = ttk.Label(section, text=MSG_NO_COVER_SELECTED, foreground="gray")
        self.cover_label.grid(row=4, column=0, sticky=tk.W, pady=2)
        
        cover_btn_frame = ttk.Frame(section)
        cover_btn_frame.grid(row=5, column=0, sticky=tk.W, pady=5)
        ttk.Button(cover_btn_frame, text="Select Cover...", 
                  command=self.callback.select_cover).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(cover_btn_frame, text="Clear", 
                  command=self.callback.clear_cover).pack(side=tk.LEFT)
    
    def _create_visual_section(self, parent, row):
        """Create visual settings section"""
        section = ttk.LabelFrame(parent, text="Visual Settings", padding="10")
        section.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Color palette
        ttk.Label(section, text="Color Palette:").grid(row=0, column=0, sticky=tk.W, pady=2)
        palette_combo = ttk.Combobox(section, textvariable=self.palette_var, 
                                     state="readonly", width=18)
        palette_combo['values'] = PALETTE_OPTIONS
        palette_combo.grid(row=1, column=0, sticky=tk.W, pady=2)
        palette_combo.bind('<<ComboboxSelected>>', 
                          lambda e: self.callback.update_preview())
        
        # Cover shape
        ttk.Label(section, text="Cover Shape:").grid(row=2, column=0, sticky=tk.W, pady=(10, 2))
        shape_frame = ttk.Frame(section)
        shape_frame.grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Radiobutton(shape_frame, text="Square", variable=self.cover_shape_var, 
                       value="square", command=self.callback.update_preview).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(shape_frame, text="Round", variable=self.cover_shape_var, 
                       value="round", command=self.callback.update_preview).pack(side=tk.LEFT)
        
        # Cover size
        ttk.Label(section, text="Cover Size:").grid(row=4, column=0, sticky=tk.W, pady=(10, 2))
        cover_size_frame = ttk.Frame(section)
        cover_size_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=2)
        cover_size_slider = ttk.Scale(cover_size_frame, from_=COVER_SIZE_MIN, to=COVER_SIZE_MAX, 
                                      variable=self.cover_size_var, orient=tk.HORIZONTAL,
                                      command=lambda v: self.callback.update_preview())
        cover_size_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.cover_size_label = ttk.Label(cover_size_frame, text="1.0x", width=5)
        self.cover_size_label.pack(side=tk.LEFT)
        self.cover_size_var.trace_add('write', 
                                      lambda *args: self.cover_size_label.config(
                                          text=f"{self.cover_size_var.get():.1f}x"))
    
    def _create_rotation_section(self, parent, row):
        """Create rotation effects section"""
        section = ttk.LabelFrame(parent, text="Rotation Effects", padding="10")
        section.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Waveform rotation
        ttk.Label(section, text="Waveform Rotation:").grid(row=0, column=0, sticky=tk.W, pady=2)
        wf_rot_combo = ttk.Combobox(section, textvariable=self.waveform_rot_var, 
                                    state="readonly", width=18)
        wf_rot_combo['values'] = WAVEFORM_ROTATION_OPTIONS
        wf_rot_combo.current(1)
        wf_rot_combo.grid(row=1, column=0, sticky=tk.W, pady=2)
        wf_rot_combo.bind('<<ComboboxSelected>>', lambda e: self.callback.update_preview())
        
        # Ring rotation
        ttk.Label(section, text="Ring Rotation:").grid(row=2, column=0, sticky=tk.W, pady=(10, 2))
        ring_rot_combo = ttk.Combobox(section, textvariable=self.ring_rot_var, 
                                      state="readonly", width=18)
        ring_rot_combo['values'] = RING_ROTATION_OPTIONS
        ring_rot_combo.current(0)
        ring_rot_combo.grid(row=3, column=0, sticky=tk.W, pady=2)
        ring_rot_combo.bind('<<ComboboxSelected>>', lambda e: self.callback.update_preview())
        
        # Ring shape
        ttk.Label(section, text="Ring Shape:").grid(row=4, column=0, sticky=tk.W, pady=(10, 2))
        ring_shape_frame = ttk.Frame(section)
        ring_shape_frame.grid(row=5, column=0, sticky=tk.W, pady=2)
        ttk.Radiobutton(ring_shape_frame, text="Circle", variable=self.ring_shape_var, 
                       value="circle", command=self.callback.update_preview).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(ring_shape_frame, text="Square", variable=self.ring_shape_var, 
                       value="square", command=self.callback.update_preview).pack(side=tk.LEFT)
        
        # Starfield rotation
        ttk.Label(section, text="Starfield Rotation:").grid(row=6, column=0, sticky=tk.W, pady=(10, 2))
        star_rot_combo = ttk.Combobox(section, textvariable=self.starfield_rot_var, 
                                      state="readonly", width=18)
        star_rot_combo['values'] = STARFIELD_ROTATION_OPTIONS
        star_rot_combo.current(0)
        star_rot_combo.grid(row=7, column=0, sticky=tk.W, pady=2)
        star_rot_combo.bind('<<ComboboxSelected>>', lambda e: self.callback.update_preview())
    
    def _create_effects_section(self, parent, row):
        """Create effects toggles section"""
        section = ttk.LabelFrame(parent, text="Effects", padding="10")
        section.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Checkbutton(section, text="Show Rings", variable=self.rings_enabled_var,
                       command=self.callback.update_preview).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        ttk.Checkbutton(section, text="Show Starfield", variable=self.starfield_enabled_var,
                       command=self.callback.update_preview).grid(row=1, column=0, sticky=tk.W, pady=2)
    
    def _create_text_section(self, parent, row):
        """Create text overlay section"""
        section = ttk.LabelFrame(parent, text="Text Overlay", padding="10")
        section.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(section, text="Text (Optional):").grid(row=0, column=0, sticky=tk.W, pady=2)
        text_entry = ttk.Entry(section, textvariable=self.text_var, width=25)
        text_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        text_entry.bind('<KeyRelease>', lambda e: self.callback.update_preview())
    
    def _create_output_section(self, parent, row):
        """Create output settings section"""
        section = ttk.LabelFrame(parent, text="Output Settings", padding="10")
        section.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Resolution
        ttk.Label(section, text="Resolution:").grid(row=0, column=0, sticky=tk.W, pady=2)
        res_combo = ttk.Combobox(section, textvariable=self.resolution_var, 
                                state="readonly", width=18)
        res_combo['values'] = RESOLUTION_OPTIONS
        res_combo.current(0)
        res_combo.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # FPS
        ttk.Label(section, text="Frame Rate:").grid(row=2, column=0, sticky=tk.W, pady=(10, 2))
        fps_combo = ttk.Combobox(section, textvariable=self.fps_var, 
                                state="readonly", width=18)
        fps_combo['values'] = FPS_OPTIONS
        fps_combo.current(1)
        fps_combo.grid(row=3, column=0, sticky=tk.W, pady=2)
    
    def _create_action_section(self, parent, row):
        """Create action buttons and progress section"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.preview_btn = ttk.Button(button_frame, text="Update Preview", 
                                      command=self.callback.update_preview)
        self.preview_btn.pack(fill=tk.X, pady=(0, 5))
        
        self.render_btn = ttk.Button(button_frame, text="Render Full Video", 
                                     command=self.callback.render_video)
        self.render_btn.pack(fill=tk.X, pady=(0, 5))
        
        # Progress section (hidden by default)
        self.progress_frame = ttk.Frame(button_frame)
        self.progress_label = ttk.Label(self.progress_frame, text="", 
                                       font=('TkDefaultFont', 9))
        self.progress_label.pack(fill=tk.X, pady=(0, 2))
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate', 
                                           maximum=100)
        self.progress_bar.pack(fill=tk.X)
        
        self.cancel_btn = ttk.Button(button_frame, text="Cancel Render", 
                                     command=self.callback.cancel_render)
    
    def get_rotation_value(self, combo_value):
        """Extract rotation axis from combo box value"""
        return combo_value.split(' - ')[0]
    
    def get_settings(self):
        """Return all current settings as a dictionary"""
        # Parse resolution
        res_str = self.resolution_var.get().split(' - ')[0]
        width, height = map(int, res_str.split('x'))
        
        return {
            'audio_path': self.audio_path,
            'cover_image_path': self.cover_path,
            'resolution': (width, height),
            'fps': self.fps_var.get(),
            'text_overlay': self.text_var.get() or None,
            'color_palette': self.palette_var.get(),
            'waveform_rotation': self.get_rotation_value(self.waveform_rot_var.get()),
            'ring_rotation': self.get_rotation_value(self.ring_rot_var.get()),
            'starfield_rotation': self.get_rotation_value(self.starfield_rot_var.get()),
            'cover_shape': self.cover_shape_var.get(),
            'cover_size': self.cover_size_var.get(),
            'disable_rings': not self.rings_enabled_var.get(),
            'disable_starfield': not self.starfield_enabled_var.get(),
            'ring_shape': self.ring_shape_var.get()
        }