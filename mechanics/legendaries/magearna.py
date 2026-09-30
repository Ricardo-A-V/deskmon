import random
import math
import tkinter as tk

class MagearnaMechanics:
    def start_magearna_mechanic(self):
        if getattr(self, 'current_state', '') in ['dragged', 'exiting']: return
        if getattr(self, 'magearna_cooldown', 0) > 0: return
        if hasattr(self, 'is_global_mechanic_active') and self.is_global_mechanic_active(): return

        name = self.pet_name.lower().replace("_", "").replace("-", "")
        if name != "magearna": return

        self.current_state = 'magearna_walk'
        self.magearna_cooldown = 108000 # 1 hour
        self.magearna_target_side = random.choice(["left", "right"])
        self.is_facing_right = (self.magearna_target_side == "right")
        self.magearna_victims = []
        
        self.schedule_loop(33, self.physics_loop)

    def _fsm_magearna_walk(self):
        speed = 4.0
        reached = False
        
        target_floor = self.v_y if getattr(self, 'gravity_inverted', False) else self.default_floor_y
        if hasattr(self, 'get_window_environment'):
            current_env, _ = self.get_window_environment()
            if current_env['hwnd']: target_floor = current_env['y']

        is_inverted = getattr(self, 'gravity_inverted', False)
        if is_inverted:
            if self.y > target_floor:
                self.v_y_velocity = getattr(self, 'v_y_velocity', 0) - 2.0
                self.y += self.v_y_velocity
                if self.y <= target_floor:
                    self.y = target_floor
                    self.v_y_velocity = 0
            else:
                self.y = target_floor
                self.v_y_velocity = 0
        else:
            if self.y < target_floor:
                self.v_y_velocity = getattr(self, 'v_y_velocity', 0) + 2.0
                self.y += self.v_y_velocity
                if self.y >= target_floor:
                    self.y = target_floor
                    self.v_y_velocity = 0
            else:
                self.y = target_floor
                self.v_y_velocity = 0
        
        if self.magearna_target_side == "left":
            self.is_facing_right = False
            self.x -= speed
            if self.x <= self.v_x + 20:
                self.x = self.v_x + 20
                reached = True
        else:
            self.is_facing_right = True
            self.x += speed
            if self.x >= self.v_x + self.v_width - self.size_w - 20:
                self.x = self.v_x + self.v_width - self.size_w - 20
                reached = True
                
        self.update_position()
        
        if reached:
            self.current_state = 'magearna_channeling'
            self.magearna_timer = 90 # 3 seconds
            self.is_facing_right = not self.is_facing_right
            self.magearna_angle = 0
            
        self.schedule_loop(33, self.physics_loop)

    def _fsm_magearna_channeling(self):
        self.magearna_timer -= 1
        self.magearna_angle += 0.4
        
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        
        r = 80
        px = cx + math.cos(self.magearna_angle) * r
        py = cy + math.sin(self.magearna_angle) * r
        vx = -math.cos(self.magearna_angle) * 3 - math.sin(self.magearna_angle) * 3
        vy = -math.sin(self.magearna_angle) * 3 + math.cos(self.magearna_angle) * 3
        self.spawn_magearna_particle(px, py, vx, vy, life=20, p_type="charge")
        
        px2 = cx + math.cos(self.magearna_angle + math.pi) * r
        py2 = cy + math.sin(self.magearna_angle + math.pi) * r
        vx2 = -math.cos(self.magearna_angle + math.pi) * 3 - math.sin(self.magearna_angle + math.pi) * 3
        vy2 = -math.sin(self.magearna_angle + math.pi) * 3 + math.cos(self.magearna_angle + math.pi) * 3
        self.spawn_magearna_particle(px2, py2, vx2, vy2, life=20, p_type="charge")
        
        if self.magearna_timer <= 0:
            self.current_state = 'magearna_laser'
            self.magearna_timer = 150 # 5 seconds
            
            # Store base coordinates for vibration
            self.mag_base_x = self.x
            self.mag_base_y = self.y
            self.magearna_victims = []
            
            self.mag_laser_win = tk.Toplevel(self.window.master)
            self.mag_laser_win.title("VFX_Magearna_Ignore")
            self.mag_laser_win.overrideredirect(True)
            self.mag_laser_win.attributes('-topmost', True)
            TRANS_COLOR = '#010101'
            self.mag_laser_win.config(bg=TRANS_COLOR)
            try: self.mag_laser_win.wm_attributes('-transparentcolor', TRANS_COLOR)
            except: pass
            
            self.mag_laser_width = self.v_width
            self.mag_laser_height = 200
            
            self.mag_laser_canvas = tk.Canvas(self.mag_laser_win, width=self.mag_laser_width, height=self.mag_laser_height, bg=TRANS_COLOR, highlightthickness=0)
            self.mag_laser_canvas.pack()
            
            self.mag_laser_x = self.v_x
            self.mag_laser_y = self.y + self.size_h/2 - self.mag_laser_height/2
            
            self.mag_laser_win.geometry(f"{self.mag_laser_width}x{self.mag_laser_height}+{int(self.mag_laser_x)}+{int(self.mag_laser_y)}")
            
            self.mag_energy_lines = []
            for _ in range(12):
                self.mag_energy_lines.append({
                    'progress': random.uniform(0.0, 1.0),
                    'speed': random.uniform(0.05, 0.15),
                    'length': random.uniform(0.05, 0.2),
                    'offset_y': random.uniform(-10, 10)
                })
            
        self.schedule_loop(33, self.physics_loop)

    def _fsm_magearna_laser(self):
        self.magearna_timer -= 1
        
        # Vibration
        if hasattr(self, 'mag_base_x'):
            self.x = self.mag_base_x + random.uniform(-2, 2)
            self.y = self.mag_base_y + random.uniform(-2, 2)
            self.update_position()
        
        if hasattr(self, 'mag_laser_win') and self.mag_laser_win and self.mag_laser_win.winfo_exists():
            self.mag_laser_canvas.delete("laser")
            
            progress = 1.0 - (self.magearna_timer / 150.0)
            thickness = 10 + (30 * progress) # Starts at 10, quadruples to 40
            
            self.mag_laser_x = self.v_x
            self.mag_laser_y = self.y + self.size_h/2 - self.mag_laser_height/2
            self.mag_laser_win.geometry(f"{self.mag_laser_width}x{self.mag_laser_height}+{int(self.mag_laser_x)}+{int(self.mag_laser_y)}")
            
            cy = self.mag_laser_height / 2
            pet_local_x = self.x - self.v_x + self.size_w/2
            
            if self.is_facing_right:
                start_x = pet_local_x + (self.size_w * 0.2) 
                end_x = self.v_width
                hitbox_start = self.x + self.size_w/2
                hitbox_end = self.v_x + self.v_width
            else:
                start_x = pet_local_x - (self.size_w * 0.2)
                end_x = 0
                hitbox_start = self.v_x
                hitbox_end = self.x + self.size_w/2
                
            # Draw core and aura (Fuchsia colors for Magearna)
            self.mag_laser_canvas.create_line(start_x, cy, end_x, cy, fill="#FF00AA", width=int(thickness*2.5), capstyle=tk.ROUND, tags="laser")
            self.mag_laser_canvas.create_line(start_x, cy, end_x, cy, fill="#FF00FF", width=int(thickness*1.5), capstyle=tk.ROUND, tags="laser")
            self.mag_laser_canvas.create_line(start_x, cy, end_x, cy, fill="#FFFFFF", width=int(thickness), capstyle=tk.ROUND, tags="laser")
            
            if not hasattr(self, 'mag_energy_lines'): self.mag_energy_lines = []
            for line in self.mag_energy_lines:
                line['progress'] += line['speed']
                if line['progress'] > 1.0 + line['length']:
                    line['progress'] = 0.0
                    line['offset_y'] = random.uniform(-thickness/1.5, thickness/1.5)
                
                p_start = max(0.0, line['progress'] - line['length'])
                p_end = min(1.0, line['progress'])
                
                if p_start < p_end:
                    lx1 = start_x + (end_x - start_x) * p_start
                    ly1 = cy + line['offset_y']
                    lx2 = start_x + (end_x - start_x) * p_end
                    ly2 = cy + line['offset_y']
                    self.mag_laser_canvas.create_line(lx1, ly1, lx2, ly2, fill="#FFFFFF", width=int(thickness/4 + 1), capstyle=tk.ROUND, tags="laser")
            
            beam_y = self.y + self.size_h/2
            if hasattr(self, 'get_all_pets'):
                for target in self.get_all_pets():
                    if target != self and target.current_state != 'exiting' and not getattr(target, 'is_egg', False):
                        if target.current_state != 'magearna_victim':
                            target_cy = target.y + target.size_h/2
                            if abs(target_cy - beam_y) < (target.size_h/2 + thickness):
                                target_cx = target.x + target.size_w/2
                                if hitbox_start <= target_cx <= hitbox_end or hitbox_end <= target_cx <= hitbox_start:
                                    self.apply_magearna_vibration(target)
            
        if self.magearna_timer <= 0:
            if hasattr(self, 'mag_laser_win') and self.mag_laser_win:
                self.mag_laser_win.destroy()
                self.mag_laser_win = None
                
            # Restore exact position
            if hasattr(self, 'mag_base_x'):
                self.x = self.mag_base_x
                self.y = self.mag_base_y
                self.update_position()
                
            self.trigger_magearna_explosion()
            
            # Launch victims
            for victim in getattr(self, 'magearna_victims', []):
                if hasattr(victim, 'current_state') and victim.current_state == 'magearna_victim':
                    if hasattr(victim, 'interrupt_current_state'): victim.interrupt_current_state()
                    victim.current_state = 'thrown'
                    victim.v_x_velocity = random.uniform(35.0, 55.0) if self.is_facing_right else random.uniform(-55.0, -35.0)
                    victim.v_y_velocity = random.uniform(-55.0, -45.0)
                    if hasattr(victim, 'mag_vib_base_x'):
                        victim.x = victim.mag_vib_base_x
                        victim.y = victim.mag_vib_base_y
                        victim.update_position()
                        delattr(victim, 'mag_vib_base_x')
                        delattr(victim, 'mag_vib_base_y')
                    
                    # Target explosion
                    cx = victim.x - victim.v_x + victim.size_w/2
                    cy = victim.y - victim.v_y + victim.size_h/2
                    for _ in range(15):
                        angle = random.uniform(0, math.pi * 2)
                        speed = random.uniform(2, 6)
                        vx = math.cos(angle) * speed
                        vy = math.sin(angle) * speed
                        self.spawn_magearna_particle(cx, cy, vx, vy, life=15, p_type="spark")
                        
            self.magearna_victims = []
            self.current_state = 'idle'
            
        self.schedule_loop(33, self.physics_loop)

    def _fsm_magearna_victim(self):
        # The victim shakes violently in place
        if not hasattr(self, 'mag_vib_base_x'):
            self.mag_vib_base_x = self.x
            self.mag_vib_base_y = self.y
            
        self.x = self.mag_vib_base_x + random.uniform(-3, 3)
        self.y = self.mag_vib_base_y + random.uniform(-3, 3)
        self.update_position()
        self.schedule_loop(33, self.physics_loop)
        
    def trigger_magearna_explosion(self):
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        for _ in range(25):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3, 8)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.spawn_magearna_particle(cx, cy, vx, vy, life=20, p_type="spark")

    def spawn_magearna_particle(self, cx, cy, vx, vy, life, p_type="charge"):
        if not hasattr(self, 'mag_vfx_win') or not self.mag_vfx_win or not self.mag_vfx_win.winfo_exists():
            self._init_magearna_vfx()
            
        color = "#FF00FF" if p_type == "charge" else "#FF00AA"
        size = 4 if p_type == "charge" else 3
        
        pid = self.mag_vfx_canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline="")
        if not hasattr(self, 'mag_particles'): self.mag_particles = []
        self.mag_particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': life, 'max_life': life, 'max_size': size, 'type': p_type})

    def _init_magearna_vfx(self):
        self.mag_vfx_win = tk.Toplevel(self.window.master)
        self.mag_vfx_win.title("VFX_Magearna_Ignore")
        self.mag_vfx_win.overrideredirect(True)
        self.mag_vfx_win.attributes('-topmost', True)
        TRANS_COLOR = '#010101'
        self.mag_vfx_win.config(bg=TRANS_COLOR)
        try: self.mag_vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass
        
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.mag_vfx_win.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x00080000 | 0x00000020 | 0x00000008)
        except: pass
        
        self.mag_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        self.mag_vfx_canvas = tk.Canvas(self.mag_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
        self.mag_vfx_canvas.pack()
        self.mag_particles = []
        self._start_magearna_particle_loop()

    def _start_magearna_particle_loop(self):
        if not hasattr(self, 'mag_particle_loop_running') or not self.mag_particle_loop_running:
            self.mag_particle_loop_running = True
            self._magearna_particle_loop()
            
    def _magearna_particle_loop(self):
        if hasattr(self, 'mag_vfx_win') and self.mag_vfx_win and self.mag_vfx_win.winfo_exists():
            alive = []
            for p in self.mag_particles:
                p['life'] -= 1
                if p['life'] > 0:
                    self.mag_vfx_canvas.move(p['id'], p['vx'], p['vy'])
                    coords = self.mag_vfx_canvas.coords(p['id'])
                    if coords:
                        cx = (coords[0] + coords[2]) / 2
                        cy = (coords[1] + coords[3]) / 2
                        r = p['max_size'] * (p['life'] / p['max_life'])
                        self.mag_vfx_canvas.coords(p['id'], cx-r, cy-r, cx+r, cy+r)
                    alive.append(p)
                else:
                    self.mag_vfx_canvas.delete(p['id'])
            self.mag_particles = alive
            
            if getattr(self, 'mag_particles', []) or getattr(self, 'current_state', '').startswith('magearna_'):
                self.window.after(33, self._magearna_particle_loop)
            else:
                self.mag_vfx_win.destroy()
                self.mag_vfx_win = None
                self.mag_particle_loop_running = False
        else:
            self.mag_particle_loop_running = False
            
    def cancel_magearna_arts(self):
        if hasattr(self, 'mag_vfx_win') and self.mag_vfx_win:
            self.mag_vfx_win.destroy()
            self.mag_vfx_win = None
        if hasattr(self, 'mag_laser_win') and self.mag_laser_win:
            self.mag_laser_win.destroy()
            self.mag_laser_win = None
            
        self.mag_particles = []
        
        # Release victims
        for victim in getattr(self, 'magearna_victims', []):
            if hasattr(victim, 'current_state') and victim.current_state == 'magearna_victim':
                if hasattr(victim, 'interrupt_current_state'): victim.interrupt_current_state()
                victim.current_state = 'thrown'
                victim.v_x_velocity = random.uniform(35.0, 55.0) if self.is_facing_right else random.uniform(-55.0, -35.0)
                victim.v_y_velocity = random.uniform(-55.0, -45.0)
                if hasattr(victim, 'mag_vib_base_x'):
                    victim.x = victim.mag_vib_base_x
                    victim.y = victim.mag_vib_base_y
                    victim.update_position()
                    delattr(victim, 'mag_vib_base_x')
                    delattr(victim, 'mag_vib_base_y')
        self.magearna_victims = []
        
        if getattr(self, 'current_state', '').startswith('magearna_'):
            self.current_state = 'falling'
            
    def apply_magearna_vibration(self, target):
        if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
            
        target.current_state = 'magearna_victim'
        self.magearna_victims.append(target)
