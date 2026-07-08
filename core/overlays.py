import tkinter as tk
import random
import time
import math
try:
    import win32gui
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

class FloodOverlay:
    def __init__(self, parent_root, v_x, v_y, v_width, v_height):
        self.window = tk.Toplevel(parent_root)
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        
        CHROMA_KEY = '#00FF00'
        self.window.config(bg=CHROMA_KEY)
        
        try: 
            self.window.wm_attributes('-transparentcolor', CHROMA_KEY)
            self.window.wm_attributes('-alpha', 0.25) 
        except tk.TclError: pass

        self.v_x = v_x
        self.v_y = v_y
        self.v_width = v_width
        self.v_height = v_height
        
        self.flood_h = int(v_height * 0.12) 
        self.current_flood_h = 0.0 
        
        self.window.geometry(f"{v_width}x{v_height}+{int(v_x)}+{int(v_y)}")

        self.canvas = tk.Canvas(self.window, width=v_width, height=v_height, bg=CHROMA_KEY, highlightthickness=0)
        self.canvas.pack()

        self.active = True
        self.is_draining = False 
        
        self.wave_resolution = 120 
        self.blocks_count = (v_width // self.wave_resolution) + 2
        
        self.rects_bg = []
        self.rects_fg = []
        for i in range(self.blocks_count):
            x = i * self.wave_resolution
            rbg = self.canvas.create_rectangle(x, v_height, x + self.wave_resolution, v_height, fill="#1B4F72", outline="", tags="wave")
            rfg = self.canvas.create_rectangle(x, v_height, x + self.wave_resolution, v_height, fill="#2980B9", outline="", tags="wave")
            self.rects_bg.append(rbg)
            self.rects_fg.append(rfg)

        self.rain_pool = []
        colors = ["#3498DB", "#5DADE2", "#85C1E9"]
        for _ in range(12): 
            pid = self.canvas.create_line(-100, -100, -100, -100, fill=random.choice(colors), width=3, tags="global_rain")
            self.rain_pool.append({'id': pid, 'active': False, 'x': -100, 'y': -100, 'length': random.randint(20, 35)})

        # STRUCTURAL FIX (Race Condition): 
        # Wait 100ms for Tkinter to finish creating the physical window.
        # Then inject Click-Through permissions directly to the OS.
        self.window.after(100, self._apply_click_through)
        
        self.animate_environment()

    def _apply_click_through(self):
        if HAS_WIN32 and self.active:
            try:
                # Get the real "Parent ID" of the OS window, not the internal Tkinter container
                hwnd = win32gui.GetParent(self.window.winfo_id())
                if not hwnd:
                    hwnd = int(self.window.wm_frame())
                    
                ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED)
            except Exception as e:
                print(f"[!] Error forcing Click-Through: {e}")

    def animate_environment(self):
        if not self.active: return
        t = time.time() * 3.0

        if getattr(self, 'is_draining', False):
            self.current_flood_h -= 1.5
            if self.current_flood_h <= 0:
                self.destroy()
                return
        else:
            self.current_flood_h = min(self.flood_h, self.current_flood_h + 1.5)

        for i in range(self.blocks_count):
            x = i * self.wave_resolution
            
            offset_bg = int(math.sin(t * 0.8 + (x * 0.004)) * 8.0 + math.cos(t * 0.6 + (x * 0.008)) * 4.0)
            offset_fg = int(math.sin(t + (x * 0.005)) * 6.0)

            y_bg = self.v_height - self.current_flood_h + offset_bg
            y_fg = self.v_height - self.current_flood_h + offset_fg

            self.canvas.coords(self.rects_bg[i], x, y_bg, x + self.wave_resolution, self.v_height)
            self.canvas.coords(self.rects_fg[i], x, y_fg, x + self.wave_resolution, self.v_height)

        if not getattr(self, 'is_draining', False):
            spawns = random.randint(1, 2) 
            for p in self.rain_pool:
                if not p['active']:
                    p['active'] = True
                    p['x'] = random.randint(0, self.v_width + 500)
                    p['y'] = random.randint(-100, -20)
                    spawns -= 1
                    if spawns <= 0: break
                    
        for p in self.rain_pool:
            if p['active']:
                p['x'] -= 15.0
                p['y'] += 40.0
                self.canvas.coords(p['id'], p['x'], p['y'], p['x'] - p['length']*0.5, p['y'] + p['length']*1.5)
                
                if p['y'] > self.v_height + 50:
                    p['active'] = False
                    self.canvas.coords(p['id'], -100, -100, -100, -100)

        self.window.after(60, self.animate_environment)

    def destroy(self):
        self.active = False
        self.window.destroy()