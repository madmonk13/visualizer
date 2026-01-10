#!/usr/bin/env python3
"""
Music Visualizer GUI - Main Application
Provides live preview and interactive controls for the music visualizer
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import GUI modules
try:
    from gui_config import (
        WINDOW_TITLE, WINDOW_SIZE, AUDIO_FILETYPES, 
        IMAGE_FILETYPES, VIDEO_FILETYPES, MSG_NO_COVER_SELECTED
    )
    from gui_controls import ControlsPanel
    from gui_preview import PreviewPanel
    from gui_renderer import RenderManager
except ImportError as e:
    print("=" * 60)
    print("ERROR: Could not import required modules")
    print("=" * 60)
    print(f"Error: {e}")
    print(f"\nCurrent directory: {os.getcwd()}")
    print(f"Script directory: {current_dir}")
    print(f"\nFiles in script directory:")
    for f in sorted(os.listdir(current_dir)):
        if f.endswith('.py'):
            print(f"  - {f}")
    print("\nMake sure these files exist in the same directory:")
    print("  - gui_config.py")
    print("  - gui_controls.py")
    print("  - gui_preview.py")
    print("  - gui_renderer.py")
    print("  - visualizer.py")
    print("  - config.py")
    print("  - audio_processor.py")
    print("  - effects.py")
    print("  - beat_detector.py")
    print("=" * 60)
    sys.exit(1)


class VisualizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        
        # Create main UI
        self._create_ui()
        
        # Initialize render manager (after panels are created)
        self.render_manager = RenderManager(self.root, self.controls, self.preview)
    
    def _create_ui(self):
        """Create the main UI layout"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Create panels
        self.controls = ControlsPanel(main_frame, self)
        self.preview = PreviewPanel(main_frame)
    
    # Callback methods for controls panel
    def select_audio(self):
        """Open file dialog to select audio"""
        filename = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=AUDIO_FILETYPES
        )
        if filename:
            self.controls.audio_path = filename
            self.controls.audio_label.config(text=os.path.basename(filename), 
                                            foreground="black")
            self.update_preview()
    
    def select_cover(self):
        """Open file dialog to select cover image"""
        filename = filedialog.askopenfilename(
            title="Select Cover Image",
            filetypes=IMAGE_FILETYPES
        )
        if filename:
            self.controls.cover_path = filename
            self.controls.cover_label.config(text=os.path.basename(filename), 
                                            foreground="black")
            self.update_preview()
    
    def clear_cover(self):
        """Clear the cover image"""
        self.controls.cover_path = None
        self.controls.cover_label.config(text=MSG_NO_COVER_SELECTED, 
                                        foreground="gray")
        self.update_preview()
    
    def update_preview(self):
        """Generate and display preview frame"""
        if not self.controls.audio_path:
            return
        
        self.render_manager.generate_preview()
    
    def render_video(self):
        """Render the full video"""
        if not self.controls.audio_path:
            messagebox.showwarning("No Audio", "Please select an audio file first.")
            return
        
        if self.render_manager.is_rendering:
            messagebox.showinfo("Rendering", "A video is already being rendered.")
            return
        
        # Ask for output location
        output_path = filedialog.asksaveasfilename(
            title="Save Video As",
            defaultextension=".mp4",
            filetypes=VIDEO_FILETYPES
        )
        
        if not output_path:
            return
        
        # Confirm before rendering
        duration_estimate = "several minutes"
        if messagebox.askyesno("Confirm Render",
                              f"This will render the full video, which may take {duration_estimate}.\n\nContinue?"):
            self.render_manager.start_render(output_path)
    
    def cancel_render(self):
        """Cancel the current render"""
        self.render_manager.cancel_render()


def main():
    """Main entry point"""
    root = tk.Tk()
    
    # Set macOS style
    style = ttk.Style()
    try:
        style.theme_use('aqua')  # macOS native theme
    except:
        pass  # Fall back to default theme on other platforms
    
    # Create and run app
    try:
        app = VisualizerGUI(root)
        root.mainloop()
    except Exception as e:
        print("=" * 60)
        print("ERROR: Failed to start GUI")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()