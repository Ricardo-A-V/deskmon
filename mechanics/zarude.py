import random
import math
import tkinter as tk

class ZarudeMechanics:
    def start_zarude_mechanic(self):
        if getattr(self, 'current_state', '') in ['dragged', 'exiting']: return
        if getattr(self, 'zarude_cooldown', 0) > 0: return
        if hasattr(self, 'is_global_mechanic_active') and self.is_global_mechanic_active(): return

        name = self.pet_name.lower().replace("_", "").replace("-", "")
        if name not in ["zarude"]: return

        self.zarude_cooldown = 108000 # 1 hour
        self.zarude_target = None
        self.zarude_timer = 90
        
        # Must be on floor to start channeling
        target_floor = self.v_y if getattr(self, 'gravity_inverted', False) else self.default_floor_y
        if hasattr(self, 'get_window_environment'):
            current_env, _ = self.get_window_environment()
            if current_env['hwnd']: target_floor = current_env['y']
            
        if abs(self.y - target_floor) > 10:
            self.current_state = 'falling'
            return
            
        self.current_state = 'zarude_channeling'
        self._init_zarude_vfx()
        self.schedule_loop(33, self.physics_loop)

    def _init_zarude_vfx(self):
        if not hasattr(self, 'zarude_vfx_win') or not self.zarude_vfx_win or not self.zarude_vfx_win.winfo_exists():
            self.zarude_vfx_win = tk.Toplevel(self.window.master)
            self.zarude_vfx_win.title("VFX_Zarude_Ignore")
            self.zarude_vfx_win.overrideredirect(True)
            self.zarude_vfx_win.attributes('-topmost', True)
            TRANS_COLOR = '#010101'
            self.zarude_vfx_win.config(bg=TRANS_COLOR)
            try: self.zarude_vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
            except: pass
            
            try:
                import ctypes
                hwnd = ctypes.windll.user32.GetParent(self.zarude_vfx_win.winfo_id())
                style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
                ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x00080000 | 0x00000020 | 0x00000008)
            except: pass
            
            self.zarude_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
            self.zarude_canvas = tk.Canvas(self.zarude_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
            self.zarude_canvas.pack()
            self.zarude_particles = []
            self.zarude_vfx_loop_running = True
            self._zarude_vfx_loop()
            
    def _zarude_vfx_loop(self):
        if hasattr(self, 'zarude_vfx_win') and self.zarude_vfx_win and self.zarude_vfx_win.winfo_exists():
            self.zarude_canvas.delete("vine")
            
            # Draw vines if swinging
            if getattr(self, 'current_state', '') in ['zarude_swinging', 'zarude_air']:
                cx = self.x - self.v_x + self.size_w/2
                cy = self.y - self.v_y + self.size_h/2
                
                # Vine to ceiling
                if hasattr(self, 'zarude_pivot_x'):
                    px = self.zarude_pivot_x - self.v_x
                    py = self.zarude_pivot_y - self.v_y
                    if hasattr(self, '_draw_pixel_line'):
                        self._draw_pixel_line(self.zarude_canvas, [px, py, cx, cy], fill="#006400", width=4, tags="vine")
                    else:
                        self.zarude_canvas.create_line(px, py, cx, cy, fill="#006400", width=4, tags="vine")
                        
                # Vine to target
                if getattr(self, 'zarude_target', None):
                    tx = self.zarude_target.x - self.v_x + self.zarude_target.size_w/2
                    ty = self.zarude_target.y - self.v_y + self.zarude_target.size_h/2
                    if hasattr(self, '_draw_pixel_line'):
                        self._draw_pixel_line(self.zarude_canvas, [cx, cy, tx, ty], fill="#228B22", width=3, tags="vine")
                    else:
                        self.zarude_canvas.create_line(cx, cy, tx, ty, fill="#228B22", width=3, tags="vine")
            
            # Update leaf particles
            alive = []
            for p in getattr(self, 'zarude_particles', []):
                p['life'] -= 1
                if p['life'] > 0:
                    self.zarude_canvas.move(p['id'], p['vx'], p['vy'])
                    if p.get('gravity'):
                        p['vy'] += 1.0
                    alive.append(p)
                else:
                    self.zarude_canvas.delete(p['id'])
            self.zarude_particles = alive
            
            if getattr(self, 'current_state', '').startswith('zarude_') or getattr(self, 'current_state', '').startswith('zarude_victim_') or self.zarude_particles:
                self.window.after(33, self._zarude_vfx_loop)
            else:
                self.zarude_vfx_win.destroy()
                self.zarude_vfx_win = None
                self.zarude_vfx_loop_running = False
        else:
            self.zarude_vfx_loop_running = False

    def trigger_zarude_leaf_vfx(self, gx, gy, explosion=True):
        if not hasattr(self, 'zarude_vfx_win') or not self.zarude_vfx_win or not self.zarude_vfx_win.winfo_exists():
            self._init_zarude_vfx()
            
        cx = gx - self.v_x
        cy = gy - self.v_y
        
        count = 30 if explosion else 2
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(5, 25) if explosion else random.uniform(1, 4)
            vx = math.cos(angle) * speed if explosion else random.uniform(-2, 2)
            vy = math.sin(angle) * speed if explosion else random.uniform(-5, -2)
            color = random.choice(["#228B22", "#00FF00", "#32CD32", "#006400"])
            size = random.choice([3, 5, 7])
            
            pid = self.zarude_canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline="")
            self.zarude_particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': random.randint(15, 30), 'gravity': explosion})

    def _fsm_zarude_channeling(self):
        self.zarude_timer -= 1
        
        # Absorb plants from below
        cx = self.x + self.size_w/2
        cy = self.y + self.size_h
        if self.zarude_timer % 2 == 0:
            self.trigger_zarude_leaf_vfx(cx + random.uniform(-40, 40), cy, explosion=False)
            
        if self.zarude_timer <= 0:
            self.current_state = 'zarude_jump_to_ceiling'
            self.v_y_velocity = -40.0
            self.v_x_velocity = 15.0 if self.is_facing_right else -15.0
            self.zarude_phase = 1
            self.zarude_swing_count = 0
            self.zarude_target_swings = random.randint(4, 8)
            
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_zarude_jump_to_ceiling(self):
        self.v_y_velocity += 1.5 # Gravity
        self.y += self.v_y_velocity
        self.x += getattr(self, 'v_x_velocity', 0)
        self.update_position()
        
        if self.y < self.v_y + 150 or self.v_y_velocity > -5:
            self.current_state = 'zarude_air'
            self.v_x_velocity = 20.0 if self.is_facing_right else -20.0
            self.v_y_velocity = 0.0
            
        self.schedule_loop(33, self.physics_loop)

    def _fsm_zarude_air(self):
        if getattr(self, 'zarude_is_pulling', False):
            self.zarude_pull_timer -= 1
            t = getattr(self, 'zarude_target', None)
            if t and t.current_state != 'exiting':
                target_x = self.x + self.size_w/2 - t.size_w/2
                target_y = self.y + self.size_h + 30
                t.x += (target_x - t.x) * 0.2
                t.y += (target_y - t.y) * 0.2
                t.update_position()
            else:
                self.zarude_target = None
                
            if self.zarude_pull_timer <= 0:
                self.zarude_is_pulling = False
                if self.zarude_target:
                    self.zarude_phase = 2
                    self.zarude_swing_count = 0
                    self.zarude_target_swings = random.randint(4, 8)
                else:
                    self.zarude_phase = 3
                    self.zarude_swing_count = 0
                    self.zarude_target_swings = 2
                    
                dir = 1 if self.is_facing_right else -1
                self.current_state = 'zarude_swinging'
                self.zarude_angle = -dir * 0.8
                cy = self.y + self.size_h/2
                self.zarude_L = max(150.0, (cy - self.v_y) / math.cos(0.8))
                self.zarude_pivot_y = self.v_y
                self.zarude_pivot_x = (self.x + self.size_w/2) - self.zarude_L * math.sin(self.zarude_angle)
            
            self.schedule_loop(33, self.physics_loop)
            return

        self.v_y_velocity += 1.5
        self.y += self.v_y_velocity
        self.x += getattr(self, 'v_x_velocity', 0)
        
        # Hit walls in air? bounce
        if self.x <= self.v_x:
            self.x = self.v_x
            self.v_x_velocity *= -1
            self.is_facing_right = True
        elif self.x >= self.v_x + self.v_width - self.size_w:
            self.x = self.v_x + self.v_width - self.size_w
            self.v_x_velocity *= -1
            self.is_facing_right = False
            
        dir = 1 if self.is_facing_right else -1
        
        # Rotate back towards 0
        self.surface_angle = self.surface_angle * 0.8
        
        if getattr(self, 'zarude_target', None):
            t = self.zarude_target
            if t.current_state != 'exiting':
                angle_rad = math.radians(self.surface_angle)
                t_dist = self.size_h/2 + 30 + t.size_h/2
                t_cx = (self.x + self.size_w/2) + t_dist * math.sin(angle_rad)
                t_cy = (self.y + self.size_h/2) + t_dist * math.cos(angle_rad)
                t.x = t_cx - t.size_w/2
                t.y = t_cy - t.size_h/2
                t.surface_angle = self.surface_angle
                t.update_position()
            else:
                self.zarude_target = None
        
        self.update_position()
        
        # Start next swing when starting to fall
        if self.v_y_velocity >= 5.0 and self.y > self.v_y + 80:
            self.zarude_swing_count += 1
            
            # Phase Logic Check
            if self.zarude_phase == 1 and self.zarude_swing_count >= self.zarude_target_swings:
                target = self._get_zarude_target()
                if target:
                    self.zarude_target = target
                    if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
                    target.current_state = 'zarude_victim_grabbed'
                    self.zarude_is_pulling = True
                    self.zarude_pull_timer = 15
                    self.v_x_velocity = 0
                    self.v_y_velocity = 0
                    self.schedule_loop(33, self.physics_loop)
                    return
                else:
                    self.zarude_phase = 3
                    self.zarude_swing_count = 0
                    self.zarude_target_swings = 2
            elif self.zarude_phase == 2 and self.zarude_swing_count >= self.zarude_target_swings:
                # Throw
                if getattr(self, 'zarude_target', None):
                    t = self.zarude_target
                    if hasattr(t, 'interrupt_current_state'): t.interrupt_current_state()
                    t.current_state = 'zarude_victim_thrown'
                    t.v_x_velocity = dir * 30.0
                    t.v_y_velocity = 45.0
                    self.trigger_zarude_leaf_vfx(self.x + self.size_w/2, self.y + self.size_h/2, explosion=True)
                    self.zarude_target = None
                    
                self.zarude_phase = 3
                self.zarude_swing_count = 0
                self.zarude_target_swings = 2
            elif self.zarude_phase == 3 and self.zarude_swing_count >= self.zarude_target_swings:
                self.current_state = 'falling'
                self.surface_angle = 0
                self.v_x_velocity = dir * 5.0
                self.v_y_velocity = -5.0
                self.schedule_loop(33, self.physics_loop)
                return
                
            # Compute new pivot
            self.current_state = 'zarude_swinging'
            self.zarude_angle = -dir * 0.8
            cy = self.y + self.size_h/2
            self.zarude_L = max(150.0, (cy - self.v_y) / math.cos(0.8))
            self.zarude_pivot_y = self.v_y
            self.zarude_pivot_x = (self.x + self.size_w/2) - self.zarude_L * math.sin(self.zarude_angle)
            
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_zarude_swinging(self):
        dir = 1 if self.is_facing_right else -1
        self.zarude_angle += dir * 0.08
        
        # Check wall collision anticipating the pivot
        cx = self.zarude_pivot_x + self.zarude_L * math.sin(self.zarude_angle)
        if cx - self.size_w/2 < self.v_x:
            self.is_facing_right = True
            dir = 1
        elif cx + self.size_w/2 > self.v_x + self.v_width:
            self.is_facing_right = False
            dir = -1
            
        self.x = self.zarude_pivot_x + self.zarude_L * math.sin(self.zarude_angle) - self.size_w/2
        self.y = self.zarude_pivot_y + self.zarude_L * math.cos(self.zarude_angle) - self.size_h/2
        self.surface_angle = math.degrees(self.zarude_angle)
        self.update_position()
        
        if getattr(self, 'zarude_target', None):
            t = self.zarude_target
            if t.current_state != 'exiting':
                t_dist = self.size_h/2 + 30 + t.size_h/2
                t_cx = (self.x + self.size_w/2) + t_dist * math.sin(self.zarude_angle)
                t_cy = (self.y + self.size_h/2) + t_dist * math.cos(self.zarude_angle)
                t.x = t_cx - t.size_w/2
                t.y = t_cy - t.size_h/2
                t.surface_angle = math.degrees(self.zarude_angle)
                t.update_position()
            else:
                self.zarude_target = None
            
        if (dir == 1 and self.zarude_angle >= 0.8) or (dir == -1 and self.zarude_angle <= -0.8):
            self.current_state = 'zarude_air'
            self.v_x_velocity = dir * 25.0
            self.v_y_velocity = -12.0 # upward leap momentum
            
        self.schedule_loop(33, self.physics_loop)

    def _get_zarude_target(self):
        if hasattr(self, 'get_all_pets'):
            excluded = ['exiting', 'dragged', 'evolving_start', 'evolving_finish', 'spawning_wild', 'despawning_wild', 'falling_pokeball', 'falling_egg', 'celebi_frozen', 'cresselia_blessing', 'diancie_frozen', 'magearna_victim', 'zeraora_victim_flying', 'zeraora_victim_paralyzed', 'zeraora_victim_vibrate', 'zeraora_victim_paralyzed_fall', 'zarude_victim_grabbed', 'zarude_victim_thrown']
            valid = [p for p in self.get_all_pets() if p != self and p.current_state not in excluded and not getattr(p, 'is_egg', False)]
            if valid:
                target = random.choice(valid)
                for prefix, cancel_func in [('dark_', 'cancel_dark_arts'), ('mewtwo_', 'cancel_mewtwo_arts'), ('hooh_', 'cancel_hooh_arts'), ('kyogre_', 'cancel_kyogre_arts'), ('groudon_', 'cancel_groudon_arts'), ('lugia_', 'cancel_lugia_arts'), ('rayquaza_', 'cancel_rayquaza_arts'), ('dialga_', 'cancel_dialga_arts'), ('palkia_', 'cancel_palkia_arts'), ('giratina_', 'cancel_giratina_arts'), ('zekrom_', 'cancel_zekrom_arts'), ('reshiram_', 'cancel_reshiram_arts'), ('victini_', 'cancel_victini_arts'), ('sea_guardian_', 'cancel_sea_guardian_arts'), ('ub_', 'cancel_ub_arts'), ('genesect_', 'cancel_genesect_arts'), ('magearna_', 'cancel_magearna_arts'), ('zeraora_', 'cancel_zeraora_arts')]:
                    if target.current_state.startswith(prefix) and hasattr(target, cancel_func): getattr(target, cancel_func)()
                    
                if target.current_state == 'bubbled' and hasattr(target, 'manage_bubble_vfx'):
                    target.manage_bubble_vfx(False)
                    if hasattr(target, 'show_bubble_burst_vfx'): target.show_bubble_burst_vfx()
                return target
        return None

    def cancel_zarude_arts(self):
        if hasattr(self, 'zarude_vfx_win') and self.zarude_vfx_win:
            self.zarude_vfx_win.destroy()
            self.zarude_vfx_win = None
            
        self.zarude_particles = []
        
        if getattr(self, 'zarude_target', None):
            t = self.zarude_target
            if hasattr(t, 'current_state') and t.current_state == 'zarude_victim_grabbed':
                if hasattr(t, 'interrupt_current_state'): t.interrupt_current_state()
                t.current_state = 'falling'
        self.zarude_target = None
        self.surface_angle = 0
        
        if getattr(self, 'current_state', '').startswith('zarude_'):
            self.current_state = 'falling'

    # -------------------------------------------------------------
    # VICTIM FSMS (These run on the victim)
    # -------------------------------------------------------------
    def _fsm_zarude_victim_grabbed(self):
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_zarude_victim_thrown(self):
        self.x += self.v_x_velocity
        self.y += self.v_y_velocity
        
        current_env, _ = getattr(self, 'get_window_environment', lambda: ({'hwnd': None, 'y': self.default_floor_y}, None))()
        physical_floor = current_env['y'] if self.y <= current_env['y'] + 60 else self.default_floor_y
        
        if self.y >= physical_floor:
            self.y = physical_floor
            
            # Massive leaf explosion
            if hasattr(self, 'trigger_zarude_leaf_vfx'):
                self.trigger_zarude_leaf_vfx(self.x + self.size_w/2, self.y + self.size_h/2, explosion=True)
                
            if hasattr(self, '_embed_victim'):
                self._embed_victim(surface='floor')
                return
            else:
                self.current_state = 'idle'
                
        self.update_position()
        self.schedule_loop(33, self.physics_loop)
