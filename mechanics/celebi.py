import os
import math
import random
import tkinter as tk
from PIL import Image, ImageTk

class CelebiMechanics:
    def cancel_celebi_arts(self):
        if hasattr(self, 'celebi_vfx_win') and self.celebi_vfx_win and self.celebi_vfx_win.winfo_exists():
            self.celebi_vfx_win.destroy()
            self.celebi_vfx_win = None

        for ghost in getattr(self, 'celebi_ghosts', []):
            target = ghost.get('target')
            if target and target.window.winfo_exists() and getattr(target, 'current_state', '') == 'celebi_frozen':
                target.current_state = 'falling'
                target.climbing_surface = 'floor'  # Inyección obligatoria
                target.anchored_hwnd = None        # Purga de seguridad
                try: target.window.attributes('-alpha', 1.0)
                except: pass

        for attr in ['celebi_timer', 'celebi_phase', 'celebi_particles', 'celebi_ghosts', 'celebi_flight_targets', 'celebi_current_target', 'celebi_finishing']:
            if hasattr(self, attr): delattr(self, attr)

        if self.current_state not in ['dragged', 'exiting']:
            self.current_state = 'thrown'
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            self.schedule_loop(50, self.physics_loop)

    def trigger_celebi_arts(self):
        self._setup_celebi_vfx_layer()
        self.celebi_phase = 0
        self.celebi_timer = 90 
        self.celebi_ghosts = []
        
        self.current_state = 'celebi_channeling'
        self.v_x_velocity = 0.0
        self.v_y_velocity = 0.0
        
        self.schedule_loop(30, self.physics_loop)

    def _setup_celebi_vfx_layer(self):
        self.celebi_particles = []
        if hasattr(self, 'celebi_vfx_win') and self.celebi_vfx_win and self.celebi_vfx_win.winfo_exists():
            self.celebi_vfx_canvas.delete("all")
            return
            
        self.celebi_vfx_win = tk.Toplevel(self.window.master)
        self.celebi_vfx_win.title("VFX_Celebi")
        self.celebi_vfx_win.overrideredirect(True)
        self.celebi_vfx_win.attributes('-topmost', True)
        
        TRANS = '#010101'
        self.celebi_vfx_win.config(bg=TRANS)
        try: self.celebi_vfx_win.wm_attributes('-transparentcolor', TRANS)
        except: pass
        
        self.celebi_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.celebi_vfx_win.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x00080000 | 0x00000020)
        except: pass

        self.celebi_vfx_canvas = tk.Canvas(self.celebi_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS, highlightthickness=0)
        self.celebi_vfx_canvas.pack()

    def _capture_temporal_ghosts(self):
        if not getattr(self, 'get_all_pets', None): return
        
        for p in self.get_all_pets():
            if p == self or getattr(p, 'is_egg', False) or p.current_state in ['exiting', 'dragged']: continue
            
            ghost_tk = None
            gid = None
            abs_x = p.x - self.v_x + p.size_w/2
            abs_y = p.y - self.v_y + p.size_h/2
            
            try:
                base_dir = getattr(p.animator, 'base_dir', p.pet_dir) if hasattr(p, 'animator') else getattr(p, 'pet_dir', '')
                img_path = None
                
                for root, dirs, files in os.walk(base_dir):
                    valid = [f for f in files if f.endswith(('.png', '.gif'))]
                    if valid:
                        valid.sort()
                        img_path = os.path.join(root, valid[0])
                        break
                        
                if img_path:
                    raw_img = Image.open(img_path).convert("RGBA")
                    
                    try: filter_mode = Image.Resampling.NEAREST
                    except AttributeError: filter_mode = Image.NEAREST
                        
                    raw_img = raw_img.resize((int(p.size_w), int(p.size_h)), filter_mode)
                    
                    if not getattr(p, 'is_facing_right', True):
                        raw_img = raw_img.transpose(Image.FLIP_LEFT_RIGHT)
                        
                    pixels = raw_img.load()
                    width, height = raw_img.size
                    
                    for y in range(height):
                        for x in range(width):
                            r, g, b, a = pixels[x, y]
                            
                            if a > 127 and not (r < 10 and g < 10 and b < 10):
                                if (x % 3 == 0) and (y % 3 == 0): 
                                    pixels[x, y] = (max(20, r), max(20, g), max(20, b), 255)
                                else:
                                    pixels[x, y] = (0, 0, 0, 0)
                            else:
                                pixels[x, y] = (0, 0, 0, 0)
                                
                    ghost_tk = ImageTk.PhotoImage(raw_img)
                    gid = self.celebi_vfx_canvas.create_image(abs_x, abs_y, image=ghost_tk, anchor=tk.CENTER)
            except Exception as e:
                pass 
                
            self.celebi_ghosts.append({
                'target': p,
                'tk_img': ghost_tk,
                'id': gid,
                'x': p.x,
                'y': p.y,
                'floor_y': getattr(p, 'floor_y', p.y),
                'anchored_hwnd': getattr(p, 'anchored_hwnd', None)
            })

    def _execute_time_freeze_vfx(self):
        if not hasattr(self, 'celebi_vfx_canvas'): return
        
        for _ in range(80):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(15.0, 60.0)
            
            abs_cx = (self.v_width / 2)
            abs_cy = (self.v_height / 2)
            
            color = random.choice(["#000000", "#1A1A1A", "#4B0082", "#8A2BE2"])
            size = random.choice([4, 6, 8, 12])
            
            pid = self.celebi_vfx_canvas.create_rectangle(abs_cx-size, abs_cy-size, abs_cx+size, abs_cy+size, fill=color, outline="")
            self.celebi_particles.append({
                'id': pid, 'x': abs_cx, 'y': abs_cy, 
                'vx': math.cos(angle) * speed, 
                'vy': math.sin(angle) * speed, 
                'life': 25, 'type': 'freeze_blast', 'size': size
            })

    def _fsm_celebi_channeling(self):
        self.celebi_timer -= 1
        
        self.fly_amplitude = getattr(self, 'fly_amplitude', 0) + 0.1
        self.y += math.sin(self.fly_amplitude) * 2.0
        
        if hasattr(self, 'celebi_vfx_canvas'):
            cx = self.x - self.v_x + self.size_w / 2
            cy = self.y - self.v_y + self.size_h / 2 + 15 
            
            t = 90 - self.celebi_timer
            angle = t * 0.25
            dist = max(0, 150 - (t * 1.5))
            
            for i in range(3):
                offset = angle + (i * (2 * math.pi / 3))
                px = cx + math.cos(offset) * dist
                py = cy + math.sin(offset) * dist
                color = random.choice(["#8A2BE2", "#9370DB", "#4B0082", "#DDA0DD"])
                s = random.choice([3, 4, 5])
                
                pid = self.celebi_vfx_canvas.create_oval(px-s, py-s, px+s, py+s, fill=color, outline="")
                self.celebi_particles.append({'id': pid, 'x': px, 'y': py, 'vx': 0, 'vy': 0, 'life': 8, 'type': 'spiral'})

        self._process_celebi_particles()
        
        if self.celebi_timer <= 0:
            self._capture_temporal_ghosts()
            
            if hasattr(self, 'celebi_vfx_canvas'):
                cx = self.x - self.v_x + self.size_w / 2
                cy = self.y - self.v_y + self.size_h / 2
                for _ in range(20):
                    a = random.uniform(0, 2 * math.pi)
                    sp = random.uniform(5.0, 15.0)
                    pid = self.celebi_vfx_canvas.create_oval(cx-3, cy-3, cx+3, cy+3, fill="#32CD32", outline="")
                    self.celebi_particles.append({'id': pid, 'x': cx, 'y': cy, 'vx': math.cos(a)*sp, 'vy': math.sin(a)*sp, 'life': 15, 'type': 'blast'})
            
            self.celebi_phase = 1
            self.celebi_timer = 500 
            self.current_state = 'celebi_wait'
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_celebi_wait(self):
        self.celebi_timer -= 1
        
        self.fly_amplitude = getattr(self, 'fly_amplitude', 0) + 0.1
        self.y += math.sin(self.fly_amplitude) * 2.0
        
        self._process_celebi_particles()
        
        if self.celebi_timer <= 0:
            self.current_state = 'celebi_freeze'
            self.celebi_timer = 30
            self._execute_time_freeze_vfx()
            
            for ghost in getattr(self, 'celebi_ghosts', []):
                target = ghost.get('target')
                if target and target.window.winfo_exists() and target.current_state != 'exiting':
                    
                    if target.current_state.startswith('dark_') and hasattr(target, 'cancel_dark_arts'): target.cancel_dark_arts()
                    if target.current_state.startswith('mewtwo_') and hasattr(target, 'cancel_mewtwo_arts'): target.cancel_mewtwo_arts()
                    if target.current_state == 'bubbled': 
                        if hasattr(target, 'manage_bubble_vfx'): target.manage_bubble_vfx(False)
                        if hasattr(target, 'show_bubble_burst_vfx'): target.show_bubble_burst_vfx()
                    if target.current_state in ['digging_in', 'digging', 'digging_out']:
                        target.canvas.itemconfig(target.canvas_image_id, state='normal')
                        target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
                        
                    target.current_state = 'celebi_frozen'
                    try: target.window.attributes('-alpha', 0.6)
                    except: pass
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_celebi_freeze(self):
        self.celebi_timer -= 1
        self._process_celebi_particles()
        
        if self.celebi_timer <= 0:
            self.current_state = 'celebi_revert_flight'
            self.celebi_flight_targets = self.celebi_ghosts.copy()
            random.shuffle(self.celebi_flight_targets)
            self.celebi_current_target = self.celebi_flight_targets.pop(0) if self.celebi_flight_targets else None
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_celebi_revert_flight(self):
        self._process_celebi_particles()
        
        if not hasattr(self, 'celebi_current_target') or not self.celebi_current_target:
            if not getattr(self, 'celebi_finishing', False):
                self.celebi_finishing = True
                self.celebi_timer = 30 
                
            self.celebi_timer -= 1
            
            self.v_x_velocity *= 0.85
            self.v_y_velocity *= 0.85
            self.x += self.v_x_velocity
            self.y += self.v_y_velocity
            
            if self.celebi_timer <= 0:
                self.cancel_celebi_arts()
                return
                
            self.update_position()
            self.schedule_loop(30, self.physics_loop)
            return
            
        target_dict = self.celebi_current_target
        target_pet = target_dict['target']
        
        if not target_pet.window.winfo_exists():
            self.celebi_current_target = self.celebi_flight_targets.pop(0) if self.celebi_flight_targets else None
            self.schedule_loop(16, self.physics_loop)
            return
            
        tx = target_pet.x + target_pet.size_w / 2
        ty = target_pet.y + target_pet.size_h / 2
        cx = self.x + self.size_w / 2
        cy = self.y + self.size_h / 2
        
        dx = tx - cx
        dy = ty - cy
        dist = math.hypot(dx, dy)
        
        if hasattr(self, 'celebi_vfx_canvas') and random.randint(1, 100) <= 70:
            t_px = self.x - self.v_x + self.size_w / 2 + random.uniform(-10, 10)
            t_py = self.y - self.v_y + self.size_h / 2 + random.uniform(-10, 10)
            color = random.choice(["#FFFF00", "#FFD700", "#FFFACD"])
            t_pid = self.celebi_vfx_canvas.create_oval(t_px-2, t_py-2, t_px+2, t_py+2, fill=color, outline="")
            self.celebi_particles.append({'id': t_pid, 'x': t_px, 'y': t_py, 'vx': random.uniform(-1, 1), 'vy': random.uniform(3.0, 7.0), 'life': 15, 'type': 'trail'})
        
        if dist < max(self.size_w, self.size_h) * 0.8:
            self._execute_reversion(target_dict)
            self.celebi_current_target = self.celebi_flight_targets.pop(0) if self.celebi_flight_targets else None
        else:
            max_speed = 18.0 
            turn_speed = 0.025 
            
            desired_vx = (dx / dist) * max_speed
            desired_vy = (dy / dist) * max_speed
            
            # --- SISTEMA DE CONTENCIÓN (STEERING AVOIDANCE) ---
            # Evalúa coordenadas absolutas y aplica repulsión si la entidad invade el margen de 150 píxeles.
            margin = 150
            repulsion = 2.0
            
            if self.x < self.v_x + margin:
                desired_vx += (self.v_x + margin - self.x) * repulsion
            elif self.x > self.v_x + self.v_width - margin:
                desired_vx -= (self.x - (self.v_x + self.v_width - margin)) * repulsion
                
            if self.y < self.v_y + margin:
                desired_vy += (self.v_y + margin - self.y) * repulsion
            elif self.y > self.v_y + self.v_height - margin:
                desired_vy -= (self.y - (self.v_y + self.v_height - margin)) * repulsion
                
            # Renormalización matemática del vector: 
            # Evita aceleraciones exponenciales al sumar la fuerza de repulsión a la velocidad máxima.
            curr_mag = math.hypot(desired_vx, desired_vy)
            if curr_mag > 0:
                desired_vx = (desired_vx / curr_mag) * max_speed
                desired_vy = (desired_vy / curr_mag) * max_speed
            # --------------------------------------------------
            
            steer_x = desired_vx - self.v_x_velocity
            steer_y = desired_vy - self.v_y_velocity
            
            self.v_x_velocity += steer_x * turn_speed
            self.v_y_velocity += steer_y * turn_speed
            
            self.x += self.v_x_velocity
            self.y += self.v_y_velocity
            self.is_facing_right = (self.v_x_velocity > 0)
            
        self.update_position()
        self.schedule_loop(16, self.physics_loop)

    def _execute_reversion(self, target_dict):
        target = target_dict['target']
        
        if hasattr(self, 'celebi_vfx_canvas'):
            cx = target.x - self.v_x + target.size_w / 2
            cy = target.y - self.v_y + target.size_h / 2
            for _ in range(25):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(8.0, 20.0)
                pid = self.celebi_vfx_canvas.create_oval(cx-3, cy-3, cx+3, cy+3, fill="#FF69B4", outline="")
                self.celebi_particles.append({'id': pid, 'x': cx, 'y': cy, 'vx': math.cos(angle)*speed, 'vy': math.sin(angle)*speed, 'life': 20, 'type': 'blast'})
                
            if target_dict.get('id'):
                self.celebi_vfx_canvas.delete(target_dict['id'])
        
        if getattr(target, 'current_state', '') == 'celebi_frozen':
            target.x = target_dict['x']
            target.y = target_dict['y']
            target.floor_y = getattr(target, 'default_floor_y', target.y)
            
            # --- PURGA FÍSICA Y VISUAL ABSOLUTA ---
            target.climbing_surface = 'floor'
            target.surface_angle = 180 if getattr(target, 'gravity_inverted', False) else 0
            target.anchored_hwnd = None
            target.anchored_rect = None
            target.canvas.itemconfig(target.canvas_image_id, state='normal')
            target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
            
            target.v_x_velocity = 0.0
            target.v_y_velocity = 0.0
            # --------------------------------------
            
            target.update_position()
            target.current_state = 'falling'
            try: target.window.attributes('-alpha', 1.0)
            except: pass
            
    def _process_celebi_particles(self):
        if not hasattr(self, 'celebi_vfx_canvas') or not self.celebi_vfx_canvas: return
        alive = []
        for p in getattr(self, 'celebi_particles', []):
            p['life'] -= 1
            
            if p['type'] == 'spiral':
                pass 
                
            elif p['type'] in ['blast', 'freeze_blast']:
                p['x'] += p['vx']
                p['y'] += p['vy']
                p['vx'] *= 0.85 
                p['vy'] *= 0.85
                if p['type'] == 'freeze_blast':
                    s = p['size'] * (p['life'] / 25.0)
                    self.celebi_vfx_canvas.coords(p['id'], p['x']-s, p['y']-s, p['x']+s, p['y']+s)
                else:
                    self.celebi_vfx_canvas.coords(p['id'], p['x']-3, p['y']-3, p['x']+3, p['y']+3)
                    
            elif p['type'] == 'trail':
                p['x'] += p['vx']
                p['y'] += p['vy']
                self.celebi_vfx_canvas.coords(p['id'], p['x']-2, p['y']-2, p['x']+2, p['y']+2)

            if p['life'] > 0:
                alive.append(p)
            else:
                self.celebi_vfx_canvas.delete(p['id'])
                
        self.celebi_particles = alive

    def _fsm_celebi_frozen(self):
        self.schedule_loop(50, self.physics_loop)