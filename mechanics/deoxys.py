import random
import math
import tkinter as tk
import time
import ctypes
import os
from PIL import Image, ImageTk, ImageDraw

try:
    import win32gui
    import win32process
    import win32con
    import win32api
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

class DeoxysRock:
    def __init__(self, parent_root, get_pets_callback, x, y, vx, vy, size):
        self.window = tk.Toplevel(parent_root)
        self.window.title("Deoxys Rock")
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        
        CHROMA_KEY = '#00FF00'
        self.window.config(bg=CHROMA_KEY)
        try: self.window.wm_attributes('-transparentcolor', CHROMA_KEY)
        except tk.TclError: pass
        
        self.get_pets = get_pets_callback
        self.size = size
        self.offset_y = -2
        
        user32 = ctypes.windll.user32
        self.v_x = user32.GetSystemMetrics(76) 
        self.v_y = user32.GetSystemMetrics(77)
        self.v_width = user32.GetSystemMetrics(78)
        self.v_height = user32.GetSystemMetrics(79)
        
        self.default_floor_y = (self.v_y + self.v_height) - self.size - self.offset_y
        self.floor_y = self.default_floor_y
        
        self.x = x
        self.y = y
        self.v_x_velocity = vx
        self.v_y_velocity = vy
        
        self.current_state = 'falling'
        self.angle = 0
        self.life_timer = 900 # 30 seconds
        
        self.canvas = tk.Canvas(self.window, width=self.size, height=self.size, bg=CHROMA_KEY, highlightthickness=0)
        self.canvas.pack()
        self.canvas_image_id = self.canvas.create_image(self.size//2, self.size//2, anchor=tk.CENTER)
        
        # Draw Rock
        self.base_img = Image.new("RGBA", (self.size, self.size), (0,0,0,0))
        draw = ImageDraw.Draw(self.base_img)
        points = []
        center = self.size / 2
        for angle_deg in range(0, 360, 45):
            angle = math.radians(angle_deg)
            r = (self.size / 2) * random.uniform(0.6, 1.0)
            points.append((center + math.cos(angle) * r, center + math.sin(angle) * r))
        draw.polygon(points, fill="#795548", outline="#3E2723")
        for _ in range(2):
            inner_pts = []
            ic = (random.uniform(self.size*0.3, self.size*0.7), random.uniform(self.size*0.3, self.size*0.7))
            for angle_deg in range(0, 360, 90):
                angle = math.radians(angle_deg + random.uniform(-20, 20))
                r = (self.size / 2) * random.uniform(0.1, 0.4)
                inner_pts.append((ic[0] + math.cos(angle) * r, ic[1] + math.sin(angle) * r))
            draw.polygon(inner_pts, fill="#5D4037")
        
        self.tk_image = ImageTk.PhotoImage(self.base_img)
        self.canvas.itemconfig(self.canvas_image_id, image=self.tk_image)
        
        self.window.geometry(f"{self.size}x{self.size}+{int(self.x)}+{int(self.y)}")
        
        self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self.on_drag_release)
        self.canvas.bind("<ButtonRelease-3>", lambda e: self.explode())
        
        self.keep_on_top()
        self.animate_loop()
        self.physics_loop()

    def keep_on_top(self):
        if self.current_state != 'exiting':
            try: self.window.attributes('-topmost', True)
            except: pass
            self.window.after(2000, self.keep_on_top)

    def explode(self):
        self.current_state = 'exiting'
        # Particle explosion visual
        for i in range(8):
            dx = random.uniform(-10, 10)
            dy = random.uniform(-10, 10)
            self.canvas.create_oval(self.size//2-2, self.size//2-2, self.size//2+2, self.size//2+2, fill="#795548", outline="#3E2723", tags=f"p_{i}")
            self.canvas.move(f"p_{i}", dx, dy)
        self.canvas.delete(self.canvas_image_id)
        self.window.after(200, self.window.destroy)

    def update_position(self):
        self.window.geometry(f"+{int(self.x)}+{int(self.y)}")
        
    def on_drag_start(self, event):
        if self.current_state == 'exiting': return
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
        
        self.life_timer -= 1
        if self.life_timer <= 0:
            self.explode()
            return
            
        if self.current_state == 'dragged':
            self.window.after(30, self.physics_loop)
            return
            
        self.v_y_velocity += 0.99 
        self.v_x_velocity *= 0.98 # slight air resistance
        
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
                self.v_y_velocity *= -0.15 # Reduced bounciness
                self.v_x_velocity *= 0.85 
            else:
                self.v_y_velocity = 0.0
                self.v_x_velocity *= 0.7 # Ground friction
            
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
                if p.current_state in ['falling_egg', 'falling_pokeball', 'exiting', 'dragged'] or getattr(p, 'is_egg', False) or p.pet_name.lower() == 'deoxys': continue
                
                p_cx = p.x + p.size_w/2
                p_cy = p.y + p.size_h/2
                
                dx = ball_cx - p_cx
                dy = ball_cy - p_cy
                dist = math.sqrt(dx**2 + dy**2)
                
                min_dist = (self.size/2) + (p.size_w/2.5) 
                if dist < min_dist:
                    force_multiplier = (p.size_w / 64.0) * (p.speed * 1.5 if p.current_state == 'walking' else 1.0)
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


class DeoxysMechanics:
    def cancel_deoxys_arts(self):
        if hasattr(self, 'deoxys_vfx_win') and self.deoxys_vfx_win and self.deoxys_vfx_win.winfo_exists():
            self.deoxys_vfx_win.destroy()
            self.deoxys_vfx_win = None
            
        for attr in ['deoxys_timer', 'deoxys_vfx_win', 'deoxys_canvas', 'deoxys_particles', 'deoxys_phase', 'deoxys_dna_angle']:
            if hasattr(self, attr): delattr(self, attr)

        self.surface_angle = 0
        if self.current_state not in ['dragged', 'exiting']:
            self.current_state = 'falling'
            self.v_y_velocity = 0

    def _fsm_deoxys_channeling(self):
        if not hasattr(self, 'deoxys_timer'):
            self.deoxys_timer = 100 # 3.3 seconds
            self.v_y_velocity = 0
            
            current_env, _ = self.get_window_environment()
            self.deoxys_vfx_win = tk.Toplevel(self.window.master)
            self.deoxys_vfx_win.title("VFX_Deoxys_Ignore")
            self.deoxys_vfx_win.overrideredirect(True)
            self.deoxys_vfx_win.attributes('-topmost', True)
            TRANS_COLOR = '#010101'
            self.deoxys_vfx_win.config(bg=TRANS_COLOR)
            try: self.deoxys_vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
            except: pass
            
            self.deoxys_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
            self.deoxys_canvas = tk.Canvas(self.deoxys_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
            self.deoxys_canvas.pack()
            self.deoxys_particles = []
            self.deoxys_vfx_loop()
            
        self.deoxys_timer -= 1
        
        # Levitate up slightly
        self.y -= 0.5
        
        # Psychic ray particles inwards
        if self.deoxys_timer % 2 == 0:
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(150, 300)
            cx = self.x - self.v_x + self.size_w/2
            cy = self.y - self.v_y + self.size_h/2
            spawn_x = cx + math.cos(angle) * dist
            spawn_y = cy + math.sin(angle) * dist
            color = random.choice(["#00BCD4", "#FF5722"])
            self.deoxys_particles.append({
                'id': self.deoxys_canvas.create_line(spawn_x, spawn_y, spawn_x, spawn_y, fill=color, width=2, tags="pt"),
                'x': spawn_x, 'y': spawn_y,
                'target_x': cx, 'target_y': cy,
                'speed': random.uniform(8.0, 15.0),
                'type': 'ray'
            })
            
        if self.deoxys_timer <= 0:
            self.current_state = 'deoxys_ascend'
            self.v_y_velocity = -60.0
            self.deoxys_dna_angle = 0.0
            
        self.update_position()
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_deoxys_ascend(self):
        self.y += self.v_y_velocity
        
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        
        self.deoxys_dna_angle += 0.4
        offset = math.sin(self.deoxys_dna_angle) * 30
        
        # Two intertwining strands
        p1_x = cx + offset
        p2_x = cx - offset
        
        self.deoxys_particles.append({'id': self.deoxys_canvas.create_oval(p1_x-4, cy-4, p1_x+4, cy+4, fill="#00BCD4", outline="#00BCD4", tags="pt"), 'x': p1_x, 'y': cy, 'type': 'dna', 'life': 15})
        self.deoxys_particles.append({'id': self.deoxys_canvas.create_oval(p2_x-4, cy-4, p2_x+4, cy+4, fill="#FF5722", outline="#FF5722", tags="pt"), 'x': p2_x, 'y': cy, 'type': 'dna', 'life': 15})
        
        if self.y < self.v_y - 200:
            self.current_state = 'deoxys_wait'
            self.deoxys_timer = 300 # 10 seconds
            self.x = -1000
            
        self.update_position()
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_deoxys_wait(self):
        self.deoxys_timer -= 1
        
        # Clean up DNA trails off screen while waiting
        if self.deoxys_timer == 280:
            pass # Particles will fade naturally
            
        if self.deoxys_timer <= 0:
            self.current_state = 'deoxys_meteor'
            target_cx = self.v_x + self.v_width / 2
            if HAS_WIN32:
                try:
                    monitors = win32api.EnumDisplayMonitors()
                    if monitors:
                        monitor_rect = random.choice(monitors)[2]
                        target_cx = (monitor_rect[0] + monitor_rect[2]) / 2
                except: pass
                
            self.meteor_x = target_cx - 80
            self.meteor_y = self.v_y - 300
            self.x = -1000
            self.y = -1000
            self.v_y_velocity = 60.0
            
            self.deoxys_meteor_pts = []
            for angle_deg in range(0, 360, 30):
                angle = math.radians(angle_deg)
                r = random.uniform(50.0, 80.0)
                self.deoxys_meteor_pts.extend([math.cos(angle) * r, math.sin(angle) * r])
            
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_deoxys_meteor(self):
        self.meteor_y += self.v_y_velocity
        
        cx = self.meteor_x - self.v_x + 80
        cy = self.meteor_y - self.v_y + 80
        
        translated_pts = []
        for i in range(0, len(self.deoxys_meteor_pts), 2):
            translated_pts.extend([self.deoxys_meteor_pts[i] + cx, self.deoxys_meteor_pts[i+1] + cy])
        
        # Big rock meteor visual with fire trail
        for i in range(5):
            tx = cx + random.randint(-40, 40)
            ty = cy - random.randint(40, 160)
            color = random.choice(["#FF5722", "#FFC107", "#F44336"])
            self.deoxys_particles.append({'id': self.deoxys_canvas.create_oval(tx-10, ty-10, tx+10, ty+10, fill=color, outline=color, tags="pt"), 'type': 'meteor_trail', 'life': 5})
            
        meteor_id = self.deoxys_canvas.create_polygon(*translated_pts, fill="#5D4037", outline="#3E2723", width=4, tags="meteor")
        self.deoxys_particles.append({'id': meteor_id, 'type': 'meteor', 'life': 1})
        
        current_env, _ = self.get_window_environment()
        floor = current_env['y'] if current_env['y'] else (self.v_y + self.v_height - 100)
        
        if self.meteor_y + 160 >= floor:
            # Impact!
            self.x = self.meteor_x + 80 - self.size_w/2
            self.y = floor - self.size_h
            self.current_state = 'deoxys_emerge'
            self.deoxys_timer = 60 # 2 seconds floating
            self.v_y_velocity = -5.0 # Fly up a bit from explosion
            
            # Massive explosion visual
            exp_id = self.deoxys_canvas.create_oval(cx-10, cy-10, cx+10, cy+10, fill="white", outline="#FF5722", width=10, tags="pt")
            self.deoxys_particles.append({'id': exp_id, 'type': 'giant_explosion', 'life': 20})
            
            # Push nearby pets
            global_cx = self.x + self.size_w/2
            global_cy = self.y + self.size_h/2
            if getattr(self, 'get_all_pets', None):
                for p in self.get_all_pets():
                    if p != self and p.current_state not in ['exiting', 'dragged', 'thrown']:
                        pcx = p.x + p.size_w/2
                        pcy = p.y + p.size_h/2
                        dist = math.hypot(global_cx - pcx, global_cy - pcy)
                        if dist < 400: # Big AOE
                            p.current_state = 'thrown'
                            dir_x = 1 if pcx > global_cx else -1
                            p.v_x_velocity = dir_x * random.uniform(30.0, 50.0)
                            p.v_y_velocity = -random.uniform(30.0, 50.0)
                            if hasattr(p, 'play_sound'):
                                try: p.play_sound("hit.wav")
                                except: pass
                                
            # Spawn rocks
            if getattr(self, 'get_all_pets', None):
                for _ in range(random.randint(5, 8)):
                    vx = random.uniform(-40.0, 40.0)
                    vy = random.uniform(-40.0, -10.0)
                    r_size = random.randint(30, 50)
                    rock = DeoxysRock(self.window.master, self.get_all_pets, self.x + self.size_w/2, self.y + self.size_h/2, vx, vy, r_size)
                    
        self.update_position()
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_deoxys_emerge(self):
        self.deoxys_timer -= 1
        
        self.v_y_velocity *= 0.9 # Brake upwards
        self.y += self.v_y_velocity
        
        if self.deoxys_timer <= 0:
            self.current_state = 'falling'
            self.deoxys_cooldown = 72000
            if hasattr(self, 'deoxys_vfx_win') and self.deoxys_vfx_win:
                self.deoxys_vfx_win.destroy()
                self.deoxys_vfx_win = None
                
        self.update_position()
        self.schedule_loop(33, self.physics_loop)
        
    def deoxys_vfx_loop(self):
        if self.current_state not in ['deoxys_channeling', 'deoxys_ascend', 'deoxys_wait', 'deoxys_meteor', 'deoxys_emerge']: return
        if not hasattr(self, 'deoxys_vfx_win') or not self.deoxys_vfx_win or not self.deoxys_vfx_win.winfo_exists(): return
        
        alive = []
        for p in self.deoxys_particles:
            if p.get('type') == 'ray':
                dx = p['target_x'] - p['x']
                dy = p['target_y'] - p['y']
                dist = math.hypot(dx, dy)
                if dist > p['speed']:
                    p['x'] += (dx/dist) * p['speed']
                    p['y'] += (dy/dist) * p['speed']
                    # Draw line from old pos to new pos
                    tail_x = p['x'] - (dx/dist)*p['speed']*2
                    tail_y = p['y'] - (dy/dist)*p['speed']*2
                    self.deoxys_canvas.coords(p['id'], p['x'], p['y'], tail_x, tail_y)
                    alive.append(p)
                else:
                    self.deoxys_canvas.delete(p['id'])
            elif p.get('type') == 'dna':
                if p['life'] > 0:
                    p['life'] -= 1
                    size = max(1, p['life']/3.75) # life 15 / 3.75 = 4
                    self.deoxys_canvas.coords(p['id'], p['x']-size, p['y']-size, p['x']+size, p['y']+size)
                    alive.append(p)
                else:
                    self.deoxys_canvas.delete(p['id'])
            elif p.get('type') == 'meteor':
                if p['life'] > 0:
                    p['life'] -= 1
                    alive.append(p)
                else:
                    self.deoxys_canvas.delete(p['id'])
            elif p.get('type') == 'meteor_trail':
                if p['life'] > 0:
                    p['life'] -= 1
                    coords = self.deoxys_canvas.coords(p['id'])
                    if coords:
                        self.deoxys_canvas.coords(p['id'], coords[0]+1, coords[1]+1, coords[2]-1, coords[3]-1)
                        alive.append(p)
                else:
                    self.deoxys_canvas.delete(p['id'])
            elif p.get('type') == 'giant_explosion':
                if p['life'] > 0:
                    p['life'] -= 1
                    coords = self.deoxys_canvas.coords(p['id'])
                    if coords:
                        # expand very fast
                        self.deoxys_canvas.coords(p['id'], coords[0]-25, coords[1]-25, coords[2]+25, coords[3]+25)
                        alive.append(p)
                else:
                    self.deoxys_canvas.delete(p['id'])
                    
        self.deoxys_particles = alive
        self.window.after(33, self.deoxys_vfx_loop)
