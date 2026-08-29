import random
import math
import tkinter as tk
from PIL import Image, ImageTk, ImageEnhance

class MarshadowMechanics:
    def start_marshadow_mechanic(self):
        if getattr(self, 'current_state', '') in ['dragged', 'exiting']: return
        if getattr(self, 'marshadow_cooldown', 0) > 0: return
        if hasattr(self, 'is_global_mechanic_active') and self.is_global_mechanic_active(): return

        name = self.pet_name.lower().replace("_", "").replace("-", "")
        if name not in ["marshadow", "marshadow1"]: return

        self.marshadow_cooldown = 3600000  # 1 hour
        self.current_state = 'marshadow_charging'
        self.marshadow_timer = 90  # 3 seconds at 30ms

        self._init_marshadow_vfx()
        self.schedule_loop(30, self.physics_loop)

    def _init_marshadow_vfx(self):
        if hasattr(self, 'marshadow_vfx_win') and self.marshadow_vfx_win and self.marshadow_vfx_win.winfo_exists():
            return
            
        self.marshadow_vfx_win = tk.Toplevel(self.window.master)
        self.marshadow_vfx_win.overrideredirect(True)
        self.marshadow_vfx_win.attributes('-topmost', True)
        TRANS_COLOR = '#010101'
        self.marshadow_vfx_win.config(bg=TRANS_COLOR)
        try: self.marshadow_vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass
        self.marshadow_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        
        # Click-through
        if 'HAS_WIN32' in globals() and globals()['HAS_WIN32']:
            try:
                import win32gui
                import win32con
                hwnd = win32gui.GetParent(self.marshadow_vfx_win.winfo_id())
                ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED)
            except: pass
        
        self.marshadow_canvas = tk.Canvas(self.marshadow_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
        self.marshadow_canvas.pack(fill="both", expand=True)
        
        self.marshadow_particles = []
        self.marshadow_target = None
        self.marshadow_victim_shadows = []
        self.marshadow_cached_shadows = {}

    def _cleanup_marshadow_vfx(self):
        if hasattr(self, 'marshadow_vfx_win') and self.marshadow_vfx_win and self.marshadow_vfx_win.winfo_exists():
            self.marshadow_vfx_win.destroy()
            self.marshadow_vfx_win = None
            
        try: self.window.attributes('-alpha', 1.0)
        except: pass

        if hasattr(self, 'marshadow_target') and self.marshadow_target:
            if getattr(self.marshadow_target, 'current_state', '').startswith('marshadow_victim_'):
                self.marshadow_target.current_state = 'falling'
                self.marshadow_target.canvas.itemconfig(self.marshadow_target.canvas_image_id, state='normal')
                
        for attr in ['marshadow_timer', 'marshadow_particles', 'marshadow_target', 'marshadow_victim_shadows', 'marshadow_cached_shadows']:
            if hasattr(self, attr): delattr(self, attr)

    def cancel_marshadow_arts(self):
        if getattr(self, 'current_state', '').startswith('marshadow_') and self.current_state not in ['marshadow_victim_submerging', 'marshadow_victim_emerging', 'marshadow_victim_flying']:
            self.current_state = 'falling'
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            self.marshadow_timer = 0
            
        if not getattr(self, 'marshadow_victim_shadows', []):
            self._cleanup_marshadow_vfx()

    def _fsm_marshadow_charging(self):
        self.marshadow_timer -= 1
        
        if hasattr(self, 'marshadow_vfx_win') and self.marshadow_vfx_win and self.marshadow_vfx_win.winfo_exists():
            cx = (self.x + self.size_w / 2) - self.v_x
            cy = (self.y + self.size_h / 2) - self.v_y
            
            # Spawn dark absorbing particles
            for _ in range(2):
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(60, 100)
                px = cx + math.cos(angle) * dist
                py = cy + math.sin(angle) * dist
                size = random.randint(3, 6)
                color = random.choice(["#222222", "#1a0033", "#330033", "#000000"])
                item = self.marshadow_canvas.create_rectangle(px, py, px+size, py+size, fill=color, outline="")
                self.marshadow_particles.append({'id': item, 'x': px, 'y': py, 'tx': cx, 'ty': cy, 'speed': random.uniform(3, 6), 'life': 20})
                
            # Move particles
            for p in self.marshadow_particles[:]:
                if 'tx' not in p: continue
                dx = p['tx'] - p['x']
                dy = p['ty'] - p['y']
                dist = math.hypot(dx, dy)
                if dist < 5 or p['life'] <= 0:
                    self.marshadow_canvas.delete(p['id'])
                    self.marshadow_particles.remove(p)
                else:
                    p['x'] += (dx/dist) * p['speed']
                    p['y'] += (dy/dist) * p['speed']
                    p['life'] -= 1
                    self.marshadow_canvas.coords(p['id'], p['x'], p['y'], p['x']+size, p['y']+size)

        if self.marshadow_timer <= 0:
            if hasattr(self, 'marshadow_canvas'):
                for p in self.marshadow_particles:
                    self.marshadow_canvas.delete(p['id'])
                self.marshadow_particles.clear()
                
            active_pets = [p for p in getattr(self.game_controller, 'active_instances', []) if p != self and p.current_state not in ['dragged', 'exiting', 'despawning_wild', 'spawning_wild']]
            if active_pets:
                self.marshadow_target = random.choice(active_pets)
                self.current_state = 'marshadow_dashing'
                try: self.window.attributes('-alpha', 0.01) # Become invisible
                except: pass
            else:
                self.cancel_marshadow_arts()

        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_marshadow_dashing(self):
        if not hasattr(self, 'marshadow_target') or not self.marshadow_target or getattr(self.marshadow_target, 'current_state', '') in ['dragged', 'exiting']:
            self.cancel_marshadow_arts()
            return
            
        tx = self.marshadow_target.x
        ty = self.marshadow_target.y
        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)
        
        speed = 25.0
        
        if dist < speed:
            self.x = tx
            self.y = ty
            self.current_state = 'marshadow_mimicking'
            self.marshadow_timer = 300 # 10 seconds
        else:
            self.x += (dx/dist) * speed
            self.y += (dy/dist) * speed
            
            if hasattr(self, 'marshadow_canvas'):
                cx = (self.x + self.size_w / 2) - self.v_x
                cy = (self.y + self.size_h / 2) - self.v_y
                size = random.randint(15, 25)
                item = self.marshadow_canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill="#111111", outline="")
                self.marshadow_particles.append({'id': item, 'life': 10, 'is_trail': True})

        self._update_marshadow_particles()
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_marshadow_mimicking(self):
        if not hasattr(self, 'marshadow_target') or not self.marshadow_target or getattr(self.marshadow_target, 'current_state', '') in ['dragged', 'exiting']:
            self.cancel_marshadow_arts()
            return
            
        self.marshadow_timer -= 1
        
        self.x = self.marshadow_target.x
        self.y = self.marshadow_target.y
        
        if hasattr(self, 'marshadow_canvas') and hasattr(self.marshadow_target, 'animator') and hasattr(self.marshadow_target.animator, 'current_processed_image'):
            raw_img = self.marshadow_target.animator.current_processed_image
            
            # The processed image is already correctly mirrored if needed
            cache_key = f"{id(raw_img)}"
            
            if len(self.marshadow_cached_shadows) > 100:
                self.marshadow_cached_shadows.clear()
                
            if cache_key not in self.marshadow_cached_shadows:
                if raw_img:
                    w, h = raw_img.size
                    new_w, new_h = int(w * 1.5), int(h * 1.5)
                    resized = raw_img.resize((new_w, new_h), Image.NEAREST)
                    
                    r, g, b, a = resized.split()
                    r = r.point(lambda p: int(p * 0.1))
                    g = g.point(lambda p: int(p * 0.1))
                    b = b.point(lambda p: int(p * 0.1))
                    a = a.point(lambda p: int(p * 0.9))
                    shadow_img = Image.merge("RGBA", (r, g, b, a))
                    self.marshadow_cached_shadows[cache_key] = ImageTk.PhotoImage(shadow_img)
            
            if cache_key in self.marshadow_cached_shadows:
                self.marshadow_canvas.delete("marshadow_mimic")
                tw = self.marshadow_target.size_w
                th = self.marshadow_target.size_h
                cx = (self.marshadow_target.x + tw/2) - self.v_x
                cy = (self.marshadow_target.y + th/2) - self.v_y
                self.marshadow_canvas.create_image(cx, cy, image=self.marshadow_cached_shadows[cache_key], tags="marshadow_mimic")

        self._update_marshadow_particles()
        
        if self.marshadow_timer <= 0:
            self.current_state = 'marshadow_submerging'
            self.marshadow_target.current_state = 'marshadow_victim_submerging'
            self.marshadow_canvas.delete("marshadow_mimic")

        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_marshadow_submerging(self):
        if not hasattr(self, 'marshadow_target') or not self.marshadow_target:
            self.cancel_marshadow_arts()
            return
            
        current_env, _ = self.marshadow_target.get_window_environment()
        target_floor_y = current_env['y']
        
        self.y += 10
        self.marshadow_target.y += 10
        
        if hasattr(self, 'marshadow_canvas'):
            cx = (self.marshadow_target.x + self.marshadow_target.size_w/2) - self.v_x
            # target_floor_y is the pet's top-left Y when standing. The physical floor is target_floor_y + size_h.
            physical_floor_cy = (target_floor_y + self.marshadow_target.size_h) - self.v_y
            cy = (self.marshadow_target.y + self.marshadow_target.size_h/2) - self.v_y
            if cy < physical_floor_cy + 50:
                for _ in range(8):
                    size = random.randint(10, 18)
                    color = random.choice(["#444444", "#2a004d", "#000000", "#1a1a1a"])
                    item = self.marshadow_canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline="")
                    self.marshadow_particles.append({'id': item, 'x': cx, 'y': cy, 'vx': random.uniform(-10, 10), 'vy': random.uniform(-18, -5), 'life': 30, 'is_explosion': True})

        self._update_marshadow_particles()
        
        if self.marshadow_target.y > target_floor_y + 150:
            self.current_state = 'marshadow_emerging_wait'
            self.marshadow_timer = 90 # 3 seconds delay
            self.marshadow_target.current_state = 'marshadow_victim_emerging'
            
            new_x = random.randint(100, self.v_width - 100)
            self.marshadow_target.x = new_x
            self.x = new_x
            
            # Temporarily move to top of screen so get_window_environment scans ALL windows below it!
            old_y = self.marshadow_target.y
            self.marshadow_target.y = self.v_y
            new_env, _ = self.marshadow_target.get_window_environment()
            self.marshadow_emerge_floor_y = new_env['y']
            
            self.marshadow_target.y = self.marshadow_emerge_floor_y + 150
            self.y = self.marshadow_emerge_floor_y + 150

        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_marshadow_emerging_wait(self):
        self.marshadow_timer -= 1
        
        floor_y = getattr(self, 'marshadow_emerge_floor_y', self.v_height - 100)
        
        if hasattr(self, 'marshadow_canvas'):
            cx = (self.x + self.size_w/2) - self.v_x
            # floor_y is the top-left Y of the pet when standing. The physical floor is floor_y + size_h.
            cy = (floor_y + self.marshadow_target.size_h) - self.v_y
            
            for _ in range(3):
                size = random.randint(10, 20)
                color = random.choice(["#444444", "#2a004d", "#000000", "#1a1a1a"])
                item = self.marshadow_canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline="")
                self.marshadow_particles.append({'id': item, 'x': cx, 'y': cy, 'vx': random.uniform(-25, 25), 'vy': random.uniform(-40, -10), 'life': 35, 'is_explosion': True})
                
        self._update_marshadow_particles()
        
        if self.marshadow_timer <= 0:
            self.current_state = 'marshadow_emerging'
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_marshadow_emerging(self):
        if not hasattr(self, 'marshadow_target') or not self.marshadow_target:
            self.cancel_marshadow_arts()
            return
            
        floor_y = getattr(self, 'marshadow_emerge_floor_y', self.v_height - 100)
        
        self.y -= 15
        self.marshadow_target.y -= 15
        
        if self.marshadow_target.y <= floor_y:
            self.marshadow_target.y = floor_y
            self.y = floor_y
            self.current_state = 'marshadow_punching'
            self.marshadow_timer = 20

        self._update_marshadow_particles()
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_marshadow_punching(self):
        self.marshadow_timer -= 1
        
        if self.marshadow_timer == 19:
            if hasattr(self, 'marshadow_canvas'):
                cx = (self.x + self.size_w/2) - self.v_x
                cy = (self.y + self.size_h/2) - self.v_y
                self._spawn_circular_explosion(cx, cy)
                
            if self.marshadow_target:
                angle = random.uniform(math.pi + 0.3, math.pi * 2 - 0.3)
                force = random.uniform(25, 40)
                self.marshadow_target.v_x_velocity = math.cos(angle) * force
                self.marshadow_target.v_y_velocity = math.sin(angle) * force
                self.marshadow_target.current_state = 'marshadow_victim_flying'
                self.marshadow_victim_shadows.append(self.marshadow_target)

        self._update_marshadow_particles()
        
        if self.marshadow_timer <= 0:
            self.current_state = 'idle'
            self.marshadow_target = None
            try: self.window.attributes('-alpha', 1.0)
            except: pass
            
            if not getattr(self, 'marshadow_victim_shadows', []):
                self._cleanup_marshadow_vfx()
            else:
                self.schedule_loop(30, self.marshadow_manage_victim_loop)

        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _spawn_circular_explosion(self, cx, cy):
        for _ in range(150):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(40, 100)
            size = random.randint(10, 30)
            color = random.choice(["#444444", "#1a0033", "#330033", "#000000", "#4d004d", "#800080"])
            item = self.marshadow_canvas.create_rectangle(cx, cy, cx+size, cy+size, fill=color, outline="")
            self.marshadow_particles.append({'id': item, 'x': cx, 'y': cy, 'vx': math.cos(angle)*speed, 'vy': math.sin(angle)*speed, 'life': 40, 'is_explosion': True})

    def _update_marshadow_particles(self):
        if not hasattr(self, 'marshadow_canvas') or not self.marshadow_canvas: return
        for p in self.marshadow_particles[:]:
            if p.get('is_trail'):
                p['life'] -= 1
                if p['life'] <= 0:
                    self.marshadow_canvas.delete(p['id'])
                    self.marshadow_particles.remove(p)
                else:
                    coords = self.marshadow_canvas.coords(p['id'])
                    if coords:
                        shrink = 1
                        self.marshadow_canvas.coords(p['id'], coords[0]+shrink, coords[1]+shrink, coords[2]-shrink, coords[3]-shrink)
            elif p.get('is_explosion'):
                p['life'] -= 1
                if p['life'] <= 0:
                    self.marshadow_canvas.delete(p['id'])
                    self.marshadow_particles.remove(p)
                else:
                    p['x'] += p['vx']
                    p['y'] += p['vy']
                    p['vx'] *= 0.85
                    p['vy'] *= 0.85
                    size = max(1, int((p['life'] / 15) * 10))
                    self.marshadow_canvas.coords(p['id'], p['x'], p['y'], p['x']+size, p['y']+size)

    def marshadow_manage_victim_loop(self):
        if not hasattr(self, 'marshadow_vfx_win') or not self.marshadow_vfx_win or not self.marshadow_vfx_win.winfo_exists():
            return
            
        all_done = True
        for target in self.marshadow_victim_shadows[:]:
            if getattr(target, 'current_state', '') == 'marshadow_victim_flying':
                all_done = False
                if hasattr(self, 'marshadow_canvas'):
                    cx = (target.x + target.size_w/2) - self.v_x
                    cy = (target.y + target.size_h/2) - self.v_y
                    size = random.randint(10, 20)
                    item = self.marshadow_canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill="#111111", outline="")
                    self.marshadow_particles.append({'id': item, 'life': 10, 'is_trail': True})
            else:
                self.marshadow_victim_shadows.remove(target)
                
        self._update_marshadow_particles()
        
        if all_done and not self.marshadow_particles and getattr(self, 'current_state', '') not in ['marshadow_punching']:
            self._cleanup_marshadow_vfx()
        else:
            self.schedule_loop(30, self.marshadow_manage_victim_loop)

    def _fsm_marshadow_victim_submerging(self):
        self.update_position()
        self.schedule_loop(30, self.physics_loop)
    
    def _fsm_marshadow_victim_emerging(self):
        self.update_position()
        self.schedule_loop(30, self.physics_loop)
    
    def _fsm_marshadow_victim_flying(self):
        self.v_y_velocity += 0.8
        self.x += self.v_x_velocity
        self.y += self.v_y_velocity
        
        floor_y = getattr(self, 'default_floor_y', self.v_height - 100)
        if self.y >= floor_y:
            self.y = floor_y
            self.current_state = 'falling'
            
        if getattr(self, 'can_screen_wrap', False):
            if self.x <= self.v_x - self.size_w: self.x = self.v_x + self.v_width
            elif self.x >= self.v_x + self.v_width: self.x = self.v_x - self.size_w
        else:
            self.x = max(self.v_x, min(self.x, (self.v_x + self.v_width) - self.size_w))
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)
