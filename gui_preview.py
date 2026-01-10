"""
GUI Preview Panel
Manages the preview canvas and display
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from gui_config import *


class PreviewPanel:
    def __init__(self, parent):
        self.parent = parent
        self.preview_image = None
        self._create_panel()
    
    def _create_panel(self):
        """Create the preview panel"""
        preview_frame = ttk.LabelFrame(self.parent, text="Live Preview", padding="10")
        preview_frame.grid(row=0, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        # Canvas for preview
        self.canvas = tk.Canvas(preview_frame, bg='black', highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Info label
        self.info_label = ttk.Label(preview_frame, text=MSG_SELECT_AUDIO_FIRST, 
                                    foreground="gray")
        self.info_label.grid(row=1, column=0, pady=(10, 0))
    
    def set_info(self, message, color="black"):
        """Update the info label"""
        self.info_label.config(text=message, foreground=color)
    
    def display_image(self, img):
        """Display an image on the preview canvas"""
        if not img:
            return
        
        self.preview_image = img
        
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width < CANVAS_MIN_WIDTH:
            canvas_width = CANVAS_DEFAULT_WIDTH
            canvas_height = CANVAS_DEFAULT_HEIGHT
        
        # Calculate scaling to fit
        img_width, img_height = img.size
        scale = min(canvas_width / img_width, canvas_height / img_height)
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # Resize preview
        display_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(display_img)
        
        # Display on canvas
        self.canvas.delete("all")
        x = (canvas_width - new_width) // 2
        y = (canvas_height - new_height) // 2
        self.canvas.create_image(x, y, anchor=tk.NW, image=photo)
        self.canvas.image = photo  # Keep reference
    
    def clear(self):
        """Clear the preview canvas"""
        self.canvas.delete("all")
        self.preview_image = None