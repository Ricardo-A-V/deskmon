import os
import math
import random
import tkinter as tk

class KoraidonMechanics:
    def cancel_koraidon_arts(self):
        # Prevents DWM memory leaks by destroying orphaned shockwave rendering windows
        if hasattr(self, 'krd_vfx_win') and self.krd_vfx_win and self.krd_vfx_win.winfo_exists():
            self.krd_vfx_win.destroy()
            self.krd_vfx_win = None

        for attr in ['krd_target_wall', 'krd_timer', 'krd_dive_vx', 'krd_dive_vy', 'krd_particles']:
            if hasattr(self, attr): delattr(self, attr)

        # Restores overridden entity physics parameters to ensure stable gravity fallbacks
        if hasattr(self, 'krd_original_flying'):
            self.is_flying = self.krd_original_flying
            delattr(self, 'krd_original_flying')

        if hasattr(self, 'krd_original_angle'):
            self.surface_angle = self.krd_original_angle
            delattr(self, 'krd_original_angle')

        if self.current_state not in ['dragged', 'exiting']:
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            self.anchored_hwnd = None
            self.current_state = 'falling'

    def _setup_krd_vfx_layer(self):
        # Deploys a full-screen transparent Canvas layer to process high-count particles optimally
        self.krd_particles = []
        if hasattr(self, 'krd_vfx_win') and self.krd_vfx_win and self.krd_vfx_win.winfo_exists():
            self.krd_vfx_canvas.delete("all")
            return
            
        self.krd_vfx_win = tk.Toplevel(self.window.master)
        self.krd_vfx_win.title("VFX_Koraidon")
        self.krd_vfx_win.overrideredirect(True)
        self.krd_vfx_win.attributes('-topmost', True)
        
        TRANS = '#010101'
        self.krd_vfx_win.config(bg=TRANS)
        try: self.krd_vfx_win.wm_attributes('-transparentcolor', TRANS)
        except: pass
        
        self.krd_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        
        # Injects WS_EX_TRANSPARENT into Windows API to discard hit-test events on the particle layer
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.krd_vfx_win.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x00080000 | 0x00000020)
        except: pass

        self.krd_vfx_canvas = tk.Canvas(self.krd_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS, highlightthickness=0)
        self.krd_vfx_canvas.pack()

    def _process_krd_particles(self):
        if not hasattr(self, 'krd_vfx_canvas') or not self.krd_vfx_canvas: return
        alive = []
        for p in getattr(self, 'krd_particles', []):
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1
            if p['life'] > 0:
                self.krd_vfx_canvas.coords(p['id'], p['x']-p['size'], p['y']-p['size'], p['x']+p['size'], p['y']+p['size'])
                alive.append(p)
            else:
                self.krd_vfx_canvas.delete(p['id'])
        self.krd_particles = alive

    def _spawn_wall_dirt(self):
        if not hasattr(self, 'krd_vfx_canvas'): return
        cx = self.x - self.v_x if self.krd_target_wall == 'left' else (self.x - self.v_x + self.size_w)
        cy = self.y - self.v_y + self.size_h / 2
        
        for _ in range(12):
            angle = random.uniform(-math.pi/2, math.pi/2) if self.krd_target_wall == 'left' else random.uniform(math.pi/2, 3*math.pi/2)
            speed = random.uniform(5.0, 15.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = random.choice(["#5C4033", "#8B5A2B", "#A0522D"])
            size = random.choice([2, 3, 4, 5])
            pid = self.krd_vfx_canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline=color)
            self.krd_particles.append({'id': pid, 'x': cx, 'y': cy, 'vx': vx, 'vy': vy, 'life': 20, 'size': size})

    def _spawn_fire_absorption(self):
        if not hasattr(self, 'krd_vfx_canvas'): return
        cx = self.x - self.v_x + self.size_w / 2
        cy = self.y - self.v_y + self.size_h / 2
        for _ in range(3):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(80, 160)
            px = cx + math.cos(angle) * dist
            py = cy + math.sin(angle) * dist
            color = random.choice(["#FF4500", "#FF8C00", "#FF0000", "#FFA500"])
            size = random.choice([2, 3, 4])
            
            speed = random.uniform(10.0, 20.0)
            vx = -math.cos(angle) * speed
            vy = -math.sin(angle) * speed
            
            pid = self.krd_vfx_canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color)
            self.krd_particles.append({'id': pid, 'x': px, 'y': py, 'vx': vx, 'vy': vy, 'life': 10, 'size': size})

    def _spawn_fire_trail(self):
        if not hasattr(self, 'krd_vfx_canvas'): return
        cx = self.x - self.v_x + self.size_w / 2
        cy = self.y - self.v_y + self.size_h / 2
        for _ in range(4):
            px = cx + random.uniform(-25, 25)
            py = cy + random.uniform(-25, 25)
            vx = random.uniform(-2.0, 2.0)
            vy = random.uniform(-2.0, 2.0)
            color = random.choice(["#FF4500", "#FF0000", "#FFA500", "#F39C12"])
            size = random.choice([3, 4, 5, 6])
            pid = self.krd_vfx_canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color)
            self.krd_particles.append({'id': pid, 'x': px, 'y': py, 'vx': vx, 'vy': vy, 'life': 15, 'size': size})

    def trigger_apex_crash(self):
        # Triggers a dismount jump to detach from window surfaces before initiating the sprint
        if self.y < self.default_floor_y - 15:
            self.current_state = 'koraidon_dismount'
            self.v_x_velocity = random.choice([-4.0, 4.0]) 
            self.v_y_velocity = -6.0 
            self.is_facing_right = (self.v_x_velocity > 0)
            
            self.krd_original_flying = getattr(self, 'is_flying', False)
            self.is_flying = False 
        else:
            self._start_koraidon_sprint()
            
        self.schedule_loop(50, self.physics_loop)

    def _fsm_koraidon_dismount(self):
        self.v_y_velocity += 1.5 
        self.x += self.v_x_velocity
        self.y += self.v_y_velocity
        
        if self.y >= self.default_floor_y and self.v_y_velocity > 0:
            self.y = self.default_floor_y
            self.v_y_velocity = 0.0
            self.v_x_velocity = 0.0
            self._start_koraidon_sprint()
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _start_koraidon_sprint(self):
        self._setup_krd_vfx_layer()
        if not hasattr(self, 'krd_original_flying'):
            self.krd_original_flying = getattr(self, 'is_flying', False)
            
        self.krd_original_angle = getattr(self, 'surface_angle', 0)
        self.is_flying = True
        
        screen_center_x = self.v_x + (self.v_width / 2)
        self.krd_target_wall = 'left' if self.x < screen_center_x else 'right'
        self.is_facing_right = (self.krd_target_wall == 'right')
        
        sprint_speed = 22.0
        self.v_x_velocity = -sprint_speed if self.krd_target_wall == 'left' else sprint_speed
        self.v_y_velocity = 0.0
        
        self.current_state = 'koraidon_sprint'

    def _fsm_koraidon_sprint(self):
        self.x += self.v_x_velocity
        self._process_krd_particles()
        
        hit_left = self.krd_target_wall == 'left' and self.x <= self.v_x
        hit_right = self.krd_target_wall == 'right' and (self.x + self.size_w) >= (self.v_x + self.v_width)
        
        if hit_left or hit_right:
            self.x = self.v_x if hit_left else (self.v_x + self.v_width - self.size_w)
            self.v_x_velocity = 0.0
            self.v_y_velocity = -18.0 
            
            self.surface_angle = 315 if hit_left else 45
            self.is_facing_right = hit_right
            self.current_state = 'koraidon_climb'
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_koraidon_climb(self):
        self.y += self.v_y_velocity
        self._process_krd_particles()
        
        monitor_midpoint_y = self.v_y + (self.v_height / 2)
        if self.y <= monitor_midpoint_y:
            self.y = monitor_midpoint_y
            
            self._spawn_wall_dirt()
            
            leap_direction = 1 if self.krd_target_wall == 'left' else -1 
            self.v_x_velocity = 15.0 * leap_direction
            self.v_y_velocity = -22.0 
            
            self.surface_angle = 0
            self.is_facing_right = (leap_direction == 1)
            self.current_state = 'koraidon_leap'
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_koraidon_leap(self):
        self.v_y_velocity += 1.5 
        self.x += self.v_x_velocity
        self.y += self.v_y_velocity
        self._process_krd_particles()
        
        if self.v_y_velocity >= 0:
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            self.current_state = 'koraidon_apex'
            self.krd_timer = 20 
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_koraidon_apex(self):
        self.krd_timer -= 1
        self._spawn_fire_absorption()
        self._process_krd_particles()
        
        if self.krd_timer <= 0:
            target = self._acquire_valid_dive_target()
            
            if not target:
                self.v_y_velocity = 50.0
                self.surface_angle = 90 
            else:
                tx_center = target.x + (target.size_w / 2)
                ty_center = target.y + (target.size_h / 2)
                kx_center = self.x + (self.size_w / 2)
                ky_center = self.y + (self.size_h / 2)
                
                dx = tx_center - kx_center
                dy = ty_center - ky_center
                distance = max(1, math.hypot(dx, dy))
                
                dive_speed = 100.0 
                self.v_x_velocity = (dx / distance) * dive_speed
                self.v_y_velocity = (dy / distance) * dive_speed
                self.is_facing_right = (dx > 0)
                
                # Dynamically maps sprite rotation to the trigonometric ballistic trajectory
                if self.is_facing_right:
                    self.surface_angle = math.degrees(math.atan2(self.v_y_velocity, self.v_x_velocity))
                else:
                    self.surface_angle = math.degrees(math.atan2(self.v_y_velocity, -self.v_x_velocity))
                
            self.current_state = 'koraidon_dive'
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_koraidon_dive(self):
        self.x += self.v_x_velocity
        self.y += self.v_y_velocity
        
        self._spawn_fire_trail()
        self._process_krd_particles()
        
        limit_bottom = (self.v_y + self.v_height) - self.size_h
        limit_top = self.v_y
        limit_left = self.v_x
        limit_right = (self.v_x + self.v_width) - self.size_w

        hit_boundary = False

        if self.y >= limit_bottom:
            self.y = limit_bottom
            hit_boundary = True
        elif self.y <= limit_top:
            self.y = limit_top
            hit_boundary = True

        if self.x <= limit_left:
            self.x = limit_left
            hit_boundary = True
        elif self.x >= limit_right:
            self.x = limit_right
            hit_boundary = True

        if hit_boundary:
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            self.surface_angle = 0 
            
            self._execute_impact_shockwave()
            
            self.current_state = 'koraidon_impact'
            self.krd_timer = 25 
            
        self.update_position()
        self.schedule_loop(16, self.physics_loop)

    def _fsm_koraidon_impact(self):
        self.krd_timer -= 1
        self._process_krd_particles()
        
        offset_x = random.choice([-5, 0, 5])
        offset_y = random.choice([-5, 0, 5])
        self.canvas.coords(self.canvas_image_id, (self.size_w//2) + offset_x, (self.size_h//2) + offset_y)
        
        if self.krd_timer <= 0:
            self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
            self.cancel_koraidon_arts()
            self.schedule_loop(50, self.physics_loop)
            return
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _acquire_valid_dive_target(self):
        if not getattr(self, 'get_all_pets', None): return None
        valid_targets = []
        for p in self.get_all_pets():
            if p == self or getattr(p, 'is_egg', False) or p.current_state in ['exiting', 'dragged']: 
                continue
            valid_targets.append(p)
        if not valid_targets: return None
        return random.choice(valid_targets)

    def _execute_impact_shockwave(self):
        if not hasattr(self, 'krd_vfx_canvas') or not self.krd_vfx_canvas: return
        
        # Centers visual shockwave cleanly regardless of the wall struck
        vfx_cx = self.x - self.v_x + self.size_w / 2
        vfx_cy = self.y - self.v_y + self.size_h / 2
        
        ring = self.krd_vfx_canvas.create_rectangle(vfx_cx - 10, vfx_cy - 10, vfx_cx + 10, vfx_cy + 10, outline="#E74C3C", width=16)
        self._animate_shockwave_ring(ring, vfx_cx, vfx_cy, 10, 0)

        if not getattr(self, 'get_all_pets', None): return
        
        # Absolute coordinates required to match remote entity matrices
        abs_cx = self.x + self.size_w / 2
        abs_cy = self.y + self.size_h / 2
        
        impact_radius = 600.0 
        for p in self.get_all_pets():
            if p == self or getattr(p, 'is_egg', False): continue
            
            px_center = p.x + (p.size_w / 2)
            py_center = p.y + (p.size_h / 2)
            
            dx = px_center - abs_cx
            dy = py_center - abs_cy
            dist = max(1.0, math.hypot(dx, dy))
            
            if dist <= impact_radius:
                force_mult = max(0.5, 1.0 - (dist / impact_radius))
                base_knockback = 80.0 
                
                if p.current_state.startswith('dark_') and hasattr(p, 'cancel_dark_arts'): p.cancel_dark_arts()
                if p.current_state.startswith('mewtwo_') and hasattr(p, 'cancel_mewtwo_arts'): p.cancel_mewtwo_arts()
                if p.current_state == 'bubbled': 
                    if hasattr(p, 'manage_bubble_vfx'): p.manage_bubble_vfx(False)
                    if hasattr(p, 'show_bubble_burst_vfx'): p.show_bubble_burst_vfx()
                if p.current_state in ['digging_in', 'digging', 'digging_out']:
                    p.canvas.itemconfig(p.canvas_image_id, state='normal')
                    p.canvas.coords(p.canvas_image_id, p.size_w//2, p.size_h//2)

                p.current_state = 'thrown'
                
                # Real 360-degree vector generation mapping
                p.v_x_velocity = (dx / dist) * base_knockback * force_mult
                p.v_y_velocity = (dy / dist) * base_knockback * force_mult
                
                # Failsafe against absolute horizontal overlaps stalling the engine
                if abs(dy) < 10:
                    p.v_y_velocity = random.choice([-20.0, 20.0])
                
                # ANTI-STICK PROTOCOL: Physically rips entities from screen limits to bypass pet.py wall-clamp logic
                if p.y <= p.v_y + 20: 
                    p.y += 25.0
                    p.v_y_velocity = abs(p.v_y_velocity) + 15.0 
                    
                if p.x <= p.v_x + 20:
                    p.x += 25.0
                    p.v_x_velocity = abs(p.v_x_velocity) + 15.0 
                    
                if p.x >= (p.v_x + p.v_width) - p.size_w - 20:
                    p.x -= 25.0
                    p.v_x_velocity = -abs(p.v_x_velocity) - 15.0 
                    
                floor_limit = (p.v_y + p.v_height) - p.size_h
                if p.y >= floor_limit - 20:
                    p.y -= 25.0
                    p.v_y_velocity = -abs(p.v_y_velocity) - 15.0 

                p.climbing_surface = 'floor'
                p.anchored_hwnd = None

    def _animate_shockwave_ring(self, ring_id, cx, cy, radius, frame):
        if not hasattr(self, 'krd_vfx_canvas') or not self.krd_vfx_canvas: return
        self.krd_vfx_canvas.delete(ring_id)
        if frame >= 20: return
            
        new_radius = radius + 25
        
        color_fade = ["#E74C3C", "#E67E22", "#F39C12", "#F1C40F", "#FFFFFF"]
        idx = min(frame // 4, 4)
        
        ring_id = self._draw_pixel_circle_bbox(
            self.krd_vfx_canvas, 
            cx - new_radius, cy - new_radius, cx + new_radius, cy + new_radius, 
            outline=color_fade[idx], width=16
        )
        
        self.window.after(16, lambda: self._animate_shockwave_ring(ring_id, cx, cy, new_radius, frame + 1))