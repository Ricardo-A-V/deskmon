import random
import math
import tkinter as tk

class LunalaMechanics:
    def cancel_lunala_arts(self):
        if hasattr(self, 'lunala_win') and self.lunala_win and self.lunala_win.winfo_exists():
            self.lunala_win.destroy()
            self.lunala_win = None

        for attr in ['lunala_phase', 'lunala_timer', 'lunala_hit_targets', 'l_particles', 'lunala_beam_step', 'lunala_exploded', 'lunala_energy_lines']:
            if hasattr(self, attr): delattr(self, attr)

        # VISUAL FIX: Explicitly delete the charging spiral particles from the Tkinter Canvas
        self.canvas.delete("vfx_l_charge")

        self.canvas.itemconfig(self.canvas_image_id, state='normal')
        self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)

        if self.current_state not in ['dragged', 'exiting']:
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            
            # LOGICAL FIX: Smooth transition to hover height. Binds the current Y coordinate 
            # to the floor_y anchor, forcing the 'ascending' FSM to interpolate the flight path.
            if getattr(self, 'is_flying', False):
                self.floor_y = self.y
                self.current_state = 'ascending'
            else:
                self.current_state = 'falling'

    def _fsm_lunala_channeling(self):
        if not hasattr(self, 'lunala_phase'):
            self.lunala_phase = 0
            self.lunala_hit_targets = set()
            self.lunala_exploded = False
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            
            self.lunala_target_x = random.randint(self.v_x + 50, self.v_x + self.v_width - self.size_w - 50)
            self.lunala_target_y = random.randint(self.v_y, self.v_y + (self.v_height // 8))
            self.is_flying = True

        if self.lunala_phase == 0:
            dx = self.lunala_target_x - self.x
            dy = self.lunala_target_y - self.y
            dist = math.hypot(dx, dy)
            
            self.is_facing_right = (dx > 0)
            
            if dist < 10:
                self.x = self.lunala_target_x
                self.y = self.lunala_target_y
                self.lunala_phase = 1
                self.lunala_timer = 40 
            else:
                self.x += (dx / dist) * 12.0
                self.y += (dy / dist) * 12.0

        elif self.lunala_phase == 1:
            self.lunala_timer -= 1
            self.spawn_lunala_spiral_vfx()
            
            if self.lunala_timer <= 0:
                self.lunala_phase = 2
                self.lunala_beam_step = 0
                # LOGICAL FIX: Total beam duration halved exactly (20 ticks instead of 40)
                self.lunala_timer = 10 
                
                self.beam_target_x = random.randint(self.v_x, self.v_x + self.v_width)
                self.beam_target_y = self.v_y + self.v_height + 150 
                self.is_facing_right = (self.beam_target_x > self.x)
                
                self.spawn_lunala_beam_vfx()

        elif self.lunala_phase == 2:
            self.lunala_timer -= 1
            self.lunala_beam_step += 1
            
            self.lunala_apply_beam_hitbox()
            
            # KINETIC FIX: The beam detonates at step 4 instead of 8 (reaches the ground twice as fast)
            if self.lunala_beam_step == 4 and not getattr(self, 'lunala_exploded', False):
                self.lunala_explode()
                self.lunala_exploded = True
            
            if self.lunala_timer <= 0:
                self.lunala_phase = 3
                self.lunala_timer = 20 
                
        elif self.lunala_phase == 3:
            self.lunala_timer -= 1
            if self.lunala_timer <= 0:
                self.cancel_lunala_arts()
                self.current_state = 'idle'
                self.lunala_cooldown = 72000 

        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def spawn_lunala_spiral_vfx(self):
        progress = 1.0 - (self.lunala_timer / 40.0) 
        cx = self.size_w / 2
        cy = self.size_h / 2
        
        for i in range(6):
            base_angle = (i * (math.pi * 2) / 6)
            current_angle = base_angle + (progress * math.pi * 2) 
            dist = (1.0 - progress) * 120 
            
            px = cx + math.cos(current_angle) * dist
            py = cy + math.sin(current_angle) * dist
            
            size = random.choice([2, 3])
            color = random.choice(["#00BFFF", "#87CEEB", "#E0FFFF"]) 
            pid = self.canvas.create_oval(px-size, py-size, px+size, py+size, fill=color, outline=color, tags="vfx_l_charge")
            
            if not hasattr(self, 'l_particles'): self.l_particles = []
            self.l_particles.append({'id': pid, 'life': 3}) 
            
        self.lunala_charge_vfx_loop()

    def lunala_charge_vfx_loop(self):
        if not hasattr(self, 'l_particles'): return
        alive = []
        for p in self.l_particles:
            if p['life'] > 0:
                p['life'] -= 1
                alive.append(p)
            else:
                self.canvas.delete(p['id'])
        self.l_particles = alive

    def spawn_lunala_beam_vfx(self):
        self.lunala_win = tk.Toplevel(self.window.master)
        self.lunala_win.title("VFX_Lunala_Ignore")
        self.lunala_win.overrideredirect(True)
        self.lunala_win.attributes('-topmost', True)
        
        TRANS_COLOR = '#010101'
        self.lunala_win.config(bg=TRANS_COLOR)
        try: self.lunala_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass

        self.lunala_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        self.lunala_canvas = tk.Canvas(self.lunala_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
        self.lunala_canvas.pack()
        
        self.lunala_beam_loop()

    def lunala_beam_loop(self):
        if getattr(self, 'current_state', '') != 'lunala_channeling': return
        if not hasattr(self, 'lunala_win') or not self.lunala_win or not self.lunala_win.winfo_exists(): return

        self.lunala_canvas.delete("vfx_l_beam")
        self.lunala_win.lift()
        
        # GEOMETRIC FIX: Removed Yveltal offset calculation.
        # The beam strictly originates from Lunala's core (Canvas center).
        start_x = (self.x + self.size_w / 2) - self.v_x
        start_y = (self.y + self.size_h / 2) - self.v_y
        
        end_x = self.beam_target_x - self.v_x
        end_y = self.beam_target_y - self.v_y
        
        # ACCELERATED PROGRESS: Divisor set to 4.0 to double the projection speed
        progress = min(1.0, getattr(self, 'lunala_beam_step', 0) / 4.0)
        
        current_x = start_x + (end_x - start_x) * progress
        current_y = start_y + (end_y - start_y) * progress
        
        if progress > 0.01:
            self.lunala_canvas.create_line(start_x, start_y, current_x, current_y, fill="#800080", width=52, capstyle=tk.ROUND, tags="vfx_l_beam")
            self.lunala_canvas.create_line(start_x, start_y, current_x, current_y, fill="#00BFFF", width=40, capstyle=tk.ROUND, tags="vfx_l_beam")
            self.lunala_canvas.create_line(start_x, start_y, current_x, current_y, fill="#E0FFFF", width=16, capstyle=tk.ROUND, tags="vfx_l_beam")

            if not hasattr(self, 'lunala_energy_lines'):
                self.lunala_energy_lines = []
                
            if random.randint(1, 100) <= 60:
                self.lunala_energy_lines.append({
                    'progress': 0.0,
                    'speed': random.uniform(0.04, 0.12),
                    'length': random.uniform(0.05, 0.15),
                    'offset_x': random.uniform(-12, 12),
                    'offset_y': random.uniform(-12, 12)
                })

            alive_lines = []
            for line in self.lunala_energy_lines:
                line['progress'] += line['speed']
                
                if line['progress'] <= progress:
                    p_start = max(0.0, line['progress'] - line['length'])
                    p_end = line['progress']
                    
                    lx1 = start_x + (end_x - start_x) * p_start + line['offset_x']
                    ly1 = start_y + (end_y - start_y) * p_start + line['offset_y']
                    lx2 = start_x + (end_x - start_x) * p_end + line['offset_x']
                    ly2 = start_y + (end_y - start_y) * p_end + line['offset_y']
                    
                    self.lunala_canvas.create_line(lx1, ly1, lx2, ly2, fill="#FFFFFF", width=3, capstyle=tk.ROUND, tags="vfx_l_beam")
                    alive_lines.append(line)
            self.lunala_energy_lines = alive_lines

        self.window.after(30, self.lunala_beam_loop)

    def lunala_apply_beam_hitbox(self):
        if not getattr(self, 'get_all_pets', None): return
        
        # GEOMETRIC FIX (Hitbox): Adapted to the new central origin of Lunala
        start_x = self.x + self.size_w / 2
        start_y = self.y + self.size_h / 2
        
        end_x = self.beam_target_x
        end_y = self.beam_target_y
        
        # ACCELERATED PROGRESS: Divisor adjusted to 4.0 in physics calculation
        progress = min(1.0, getattr(self, 'lunala_beam_step', 0) / 4.0)
        current_end_x = start_x + (end_x - start_x) * progress
        current_end_y = start_y + (end_y - start_y) * progress
        
        for target in self.get_all_pets():
            if target != self and target.current_state != 'exiting' and not getattr(target, 'is_egg', False):
                if id(target) in getattr(self, 'lunala_hit_targets', set()): continue
                
                target_cx = target.x + target.size_w / 2
                target_cy = target.y + target.size_h / 2
                
                line_dx = current_end_x - start_x
                line_dy = current_end_y - start_y
                line_length_sq = line_dx**2 + line_dy**2
                
                if line_length_sq == 0:
                    dist = math.hypot(target_cx - start_x, target_cy - start_y)
                else:
                    t = max(0, min(1, ((target_cx - start_x) * line_dx + (target_cy - start_y) * line_dy) / line_length_sq))
                    proj_x = start_x + t * line_dx
                    proj_y = start_y + t * line_dy
                    dist = math.hypot(target_cx - proj_x, target_cy - proj_y)
                    
                if dist < 80: 
                    self.lunala_hit_targets.add(id(target))
                    self.apply_lunala_knockback(target)

    def lunala_explode(self):
        # IMPACT FIX: Radius reduced by 15% (from 1000 to 850) to be subtly smaller
        impact_radius = 850 
        
        if hasattr(self, 'lunala_canvas'):
            cx = self.beam_target_x - self.v_x
            cy = self.v_height 
            
            exp_state = {'radius': 100.0, 'width': 60.0}
            
            def animate_lunala_shockwave():
                if not hasattr(self, 'lunala_canvas') or getattr(self, 'current_state', '') != 'lunala_channeling': return
                try:
                    self.lunala_canvas.delete("vfx_l_exp")
                    # Expansion slightly slowed to maintain visual consistency with the new max radius
                    exp_state['radius'] += 135.0
                    exp_state['width'] *= 0.6 
                    
                    if exp_state['radius'] >= impact_radius or exp_state['width'] < 1.0:
                        return 
                        
                    r = exp_state['radius']
                    w = int(exp_state['width'])
                    self.lunala_canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline="#800080", width=w, tags="vfx_l_exp")
                    self.lunala_canvas.create_oval(cx-r*0.9, cy-r*0.9, cx+r*0.9, cy+r*0.9, outline="#00BFFF", width=max(1, w//2), tags="vfx_l_exp")
                    
                    self.window.after(30, animate_lunala_shockwave)
                except:
                    pass
                
            animate_lunala_shockwave()

        if getattr(self, 'get_all_pets', None):
            for target in self.get_all_pets():
                if target != self and target.current_state != 'exiting' and not getattr(target, 'is_egg', False):
                    if id(target) in getattr(self, 'lunala_hit_targets', set()): continue
                    dist = math.hypot(self.beam_target_x - target.x, self.beam_target_y - target.y)
                    if dist <= impact_radius:
                        self.lunala_hit_targets.add(id(target))
                        self.apply_lunala_knockback(target)

    def apply_lunala_knockback(self, target):
        if target.current_state.startswith('dark_'): target.cancel_dark_arts()
        if getattr(target, 'is_glitching', False):
            target.is_glitching = False
            target.glitch_teleports_left = 0
            
        for prefix, cancel_func in [('mewtwo_', 'cancel_mewtwo_arts'), ('hooh_', 'cancel_hooh_arts'), ('kyogre_', 'cancel_kyogre_arts'), ('groudon_', 'cancel_groudon_arts'), ('lugia_', 'cancel_lugia_arts'), ('rayquaza_', 'cancel_rayquaza_arts'), ('dialga_', 'cancel_dialga_arts'), ('palkia_', 'cancel_palkia_arts'), ('giratina_', 'cancel_giratina_arts'), ('zekrom_', 'cancel_zekrom_arts'), ('reshiram_', 'cancel_reshiram_arts'), ('kyurem_', 'cancel_kyurem_arts'), ('xerneas_', 'cancel_xerneas_arts'), ('yveltal_', 'cancel_yveltal_arts'), ('zygarde_', 'cancel_zygarde_arts')]:
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
        
        self.spawn_lunala_knockback_vfx(target)

    def spawn_lunala_knockback_vfx(self, target):
        if not hasattr(target, 'z_target_particles'): target.z_target_particles = []
        cx = target.size_w / 2
        cy = target.size_h / 2
        
        for _ in range(12):
            size = random.choice([3, 4, 5])
            color = random.choice(["#00BFFF", "#87CEEB", "#E0FFFF"])
            pid = target.canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline=color, tags="vfx_l_hit")
            
            target.z_target_particles.append({
                'id': pid,
                'vx': random.uniform(-10, 10),
                'vy': random.uniform(-12, 2),
                'life': 15,
                'type': 'dirt'
            })
            
        target.lunala_hit_vfx_loop()

    def lunala_hit_vfx_loop(self):
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
            self.window.after(30, self.lunala_hit_vfx_loop)