import random
import math
import tkinter as tk
import time

class GenesectMechanics:
    def start_genesect_mechanic(self):
        if getattr(self, 'current_state', '') in ['dragged', 'exiting']: return
        if getattr(self, 'genesect_cooldown', 0) > 0: return
        if hasattr(self, 'is_global_mechanic_active') and self.is_global_mechanic_active(ignore_genesect=True): return

        name = self.pet_name.lower().replace("_", "").replace("-", "")
        if name != "genesect": return

        self.current_state = 'genesect_walk'
        self.genesect_cooldown = 108000 # 1 hour
        self.genesect_target_side = random.choice(["left", "right"])
        self.is_facing_right = (self.genesect_target_side == "right")
        
        self.schedule_loop(33, self.physics_loop)

    def _fsm_genesect_walk(self):
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
        
        if self.genesect_target_side == "left":
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
            self.current_state = 'genesect_channeling'
            self.genesect_timer = 90 # 3 seconds
            self.is_facing_right = not self.is_facing_right
            self.genesect_angle = 0
            
        self.schedule_loop(33, self.physics_loop)

    def _fsm_genesect_channeling(self):
        self.genesect_timer -= 1
        self.genesect_angle += 0.3
        
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        
        px = cx + math.cos(self.genesect_angle) * 50
        py = cy + math.sin(self.genesect_angle) * 50
        self.spawn_genesect_particle(px, py, 0, 0, life=10, p_type="charge")
        
        px2 = cx + math.cos(self.genesect_angle + math.pi) * 50
        py2 = cy + math.sin(self.genesect_angle + math.pi) * 50
        self.spawn_genesect_particle(px2, py2, 0, 0, life=10, p_type="charge")
        
        if self.genesect_timer <= 0:
            self.current_state = 'genesect_laser'
            self.genesect_timer = 150 # 5 seconds
            
            # Store base coordinates for vibration
            self.gen_base_x = self.x
            self.gen_base_y = self.y
            
            self.gen_laser_win = tk.Toplevel(self.window.master)
            self.gen_laser_win.title("VFX_Genesect_Ignore")
            self.gen_laser_win.overrideredirect(True)
            self.gen_laser_win.attributes('-topmost', True)
            TRANS_COLOR = '#010101'
            self.gen_laser_win.config(bg=TRANS_COLOR)
            try: self.gen_laser_win.wm_attributes('-transparentcolor', TRANS_COLOR)
            except: pass
            
            self.gen_laser_width = self.v_width
            self.gen_laser_height = 200
            
            self.gen_laser_canvas = tk.Canvas(self.gen_laser_win, width=self.gen_laser_width, height=self.gen_laser_height, bg=TRANS_COLOR, highlightthickness=0)
            self.gen_laser_canvas.pack()
            
            self.gen_laser_x = self.v_x
            self.gen_laser_y = self.y + self.size_h/2 - self.gen_laser_height/2
            
            self.gen_laser_win.geometry(f"{self.gen_laser_width}x{self.gen_laser_height}+{int(self.gen_laser_x)}+{int(self.gen_laser_y)}")
            
            self.gen_energy_lines = []
            for _ in range(12):
                self.gen_energy_lines.append({
                    'progress': random.uniform(0.0, 1.0),
                    'speed': random.uniform(0.05, 0.15),
                    'length': random.uniform(0.05, 0.2),
                    'offset_y': random.uniform(-10, 10)
                })
            
        self.schedule_loop(33, self.physics_loop)

    def _fsm_genesect_laser(self):
        self.genesect_timer -= 1
        
        # Vibration
        if hasattr(self, 'gen_base_x'):
            self.x = self.gen_base_x + random.uniform(-2, 2)
            self.y = self.gen_base_y + random.uniform(-2, 2)
            self.update_position()
        
        if hasattr(self, 'gen_laser_win') and self.gen_laser_win and self.gen_laser_win.winfo_exists():
            self.gen_laser_canvas.delete("laser")
            
            progress = 1.0 - (self.genesect_timer / 150.0)
            thickness = 10 + (30 * progress) # Starts at 10, quadruples to 40
            
            self.gen_laser_x = self.v_x
            self.gen_laser_y = self.y + self.size_h/2 - self.gen_laser_height/2
            self.gen_laser_win.geometry(f"{self.gen_laser_width}x{self.gen_laser_height}+{int(self.gen_laser_x)}+{int(self.gen_laser_y)}")
            
            cy = self.gen_laser_height / 2
            pet_local_x = self.x - self.v_x + self.size_w/2
            
            if self.is_facing_right:
                start_x = pet_local_x + (self.size_w * 0.2) # Start from slightly in front of him
                end_x = self.v_width
                hitbox_start = self.x + self.size_w/2
                hitbox_end = self.v_x + self.v_width
            else:
                start_x = pet_local_x - (self.size_w * 0.2)
                end_x = 0
                hitbox_start = self.v_x
                hitbox_end = self.x + self.size_w/2
                
            # Draw core and aura to make it look powerful
            self.gen_laser_canvas.create_line(start_x, cy, end_x, cy, fill="#27AE60", width=int(thickness*2.5), capstyle=tk.ROUND, tags="laser")
            self.gen_laser_canvas.create_line(start_x, cy, end_x, cy, fill="#2ECC71", width=int(thickness*1.5), capstyle=tk.ROUND, tags="laser")
            self.gen_laser_canvas.create_line(start_x, cy, end_x, cy, fill="#FFFFFF", width=int(thickness), capstyle=tk.ROUND, tags="laser")
            
            if not hasattr(self, 'gen_energy_lines'): self.gen_energy_lines = []
            for line in self.gen_energy_lines:
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
                    self.gen_laser_canvas.create_line(lx1, ly1, lx2, ly2, fill="#FFFFFF", width=int(thickness/4 + 1), capstyle=tk.ROUND, tags="laser")
            
            beam_y = self.y + self.size_h/2
            if hasattr(self, 'get_all_pets'):
                for target in self.get_all_pets():
                    if target != self and target.current_state != 'exiting' and not getattr(target, 'is_egg', False):
                        if not getattr(target, 'is_glitching', False):
                            target_cy = target.y + target.size_h/2
                            if abs(target_cy - beam_y) < (target.size_h/2 + thickness):
                                target_cx = target.x + target.size_w/2
                                if hitbox_start <= target_cx <= hitbox_end or hitbox_end <= target_cx <= hitbox_start:
                                    self.apply_genesect_glitch(target)
            
        if self.genesect_timer <= 0:
            if hasattr(self, 'gen_laser_win') and self.gen_laser_win:
                self.gen_laser_win.destroy()
                self.gen_laser_win = None
                
            # Restore exact position
            if hasattr(self, 'gen_base_x'):
                self.x = self.gen_base_x
                self.y = self.gen_base_y
                self.update_position()
                
            self.trigger_genesect_explosion()
            self.current_state = 'idle'
            
        self.schedule_loop(33, self.physics_loop)
        
    def trigger_genesect_explosion(self):
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        for _ in range(25):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3, 8)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.spawn_genesect_particle(cx, cy, vx, vy, life=20, p_type="spark")

    def spawn_genesect_particle(self, cx, cy, vx, vy, life, p_type="charge"):
        if not hasattr(self, 'gen_vfx_win') or not self.gen_vfx_win or not self.gen_vfx_win.winfo_exists():
            self._init_genesect_vfx()
            
        color = "#2ECC71" if p_type == "charge" else "#FFFFFF"
        size = 4 if p_type == "charge" else 3
        
        pid = self.gen_vfx_canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline="")
        if not hasattr(self, 'gen_particles'): self.gen_particles = []
        self.gen_particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': life, 'max_life': life, 'max_size': size, 'type': p_type})

    def _init_genesect_vfx(self):
        self.gen_vfx_win = tk.Toplevel(self.window.master)
        self.gen_vfx_win.title("VFX_Genesect_Ignore")
        self.gen_vfx_win.overrideredirect(True)
        self.gen_vfx_win.attributes('-topmost', True)
        TRANS_COLOR = '#010101'
        self.gen_vfx_win.config(bg=TRANS_COLOR)
        try: self.gen_vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass
        
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.gen_vfx_win.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x00080000 | 0x00000020 | 0x00000008)
        except: pass
        
        self.gen_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        self.gen_vfx_canvas = tk.Canvas(self.gen_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
        self.gen_vfx_canvas.pack()
        self.gen_particles = []
        self._start_genesect_particle_loop()

    def _start_genesect_particle_loop(self):
        if not hasattr(self, 'gen_particle_loop_running') or not self.gen_particle_loop_running:
            self.gen_particle_loop_running = True
            self._genesect_particle_loop()
            
    def _genesect_particle_loop(self):
        if hasattr(self, 'gen_vfx_win') and self.gen_vfx_win and self.gen_vfx_win.winfo_exists():
            alive = []
            for p in self.gen_particles:
                p['life'] -= 1
                if p['life'] > 0:
                    self.gen_vfx_canvas.move(p['id'], p['vx'], p['vy'])
                    coords = self.gen_vfx_canvas.coords(p['id'])
                    if coords:
                        cx = (coords[0] + coords[2]) / 2
                        cy = (coords[1] + coords[3]) / 2
                        r = p['max_size'] * (p['life'] / p['max_life'])
                        self.gen_vfx_canvas.coords(p['id'], cx-r, cy-r, cx+r, cy+r)
                    alive.append(p)
                else:
                    self.gen_vfx_canvas.delete(p['id'])
            self.gen_particles = alive
            
            if getattr(self, 'gen_particles', []) or getattr(self, 'current_state', '').startswith('genesect_') or getattr(self, 'is_glitching', False):
                self.window.after(33, self._genesect_particle_loop)
            else:
                self.gen_vfx_win.destroy()
                self.gen_vfx_win = None
                self.gen_particle_loop_running = False
        else:
            self.gen_particle_loop_running = False
            
    def cancel_genesect_arts(self):
        if hasattr(self, 'gen_vfx_win') and self.gen_vfx_win:
            self.gen_vfx_win.destroy()
            self.gen_vfx_win = None
        if hasattr(self, 'gen_laser_win') and self.gen_laser_win:
            self.gen_laser_win.destroy()
            self.gen_laser_win = None
            
        self.gen_particles = []
        if getattr(self, 'current_state', '').startswith('genesect_'):
            self.current_state = 'falling'
            
    def apply_genesect_glitch(self, target):
        if target.current_state.startswith('dark_'): target.cancel_dark_arts()
        
        for prefix, cancel_func in [('mewtwo_', 'cancel_mewtwo_arts'), ('hooh_', 'cancel_hooh_arts'), ('kyogre_', 'cancel_kyogre_arts'), ('groudon_', 'cancel_groudon_arts'), ('lugia_', 'cancel_lugia_arts'), ('rayquaza_', 'cancel_rayquaza_arts'), ('dialga_', 'cancel_dialga_arts'), ('palkia_', 'cancel_palkia_arts'), ('giratina_', 'cancel_giratina_arts'), ('zekrom_', 'cancel_zekrom_arts'), ('reshiram_', 'cancel_reshiram_arts'), ('victini_', 'cancel_victini_arts'), ('sea_guardian_', 'cancel_sea_guardian_arts')]:
            if target.current_state.startswith(prefix) and hasattr(target, cancel_func): getattr(target, cancel_func)()
            
        if target.current_state == 'bubbled' and hasattr(target, 'manage_bubble_vfx'):
            target.manage_bubble_vfx(False)
            if hasattr(target, 'show_bubble_burst_vfx'): target.show_bubble_burst_vfx()
            
        if target.current_state in ['tk_lifted', 'tk_channeling'] and hasattr(target, 'manage_tk_aura'):
            target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
            
        target.is_glitching = True
        target.has_genesect_glitch = True
        target.glitch_teleports_left = 5 # Will result in ~11 seconds of glitching behavior
        
        if hasattr(target, 'schedule_glitch_teleport'):
            target.schedule_glitch_teleport()
        else:
            if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
            target.current_state = 'idle'
