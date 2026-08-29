import tkinter as tk
import time
import math
import random
import os
import sys
from PIL import Image, ImageTk

class DesktopTrainer:
    def __init__(self, engine, trainer_type="boy", spawn_from_side=False):
        self.engine = engine
        self.trainer_type = trainer_type
        
        self.window = tk.Toplevel(self.engine.root)
        self.window.title(f"DesktopTrainer_{trainer_type}")
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        
        TRANS_COLOR = '#010101'
        self.window.config(bg=TRANS_COLOR)
        try:
            self.window.wm_attributes('-transparentcolor', TRANS_COLOR)
        except:
            pass
            
        # Increase size by 1.3 times relative to 72x72 height
        self.size_h = int(72 * 1.3)
        # Maintain 27:25 aspect ratio (width is slightly larger)
        self.size_w = int(self.size_h * (27 / 25.0))
        self.canvas = tk.Canvas(self.window, width=self.size_w, height=self.size_h, bg=TRANS_COLOR, highlightthickness=0)
        self.canvas.pack()
        
        # Determine base directory for sprites
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.base_dir = base_dir
        self.sprites_dir = os.path.join(base_dir, "game_env", f"trainer_sprites_{self.trainer_type}")
        
        def load_and_scale(path):
            img = Image.open(path).convert("RGBA")
            img = img.resize((self.size_w, self.size_h), Image.Resampling.NEAREST)
            return ImageTk.PhotoImage(img)

        self.images = {
            "front": load_and_scale(os.path.join(self.sprites_dir, "trainer_front_00.png")),
            "left": [load_and_scale(os.path.join(self.sprites_dir, f"trainer_left_0{i}.png")) for i in range(4)],
            "right": [load_and_scale(os.path.join(self.sprites_dir, f"trainer_right_0{i}.png")) for i in range(4)]
        }
        
        self.canvas_image_id = self.canvas.create_image(self.size_w//2, self.size_h//2, image=self.images["front"])
        
        # Default environment calculation (similar to pet)
        self.offset_y = 40  # Push down to fix floating
        import ctypes
        user32 = ctypes.windll.user32
        self.v_x = user32.GetSystemMetrics(76)
        self.v_y = user32.GetSystemMetrics(77)
        self.v_width = user32.GetSystemMetrics(78)
        self.v_height = user32.GetSystemMetrics(79)
        
        self.default_floor_y = self.v_y + self.v_height - 40 - self.size_h + self.offset_y
        try:
            import win32gui
            taskbar_handle = win32gui.FindWindow("Shell_TrayWnd", None)
            if taskbar_handle:
                rect = win32gui.GetWindowRect(taskbar_handle)
                taskbar_y = rect[1]
                self.default_floor_y = taskbar_y - self.size_h + self.offset_y
        except:
            pass
        
        self.y = self.default_floor_y
        
        if spawn_from_side:
            if random.choice([True, False]):
                self.x = self.v_x - self.size_w - 50
            else:
                self.x = self.v_x + self.v_width + 50
            self.target_x = self.v_x + random.randint(100, self.v_width - 100 - self.size_w)
            self.is_moving = True
        else:
            self.x = self.v_x + random.randint(100, self.v_width - 100 - self.size_w)
            self.target_x = self.x
            self.is_moving = False
            
        self.window.geometry(f"{self.size_w}x{self.size_h}+{int(self.x)}+{int(self.y)}")
        self.frame_idx = 0
        self.running = True
        self.topmost_timer = 2000
        
        self.loop()
        
    def walk_away_and_destroy(self, callback=None):
        self.destroy_callback = callback
        if self.x > self.v_x + self.v_width / 2:
            self.target_x = self.v_x + self.v_width + 50
        else:
            self.target_x = self.v_x - self.size_w - 50
        self.is_moving = True

    def update_position(self):
        self.window.geometry(f"{self.size_w}x{self.size_h}+{int(self.x)}+{int(self.y)}")
        
    def loop(self):
        if not getattr(self, 'running', True): return
        
        self.topmost_timer -= 30
        if self.topmost_timer <= 0:
            try: self.window.attributes('-topmost', True)
            except: pass
            self.topmost_timer = 2000
            
        if not self.is_moving:
            if random.random() < 0.02:
                self.target_x = self.v_x + random.randint(50, self.v_width - 50 - self.size_w)
                self.is_moving = True
            else:
                self.canvas.itemconfig(self.canvas_image_id, image=self.images["front"])
        else:
            dist = self.target_x - self.x
            if abs(dist) < 5:
                if hasattr(self, 'destroy_callback'):
                    cb = self.destroy_callback
                    self.destroy()
                    if cb: cb()
                    return
                self.is_moving = False
                self.canvas.itemconfig(self.canvas_image_id, image=self.images["front"])
            else:
                speed = 4.4
                if dist > 0:
                    self.x += speed
                    self.frame_idx = (self.frame_idx + 1) % 40
                    img = self.images["right"][self.frame_idx // 10]
                else:
                    self.x -= speed
                    self.frame_idx = (self.frame_idx + 1) % 40
                    img = self.images["left"][self.frame_idx // 10]
                self.canvas.itemconfig(self.canvas_image_id, image=img)
                
        self.update_position()
        self.window.after(30, self.loop)
        
    def spawn_pokeball_to(self, target_x, target_y, callback=None):
        ball_win = tk.Toplevel(self.window.master)
        ball_win.title("Trainer_Pokeball")
        ball_win.overrideredirect(True)
        ball_win.attributes('-topmost', True)
        
        TRANS_COLOR = '#010101'
        ball_win.config(bg=TRANS_COLOR)
        try: ball_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass
        
        b_size = 48
        b_canvas = tk.Canvas(ball_win, width=b_size, height=b_size, bg=TRANS_COLOR, highlightthickness=0)
        b_canvas.pack()
        
        # Load real pokeball image
        try:
            pb_dir = os.path.join(self.base_dir, "game_env", "ui")
            available_pbs = [f for f in os.listdir(pb_dir) if f.startswith("pokeball") and f.endswith(".png")]
            pb_file = random.choice(available_pbs) if available_pbs else "pokeball.png"
            raw_img = Image.open(os.path.join(pb_dir, pb_file)).convert("RGBA")
            r, g, b, a = raw_img.split()
            a = a.point(lambda p: 255 if p > 127 else 0) 
            pb_raw = Image.merge("RGBA", (r, g, b, a))
        except:
            pb_raw = None
            pb_file = None

        # Center start position at trainer
        start_x = self.x + self.size_w/2
        start_y = self.y + self.size_h/2
        
        frames = 30
        dx = (target_x - start_x)
        dy = (target_y - start_y)
        
        # Parabolic arc
        def animate_ball(step=0):
            if step <= frames:
                progress = step / frames
                
                arc_height = 150
                parabola = -arc_height * (1 - (2 * progress - 1)**2)
                
                cx = start_x + dx * progress - b_size/2
                cy = start_y + dy * progress + parabola - b_size/2
                
                ball_win.geometry(f"{b_size}x{b_size}+{int(cx)}+{int(cy)}")
                
                if pb_raw:
                    rotation = 360 * progress * 2 
                    rotated = pb_raw.rotate(rotation, expand=False, resample=Image.NEAREST)
                    tk_img = ImageTk.PhotoImage(rotated.resize((b_size, b_size), Image.Resampling.NEAREST))
                    b_canvas.delete("all")
                    b_canvas.create_image(b_size//2, b_size//2, image=tk_img)
                    b_canvas.image = tk_img 
                
                ball_win.after(30, lambda: animate_ball(step + 1))
            else:
                ball_win.destroy()
                if callback:
                    callback(pb_file)
                    
        animate_ball(0)

    def destroy(self):
        self.running = False
        try:
            self.window.destroy()
        except:
            pass
