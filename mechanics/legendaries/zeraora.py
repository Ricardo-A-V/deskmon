import random
import math
import tkinter as tk

class ZeraoraMechanics:
    def start_zeraora_mechanic(self):
        if getattr(self, 'current_state', '') in ['dragged', 'exiting']: return
        if getattr(self, 'zeraora_cooldown', 0) > 0: return
        if hasattr(self, 'is_global_mechanic_active') and self.is_global_mechanic_active(): return

        name = self.pet_name.lower().replace("_", "").replace("-", "")
        if name not in ["zeraora"]: return

        self.zeraora_cooldown = 108000 # 1 hour
        self.zeraora_target = None
        self.zeraora_hit_count = 0
        
        # Determine if on floor
        target_floor = self.v_y if getattr(self, 'gravity_inverted', False) else self.default_floor_y
        if hasattr(self, 'get_window_environment'):
            current_env, _ = self.get_window_environment()
            if current_env['hwnd']: target_floor = current_env['y']
            
        if abs(self.y - target_floor) > 10:
            self.current_state = 'zeraora_jump_floor'
        else:
            self.current_state = 'zeraora_channeling'
            self.zeraora_timer = 90
            self._init_zeraora_vfx()
            
        self.schedule_loop(33, self.physics_loop)

    def _fsm_zeraora_jump_floor(self):
        target_floor = self.v_y if getattr(self, 'gravity_inverted', False) else self.default_floor_y
        if hasattr(self, 'get_window_environment'):
            current_env, _ = self.get_window_environment()
            if current_env['hwnd']: target_floor = current_env['y']
            
        is_inverted = getattr(self, 'gravity_inverted', False)
        gravity = -1.5 if is_inverted else 1.5
        
        self.v_y_velocity = getattr(self, 'v_y_velocity', 0) + gravity
        self.y += self.v_y_velocity
        
        reached = False
        if is_inverted and self.y <= target_floor:
            self.y = target_floor
            reached = True
        elif not is_inverted and self.y >= target_floor:
            self.y = target_floor
            reached = True
            
        if reached:
            self.v_y_velocity = 0
            self.current_state = 'zeraora_channeling'
            self.zeraora_timer = 90
            self._init_zeraora_vfx()
            
        self.update_position()
        self.schedule_loop(33, self.physics_loop)

    def _init_zeraora_vfx(self):
        if not hasattr(self, 'zeraora_vfx_win') or not self.zeraora_vfx_win or not self.zeraora_vfx_win.winfo_exists():
            self.zeraora_vfx_win = tk.Toplevel(self.window.master)
            self.zeraora_vfx_win.title("VFX_Zeraora_Ignore")
            self.zeraora_vfx_win.overrideredirect(True)
            self.zeraora_vfx_win.attributes('-topmost', True)
            TRANS_COLOR = '#010101'
            self.zeraora_vfx_win.config(bg=TRANS_COLOR)
            try: self.zeraora_vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
            except: pass
            
            try:
                import ctypes
                hwnd = ctypes.windll.user32.GetParent(self.zeraora_vfx_win.winfo_id())
                style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
                ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x00080000 | 0x00000020 | 0x00000008)
            except: pass
            
            self.zeraora_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
            self.zeraora_vfx_canvas = tk.Canvas(self.zeraora_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
            self.zeraora_vfx_canvas.pack()
            self.zeraora_particles = []
            self.zeraora_trails = []
            self._start_zeraora_particle_loop()
            
    def _start_zeraora_particle_loop(self):
        if not hasattr(self, 'zeraora_particle_loop_running') or not self.zeraora_particle_loop_running:
            self.zeraora_particle_loop_running = True
            self._zeraora_particle_loop()
            
    def _zeraora_particle_loop(self):
        if hasattr(self, 'zeraora_vfx_win') and self.zeraora_vfx_win and self.zeraora_vfx_win.winfo_exists():
            alive = []
            for p in getattr(self, 'zeraora_particles', []):
                p['life'] -= 1
                if p['life'] > 0:
                    self.zeraora_vfx_canvas.move(p['id'], p['vx'], p['vy'])
                    coords = self.zeraora_vfx_canvas.coords(p['id'])
                    if coords:
                        cx = (coords[0] + coords[2]) / 2
                        cy = (coords[1] + coords[3]) / 2
                        r = p['max_size'] * (p['life'] / p['max_life'])
                        self.zeraora_vfx_canvas.coords(p['id'], cx-r, cy-r, cx+r, cy+r)
                    alive.append(p)
                else:
                    self.zeraora_vfx_canvas.delete(p['id'])
            self.zeraora_particles = alive
            
            alive_trails = []
            for t in getattr(self, 'zeraora_trails', []):
                t['life'] -= 1
                if t['life'] > 0:
                    self.zeraora_vfx_canvas.itemconfig(t['id'], fill=t['color'])
                    alive_trails.append(t)
                else:
                    self.zeraora_vfx_canvas.delete(t['id'])
            self.zeraora_trails = alive_trails
            
            if getattr(self, 'zeraora_particles', []) or getattr(self, 'zeraora_trails', []) or getattr(self, 'current_state', '').startswith('zeraora_') or getattr(self, 'current_state', '').startswith('zeraora_victim_'):
                self.window.after(33, self._zeraora_particle_loop)
            else:
                self.zeraora_vfx_win.destroy()
                self.zeraora_vfx_win = None
                self.zeraora_particle_loop_running = False
        else:
            self.zeraora_particle_loop_running = False

    def spawn_zeraora_particle(self, cx, cy, vx, vy, life, p_type="spark"):
        if not hasattr(self, 'zeraora_vfx_win') or not self.zeraora_vfx_win or not self.zeraora_vfx_win.winfo_exists():
            self._init_zeraora_vfx()
            
        color = "#FFFF00" if p_type == "spark" else "#00FFFF"
        size = 3 if p_type == "spark" else 5
        
        pid = self.zeraora_vfx_canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline="")
        if not hasattr(self, 'zeraora_particles'): self.zeraora_particles = []
        self.zeraora_particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': life, 'max_life': life, 'max_size': size, 'type': p_type})
        
    def draw_zeraora_trail(self, x1, y1, x2, y2, color, width, life):
        if not hasattr(self, 'zeraora_vfx_win') or not self.zeraora_vfx_win or not self.zeraora_vfx_win.winfo_exists():
            self._init_zeraora_vfx()
            
        # Draw zigzag lightning
        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)
        segments = max(2, int(length / 20))
        
        points = [x1, y1]
        for i in range(1, segments):
            px = x1 + (dx * i / segments) + random.uniform(-15, 15)
            py = y1 + (dy * i / segments) + random.uniform(-15, 15)
            points.extend([px, py])
        points.extend([x2, y2])
        
        if hasattr(self, '_draw_pixel_line'):
            pid = self._draw_pixel_line(self.zeraora_vfx_canvas, points, fill=color, width=width, tags="lightning")
        else:
            pid = self.zeraora_vfx_canvas.create_line(points, fill=color, width=width, tags="lightning")
            
        if not hasattr(self, 'zeraora_trails'): self.zeraora_trails = []
        self.zeraora_trails.append({'id': pid, 'life': life, 'max_life': life, 'color': color})

    def trigger_zeraora_punch_vfx(self, cx, cy):
        for _ in range(20):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(5, 15)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.spawn_zeraora_particle(cx, cy, vx, vy, life=15, p_type=random.choice(["spark", "blue"]))
        
        # Screen flash impact and Lati-style yellow rings
        if hasattr(self, 'zeraora_vfx_canvas'):
            pid = self.zeraora_vfx_canvas.create_oval(cx-40, cy-40, cx+40, cy+40, fill="#FFFFFF", outline="")
            self.zeraora_trails.append({'id': pid, 'life': 5, 'max_life': 5, 'color': "#FFFFFF"})
            
            if hasattr(self, '_draw_pixel_circle_bbox'):
                inner = self._draw_pixel_circle_bbox(self.zeraora_vfx_canvas, cx-10, cy-10, cx+10, cy+10, fill="white", outline="", tags="z_ring")
                outer = self._draw_pixel_circle_bbox(self.zeraora_vfx_canvas, cx-20, cy-20, cx+20, cy+20, outline="#FFFF00", width=4, tags="z_ring")
                self.zeraora_trails.append({'id': inner, 'life': 10, 'max_life': 10, 'color': "white"})
                self.zeraora_trails.append({'id': outer, 'life': 10, 'max_life': 10, 'color': "#FFFF00"})

    def _fsm_zeraora_channeling(self):
        self.zeraora_timer -= 1
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        
        # Absorb particles
        r = 100
        angle = random.uniform(0, math.pi * 2)
        px = cx + math.cos(angle) * r
        py = cy + math.sin(angle) * r
        vx = (cx - px) / 10
        vy = (cy - py) / 10
        self.spawn_zeraora_particle(px, py, vx, vy, life=10, p_type=random.choice(["spark", "blue"]))
        
        if self.zeraora_timer <= 0:
            # Find target
            if hasattr(self, 'get_all_pets'):
                excluded_states = ['exiting', 'dragged', 'evolving_start', 'evolving_finish', 'spawning_wild', 'despawning_wild', 'falling_pokeball', 'falling_egg', 'celebi_frozen', 'cresselia_blessing', 'diancie_frozen', 'magearna_victim', 'zeraora_victim_flying', 'zeraora_victim_paralyzed', 'zeraora_victim_vibrate', 'zeraora_victim_paralyzed_fall']
                valid_targets = [p for p in self.get_all_pets() if p != self and p.current_state not in excluded_states and not getattr(p, 'is_egg', False)]
                if valid_targets:
                    target = random.choice(valid_targets)
                    self.zeraora_target = target
                    self.apply_zeraora_victim(target)
                    self.current_state = 'zeraora_dash_to_target'
                    self.zeraora_timer = 3 # frames to reach target
                    
                    self.zeraora_dash_start_x = self.x
                    self.zeraora_dash_start_y = self.y
                    self.zeraora_dash_end_x = target.x
                    self.zeraora_dash_end_y = target.y
                else:
                    self.current_state = 'idle'
            else:
                self.current_state = 'idle'
                
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_zeraora_dash_to_target(self):
        self.zeraora_timer -= 1
        
        self.canvas.itemconfig(self.canvas_image_id, state='hidden')
        
        if self.zeraora_timer % 2 == 0:
            cx1 = self.x - self.v_x + self.size_w/2
            cy1 = self.y - self.v_y + self.size_h/2
            
            progress = 1.0 - (self.zeraora_timer / 3.0)
            self.x = self.zeraora_dash_start_x + (self.zeraora_dash_end_x - self.zeraora_dash_start_x) * progress
            self.y = self.zeraora_dash_start_y + (self.zeraora_dash_end_y - self.zeraora_dash_start_y) * progress
            self.update_position()
            
            cx2 = self.x - self.v_x + self.size_w/2
            cy2 = self.y - self.v_y + self.size_h/2
            
            self.draw_zeraora_trail(cx1, cy1, cx2, cy2, random.choice(["#FFFF00", "#00FFFF", "#FFFFFF"]), 4, 10)
            
            # Pixelated small electric cluster
            if hasattr(self, 'zeraora_vfx_canvas'):
                r = 15
                for _ in range(5):
                    ox = random.uniform(-r, r)
                    oy = random.uniform(-r, r)
                    size = random.choice([2, 4, 6])
                    color = random.choice(["#FFFF00", "#FFFFFF", "#00FFFF"])
                    pid = self.zeraora_vfx_canvas.create_rectangle(cx2+ox-size, cy2+oy-size, cx2+ox+size, cy2+oy+size, fill=color, outline="")
                    self.zeraora_trails.append({'id': pid, 'life': 2, 'max_life': 2, 'color': color})
            
        if self.zeraora_timer <= 0:
            self.canvas.itemconfig(self.canvas_image_id, state='normal')
            self.x = self.zeraora_dash_end_x
            self.y = self.zeraora_dash_end_y
            if self.zeraora_dash_start_x != self.zeraora_dash_end_x:
                self.is_facing_right = (self.zeraora_dash_start_x > self.zeraora_dash_end_x)
            self.update_position()
            
            if self.zeraora_target and hasattr(self.zeraora_target, 'current_state') and self.zeraora_target.current_state.startswith('zeraora_victim'):
                self.zeraora_hit_count += 1
                
                # Punch VFX
                cx = self.x - self.v_x + self.size_w/2
                cy = self.y - self.v_y + self.size_h/2
                self.trigger_zeraora_punch_vfx(cx, cy)
                
                if self.zeraora_hit_count < 10:
                    # Launch target
                    target = self.zeraora_target
                    dest_x = random.randint(self.v_x + 50, self.v_x + self.v_width - 50 - target.size_w)
                    dest_y = random.randint(self.v_y + 50, self.v_y + self.v_height - 50 - target.size_h)
                    
                    if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
                    target.current_state = 'zeraora_victim_flying'
                    target.zeraora_flight_timer = 8 # 2x faster than 17
                    target.zeraora_flight_start_x = target.x
                    target.zeraora_flight_start_y = target.y
                    target.zeraora_flight_end_x = dest_x
                    target.zeraora_flight_end_y = dest_y
                    
                    self.current_state = 'zeraora_dash_intercept'
                    self.zeraora_timer = 4 # 2x faster than 8
                    self.zeraora_dash_start_x = self.x
                    self.zeraora_dash_start_y = self.y
                    self.zeraora_dash_end_x = dest_x
                    self.zeraora_dash_end_y = dest_y
                else:
                    # 5th hit
                    target = self.zeraora_target
                    if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
                    target.current_state = 'zeraora_victim_vibrate'
                    target.zeraora_flight_timer = 60 # 2 seconds
                    target.zeraora_vib_base_x = target.x
                    target.zeraora_vib_base_y = target.y
                    
                    self.current_state = 'falling'
                    self.zeraora_target = None
                    self.zeraora_hit_count = 0
            else:
                self.current_state = 'falling'
                self.zeraora_target = None
                self.zeraora_hit_count = 0
                
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_zeraora_dash_intercept(self):
        self.zeraora_timer -= 1
        
        self.canvas.itemconfig(self.canvas_image_id, state='hidden')
        
        if self.zeraora_timer % 2 == 0:
            cx1 = self.x - self.v_x + self.size_w/2
            cy1 = self.y - self.v_y + self.size_h/2
            
            progress = min(1.0, 1.0 - (self.zeraora_timer / 8.0))
            self.x = self.zeraora_dash_start_x + (self.zeraora_dash_end_x - self.zeraora_dash_start_x) * progress
            self.y = self.zeraora_dash_start_y + (self.zeraora_dash_end_y - self.zeraora_dash_start_y) * progress
            self.update_position()
            
            cx2 = self.x - self.v_x + self.size_w/2
            cy2 = self.y - self.v_y + self.size_h/2
            
            self.draw_zeraora_trail(cx1, cy1, cx2, cy2, random.choice(["#FFFF00", "#00FFFF", "#FFFFFF"]), 4, 10)
            
            # Pixelated small electric cluster
            if hasattr(self, 'zeraora_vfx_canvas'):
                r = 15
                for _ in range(5):
                    ox = random.uniform(-r, r)
                    oy = random.uniform(-r, r)
                    size = random.choice([2, 4, 6])
                    color = random.choice(["#FFFF00", "#FFFFFF", "#00FFFF"])
                    pid = self.zeraora_vfx_canvas.create_rectangle(cx2+ox-size, cy2+oy-size, cx2+ox+size, cy2+oy+size, fill=color, outline="")
                    self.zeraora_trails.append({'id': pid, 'life': 2, 'max_life': 2, 'color': color})
            
        if self.zeraora_timer <= 0:
            self.canvas.itemconfig(self.canvas_image_id, state='normal')
            self.x = self.zeraora_dash_end_x
            self.y = self.zeraora_dash_end_y
            if self.zeraora_dash_start_x != self.zeraora_dash_end_x:
                self.is_facing_right = (self.zeraora_dash_start_x > self.zeraora_dash_end_x)
            self.update_position()
            self.current_state = 'zeraora_intercept_wait'
            
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_zeraora_intercept_wait(self):
        # Wait for target to arrive
        if not self.zeraora_target or not hasattr(self.zeraora_target, 'current_state') or not self.zeraora_target.current_state.startswith('zeraora_victim'):
            self.current_state = 'falling'
            self.zeraora_target = None
            self.zeraora_hit_count = 0
        else:
            if self.zeraora_target.current_state == 'zeraora_victim_arrived':
                # Target arrived, hit again
                self.zeraora_target.current_state = 'zeraora_victim_frozen'
                self.current_state = 'zeraora_dash_to_target' # reuse the hit logic by dashing 0 distance
                self.zeraora_timer = 1
                self.zeraora_dash_start_x = self.x
                self.zeraora_dash_start_y = self.y
                self.zeraora_dash_end_x = self.zeraora_target.x
                self.zeraora_dash_end_y = self.zeraora_target.y
                
        self.schedule_loop(33, self.physics_loop)

    def apply_zeraora_victim(self, target):
        for prefix, cancel_func in [('dark_', 'cancel_dark_arts'), ('mewtwo_', 'cancel_mewtwo_arts'), ('hooh_', 'cancel_hooh_arts'), ('kyogre_', 'cancel_kyogre_arts'), ('groudon_', 'cancel_groudon_arts'), ('lugia_', 'cancel_lugia_arts'), ('rayquaza_', 'cancel_rayquaza_arts'), ('dialga_', 'cancel_dialga_arts'), ('palkia_', 'cancel_palkia_arts'), ('giratina_', 'cancel_giratina_arts'), ('zekrom_', 'cancel_zekrom_arts'), ('reshiram_', 'cancel_reshiram_arts'), ('victini_', 'cancel_victini_arts'), ('sea_guardian_', 'cancel_sea_guardian_arts'), ('ub_', 'cancel_ub_arts'), ('genesect_', 'cancel_genesect_arts'), ('magearna_', 'cancel_magearna_arts')]:
            if target.current_state.startswith(prefix) and hasattr(target, cancel_func): getattr(target, cancel_func)()
            
        if target.current_state == 'bubbled' and hasattr(target, 'manage_bubble_vfx'):
            target.manage_bubble_vfx(False)
            if hasattr(target, 'show_bubble_burst_vfx'): target.show_bubble_burst_vfx()
            
        if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
        target.current_state = 'zeraora_victim_frozen'
        
    def cancel_zeraora_arts(self):
        self.canvas.itemconfig(self.canvas_image_id, state='normal')
        if hasattr(self, 'zeraora_vfx_win') and self.zeraora_vfx_win:
            self.zeraora_vfx_win.destroy()
            self.zeraora_vfx_win = None
            
        self.zeraora_particles = []
        self.zeraora_trails = []
        
        if getattr(self, 'zeraora_target', None):
            t = self.zeraora_target
            if hasattr(t, 'current_state') and t.current_state.startswith('zeraora_victim'):
                if hasattr(t, 'interrupt_current_state'): t.interrupt_current_state()
                t.current_state = 'falling'
        self.zeraora_target = None
        
        if getattr(self, 'current_state', '').startswith('zeraora_'):
            self.current_state = 'falling'

    # -------------------------------------------------------------
    # VICTIM FSMS (These run on the victim)
    # -------------------------------------------------------------
    def _fsm_zeraora_victim_frozen(self):
        # Just frozen in place
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_zeraora_victim_flying(self):
        self.zeraora_flight_timer -= 1
        
        progress = 1.0 - (self.zeraora_flight_timer / 17.0)
        self.x = self.zeraora_flight_start_x + (self.zeraora_flight_end_x - self.zeraora_flight_start_x) * progress
        self.y = self.zeraora_flight_start_y + (self.zeraora_flight_end_y - self.zeraora_flight_start_y) * progress
        self.update_position()
        
        # Trail behind victim
        if hasattr(self, 'spawn_zeraora_particle') and self.zeraora_flight_timer % 2 == 0:
            cx = self.x - self.v_x + self.size_w/2
            cy = self.y - self.v_y + self.size_h/2
            self.spawn_zeraora_particle(cx, cy, 0, 0, life=10, p_type="spark")
            
        if self.zeraora_flight_timer <= 0:
            self.x = self.zeraora_flight_end_x
            self.y = self.zeraora_flight_end_y
            self.update_position()
            self.current_state = 'zeraora_victim_arrived'
            
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_zeraora_victim_arrived(self):
        # Wait for Zeraora to punch
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_zeraora_victim_vibrate(self):
        self.zeraora_flight_timer -= 1
        
        self.x = self.zeraora_vib_base_x + random.uniform(-4, 4)
        self.y = self.zeraora_vib_base_y + random.uniform(-4, 4)
        self.update_position()
        
        if self.zeraora_flight_timer % 5 == 0 and hasattr(self, 'spawn_zeraora_particle'):
            cx = self.x - self.v_x + self.size_w/2
            cy = self.y - self.v_y + self.size_h/2
            self.spawn_zeraora_particle(cx + random.uniform(-20, 20), cy + random.uniform(-20, 20), random.uniform(-2, 2), random.uniform(-2, 2), life=10, p_type="spark")
            
        if self.zeraora_flight_timer <= 0:
            if hasattr(self, 'apply_paralysis'):
                self.apply_paralysis(self)
                self.v_x_velocity = random.uniform(25.0, 45.0) * random.choice([1, -1])
                self.v_y_velocity = random.uniform(-45.0, -30.0)
                
                if hasattr(self, 'trigger_zeraora_punch_vfx'):
                    cx = self.x - self.v_x + self.size_w/2
                    cy = self.y - self.v_y + self.size_h/2
                    self.trigger_zeraora_punch_vfx(cx, cy)
                    for _ in range(25):
                        angle = random.uniform(0, math.pi * 2)
                        speed = random.uniform(10, 30)
                        self.spawn_zeraora_particle(cx, cy, math.cos(angle)*speed, math.sin(angle)*speed, 20, "spark")
            else:
                self.current_state = 'falling'
            
        self.schedule_loop(33, self.physics_loop)
