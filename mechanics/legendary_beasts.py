import os
import math
import random
import tkinter as tk

class LegendaryBeastsMechanics:
    def _draw_pixel_line(self, canvas, pts, fill, width, tags=""):
        import math, random
        p_size = max(4, int(width))
        uid = f"pix_line_{random.randint(10000, 99999)}"
        all_tags = (tags, uid) if tags else (uid,)
        
        ortho_pts = []
        for i in range(0, len(pts)-2, 2):
            x0, y0 = pts[i], pts[i+1]
            x1, y1 = pts[i+2], pts[i+3]
            
            x0 = round(x0 / p_size) * p_size
            y0 = round(y0 / p_size) * p_size
            x1 = round(x1 / p_size) * p_size
            y1 = round(y1 / p_size) * p_size
            
            if i == 0: ortho_pts.extend([x0, y0])
            
            dist = math.hypot(x1 - x0, y1 - y0)
            if dist == 0: continue
            
            steps = max(1, int(dist / (p_size * 0.8)))
            cx, cy = x0, y0
            for step in range(1, steps + 1):
                t = step / steps
                nx = round((x0 + (x1 - x0) * t) / p_size) * p_size
                ny = round((y0 + (y1 - y0) * t) / p_size) * p_size
                
                if nx != cx or ny != cy:
                    if nx != cx and ny != cy: ortho_pts.extend([nx, cy])
                    cx, cy = nx, ny
                    ortho_pts.extend([cx, cy])
                    
        if len(ortho_pts) >= 4:
            canvas.create_line(
                *ortho_pts, fill=fill, width=p_size, 
                capstyle="projecting", joinstyle="miter", tags=all_tags
            )
        return uid

    def _draw_pixel_polygon(self, canvas, pts, fill, outline, p_size=6, tags=""):
        import random
        uid = f"pix_poly_{random.randint(10000, 99999)}"
        all_tags = (tags, uid) if tags else (uid,)
        edges = []
        for i in range(0, len(pts), 2):
            x1, y1 = pts[i], pts[i+1]
            nx, ny = pts[(i+2)%len(pts)], pts[(i+3)%len(pts)]
            edges.append((x1, y1, nx, ny))
        min_y = min(pts[1::2])
        max_y = max(pts[1::2])
        min_y = round(min_y / p_size) * p_size
        max_y = round(max_y / p_size) * p_size
        for y in range(int(min_y), int(max_y) + p_size, p_size):
            y_mid = y + p_size / 2.0
            intersects = []
            for ex1, ey1, ex2, ey2 in edges:
                if (ey1 <= y_mid < ey2) or (ey2 <= y_mid < ey1):
                    t = (y_mid - ey1) / (ey2 - ey1)
                    ix = ex1 + t * (ex2 - ex1)
                    intersects.append(ix)
            intersects.sort()
            for i in range(0, len(intersects)-1, 2):
                x_start = round(intersects[i] / p_size) * p_size
                x_end = round(intersects[i+1] / p_size) * p_size
                if x_start == x_end: x_end += p_size
                canvas.create_rectangle(x_start, y, x_end, y + p_size, fill=fill, outline="", tags=all_tags)
        return uid

    def cancel_beast_arts(self):
        # Flushes VFX memory immediately upon interruption
        if hasattr(self, 'beast_vfx_win') and self.beast_vfx_win and self.beast_vfx_win.winfo_exists():
            self.beast_vfx_win.destroy()
            self.beast_vfx_win = None

        for attr in ['beast_timer', 'beast_phase', 'beast_type', 'beast_particles', 'beast_roar_level', 'beast_dash_target']:
            if hasattr(self, attr): delattr(self, attr)

        self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)

        if self.current_state not in ['dragged', 'exiting']:
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            self.current_state = 'falling'
            self.schedule_loop(50, self.physics_loop)

    def trigger_beast_arts(self):
        name = self.pet_name.lower().replace("_", "").replace("-", "")
        if name in ["raikou", "ragingbolt"]: self.beast_type = "raikou"
        elif name in ["entei", "gougingfire"]: self.beast_type = "entei"
        elif name in ["suicune", "walkingwake"]: self.beast_type = "suicune"
        else: return

        # Validates physical altitude. If anchored to a window, preemptively routes to a dismount sequence.
        if getattr(self, 'anchored_hwnd', None) or self.y < self.default_floor_y - 15:
            self.anchored_hwnd = None
            self.current_state = 'beast_dismount'
            self.v_y_velocity = -5.0 # Generates the initial upward impulse for the parabolic trajectory
            self.schedule_loop(30, self.physics_loop)
            return

        self._start_beast_channeling()

    def _fsm_beast_dismount(self):
        # Applies standard gravity accumulation to pull the entity towards the absolute OS floor
        self.v_y_velocity += 1.5 
        self.y += self.v_y_velocity
        
        # Injects horizontal velocity to clear the window boundaries and prevent clipping against edges
        self.x += 4.0 if self.is_facing_right else -4.0
        
        # Validates absolute floor collision to safely trigger the actual ability
        if self.y >= self.default_floor_y:
            self.y = self.default_floor_y
            self.floor_y = self.default_floor_y
            self.v_y_velocity = 0.0
            self._start_beast_channeling()
            return
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _start_beast_channeling(self):
        # Safely initializes the ability variables only after physical grounding is confirmed
        self._setup_beast_vfx_layer()
        self.beast_phase = 0
        self.beast_roar_level = 0
        self.beast_timer = 60 
        self.current_state = 'beast_channeling'
        self.v_x_velocity = 0.0
        self.v_y_velocity = 0.0
        self.schedule_loop(30, self.physics_loop)

    def _setup_beast_vfx_layer(self):
        self.beast_particles = []
        if hasattr(self, 'beast_vfx_win') and self.beast_vfx_win and self.beast_vfx_win.winfo_exists():
            self.beast_vfx_canvas.delete("all")
            return
            
        self.beast_vfx_win = tk.Toplevel(self.window.master)
        self.beast_vfx_win.title("VFX_Legendary_Beasts")
        self.beast_vfx_win.overrideredirect(True)
        self.beast_vfx_win.attributes('-topmost', True)
        
        TRANS = '#010101'
        self.beast_vfx_win.config(bg=TRANS)
        try: self.beast_vfx_win.wm_attributes('-transparentcolor', TRANS)
        except: pass
        
        self.beast_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.beast_vfx_win.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x00080000 | 0x00000020)
        except: pass

        self.beast_vfx_canvas = tk.Canvas(self.beast_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS, highlightthickness=0)
        self.beast_vfx_canvas.pack()

    def _spawn_beast_absorption(self):
        if not hasattr(self, 'beast_vfx_canvas'): return
        cx = self.x - self.v_x + self.size_w / 2
        cy = self.y - self.v_y + self.size_h / 2
        
        for _ in range(2):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(80, 150)
            px = cx + math.cos(angle) * dist
            py = cy + math.sin(angle) * dist
            
            if self.beast_type == "raikou": color = random.choice(["#FFFF00", "#FFD700", "#FFFFFF"])
            elif self.beast_type == "entei": color = random.choice(["#FF4500", "#FF0000", "#F1C40F"])
            else: color = random.choice(["#00FFFF", "#87CEFA", "#FFFFFF"])
                
            size = random.choice([2, 3, 4])
            speed = random.uniform(8.0, 15.0)
            vx = -math.cos(angle) * speed
            vy = -math.sin(angle) * speed
            
            pid = self.beast_vfx_canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color)
            self.beast_particles.append({'id': pid, 'x': px, 'y': py, 'vx': vx, 'vy': vy, 'life': 10, 'size': size, 'type': 'absorb'})

    def _spawn_beast_trail(self):
        if not hasattr(self, 'beast_vfx_canvas'): return
        cx = self.x - self.v_x + self.size_w / 2
        cy = self.y - self.v_y + self.size_h / 2
        
        if self.beast_type == "raikou": color = random.choice(["#FFFF00", "#FFD700"])
        elif self.beast_type == "entei": color = random.choice(["#FF4500", "#FF0000"])
        else: color = random.choice(["#00FFFF", "#87CEFA"])
            
        size = random.choice([4, 6, 8])
        px = cx + random.uniform(-15, 15)
        py = cy + random.uniform(-10, 20)
        pid = self.beast_vfx_canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color)
        self.beast_particles.append({'id': pid, 'x': px, 'y': py, 'vx': 0, 'vy': 0, 'life': 15, 'size': size, 'type': 'trail'})

    def _execute_beast_roar(self):
        if not hasattr(self, 'beast_vfx_canvas'): return
        cx = self.x - self.v_x + self.size_w / 2
        cy = self.y - self.v_y + self.size_h / 2
        
        ranges = [150, 300, 600]
        current_range = ranges[self.beast_roar_level]
        
        if self.beast_type == "raikou":
            # Generates mathematical fractal trees that will be animated dynamically in the process loop
            for _ in range(6 * (self.beast_roar_level + 1)):
                angle = random.uniform(0, 2 * math.pi)
                dist = current_range
                pts = [(cx, cy)]
                curr_dist = 0
                curr_x, curr_y = cx, cy
                
                while curr_dist < dist:
                    step = random.uniform(20, 60)
                    curr_dist += step
                    curr_x += math.cos(angle + random.uniform(-0.8, 0.8)) * step
                    curr_y += math.sin(angle + random.uniform(-0.8, 0.8)) * step
                    pts.append((curr_x, curr_y))
                    
                w = random.choice([3, 5, 7])
                color = random.choice(["#FFFF00", "#FFD700", "#FFFFFF"])
                
                # Flattens the array for Tkinter
                flat_pts = [coord for pt in pts for coord in pt]
                pid = self._draw_pixel_line(self.beast_vfx_canvas, flat_pts, fill=color, width=w, tags="beast_lightning")
                
                self.beast_particles.append({
                    'id': pid, 'base_pts': pts, 'color': color, 'w': w, 
                    'life': 10 + self.beast_roar_level * 5, 'type': 'lightning'
                })
                
            self._apply_radial_hitbox(current_range, "raikou")
                
        elif self.beast_type == "entei":
            # Exponential scaling for true volumetric eruption
            particle_counts = [50, 150, 400] 
            count = particle_counts[self.beast_roar_level]
            
            # Repositions origin from the sprite's center to the physical floor
            floor_y = cy + self.size_h / 2
            
            for _ in range(count):
                angle = random.uniform(math.pi + 0.2, 2 * math.pi - 0.2) 
                speed = random.uniform(10.0, 35.0 + (self.beast_roar_level * 15.0))
                
                px = cx + random.uniform(-current_range * 0.7, current_range * 0.7)
                py = floor_y + random.uniform(-10, 10) 
                s = random.randint(8, 16 + (self.beast_roar_level * 8))
                color = random.choice(["#FFFFFF", "#F1C40F", "#FFA500", "#FF4500", "#FF0000", "#8B0000"])
                
                pid = self.beast_vfx_canvas.create_rectangle(px-s, py-s, px+s, py+s, fill=color, outline="", tags="beast_fire")
                
                # vy - 2.0 creates a forced updraft defying standard radial gravity
                self.beast_particles.append({
                    'id': pid, 'x': px, 'y': py, 
                    'vx': math.cos(angle) * speed * 0.5, 
                    'vy': -abs(math.sin(angle) * speed), 
                    'life': random.randint(20, 35 + self.beast_roar_level * 15), 
                    'size': s, 'type': 'fire'
                })
            self._apply_radial_hitbox(current_range, "entei")
                
        elif self.beast_type == "suicune":
            wave_lifespans = [30, 60, 9999] 
            wave_speeds = [15.0, 20.0, 25.0]
            wave_sizes = [80, 140, 250]
            
            life = wave_lifespans[self.beast_roar_level]
            speed = wave_speeds[self.beast_roar_level]
            size = wave_sizes[self.beast_roar_level]
            floor_y = self.y - self.v_y + self.size_h
            
            for direction in [-1, 1]:
                color = "#00BFFF" if self.beast_roar_level == 2 else "#87CEFA"
                
                self.beast_particles.append({
                    'id': "dummy", 'x': cx, 'y': floor_y, 'vx': speed * direction, 'vy': 0, 
                    'life': life, 'size': size, 'dir': direction, 'type': 'wave', 
                    'level': self.beast_roar_level, 'phase': 0.0, 'color': color
                })

    def _apply_radial_hitbox(self, impact_radius, b_type):
        if not getattr(self, 'get_all_pets', None): return
        abs_cx = self.x + self.size_w / 2
        abs_cy = self.y + self.size_h / 2
        
        for p in self.get_all_pets():
            if p == self or getattr(p, 'is_egg', False) or p.current_state in ['exiting', 'dragged']: continue
            px_center = p.x + (p.size_w / 2)
            py_center = p.y + (p.size_h / 2)
            if math.hypot(px_center - abs_cx, py_center - abs_cy) <= impact_radius:
                if b_type == "raikou" and hasattr(self, 'apply_paralysis'): self.apply_paralysis(p)
                elif b_type == "entei" and hasattr(self, 'apply_burn'): self.apply_burn(p)

    def _process_beast_particles(self):
        if not hasattr(self, 'beast_vfx_canvas') or not self.beast_vfx_canvas: return
        alive = []
        for p in getattr(self, 'beast_particles', []):
            p['life'] -= 1
            
            if p['type'] == 'trail':
                p['size'] *= 0.85
                self.beast_vfx_canvas.coords(p['id'], p['x']-p['size'], p['y']-p['size'], p['x']+p['size'], p['y']+p['size'])
                
            elif p['type'] == 'lightning':
                # Jitter animation: offsets coordinates per frame to create high-voltage flickering
                new_flat = []
                for i, (bx, by) in enumerate(p['base_pts']):
                    if i == 0: 
                        new_flat.extend([bx, by]) # Root stays anchored to Raikou
                    else:
                        new_flat.extend([bx + random.uniform(-12, 12), by + random.uniform(-12, 12)])
                
                new_width = random.randint(1, p['w'] + 3)
                new_color = random.choice(["#FFFFFF", p['color']])
                self.beast_vfx_canvas.delete(p['id'])
                p['id'] = self._draw_pixel_line(self.beast_vfx_canvas, new_flat, fill=new_color, width=new_width, tags="beast_lightning")

            elif p['type'] == 'fire':
                # Implements aerial friction to compress the burst as it expands
                p['vx'] *= 0.92 
                p['vy'] *= 0.95
                p['x'] += p['vx']
                p['y'] += p['vy']
                p['size'] *= 0.88 # Shrinks as it burns out
                s = p['size']
                self.beast_vfx_canvas.coords(p['id'], p['x']-s, p['y']-s, p['x']+s, p['y']+s)
                
            elif p['type'] == 'wave':
                p['x'] += p['vx']
                p['phase'] += 0.4 # Animates the crest oscillation
                s = p['size']
                d = p['dir']
                
                bx, by = p['x'], p['y']
                crest_offset = math.sin(p['phase']) * (s * 0.15) # Dynamic height modulation
                
                # Constructs a 6-point aerodynamic teardrop shape using Tkinter's B-Spline interpolation
                if d == 1: # Surfing Right
                    pts = [
                        bx - s*1.2, by,                     # Tail trailing edge
                        bx + s*0.6, by,                     # Front base
                        bx + s*0.3, by - s*0.8 + crest_offset, # Front crest curve
                        bx - s*0.1, by - s + crest_offset,  # Peak apex
                        bx - s*0.5, by - s*0.5,             # Upper back curve
                        bx - s*0.9, by - s*0.2              # Lower back slope
                    ]
                else: # Surfing Left
                    pts = [
                        bx + s*1.2, by,
                        bx - s*0.6, by,
                        bx - s*0.3, by - s*0.8 + crest_offset,
                        bx + s*0.1, by - s + crest_offset,
                        bx + s*0.5, by - s*0.5,
                        bx + s*0.9, by - s*0.2
                    ]
                
                self.beast_vfx_canvas.delete(p['id'])
                p['id'] = self._draw_pixel_polygon(self.beast_vfx_canvas, pts, fill=p.get('color', "#87CEFA"), outline="", p_size=8, tags="beast_wave")
                
                # Emits white foam particles consistently from the oscillating apex
                if random.randint(1, 100) <= 60:
                    crest_x = bx + (s*0.2 * d)
                    crest_y = by - s + crest_offset
                    f_pid = self.beast_vfx_canvas.create_rectangle(crest_x-5, crest_y-5, crest_x+5, crest_y+5, fill="#FFFFFF", outline="")
                    self.beast_particles.append({'id': f_pid, 'x': crest_x, 'y': crest_y, 'vx': p['vx']*0.3 + random.uniform(-3, 3), 'vy': random.uniform(-4, 1), 'life': 12, 'type': 'splash'})

                wave_abs_x = p['x'] + self.v_x
                limit_left = self.v_x
                limit_right = self.v_x + self.v_width
                
                # Precise mathematical collision based on the aerodynamic front edge rather than a static bounding box
                front_edge = wave_abs_x + (s * 0.6 * d)
                hit_wall = (d == -1 and front_edge <= limit_left) or (d == 1 and front_edge >= limit_right)
                
                if p['life'] <= 0 or hit_wall:
                    p['life'] = 0
                    
                    # Hydrodynamic crash generation at the exact point of impact
                    for _ in range(35):
                        drop_vx = random.uniform(-15.0, 15.0)
                        drop_vy = random.uniform(-25.0, 0.0)
                        d_pid = self.beast_vfx_canvas.create_rectangle(p['x']-4, p['y']-s/2-4, p['x']+4, p['y']-s/2+4, fill="#00FFFF", outline="")
                        self.beast_particles.append({'id': d_pid, 'x': p['x'], 'y': p['y']-s/2, 'vx': drop_vx, 'vy': drop_vy, 'life': 25, 'type': 'splash'})
                else:
                    if getattr(self, 'get_all_pets', None):
                        for target in self.get_all_pets():
                            if target == self or getattr(target, 'is_egg', False) or target.current_state in ['exiting', 'dragged']: continue
                            tx_center = target.x + target.size_w / 2
                            ty_center = target.y + target.size_h / 2
                            
                            # Sweeping intersection evaluation
                            if p['y'] - s < ty_center < p['y'] + 15 and abs(tx_center - wave_abs_x) < s*0.6:
                                if target.current_state.startswith('dark_') and hasattr(target, 'cancel_dark_arts'): target.cancel_dark_arts()
                                if target.current_state.startswith('mewtwo_') and hasattr(target, 'cancel_mewtwo_arts'): target.cancel_mewtwo_arts()
                                if target.current_state in ['digging_in', 'digging', 'digging_out']:
                                    target.canvas.itemconfig(target.canvas_image_id, state='normal')
                                    target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
                                
                                if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
                                target.current_state = 'thrown'
                                target.v_y_velocity = -4.0 # Forces targeted buoyancy inside the wave
                                target.v_x_velocity = p['vx'] * 0.9
                                target.x += p['vx'] 
                                target.anchored_hwnd = None
                                target.climbing_surface = 'floor'

            elif p['type'] == 'splash':
                p['vy'] += 1.8 
                p['x'] += p['vx']
                p['y'] += p['vy']
                self.beast_vfx_canvas.coords(p['id'], p['x']-3, p['y']-3, p['x']+3, p['y']+3)

            if p['life'] > 0:
                alive.append(p)
            else:
                self.beast_vfx_canvas.delete(p['id'])
                
        self.beast_particles = alive

    def _fsm_beast_channeling(self):
        self.beast_timer -= 1
        self._spawn_beast_absorption()
        self._process_beast_particles()
        
        if self.beast_timer <= 0:
            self.current_state = 'beast_roar'
            self.beast_timer = 40 
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_beast_roar(self):
        self.beast_timer -= 1
        self._process_beast_particles()
        
        offset_x = random.choice([-5, 0, 5])
        offset_y = random.choice([-3, 0, 3])
        self.canvas.coords(self.canvas_image_id, (self.size_w//2) + offset_x, (self.size_h//2) + offset_y)
        
        if self.beast_timer == 30:
            self._execute_beast_roar()
            
        if self.beast_timer <= 0:
            self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
            if self.beast_roar_level < 2:
                self.beast_roar_level += 1
                self.current_state = 'beast_dash'
                self.beast_dash_target = random.randint(self.v_x + 100, self.v_x + self.v_width - 100)
                self.is_facing_right = (self.beast_dash_target > self.x)
            else:
                self.current_state = 'beast_wait_clear'
                self.beast_timer = 150 
                
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_beast_dash(self):
        self._process_beast_particles()
        self._spawn_beast_trail()
        
        dist = abs(self.beast_dash_target - self.x)
        dash_speed = 45.0
        
        if dist <= dash_speed:
            self.x = self.beast_dash_target
            self.current_state = 'beast_roar'
            self.beast_timer = 40 
        else:
            self.x += dash_speed if self.is_facing_right else -dash_speed
            
        self.update_position()
        self.schedule_loop(16, self.physics_loop)

    def _fsm_beast_wait_clear(self):
        self.beast_timer -= 1
        self._process_beast_particles()
        
        if not self.beast_particles or self.beast_timer <= 0:
            self.cancel_beast_arts()
            return
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)