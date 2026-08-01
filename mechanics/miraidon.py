import os
import math
import random
import tkinter as tk

class MiraidonMechanics:
    def cancel_miraidon_arts(self):
        if hasattr(self, 'mrd_vfx_win') and self.mrd_vfx_win and self.mrd_vfx_win.winfo_exists():
            self.mrd_vfx_win.destroy()
            self.mrd_vfx_win = None

        for attr in ['mrd_timer', 'mrd_dash_count', 'mrd_particles', 'mrd_trail', 'mrd_target', 'mrd_para_timer']:
            if hasattr(self, attr): delattr(self, attr)

        self.canvas.delete("vfx_mrd_para")

        if hasattr(self, 'mrd_original_flying'):
            self.is_flying = self.mrd_original_flying
            delattr(self, 'mrd_original_flying')

        if hasattr(self, 'mrd_original_angle'):
            self.surface_angle = self.mrd_original_angle
            delattr(self, 'mrd_original_angle')

        if hasattr(self, 'fsm') and hasattr(self, '_fsm_active'):
            self.fsm['idle'] = self._fsm_active
            self.fsm['walking'] = self._fsm_active

        if self.current_state not in ['dragged', 'exiting'] and getattr(self, 'current_state', '') != 'miraidon_paralyzed':
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            self.anchored_hwnd = None
            self.surface_angle = 0
            
            if getattr(self, 'is_flying', False):
                self.floor_y = getattr(self, 'target_floor_y', self.y)
                self.current_state = 'ascending'
            else:
                self.current_state = 'falling'

    def trigger_electro_drift(self):
        self._setup_mrd_vfx_layer()
        self.mrd_original_flying = getattr(self, 'is_flying', False)
        self.mrd_original_angle = getattr(self, 'surface_angle', 0)
        self.is_flying = True
        
        if hasattr(self, 'fsm') and hasattr(self, '_fsm_wait'):
            self.fsm['idle'] = self._fsm_wait
            self.fsm['walking'] = self._fsm_wait
            
        self.current_state = 'miraidon_absorb'
        self.mrd_timer = 90 
        self.v_x_velocity = 0.0
        self.v_y_velocity = 0.0
        self.schedule_loop(30, self.physics_loop)

    def _setup_mrd_vfx_layer(self):
        self.mrd_particles = []
        self.mrd_trail = []
        if hasattr(self, 'mrd_vfx_win') and self.mrd_vfx_win and self.mrd_vfx_win.winfo_exists():
            self.mrd_vfx_canvas.delete("all")
            return
            
        self.mrd_vfx_win = tk.Toplevel(self.window.master)
        self.mrd_vfx_win.title("VFX_Miraidon")
        self.mrd_vfx_win.overrideredirect(True)
        self.mrd_vfx_win.attributes('-topmost', True)
        
        TRANS = '#010101'
        self.mrd_vfx_win.config(bg=TRANS)
        try: self.mrd_vfx_win.wm_attributes('-transparentcolor', TRANS)
        except: pass
        
        self.mrd_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.mrd_vfx_win.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x00080000 | 0x00000020)
        except: pass

        self.mrd_vfx_canvas = tk.Canvas(self.mrd_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS, highlightthickness=0)
        self.mrd_vfx_canvas.pack()

    def _process_mrd_particles(self):
        if not hasattr(self, 'mrd_vfx_canvas') or not self.mrd_vfx_canvas: return
        alive = []
        for p in getattr(self, 'mrd_particles', []):
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1
            if p['life'] > 0:
                self.mrd_vfx_canvas.coords(p['id'], p['x']-p['size'], p['y']-p['size'], p['x']+p['size'], p['y']+p['size'])
                alive.append(p)
            else:
                self.mrd_vfx_canvas.delete(p['id'])
        self.mrd_particles = alive

    def _process_mrd_trail(self):
        if not hasattr(self, 'mrd_vfx_canvas') or not self.mrd_vfx_canvas: return
        
        alive_trail = []
        for t in getattr(self, 'mrd_trail', []):
            t['life'] -= 1
            if t['life'] > 0:
                color_fade = ["#00FFFF", "#00BFFF", "#1E90FF", "#00008B"]
                idx = min(len(color_fade)-1, int((60 - t['life']) / 15))
                self.mrd_vfx_canvas.itemconfig(t['id'], fill=color_fade[idx], outline=color_fade[idx])
                alive_trail.append(t)
            else:
                self.mrd_vfx_canvas.delete(t['id'])
        self.mrd_trail = alive_trail
        
        if not getattr(self, 'get_all_pets', None): return
        for p in self.get_all_pets():
            if p == self or getattr(p, 'is_egg', False) or p.current_state in ['exiting', 'dragged', 'miraidon_paralyzed']: 
                continue
            
            px_center = p.x + (p.size_w / 2)
            py_center = p.y + (p.size_h / 2)
            
            for t in self.mrd_trail:
                # CORRECCIÓN: Translación matemática para devolver las coordenadas 
                # relativas del Canvas al espacio absoluto de colisión de Windows
                abs_tx = t['x'] + self.v_x
                abs_ty = t['y'] + self.v_y
                
                if math.hypot(px_center - abs_tx, py_center - abs_ty) < (p.size_w / 2 + t['size']):
                    self._apply_miraidon_paralysis(p)
                    break

    def _apply_miraidon_paralysis(self, target):
        if target.current_state.startswith('dark_') and hasattr(target, 'cancel_dark_arts'): target.cancel_dark_arts()
        elif target.current_state == 'tk_channeling':
            target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
            if getattr(target, 'tk_target', None):
                t_targ = target.tk_target
                target.manage_tk_aura(t_targ.canvas, t_targ.size_w if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size, t_targ.size_h if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size, False)
                t_targ.current_state = 'falling'
                if hasattr(t_targ, 'tk_master'): t_targ.tk_master = None
            target.tk_target = None
        elif target.current_state == 'tk_lifted':
            target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
            if getattr(target, 'tk_master', None):
                target.tk_master.tk_target = None
                target.tk_master.manage_tk_aura(target.tk_master.canvas, target.tk_master.size_w, target.tk_master.size_h, False)
                target.tk_master.current_state = 'falling'
            target.tk_master = None
        elif target.current_state == 'bubbled':
            target.manage_bubble_vfx(False)
            target.show_bubble_burst_vfx()
        elif target.current_state in ['digging_in', 'digging', 'digging_out']:
            target.canvas.itemconfig(target.canvas_image_id, state='normal')
            target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
            
        if getattr(target, 'is_glitching', False):
            target.is_glitching = False
            target.glitch_teleports_left = 0
            
        for prefix, cancel_func in [('mewtwo_', 'cancel_mewtwo_arts'), ('hooh_', 'cancel_hooh_arts'), ('kyogre_', 'cancel_kyogre_arts'), ('groudon_', 'cancel_groudon_arts'), ('lugia_', 'cancel_lugia_arts'), ('rayquaza_', 'cancel_rayquaza_arts'), ('dialga_', 'cancel_dialga_arts'), ('palkia_', 'cancel_palkia_arts'), ('giratina_', 'cancel_giratina_arts'), ('koraidon_', 'cancel_koraidon_arts')]:
            if target.current_state.startswith(prefix) and hasattr(target, cancel_func): getattr(target, cancel_func)()

        target.canvas.itemconfig(target.canvas_image_id, state='normal')
        try: target.window.attributes('-alpha', 1.0)
        except: pass

        target.current_state = 'miraidon_paralyzed'
        target.mrd_para_timer = 300 
        target.v_x_velocity = 0.0
        target.v_y_velocity = 0.0
        
        target.miraidon_para_vfx_loop()

    def _fsm_miraidon_paralyzed(self):
        self.mrd_para_timer -= 1
        
        # Retains native robotic jitter effect
        if self.mrd_para_timer % 8 == 0:
            offset_x = random.choice([-3, 0, 3])
            offset_y = random.choice([-3, 0, 3])
            self.canvas.coords(self.canvas_image_id, (self.size_w//2) + offset_x, (self.size_h//2) + offset_y)
            
        # Applies horizontal inertia explicitly to enable lateral throw trajectories
        self.v_x_velocity *= 0.95 
        self.x += self.v_x_velocity
        
        # Resolves lateral collisions dynamically
        if getattr(self, 'can_screen_wrap', False):
            if self.x <= self.v_x - self.size_w: self.x = self.v_x + self.v_width
            elif self.x >= self.v_x + self.v_width: self.x = self.v_x - self.size_w
        else:
            if self.x <= self.v_x:
                self.x = self.v_x
                self.v_x_velocity *= -0.7 
            elif self.x >= (self.v_x + self.v_width) - self.size_w:
                self.x = (self.v_x + self.v_width) - self.size_w
                self.v_x_velocity *= -0.7

        gravity = 4.0 if getattr(self, 'heavy_fall', False) else 1.5
        self.v_y_velocity += gravity
        self.y += self.v_y_velocity
        
        current_env, _ = self.get_window_environment()
        
        # Calculates fall tolerance to prevent high-velocity tunneling
        fall_tolerance = max(15, int(self.v_y_velocity) + 15) if self.v_y_velocity > 0 else 15
        physical_floor = current_env['y'] if self.y <= current_env['y'] + fall_tolerance else self.default_floor_y
        
        if self.y >= physical_floor:
            self.y = physical_floor
            self.v_y_velocity = 0.0
            self.v_x_velocity = 0.0 
            
        self.update_position()
        
        if self.mrd_para_timer <= 0:
            self.canvas.delete("vfx_mrd_para")
            self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
            if getattr(self, 'is_flying', False):
                self.floor_y = getattr(self, 'target_floor_y', self.y)
                self.current_state = 'ascending'
            else:
                self.current_state = 'idle'
                
        # Accelerated to 20ms to match the native throwing frame rate
        self.schedule_loop(20, self.physics_loop)

    def miraidon_para_vfx_loop(self):
        # Whitelists the dragged state to maintain visual persistence during user interaction
        if getattr(self, 'current_state', '') not in ['miraidon_paralyzed', 'dragged']: 
            self.canvas.delete("vfx_mrd_para")
            return
            
        self.canvas.delete("vfx_mrd_para")
        if random.randint(1, 100) <= 30: 
            cx = self.size_w / 2
            cy = self.size_h / 2
            rx = cx + random.randint(-20, 20)
            ry = cy + random.randint(-20, 20)
            self.canvas.create_line(rx-5, ry-5, rx+5, ry+5, fill="#FFFF00", width=2, tags="vfx_mrd_para")
            self.canvas.create_line(rx+5, ry-5, rx-5, ry+5, fill="#FFFF00", width=2, tags="vfx_mrd_para")
            
        self.window.after(100, self.miraidon_para_vfx_loop)

    def _spawn_electric_absorption(self):
        if not hasattr(self, 'mrd_vfx_canvas'): return
        cx = self.x - self.v_x + self.size_w / 2
        cy = self.y - self.v_y + self.size_h / 2
        
        for _ in range(3):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(80, 160)
            px = cx + math.cos(angle) * dist
            py = cy + math.sin(angle) * dist
            color = random.choice(["#00FFFF", "#00BFFF", "#7DF9FF", "#E0FFFF"])
            size = random.choice([2, 3, 4])
            
            speed = random.uniform(10.0, 20.0)
            vx = -math.cos(angle) * speed
            vy = -math.sin(angle) * speed
            
            pid = self.mrd_vfx_canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color)
            self.mrd_particles.append({'id': pid, 'x': px, 'y': py, 'vx': vx, 'vy': vy, 'life': 10, 'size': size})

    def _spawn_electric_trail_segment(self):
        if not hasattr(self, 'mrd_vfx_canvas'): return
        cx = self.x - self.v_x + self.size_w / 2
        cy = self.y - self.v_y + self.size_h / 2
        
        color = "#00FFFF"
        size = 8
        px = cx + random.uniform(-10, 10)
        py = cy + random.uniform(-10, 10)
        pid = self.mrd_vfx_canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color)
        
        self.mrd_trail.append({'id': pid, 'x': px, 'y': py, 'life': 60, 'size': size})

    def _fsm_miraidon_absorb(self):
        self.mrd_timer -= 1
        self._spawn_electric_absorption()
        self._process_mrd_particles()
        
        if self.mrd_timer <= 0:
            self.current_state = 'miraidon_descent'
            self.v_y_velocity = 8.0 
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_miraidon_descent(self):
        self.y += self.v_y_velocity
        self._process_mrd_particles()
        
        if self.y >= self.default_floor_y:
            self.y = self.default_floor_y
            self.mrd_dash_count = 0
            
            self.v_y_velocity = 0.0
            self.is_facing_right = random.choice([True, False])
            self.v_x_velocity = 50.0 if self.is_facing_right else -50.0
            
            self.surface_angle = 0
            self.current_state = 'miraidon_dash'
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_miraidon_dash(self):
        self.x += self.v_x_velocity
        self.y += self.v_y_velocity
        
        self._spawn_electric_trail_segment()
        self._process_mrd_trail()
        
        limit_bottom = getattr(self, 'default_floor_y', (self.v_y + self.v_height) - self.size_h)
        limit_top = self.v_y
        limit_left = self.v_x
        limit_right = (self.v_x + self.v_width) - self.size_w
        
        hit_boundary = False
        target_reached = False
        vx_new, vy_new = self.v_x_velocity, self.v_y_velocity

        if self.mrd_dash_count == 5 and getattr(self, 'mrd_target', None):
            if self.mrd_target.window.winfo_exists():
                tx = self.mrd_target.x + self.mrd_target.size_w / 2
                ty = self.mrd_target.y + self.mrd_target.size_h / 2
                mx = self.x + self.size_w / 2
                my = self.y + self.size_h / 2
                if math.hypot(tx - mx, ty - my) < max(self.size_w, self.size_h):
                    target_reached = True
            else:
                self.mrd_target = None 

        # Colisionador de Esquinas y Planos: Obliga la alteración del vector evadiendo el límite impactado
        if self.y >= limit_bottom and self.v_y_velocity > 0:
            self.y = limit_bottom
            hit_boundary = True
            vy_new = random.uniform(-50.0, -20.0) 
            vx_new = random.uniform(-40.0, 40.0)
        elif self.y <= limit_top and self.v_y_velocity < 0:
            self.y = limit_top
            hit_boundary = True
            vy_new = random.uniform(20.0, 50.0) 
            vx_new = random.uniform(-40.0, 40.0)
            
        if self.x <= limit_left and self.v_x_velocity < 0:
            self.x = limit_left
            hit_boundary = True
            vx_new = random.uniform(20.0, 50.0) 
            # Inyección anti-adherencia: Fuerza el despegue si el impacto lateral ocurre a ras del suelo
            if self.y >= limit_bottom - 5: 
                vy_new = random.uniform(-50.0, -20.0)
            elif self.y <= limit_top + 5:
                vy_new = random.uniform(20.0, 50.0)
            else:
                vy_new = random.uniform(-40.0, 40.0)
                
        elif self.x >= limit_right and self.v_x_velocity > 0:
            self.x = limit_right
            hit_boundary = True
            vx_new = random.uniform(-50.0, -20.0) 
            if self.y >= limit_bottom - 5:
                vy_new = random.uniform(-50.0, -20.0)
            elif self.y <= limit_top + 5:
                vy_new = random.uniform(20.0, 50.0)
            else:
                vy_new = random.uniform(-40.0, 40.0)

        if hit_boundary or target_reached:
            self.mrd_dash_count += 1
            
            if self.mrd_dash_count >= 6 or target_reached:
                self.v_x_velocity = 0.0
                self.v_y_velocity = 0.0
                self.surface_angle = 0
                self._execute_miraidon_shockwave()
                self.current_state = 'miraidon_impact'
                self.mrd_timer = 20
            elif self.mrd_dash_count == 5:
                target = self._acquire_valid_dive_target()
                if target:
                    self.mrd_target = target
                    tx = target.x + target.size_w / 2
                    ty = target.y + target.size_h / 2
                    mx = self.x + self.size_w / 2
                    my = self.y + self.size_h / 2
                    vx_new = tx - mx
                    vy_new = ty - my
                else:
                    self.mrd_target = None
                    
                self._normalize_dash_vector(vx_new, vy_new)
            else:
                self._normalize_dash_vector(vx_new, vy_new)
                
        self.update_position()
        self.schedule_loop(16, self.physics_loop)

    def _normalize_dash_vector(self, vx_new, vy_new):
        dist = max(1.0, math.hypot(vx_new, vy_new))
        self.v_x_velocity = (vx_new / dist) * 50.0
        self.v_y_velocity = (vy_new / dist) * 50.0
        
        self.is_facing_right = (self.v_x_velocity > 0)
        
        if self.is_facing_right:
            self.surface_angle = math.degrees(math.atan2(self.v_y_velocity, self.v_x_velocity))
        else:
            self.surface_angle = math.degrees(math.atan2(self.v_y_velocity, -self.v_x_velocity))

    def _fsm_miraidon_impact(self):
        self.mrd_timer -= 1
        self._process_mrd_trail()
        
        offset_x = random.choice([-3, 0, 3])
        offset_y = random.choice([-3, 0, 3])
        self.canvas.coords(self.canvas_image_id, (self.size_w//2) + offset_x, (self.size_h//2) + offset_y)
        
        if self.mrd_timer <= 0:
            self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
            self.cancel_miraidon_arts()
            self.schedule_loop(50, self.physics_loop)
            return
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _acquire_valid_dive_target(self):
        if not getattr(self, 'get_all_pets', None): return None
        valid_targets = []
        for p in self.get_all_pets():
            if p == self or getattr(p, 'is_egg', False) or p.current_state in ['exiting', 'dragged', 'miraidon_paralyzed']: 
                continue
            valid_targets.append(p)
        if not valid_targets: return None
        return random.choice(valid_targets)

    def _execute_miraidon_shockwave(self):
        if not hasattr(self, 'mrd_vfx_canvas') or not self.mrd_vfx_canvas: return
        
        cx = self.x - self.v_x + self.size_w / 2
        cy = self.y - self.v_y + self.size_h / 2
        
        ring = self.mrd_vfx_canvas.create_oval(cx - 10, cy - 10, cx + 10, cy + 10, outline="#00FFFF", width=10)
        self._animate_mrd_shockwave_ring(ring, cx, cy, 10, 0)

        if not getattr(self, 'get_all_pets', None): return
        
        abs_cx = self.x + self.size_w / 2
        abs_cy = self.y + self.size_h / 2
        
        impact_radius = 350.0 
        for p in self.get_all_pets():
            if p == self or getattr(p, 'is_egg', False): continue
            
            px_center = p.x + (p.size_w / 2)
            py_center = p.y + (p.size_h / 2)
            
            dx = px_center - abs_cx
            dy = py_center - abs_cy
            dist = max(1.0, math.hypot(dx, dy))
            
            if dist <= impact_radius:
                force_mult = max(0.5, 1.0 - (dist / impact_radius))
                base_knockback = 40.0 
                
                if p.current_state.startswith('dark_') and hasattr(p, 'cancel_dark_arts'): p.cancel_dark_arts()
                if p.current_state.startswith('mewtwo_') and hasattr(p, 'cancel_mewtwo_arts'): p.cancel_mewtwo_arts()
                if p.current_state.startswith('koraidon_') and hasattr(p, 'cancel_koraidon_arts'): p.cancel_koraidon_arts()
                if p.current_state == 'bubbled': 
                    if hasattr(p, 'manage_bubble_vfx'): p.manage_bubble_vfx(False)
                    if hasattr(p, 'show_bubble_burst_vfx'): p.show_bubble_burst_vfx()
                if p.current_state in ['digging_in', 'digging', 'digging_out']:
                    p.canvas.itemconfig(p.canvas_image_id, state='normal')
                    p.canvas.coords(p.canvas_image_id, p.size_w//2, p.size_h//2)

                p.current_state = 'thrown'
                p.v_x_velocity = (dx / dist) * base_knockback * force_mult
                p.v_y_velocity = -25.0 * force_mult 
                
                if p.y <= p.v_y + 20: p.y += 25.0
                if p.x <= p.v_x + 20: p.x += 25.0
                if p.x >= (p.v_x + p.v_width) - p.size_w - 20: p.x -= 25.0

                p.climbing_surface = 'floor'
                p.anchored_hwnd = None

    def _animate_mrd_shockwave_ring(self, ring_id, cx, cy, radius, frame):
        if not hasattr(self, 'mrd_vfx_canvas') or not self.mrd_vfx_canvas: return
        if frame > 15:
            self.mrd_vfx_canvas.delete(ring_id)
            return
            
        new_radius = radius + 35
        self.mrd_vfx_canvas.coords(ring_id, cx - new_radius, cy - new_radius, cx + new_radius, cy + new_radius)
        self.window.after(16, lambda: self._animate_mrd_shockwave_ring(ring_id, cx, cy, new_radius, frame + 1))