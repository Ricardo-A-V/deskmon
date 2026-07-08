import tkinter as tk
import ctypes
import random
import os
import time
import math
from PIL import Image, ImageTk
try:
    import win32gui
    import win32process
    import win32con
    import win32api
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

# --- INTERACTIVE POKEBALL ---
class InteractivePokeball:
    def __init__(self, parent_root, base_dir, get_pets_callback, on_destroy_callback):
        self.window = tk.Toplevel(parent_root)
        self.window.title("Toy Pokeball")
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        
        CHROMA_KEY = '#00FF00'
        self.window.config(bg=CHROMA_KEY)
        try: self.window.wm_attributes('-transparentcolor', CHROMA_KEY)
        except tk.TclError: pass
        
        self.get_pets = get_pets_callback
        self.on_destroy = on_destroy_callback
        self.base_dir = base_dir
        
        self.size = 40
        self.offset_y = -6
        
        user32 = ctypes.windll.user32
        self.v_x = user32.GetSystemMetrics(76) 
        self.v_y = user32.GetSystemMetrics(77)
        self.v_width = user32.GetSystemMetrics(78)
        self.v_height = user32.GetSystemMetrics(79)
        
        self.default_floor_y = (self.v_y + self.v_height) - self.size - self.offset_y
        self.floor_y = self.default_floor_y
        
        self.x = random.randint(self.v_x, self.v_x + self.v_width - self.size)
        self.y = self.v_y - self.size
        self.v_x_velocity = 0.0
        self.v_y_velocity = 0.0
        
        self.current_state = 'falling'
        self.angle = 0
        
        self.canvas = tk.Canvas(self.window, width=self.size, height=self.size, bg=CHROMA_KEY, highlightthickness=0)
        self.canvas.pack()
        self.canvas_image_id = self.canvas.create_image(self.size//2, self.size//2, anchor=tk.CENTER)
        
        pb_dir = os.path.join(self.base_dir, "game_env", "ui")
        available_pbs = [f for f in os.listdir(pb_dir) if f.startswith("pokeball") and f.endswith(".png")]
        pb_file = random.choice(available_pbs) if available_pbs else "pokeball.png"
        
        try:
            raw_img = Image.open(os.path.join(pb_dir, pb_file)).convert("RGBA")
            r, g, b, a = raw_img.split()
            a = a.point(lambda p: 255 if p > 127 else 0)
            self.base_img = Image.merge("RGBA", (r, g, b, a)).resize((self.size, self.size), Image.Resampling.NEAREST)
            self.tk_image = ImageTk.PhotoImage(self.base_img)
            self.canvas.itemconfig(self.canvas_image_id, image=self.tk_image)
        except Exception as e:
            self.window.after(100, self.destroy)
            return
            
        self.window.geometry(f"{self.size}x{self.size}+{int(self.x)}+{int(self.y)}")
        
        self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self.on_drag_release)
        self.canvas.bind("<ButtonRelease-3>", lambda e: self.destroy())
        
        self.keep_on_top()
        self.animate_loop()
        self.physics_loop()

    def keep_on_top(self):
        if self.current_state != 'exiting':
            try: self.window.attributes('-topmost', True)
            except: pass
            self.window.after(2000, self.keep_on_top)

    def manage_tk_aura(self, canvas, w, h, is_active):
        if is_active:
            canvas.delete("tk_aura") 
            t = time.time()
            cx, cy = w / 2, h / 2
            base_radius = max(w, h) * 0.6
            
            # Swarm of 24 psychic particles generated mathematically in real time
            for i in range(24):
                # 1. Asymmetrical velocity (Some particles go fast, others slow, others in reverse)
                speed = 1.5 + (math.sin(i * 7.1) * 2.0)
                angle = (t * speed) + (i * 0.8)
                
                # 2. Radius dispersion (Breaks the circumference to create a chaotic cloud)
                scatter = math.cos(i * 13.3) * (base_radius * 0.5)
                r = base_radius + scatter
                
                px = cx + math.cos(angle) * r
                py = cy + math.sin(angle) * r
                
                # 3. Individual blink phase based on time
                blink_phase = math.sin(t * 12.0 + i * 3.14)
                
                if blink_phase > 0.5:
                    color = "#FFFFFF" # Intense white flash
                    size = 2
                elif blink_phase > -0.3:
                    color = "#D24DFF" # Base energy purple
                    size = 1
                else:
                    continue # Invisible particle (simulates turning off completely)
                
                canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color, tags="tk_aura")
                
            canvas.tag_lower("tk_aura") # Force the cloud behind the sprite
        else:
            canvas.delete("tk_aura")

    def destroy(self):
        self.current_state = 'exiting'
        if self.on_destroy:
            self.on_destroy()
        self.window.destroy()

    def update_position(self):
        self.window.geometry(f"+{int(self.x)}+{int(self.y)}")
        
    def on_drag_start(self, event):
        if self.current_state == 'exiting': return
        
        # FIX: Release the object from telekinesis and tell the Master to stop
        if self.current_state == 'tk_controlled':
            self.current_state = 'falling'
            self.manage_tk_aura(self.canvas, self.size, self.size, False)
            master = getattr(self, 'tk_master', None)
            if master and master.current_state == 'tk_channeling':
                master.current_state = 'idle'
                master.manage_tk_aura(master.canvas, master.size_w, master.size_h, False)
                master.tk_target = None
            self.tk_master = None
            
        self.drag_offset_x = event.x
        self.drag_offset_y = event.y
        self.drag_start_x = self.window.winfo_pointerx()
        self.drag_start_y = self.window.winfo_pointery()
        self.is_dragging = False

    def on_drag_motion(self, event):
        if self.current_state == 'exiting': return
        pointer_x = self.window.winfo_pointerx()
        pointer_y = self.window.winfo_pointery()

        if not getattr(self, 'is_dragging', False):
            if abs(pointer_x - getattr(self, 'drag_start_x', pointer_x)) > 5 or \
               abs(pointer_y - getattr(self, 'drag_start_y', pointer_y)) > 5:
                self.is_dragging = True
                self.current_state = 'dragged'
                self.v_x_velocity = 0.0
                self.v_y_velocity = 0.0
                self.last_drag_time = time.time()
                self.last_mouse_x = pointer_x
                self.last_mouse_y = pointer_y
            else:
                return

        self.x = pointer_x - self.drag_offset_x
        self.y = pointer_y - self.drag_offset_y
        self.update_position()

        current_time = time.time()
        dt = current_time - getattr(self, 'last_drag_time', current_time)
        if dt > 0:
            self.v_x_velocity = (pointer_x - self.last_mouse_x) / (dt * 150.0) 
            self.v_y_velocity = (pointer_y - self.last_mouse_y) / (dt * 150.0)
        
        self.last_mouse_x = pointer_x
        self.last_mouse_y = pointer_y
        self.last_drag_time = current_time

    def on_drag_release(self, event):
        if getattr(self, 'is_dragging', False):
            self.is_dragging = False
            self.anchored_hwnd = None
            
            v_x = getattr(self, 'v_x_velocity', 0.0)
            v_y = getattr(self, 'v_y_velocity', 0.0)
            
            if math.isnan(v_x) or math.isinf(v_x): v_x = 0.0
            if math.isnan(v_y) or math.isinf(v_y): v_y = 0.0

            self.v_x_velocity = max(-40.0, min(40.0, v_x))
            self.v_y_velocity = max(-40.0, min(40.0, v_y))
            
            self.current_state = 'thrown'

    def get_window_environment(self):
        current_env = {'y': self.default_floor_y, 'hwnd': None, 'rect': None}
        if not HAS_WIN32: return current_env
        
        center_x = self.x + self.size // 2
        bottom_y = self.y
        CURRENT_PID = os.getpid()
        valid_windows = []
        
        def win_enum_handler(hwnd, ctx):
            if not win32gui.IsWindowVisible(hwnd): return
            if win32gui.IsIconic(hwnd): return 
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pid == CURRENT_PID:
                    # FIX EXCEPTION: Allow collision with Bill's PC
                    title = win32gui.GetWindowText(hwnd)
                    if title != "Bill's PC":
                        return
            except: pass
            try:
                is_cloaked = ctypes.c_int(0)
                ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(is_cloaked), ctypes.sizeof(is_cloaked))
                if is_cloaked.value != 0: return
            except: pass
            try:
                ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                if ex_style & win32con.WS_EX_TRANSPARENT: return
            except: pass
            class_name = win32gui.GetClassName(hwnd)
            if class_name in ("Progman", "WorkerW", "Shell_TrayWnd", "EdgeUiInputTopWndClass", "DummyDWMWindow", "PopupHost"): return
            title = win32gui.GetWindowText(hwnd)
            if not title: return 
            rect = win32gui.GetWindowRect(hwnd)
            w_width = rect[2] - rect[0]
            w_height = rect[3] - rect[1]
            if w_width < 100 or w_height < 100: return
            
            placement = win32gui.GetWindowPlacement(hwnd) 
            is_fullscreen = False
            if placement[1] == win32con.SW_SHOWMAXIMIZED:
                is_fullscreen = True
            else:
                try:
                    monitor = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
                    mon_info = win32api.GetMonitorInfo(monitor)
                    mon_w = mon_info['Monitor'][2] - mon_info['Monitor'][0]
                    mon_h = mon_info['Monitor'][3] - mon_info['Monitor'][1]
                    if w_width >= mon_w - 10 and w_height >= mon_h - 10:
                        is_fullscreen = True
                except:
                    if w_width >= self.v_width and w_height >= (self.v_height - 10):
                        is_fullscreen = True
                        
            win_floor = rect[1] - self.size - self.offset_y
            valid_windows.append({'hwnd': hwnd, 'rect': rect, 'floor': win_floor, 'z': len(valid_windows), 'walkable': not is_fullscreen})
            
        win32gui.EnumWindows(win_enum_handler, None)
        
        under_windows = [w for w in valid_windows if w['walkable'] and w['rect'][0] <= center_x <= w['rect'][2] and w['floor'] >= bottom_y - 15]
        if under_windows:
            under_windows.sort(key=lambda w: w['floor'])
            for uw in under_windows:
                is_occluded = False
                check_y = uw['rect'][1] + 5
                for ow in valid_windows:
                    if ow['z'] < uw['z'] and ow['rect'][0] <= center_x <= ow['rect'][2] and ow['rect'][1] <= check_y <= ow['rect'][3]:
                        is_occluded = True
                        break
                if not is_occluded:
                    current_env['y'] = uw['floor']
                    current_env['hwnd'] = uw['hwnd']
                    current_env['rect'] = uw['rect']
                    break
        return current_env

    def animate_loop(self):
        if self.current_state == 'exiting': return
        
        if getattr(self, 'anchored_hwnd', None) and self.current_state == 'idle':
            try:
                if HAS_WIN32 and win32gui.IsWindowVisible(self.anchored_hwnd) and not win32gui.IsIconic(self.anchored_hwnd):
                    new_rect = win32gui.GetWindowRect(self.anchored_hwnd)
                    old_rect = getattr(self, 'anchored_rect', new_rect)
                    delta_x = new_rect[0] - old_rect[0]
                    delta_y = new_rect[1] - old_rect[1]
                    if delta_x != 0 or delta_y != 0:
                        self.x += delta_x
                        self.y += delta_y
                        self.floor_y += delta_y
                        self.x = max(self.v_x, min(self.x, (self.v_x + self.v_width) - self.size))
                        self.update_position()
                    self.anchored_rect = new_rect
                else:
                    self.anchored_hwnd = None
            except:
                self.anchored_hwnd = None

        if abs(self.v_x_velocity) > 0.5:
            self.angle = (self.angle - self.v_x_velocity * 4) % 360
            self.tk_image = ImageTk.PhotoImage(self.base_img.rotate(self.angle, resample=Image.NEAREST, expand=False))
            self.canvas.itemconfig(self.canvas_image_id, image=self.tk_image)
            
        self.window.after(16, self.animate_loop)

    def physics_loop(self):
        if self.current_state == 'exiting': return
        if self.current_state == 'dragged':
            self.window.after(30, self.physics_loop)
            return
        
        # FIX: Telekinetic Control for the Toy
        if self.current_state == 'tk_controlled':
            if not hasattr(self, 'tk_master') or not self.tk_master.window.winfo_exists() or self.tk_master.current_state != 'tk_channeling':
                self.current_state = 'falling'
                self.manage_tk_aura(self.canvas, self.size, self.size, False)
            self.window.after(30, self.physics_loop)
            return

        self.v_y_velocity += 0.99 
        self.v_x_velocity *= 0.99 
        
        self.y += self.v_y_velocity
        self.x += self.v_x_velocity

        if self.x <= self.v_x:
            self.x = self.v_x
            self.v_x_velocity *= -0.5 
        elif self.x >= (self.v_x + self.v_width) - self.size:
            self.x = (self.v_x + self.v_width) - self.size
            self.v_x_velocity *= -0.5

        if self.y <= self.v_y:
            self.y = self.v_y
            self.v_y_velocity *= -0.5 

        current_env = self.get_window_environment()
        if self.y <= current_env['y'] + 15:
            physical_floor = current_env['y']
            if current_env['hwnd']:
                if getattr(self, 'anchored_hwnd', None) != current_env['hwnd']:
                    self.anchored_hwnd = current_env['hwnd']
                    self.anchored_rect = current_env['rect']
        else:
            physical_floor = self.default_floor_y
            self.anchored_hwnd = None

        if self.y >= physical_floor and self.v_y_velocity > 0:
            self.y = physical_floor
            self.floor_y = physical_floor
            
            if self.v_y_velocity > 2.0:
                self.v_y_velocity *= -0.75 
                self.v_x_velocity *= 0.85 
            else:
                self.v_y_velocity = 0.0
                self.v_x_velocity *= 0.6
            
            if abs(self.v_x_velocity) < 0.5 and abs(self.v_y_velocity) < 0.5:
                self.current_state = 'idle'
                self.v_x_velocity = 0
                self.v_y_velocity = 0
        else:
            self.current_state = 'falling'

        if self.current_state != 'dragged':
            ball_cx = self.x + self.size/2
            ball_cy = self.y + self.size/2
            
            for p in self.get_pets():
                # FIX: The Pokeball now physically ignores eggs
                if p.current_state in ['falling_egg', 'falling_pokeball', 'exiting', 'dragged'] or getattr(p, 'is_egg', False): continue
                
                p_cx = p.x + p.size_w/2
                p_cy = p.y + p.size_h/2
                
                dx = ball_cx - p_cx
                dy = ball_cy - p_cy
                dist = math.sqrt(dx**2 + dy**2)
                
                min_dist = (self.size/2) + (p.size_w/2.5) 
                
                if dist < min_dist:
                    force_multiplier = (p.size_w / 64.0) * (p.speed * 1.5 if p.current_state == 'walking' else 1.0)
                    
                    # STRUCTURAL FIX: Prevent the toy ball from corrupting Dark type and Legendaries
                    if p.current_state.startswith('dark_'):
                        p.cancel_dark_arts()
                    elif p.current_state in ['lugia_channeling', 'lugia_dash']:
                        p.cancel_lugia_arts()

                    if p.current_state == 'walking':
                        push_dir = 1 if p.is_facing_right else -1
                        self.v_x_velocity = push_dir * force_multiplier * 2.7
                    else:
                        if dx != 0:
                            self.v_x_velocity = (dx/dist) * force_multiplier * 2.7
                        else:
                            self.v_x_velocity = random.choice([-1, 1]) * force_multiplier * 2.7
                            
                    self.v_y_velocity = -force_multiplier * 2.7 - 2.7
                    self.y -= 5 
                    self.current_state = 'thrown'
                    self.anchored_hwnd = None
                    break 
        
        self.update_position()
        self.window.after(30, self.physics_loop)


