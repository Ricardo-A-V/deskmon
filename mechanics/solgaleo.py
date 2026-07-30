import random
import math
import tkinter as tk

class SolgaleoMechanics:
    def cancel_solgaleo_arts(self):
        if hasattr(self, 'solgaleo_win') and self.solgaleo_win and self.solgaleo_win.winfo_exists():
            self.solgaleo_win.destroy()
            self.solgaleo_win = None

        for attr in ['solgaleo_phase', 'solgaleo_timer', 'solgaleo_hit_targets', 's_particles', 'solgaleo_beam_step', 'solgaleo_energy_lines', 'solgaleo_start_angle', 'solgaleo_pulse', 's_jump_particles', 's_shatter_particles']:
            if hasattr(self, attr): delattr(self, attr)

        self.canvas.itemconfig(self.canvas_image_id, state='normal')
        self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
        
        self.surface_angle = 180 if getattr(self, 'gravity_inverted', False) else 0
        
        # Hard assignment prevents the physics engine from applying hover sinusoidal waves during aftermath states.
        # Solgaleo is strictly a ground unit, dynamic config reads here introduce race conditions.
        self.is_flying = False

        if self.current_state not in ['dragged', 'exiting']:
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            self.current_state = 'falling'

    def _fsm_solgaleo_channeling(self):
        if not hasattr(self, 'solgaleo_phase'):
            self.solgaleo_phase = 0
            self.solgaleo_timer = 20 
            self.solgaleo_hit_targets = set()
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            self.is_flying = True 
            
            self.solgaleo_target_x = random.randint(self.v_x + 50, self.v_x + self.v_width - self.size_w - 50)
            
            safe_margin = int(max(self.size_w, self.size_h) * 1.75) + 20
            min_y = self.v_y + safe_margin
            max_y = self.v_y + (self.v_height // 4)
            if min_y > max_y: max_y = min_y + 50
            
            self.solgaleo_target_y = random.randint(min_y, max_y)

        if self.solgaleo_phase == 0:
            self.solgaleo_timer -= 1
            self.is_facing_right = (self.solgaleo_target_x > self.x)
            self.x += 8.0 if self.is_facing_right else -8.0
            
            if self.solgaleo_timer <= 0:
                self.solgaleo_phase = 1
                self.solgaleo_timer = 20 
                self.create_solgaleo_global_canvas()
                self.spawn_solgaleo_jump_vfx()

        elif self.solgaleo_phase == 1:
            dx = self.solgaleo_target_x - self.x
            dy = self.solgaleo_target_y - self.y
            
            self.x += dx * 0.15
            self.y += dy * 0.15
            
            self.solgaleo_timer -= 1
            if self.solgaleo_timer <= 0:
                self.x = self.solgaleo_target_x
                self.y = self.solgaleo_target_y
                self.solgaleo_phase = 2
                self.solgaleo_timer = 40 
                self.spawn_solgaleo_fireball_vfx()

        elif self.solgaleo_phase == 2:
            self.solgaleo_timer -= 1
            
            if self.solgaleo_timer <= 0:
                self.solgaleo_phase = 3
                self.solgaleo_beam_step = 0
                self.solgaleo_timer = 10 
                
                self.beam_target_x = random.randint(self.v_x, self.v_x + self.v_width)
                self.beam_target_y = self.v_y + self.v_height + 150 
                
                # STRICT FIX: Set the visual direction BEFORE calculating the rotation angle
                self.is_facing_right = (self.beam_target_x > self.x)
                
                dx = self.beam_target_x - self.x
                dy = self.beam_target_y - self.y
                
                # LOCALIZED TRIGONOMETRY: By using abs(dx), the angle is calculated relative to 
                # the sprite's forward vector. The animator's horizontal flip handles the left/right global orientation.
                # PIL rotates counter-clockwise for positive values, so we invert it for downward (-Y) pitch.
                local_angle = math.degrees(math.atan2(dy, abs(dx)))
                self.solgaleo_target_angle = -local_angle
                self.solgaleo_start_angle = 0.0

        elif self.solgaleo_phase == 3:
            self.solgaleo_timer -= 1
            self.solgaleo_beam_step += 1
            
            progress = 1.0 - (self.solgaleo_timer / 10.0)
            
            # KINETIC FIX: Smoothstep interpolation function for fluid, non-linear rotation
            smooth_progress = progress * progress * (3 - 2 * progress)
            self.surface_angle = self.solgaleo_start_angle + ((self.solgaleo_target_angle - self.solgaleo_start_angle) * smooth_progress)
            
            self.draw_sunsteel_beam(progress)
            
            if self.solgaleo_timer <= 0:
                self.solgaleo_phase = 4
                self.solgaleo_timer = 10 
                
                # Lock the final angle to prevent drift during the dive
                self.surface_angle = self.solgaleo_target_angle
                self.spawn_fireball_shatter_vfx()

        elif self.solgaleo_phase == 4:
            self.solgaleo_timer -= 1
            progress = 1.0 - (self.solgaleo_timer / 10.0)
            
            self.x = self.solgaleo_target_x + ((self.beam_target_x - self.solgaleo_target_x) * progress)
            self.y = self.solgaleo_target_y + ((self.beam_target_y - self.solgaleo_target_y) * progress)
            
            # EXPLICIT ANGLE RETENTION: Ensures the FSM or animator doesn't overwrite the pitch while diving
            self.surface_angle = getattr(self, 'solgaleo_target_angle', 0)
            
            current_env, _ = self.get_window_environment()
            impact_y = current_env['y'] if self.y <= current_env['y'] else self.default_floor_y
            
            if self.y >= impact_y or self.solgaleo_timer <= 0:
                self.y = impact_y
                self.solgaleo_phase = 5
                self.solgaleo_timer = 20 
                
                self.is_flying = False 
                self.solgaleo_explode()
                
                # KINETIC RESET: Snap the rotation back to 0 strictly upon colliding with the ground
                self.surface_angle = 0
                if getattr(self, 'heavy_fall', False): self.trigger_landing_shake()

        elif self.solgaleo_phase == 5:
            self.solgaleo_timer -= 1
            if self.solgaleo_timer <= 0:
                self.solgaleo_cooldown = 72000 
                self.cancel_solgaleo_arts() 
                
        self.update_position()
        self.schedule_loop(50, self.physics_loop)
        
    def create_solgaleo_global_canvas(self):
        self.solgaleo_win = tk.Toplevel(self.window.master)
        self.solgaleo_win.title("VFX_Solgaleo_Ignore")
        self.solgaleo_win.overrideredirect(True)
        self.solgaleo_win.attributes('-topmost', True)
        
        TRANS_COLOR = '#010101'
        self.solgaleo_win.config(bg=TRANS_COLOR)
        try: self.solgaleo_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass

        self.solgaleo_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        self.solgaleo_canvas = tk.Canvas(self.solgaleo_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
        self.solgaleo_canvas.pack()
        self.solgaleo_win.lift()

    def spawn_solgaleo_jump_vfx(self):
        if not hasattr(self, 'solgaleo_canvas'): return
        if not hasattr(self, 's_jump_particles'): self.s_jump_particles = []
        
        cx = (self.x + self.size_w / 2) - self.v_x
        cy = (self.y + self.size_h) - self.v_y
        
        for _ in range(30):
            size = random.choice([4, 6, 8])
            color = random.choice(["#FF8C00", "#FF4500", "#5C4033", "#8B5A2B"])
            pid = self.solgaleo_canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline=color, tags="vfx_s_jump")
            self.s_jump_particles.append({
                'id': pid,
                'vx': random.uniform(-15, 15),
                'vy': random.uniform(-20, -5),
                'life': 30,
                'type': 'jump'
            })
        self.solgaleo_jump_vfx_loop()

    def solgaleo_jump_vfx_loop(self):
        if not hasattr(self, 's_jump_particles') or not hasattr(self, 'solgaleo_canvas'): return
        alive = []
        for p in self.s_jump_particles:
            if p['life'] > 0:
                self.solgaleo_canvas.move(p['id'], p['vx'], p['vy'])
                p['vy'] += 1.5 
                p['life'] -= 1
                alive.append(p)
            else:
                self.solgaleo_canvas.delete(p['id'])
                
        self.s_jump_particles = alive
        if self.s_jump_particles:
            self.window.after(30, self.solgaleo_jump_vfx_loop)

    def spawn_solgaleo_fireball_vfx(self):
        self.solgaleo_pulse = 0.0
        self.solgaleo_fireball_vfx_loop()

    def solgaleo_fireball_vfx_loop(self):
        if getattr(self, 'current_state', '') != 'solgaleo_channeling' or getattr(self, 'solgaleo_phase', 0) > 3:
            if hasattr(self, 'solgaleo_canvas'): 
                self.solgaleo_canvas.delete("vfx_s_fireball")
                self.solgaleo_canvas.delete("vfx_s_fireball_rings")
            return
            
        if not hasattr(self, 'solgaleo_canvas'): return
        
        self.solgaleo_canvas.delete("vfx_s_fireball_rings") 
        
        cx = (self.x + self.size_w / 2) - self.v_x
        cy = (self.y + self.size_h / 2) - self.v_y
        
        max_r = (min(self.size_w, self.size_h) / 2) * 1.75 
        
        if max_r > 5:
            self.solgaleo_pulse = getattr(self, 'solgaleo_pulse', 0) + 0.15
            
            inner_pulse_mod = math.sin(self.solgaleo_pulse) * 0.05
            r1 = max_r
            r2 = r1 * (0.85 + inner_pulse_mod)
            r3 = r1 * (0.60 + inner_pulse_mod)
            
            self.solgaleo_canvas.create_oval(cx-r1, cy-r1, cx+r1, cy+r1, fill="#FF4500", outline="#FF4500", tags=("vfx_s_fireball", "vfx_s_fireball_rings"))
            self.solgaleo_canvas.create_oval(cx-r2, cy-r2, cx+r2, cy+r2, fill="#FFD700", outline="#FFD700", tags=("vfx_s_fireball", "vfx_s_fireball_rings"))
            self.solgaleo_canvas.create_oval(cx-r3, cy-r3, cx+r3, cy+r3, fill="#FFFFFF", outline="#FFFFFF", tags=("vfx_s_fireball", "vfx_s_fireball_rings"))
            
            for _ in range(4):
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(0, r1)
                
                px = cx + math.cos(angle) * dist
                py = cy + math.sin(angle) * dist
                
                speed = random.uniform(2.0, 7.0)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                
                size = random.choice([3, 4, 5])
                color = random.choice(["#FF8C00", "#FFD700", "#FFFFFF", "#FF4500"])
                
                pid = self.solgaleo_canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color, tags="vfx_s_fireball")
                
                if not hasattr(self, 's_particles'): self.s_particles = []
                self.s_particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': 15})

        alive = []
        if hasattr(self, 's_particles'):
            for p in self.s_particles:
                if p['life'] > 0:
                    self.solgaleo_canvas.move(p['id'], p['vx'], p['vy'])
                    p['life'] -= 1
                    alive.append(p)
                else:
                    self.solgaleo_canvas.delete(p['id'])
            self.s_particles = alive
            
        # FIX Z-ORDER: Overrides the VFX canvas priority, guaranteeing the pet renders on top
        try: self.window.lift()
        except: pass
            
        self.window.after(40, self.solgaleo_fireball_vfx_loop)

    def draw_sunsteel_beam(self, progress):
        if not hasattr(self, 'solgaleo_win') or not self.solgaleo_win: return
        self.solgaleo_canvas.delete("vfx_s_beam")
        
        self.solgaleo_win.lift()
        # FIX Z-ORDER: Forces the pet model over the beam's layer
        try: self.window.lift()
        except: pass
        
        start_x = (self.x + self.size_w / 2) - self.v_x
        start_y = (self.y + self.size_h / 2) - self.v_y
        
        end_x = self.beam_target_x - self.v_x
        end_y = self.beam_target_y - self.v_y
        
        current_x = start_x + (end_x - start_x) * progress
        current_y = start_y + (end_y - start_y) * progress
        
        if progress > 0.01:
            self.solgaleo_canvas.create_line(start_x, start_y, current_x, current_y, fill="#FF8C00", width=91, capstyle=tk.ROUND, tags="vfx_s_beam")
            self.solgaleo_canvas.create_line(start_x, start_y, current_x, current_y, fill="#FFD700", width=70, capstyle=tk.ROUND, tags="vfx_s_beam")
            self.solgaleo_canvas.create_line(start_x, start_y, current_x, current_y, fill="#FFFFFF", width=28, capstyle=tk.ROUND, tags="vfx_s_beam")

            if not hasattr(self, 'solgaleo_energy_lines'):
                self.solgaleo_energy_lines = []
                
            if random.randint(1, 100) <= 60:
                self.solgaleo_energy_lines.append({
                    'progress': 0.0,
                    'speed': random.uniform(0.04, 0.12),
                    'length': random.uniform(0.05, 0.15),
                    'offset_x': random.uniform(-12, 12),
                    'offset_y': random.uniform(-12, 12)
                })

            alive_lines = []
            for line in self.solgaleo_energy_lines:
                line['progress'] += line['speed']
                if line['progress'] <= progress:
                    p_start = max(0.0, line['progress'] - line['length'])
                    p_end = line['progress']
                    
                    lx1 = start_x + (end_x - start_x) * p_start + line['offset_x']
                    ly1 = start_y + (end_y - start_y) * p_start + line['offset_y']
                    lx2 = start_x + (end_x - start_x) * p_end + line['offset_x']
                    ly2 = start_y + (end_y - start_y) * p_end + line['offset_y']
                    
                    self.solgaleo_canvas.create_line(lx1, ly1, lx2, ly2, fill="#FFFFFF", width=3, capstyle=tk.ROUND, tags="vfx_s_beam")
                    alive_lines.append(line)
            self.solgaleo_energy_lines = alive_lines

    def solgaleo_explode(self):
        impact_radius = 850 
        
        if hasattr(self, 'solgaleo_canvas'):
            cx = self.x + self.size_w/2 - self.v_x
            cy = self.y + self.size_h - self.v_y 
            
            exp_state = {'radius': 100.0, 'width': 60.0}
            
            def animate_solgaleo_shockwave():
                if not hasattr(self, 'solgaleo_canvas') or getattr(self, 'solgaleo_win', None) is None: return
                try:
                    self.solgaleo_canvas.delete("vfx_s_exp")
                    exp_state['radius'] += 135.0
                    exp_state['width'] *= 0.6 
                    
                    if exp_state['radius'] >= impact_radius or exp_state['width'] < 1.0:
                        self.solgaleo_canvas.delete("all")
                        if hasattr(self, 'solgaleo_win') and self.solgaleo_win:
                            self.solgaleo_win.destroy()
                            self.solgaleo_win = None
                        return 
                        
                    r = exp_state['radius']
                    w = int(exp_state['width'])
                    self.solgaleo_canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline="#FF8C00", width=w, tags="vfx_s_exp")
                    self.solgaleo_canvas.create_oval(cx-r*0.9, cy-r*0.9, cx+r*0.9, cy+r*0.9, outline="#FFD700", width=max(1, w//2), tags="vfx_s_exp")
                    
                    self.window.after(30, animate_solgaleo_shockwave)
                except:
                    pass
                
            animate_solgaleo_shockwave()

        if getattr(self, 'get_all_pets', None):
            for target in self.get_all_pets():
                if target != self and target.current_state != 'exiting' and not getattr(target, 'is_egg', False):
                    if id(target) in getattr(self, 'solgaleo_hit_targets', set()): continue
                    dist = math.hypot(self.beam_target_x - target.x, self.beam_target_y - target.y)
                    if dist <= impact_radius:
                        self.solgaleo_hit_targets.add(id(target))
                        self.apply_solgaleo_knockback(target)

    def apply_solgaleo_knockback(self, target):
        if target.current_state.startswith('dark_'): target.cancel_dark_arts()
        if getattr(target, 'is_glitching', False):
            target.is_glitching = False
            target.glitch_teleports_left = 0
            
        for prefix, cancel_func in [('mewtwo_', 'cancel_mewtwo_arts'), ('hooh_', 'cancel_hooh_arts'), ('kyogre_', 'cancel_kyogre_arts'), ('groudon_', 'cancel_groudon_arts'), ('lugia_', 'cancel_lugia_arts'), ('rayquaza_', 'cancel_rayquaza_arts'), ('dialga_', 'cancel_dialga_arts'), ('palkia_', 'cancel_palkia_arts'), ('giratina_', 'cancel_giratina_arts'), ('zekrom_', 'cancel_zekrom_arts'), ('reshiram_', 'cancel_reshiram_arts'), ('kyurem_', 'cancel_kyurem_arts'), ('xerneas_', 'cancel_xerneas_arts'), ('yveltal_', 'cancel_yveltal_arts'), ('zygarde_', 'cancel_zygarde_arts'), ('lunala_', 'cancel_lunala_arts')]:
            if target.current_state.startswith(prefix) and hasattr(target, cancel_func): getattr(target, cancel_func)()

        target.canvas.itemconfig(target.canvas_image_id, state='normal')
        if hasattr(target, 'dark_mode'): target.dark_mode = False 
        try: target.window.attributes('-alpha', 1.0)
        except: pass

        target.climbing_surface = 'floor'
        target.surface_angle = 180 if getattr(target, 'gravity_inverted', False) else 0
        target.anchored_hwnd = None
        target.y -= 25 
        
        push_dir = 1.0 if target.x > self.beam_target_x else -1.0
        
        target.current_state = 'thrown'
        target.v_x_velocity = random.uniform(25.0, 35.0) * push_dir
        target.v_y_velocity = random.uniform(-18.0, -25.0)
        target.is_flying = False 
        
        self.spawn_solgaleo_knockback_vfx(target)

    def spawn_solgaleo_knockback_vfx(self, target):
        if not hasattr(target, 'z_target_particles'): target.z_target_particles = []
        cx = target.size_w / 2
        cy = target.size_h / 2
        
        for _ in range(12):
            size = random.choice([3, 4, 5])
            color = random.choice(["#FF8C00", "#FFD700", "#FFFFFF"])
            pid = target.canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline=color, tags="vfx_s_hit")
            
            target.z_target_particles.append({
                'id': pid,
                'vx': random.uniform(-10, 10),
                'vy': random.uniform(-12, 2),
                'life': 15,
                'type': 'dirt'
            })
            
        target.solgaleo_hit_vfx_loop()

    def solgaleo_hit_vfx_loop(self):
        if not hasattr(self, 'z_target_particles'): return
        alive = []
        for p in self.z_target_particles:
            if p['life'] > 0:
                self.canvas.move(p['id'], p['vx'], p['vy'])
                if p['type'] == 'dirt': p['vy'] += 0.8 
                p['life'] -= 1
                alive.append(p)
            else:
                self.canvas.delete(p['id'])
        self.z_target_particles = alive
        if self.z_target_particles:
            self.window.after(30, self.solgaleo_hit_vfx_loop)

    def spawn_fireball_shatter_vfx(self):
        # Injects an omnidirectional kinetic burst at the exact position of the apex.
        # This replaces the fireball visually without moving along with the downward dive.
        if not hasattr(self, 'solgaleo_canvas'): return
        
        cx = (self.x + self.size_w / 2) - self.v_x
        cy = (self.y + self.size_h / 2) - self.v_y
        
        for _ in range(35):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(15.0, 35.0)
            
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            size = random.choice([4, 6, 8])
            color = random.choice(["#FF4500", "#FFD700", "#FFFFFF"])
            
            pid = self.solgaleo_canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline=color, tags="vfx_s_shatter")
            
            if not hasattr(self, 's_shatter_particles'): self.s_shatter_particles = []
            self.s_shatter_particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': 12})
            
        self.solgaleo_shatter_vfx_loop()

    def solgaleo_shatter_vfx_loop(self):
        if not hasattr(self, 's_shatter_particles') or not hasattr(self, 'solgaleo_canvas'): return
        
        alive = []
        for p in self.s_shatter_particles:
            if p['life'] > 0:
                self.solgaleo_canvas.move(p['id'], p['vx'], p['vy'])
                
                p['vx'] *= 0.8
                p['vy'] *= 0.8
                p['life'] -= 1
                alive.append(p)
            else:
                self.solgaleo_canvas.delete(p['id'])
                
        self.s_shatter_particles = alive
        
        # FIX Z-ORDER: Reaffirms pet placement during the shatter animation
        try: self.window.lift()
        except: pass
        
        if self.s_shatter_particles:
            self.window.after(30, self.solgaleo_shatter_vfx_loop)