# --- INJECTION: CONSUMABLE BERRY ---
class InteractiveBerry(InteractivePokeball):
    def __init__(self, parent_root, base_dir, get_pets_callback, on_destroy_callback):
        self.window = tk.Toplevel(parent_root)
        self.window.title("Consumable Berry")
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        CHROMA_KEY = '#00FF00'
        self.window.config(bg=CHROMA_KEY)
        try: self.window.wm_attributes('-transparentcolor', CHROMA_KEY)
        except tk.TclError: pass
        self.get_pets = get_pets_callback
        self.on_destroy = on_destroy_callback
        self.base_dir = base_dir
        
        self.size_baya = 40 
        self.size = self.size_baya
        self.offset_y = -6
        user32 = ctypes.windll.user32
        self.v_x = user32.GetSystemMetrics(76) 
        self.v_y = user32.GetSystemMetrics(77)
        self.v_width = user32.GetSystemMetrics(78)
        self.v_height = user32.GetSystemMetrics(79)
        self.default_floor_y = (self.v_y + self.v_height) - self.size - self.offset_y
        self.floor_y = self.default_floor_y
        
        spawn_edge = random.choice(['left', 'right', 'top'])
        if spawn_edge == 'left':
            self.x = self.v_x - self.size
            self.y = random.randint(self.v_y, self.v_y + self.v_height // 2)
            self.v_x_velocity = random.uniform(40.0, 60.0) 
            self.v_y_velocity = random.uniform(-10.0, -5.0)
        elif spawn_edge == 'right':
            self.x = self.v_x + self.v_width + self.size
            self.y = random.randint(self.v_y, self.v_y + self.v_height // 2)
            self.v_x_velocity = random.uniform(-60.0, -40.0) 
            self.v_y_velocity = random.uniform(-10.0, -5.0)
        else:
            self.x = random.randint(self.v_x, self.v_x + self.v_width - self.size)
            self.y = self.v_y - self.size
            self.v_x_velocity = random.uniform(-15.0, 15.0)
            self.v_y_velocity = 5.0
            
        self.current_state = 'thrown'
        self.angle = 0
        self.canvas = tk.Canvas(self.window, width=self.size, height=self.size, bg=CHROMA_KEY, highlightthickness=0)
        self.canvas.pack()
        self.canvas_image_id = self.canvas.create_image(self.size//2, self.size//2, anchor=tk.CENTER)
        
        pb_dir = os.path.join(self.base_dir, "game_env", "ui")
        available_berries = [f for f in os.listdir(pb_dir) if f.lower().endswith("berry.png")]
        if not available_berries: available_berries = [f for f in os.listdir(pb_dir) if f.startswith("pokeball") and f.endswith(".png")]
        pb_file = random.choice(available_berries) if available_berries else "pokeball.png"
        
        try:
            raw_img = Image.open(os.path.join(pb_dir, pb_file)).convert("RGBA")
            r, g, b, a = raw_img.split()
            a = a.point(lambda p: 255 if p > 127 else 0)
            self.base_img = Image.merge("RGBA", (r, g, b, a)).resize((self.size, self.size), Image.Resampling.NEAREST)
            self.tk_image = ImageTk.PhotoImage(self.base_img)
            self.canvas.itemconfig(self.canvas_image_id, image=self.tk_image)
        except:
            self.window.after(100, self.destroy)
            return
            
        self.window.geometry(f"{self.size}x{self.size}+{int(self.x)}+{int(self.y)}")
        self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self.on_drag_release)
        self.canvas.bind("<ButtonRelease-3>", lambda e: self.destroy())
        self.keep_on_top()
        self.animate_loop()
        self.physics_loop()

    def physics_loop(self):
        if self.current_state == 'exiting': return
        if self.current_state == 'dragged':
            self.window.after(30, self.physics_loop)
            return

        # FIX: Telekinetic Control for the Berry
        if self.current_state == 'tk_controlled':
            if not hasattr(self, 'tk_master') or not self.tk_master.window.winfo_exists() or self.tk_master.current_state != 'tk_channeling':
                self.current_state = 'falling'
                self.manage_tk_aura(self.canvas, self.size, self.size, False)
            self.window.after(30, self.physics_loop)
            return

        self.v_y_velocity += 0.8 
        self.v_x_velocity *= 0.99 
        self.y += self.v_y_velocity
        self.x += self.v_x_velocity

        if self.x <= self.v_x:
            self.x = self.v_x
            self.v_x_velocity *= -0.5 
        elif self.x >= (self.v_x + self.v_width) - self.size:
            self.x = (self.v_x + self.v_width) - self.size
            self.v_x_velocity *= -0.5

        if self.y <= self.v_y:
            self.y = self.v_y
            self.v_y_velocity *= -0.75 

        current_env = self.get_window_environment()
        if self.y <= current_env['y'] + 15:
            physical_floor = current_env['y']
            if current_env['hwnd']:
                if getattr(self, 'anchored_hwnd', None) != current_env['hwnd']:
                    self.anchored_hwnd = current_env['hwnd']
                    self.anchored_rect = current_env['rect']
        else:
            physical_floor = self.default_floor_y
            self.anchored_hwnd = None

        if self.y >= physical_floor and self.v_y_velocity > 0:
            self.y = physical_floor
            self.floor_y = physical_floor
            if self.v_y_velocity > 2.0:
                self.v_y_velocity *= -0.05 
                self.v_x_velocity *= 0.6 
            else:
                self.v_y_velocity = 0.0
                self.v_x_velocity *= 0.3
            if abs(self.v_x_velocity) < 0.5 and abs(self.v_y_velocity) < 0.5:
                self.current_state = 'idle'
                self.v_x_velocity = 0
                self.v_y_velocity = 0
        else: self.current_state = 'falling'
        self.update_position()
        self.window.after(30, self.physics_loop)

# --- WATER BUBBLE PROJECTILE ---
class BubbleProjectile:
    def __init__(self, parent_root, base_dir, start_x, start_y, target, on_hit_callback):
        self.window = tk.Toplevel(parent_root)
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        CHROMA_KEY = '#00FF00'
        self.window.config(bg=CHROMA_KEY)
        try: self.window.wm_attributes('-transparentcolor', CHROMA_KEY)
        except tk.TclError: pass
        
        self.target = target
        self.on_hit = on_hit_callback
        self.size = 15
        self.x = start_x
        self.y = start_y
        
        self.canvas = tk.Canvas(self.window, width=self.size, height=self.size, bg=CHROMA_KEY, highlightthickness=0)
        self.canvas.pack()
        self.canvas_image_id = self.canvas.create_image(self.size//2, self.size//2, anchor=tk.CENTER)
        
        try:
            ui_dir = os.path.join(base_dir, "game_env", "ui")
            raw_img = Image.open(os.path.join(ui_dir, "bubble.png")).convert("RGBA")
            r, g, b, a = raw_img.split()
            a = a.point(lambda p: 255 if p > 127 else 0)
            base_img = Image.merge("RGBA", (r, g, b, a))
            self.tk_image = ImageTk.PhotoImage(base_img.resize((self.size, self.size), Image.Resampling.NEAREST))
            self.canvas.itemconfig(self.canvas_image_id, image=self.tk_image)
        except:
            self.window.after(10, self.destroy)
            return
            
        self.window.geometry(f"{self.size}x{self.size}+{int(self.x)}+{int(self.y)}")
        self.physics_loop()
        
    def destroy(self):
        self.window.destroy()
        
    def physics_loop(self):
        if not self.target or not self.target.window.winfo_exists() or self.target.current_state in ['exiting', 'dragged', 'bubbled']:
            self.destroy()
            return
            
        t_cx = self.target.x + self.target.size_w/2
        t_cy = self.target.y + self.target.size_h/2
        my_cx = self.x + self.size/2
        my_cy = self.y + self.size/2
        
        dx = t_cx - my_cx
        dy = t_cy - my_cy
        dist = math.sqrt(dx**2 + dy**2)
        
        # Upon touching the target, the projectile explodes and activates the giant bubble state
        if dist < 20:
            self.on_hit(self.target)
            self.destroy()
            return
            
        speed = 10.0
        self.x += (dx/max(1, dist)) * speed
        self.y += (dy/max(1, dist)) * speed
        
        self.window.geometry(f"+{int(self.x)}+{int(self.y)}")
        self.window.after(30, self.physics_loop)