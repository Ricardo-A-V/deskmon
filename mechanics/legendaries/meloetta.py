import random
import math
import tkinter as tk
import time
import os

class MeloettaMechanics:
    def start_meloetta_mechanic(self):
        if getattr(self, 'current_state', '') in ['dragged', 'exiting']: return
        if getattr(self, 'meloetta_cooldown', 0) > 0: return
        if hasattr(self, 'is_global_mechanic_active') and self.is_global_mechanic_active(ignore_meloetta=True): return

        name = self.pet_name.lower().replace("_", "").replace("-", "")
        if name not in ["meloetta", "meloetta1"]: return

        self.meloetta_cooldown = 108000 # 1 hour
        self.meloetta_form = name
        
        if hasattr(self, 'is_climbing'): self.is_climbing = False
        if hasattr(self, 'climbing_surface'): self.climbing_surface = 'floor'
        if hasattr(self, 'gravity_inverted'): self.gravity_inverted = False
        self.surface_angle = 0
        self.floor_y = getattr(self, 'default_floor_y', self.y)

        
        if self.meloetta_form == "meloetta":
            self.current_state = 'meloetta_aria_charge'
            self.meloetta_timer = 90 # 3 seconds
            self.meloetta_angle = 0
            self.meloetta_notes = []
            self._init_meloetta_vfx()
        else:
            self.current_state = 'meloetta_pirouette_walk'
            self.meloetta_notes = []
            self.meloetta_spawn_timer = 0
            self._init_meloetta_vfx()
            # Calculate target center
            try:
                import win32api
                monitor_info = win32api.GetMonitorInfo(win32api.MonitorFromPoint((int(self.x), int(self.y))))
                monitor_area = monitor_info.get("Monitor", (self.v_x, self.v_y, self.v_x + self.v_width, self.v_y + self.v_height))
                self.meloetta_target_x = monitor_area[0] + (monitor_area[2] - monitor_area[0]) / 2 - self.size_w / 2
            except:
                self.meloetta_target_x = self.v_x + self.v_width / 2
                
            self.is_facing_right = self.meloetta_target_x > self.x
            current_env, _ = self.get_window_environment() if hasattr(self, 'get_window_environment') else (None, None)
            import win32api
            import win32con
            try:
                monitor = win32api.MonitorFromPoint((int(self.x), int(self.y)), win32con.MONITOR_DEFAULTTONEAREST)
                mon_info = win32api.GetMonitorInfo(monitor)
                self.meloetta_target_x = (mon_info['Monitor'][0] + mon_info['Monitor'][2]) / 2
            except:
                self.meloetta_target_x = self.v_x + self.v_width / 2

        self.schedule_loop(33, self.physics_loop)

    def _init_meloetta_vfx(self):
        if not hasattr(self, 'mel_vfx_win') or not self.mel_vfx_win or not self.mel_vfx_win.winfo_exists():
            self.mel_vfx_win = tk.Toplevel(self.window.master)
            self.mel_vfx_win.title("VFX_Meloetta_Ignore")
            self.mel_vfx_win.overrideredirect(True)
            self.mel_vfx_win.attributes('-topmost', True)
            TRANS_COLOR = '#010101'
            self.mel_vfx_win.config(bg=TRANS_COLOR)
            try: self.mel_vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
            except: pass
            
            try:
                import ctypes
                hwnd = ctypes.windll.user32.GetParent(self.mel_vfx_win.winfo_id())
                style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
                ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x00080000 | 0x00000020 | 0x00000008)
            except: pass
            
            self.mel_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
            self.mel_vfx_canvas = tk.Canvas(self.mel_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
            self.mel_vfx_canvas.pack()
            self.mel_particles = []
            self.mel_drawn_notes = []
            self.mel_pentagram = []
            if hasattr(self, 'window'):
                try: self.window.lift()
                except: pass
            self._start_meloetta_particle_loop()

    def _start_meloetta_particle_loop(self):
        if not getattr(self, 'mel_particle_loop_running', False):
            self.mel_particle_loop_running = True
            self._meloetta_particle_loop()

    def _meloetta_particle_loop(self):
        if hasattr(self, 'mel_vfx_win') and self.mel_vfx_win and self.mel_vfx_win.winfo_exists():
            alive = []
            for p in self.mel_particles:
                p['life'] -= 1
                if p['life'] > 0:
                    if p.get('decay') and p['life'] == p['decay']:
                        p['life'] = 0
                        coords = self.mel_vfx_canvas.coords(p['id'])
                        if coords:
                            for _ in range(8):
                                self.mel_particles.append({'id': self.mel_vfx_canvas.create_rectangle(coords[0]-3, coords[1]-3, coords[0]+3, coords[1]+3, fill="#88FF88", outline=""), 'vx': random.uniform(-4, 4), 'vy': random.uniform(-6, -1), 'life': 20, 'type': 'explosion'})
                        self.mel_vfx_canvas.delete(p['id'])
                        continue
                    self.mel_vfx_canvas.move(p['id'], p['vx'], p['vy'])
                    if p.get('type') == 'note':
                        # Float note slightly
                        p['vy'] += math.sin(p['life'] * 0.2) * 0.5
                    elif p.get('type') == 'fired_note':
                        # Collision detection
                        coords = self.mel_vfx_canvas.coords(p['id'])
                        if coords and hasattr(self, 'get_all_pets'):
                            px, py = coords[0] + self.v_x, coords[1] + self.v_y
                            for other_pet in self.get_all_pets():
                                if getattr(other_pet, 'pet_name', '') != self.pet_name and other_pet.current_state != 'exiting':
                                    if other_pet.x < px < other_pet.x + other_pet.size_w and other_pet.y < py < other_pet.y + other_pet.size_h:
                                        self.apply_meloetta_dance(other_pet)
                                        p['life'] = 0
                                        for _ in range(8):
                                            self.mel_particles.append({'id': self.mel_vfx_canvas.create_rectangle(coords[0]-3, coords[1]-3, coords[0]+3, coords[1]+3, fill="#88FF88", outline=""), 'vx': random.uniform(-4, 4), 'vy': random.uniform(-6, -1), 'life': 20, 'type': 'explosion'})
                                        break
                    elif p.get('type') == 'explosion':
                        p['vy'] += 0.4
                    elif p.get('type') == 'orbit':
                        # Orbital logic handled in state machine, just update position
                        pass
                        
                    if p['life'] > 0:
                        alive.append(p)
                    else:
                        self.mel_vfx_canvas.delete(p['id'])
                else:
                    self.mel_vfx_canvas.delete(p['id'])
            self.mel_particles = alive
            
            # Pentagram trail fade
            alive_penta = []
            for line in self.mel_pentagram:
                line['life'] -= 1
                if line['life'] > 0:
                    alive_penta.append(line)
                else:
                    self.mel_vfx_canvas.delete(line['id'])
            self.mel_pentagram = alive_penta
            
            # Float Aria notes
            if self.mel_drawn_notes:
                self.mel_float_timer = getattr(self, 'mel_float_timer', 0) + 1
                for note in self.mel_drawn_notes:
                    if 'x' in note and 'y' in note:
                        offset_y = math.sin(self.mel_float_timer * 0.15 + note['id']) * 5
                        self.mel_vfx_canvas.coords(note['id'], note['x'], note['y'] + offset_y)
            
            if self.mel_particles or self.mel_pentagram or self.mel_drawn_notes or getattr(self, 'current_state', '').startswith('meloetta_') or getattr(self, 'current_state', '') == 'dancing':
                self.window.after(33, self._meloetta_particle_loop)
            else:
                self.mel_vfx_win.destroy()
                self.mel_vfx_win = None
                self.mel_particle_loop_running = False
        else:
            self.mel_particle_loop_running = False

    def cancel_meloetta_arts(self):
        if hasattr(self, 'mel_vfx_win') and self.mel_vfx_win:
            self.mel_vfx_win.destroy()
            self.mel_vfx_win = None
        self.mel_particles = []
        self.mel_pentagram = []
        self.mel_drawn_notes = []
        self.surface_angle = 0
        if getattr(self, 'current_state', '').startswith('meloetta_'):
            self.current_state = 'falling'

    # --- ARIA FORM (GREEN) ---
    def _fsm_meloetta_aria_charge(self):
        self.meloetta_timer -= 1
        self.meloetta_angle += 0.2
        
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        
        # Spiral particles
        r = 100 * (self.meloetta_timer / 90.0)
        px = cx + math.cos(self.meloetta_angle * 3) * r
        py = cy + math.sin(self.meloetta_angle * 3) * r
        
        if hasattr(self, 'mel_vfx_canvas'):
            pid = self.mel_vfx_canvas.create_rectangle(px-3, py-3, px+3, py+3, fill="#88FF88", outline="")
            dx = (cx - px) / 10.0
            dy = (cy - py) / 10.0
            self.mel_particles.append({'id': pid, 'vx': dx, 'vy': dy, 'life': 10, 'type': 'spiral'})
            
        if self.meloetta_timer <= 0:
            self.current_state = 'meloetta_aria_fly_up'
            self.meloetta_timer = 0
            self.meloetta_target_y = self.v_y + 100
            
            # Decide float direction here, but keep is_facing_right matching flight
            self.meloetta_float_right = random.choice([True, False])
            if self.meloetta_float_right:
                self.meloetta_target_x = self.v_x + 100
            else:
                self.meloetta_target_x = self.v_x + self.v_width - self.size_w - 100
            
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_meloetta_aria_fly_up(self):
        speed = 8.0
        self.meloetta_timer += 1
        dx = self.meloetta_target_x - self.x
        dy = self.meloetta_target_y - self.y
        dist = math.hypot(dx, dy)
        
        self.is_facing_right = dx > 0
        
        if dist < speed:
            self.x = self.meloetta_target_x
            self.y = self.meloetta_target_y
            self.current_state = 'meloetta_aria_float'
            self.is_facing_right = getattr(self, 'meloetta_float_right', True)
            self.meloetta_timer = 0
        else:
            perp_x = -dy / dist
            perp_y = dx / dist
            wave = math.sin(self.meloetta_timer * 0.2) * 3.0
            self.x += (dx / dist) * speed + perp_x * wave
            self.y += (dy / dist) * speed + perp_y * wave
            
        self.update_position()
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_meloetta_aria_float(self):
        speed = 6.0
        reached = False
        
        # Float gracefully across
        if self.is_facing_right:
            self.x += speed
            if self.x >= self.v_x + self.v_width - self.size_w - 100:
                reached = True
        else:
            self.x -= speed
            if self.x <= self.v_x + 100:
                reached = True
                
        # Bobbing
        self.y += math.sin(time.time() * 3) * 1.5
        self.update_position()
        
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        
        # Draw pentagram trail
        if hasattr(self, 'mel_vfx_canvas'):
            for i in range(-2, 3):
                py = cy + i * 10
                pid = self.mel_vfx_canvas.create_line(cx, py, cx - (10 if self.is_facing_right else -10), py, fill="#000000", width=1)
                self.mel_pentagram.append({'id': pid, 'life': 60})
                
        # Drop note every 1 second (30 frames)
        self.meloetta_timer += 1
        if self.meloetta_timer >= 30:
            self.meloetta_timer = 0
            if hasattr(self, 'mel_vfx_canvas'):
                colors = ["#55FF55", "#00FF00", "#88FF88"]
                pid = self.mel_vfx_canvas.create_text(cx, cy, text="♪", font=("Fixedsys", 24), fill=random.choice(colors))
                self.mel_drawn_notes.append({'id': pid, 'x': cx, 'y': cy})
                
        if reached:
            self.current_state = 'meloetta_aria_wait'
            self.surface_angle = 0
            self.meloetta_timer = 60 # 2 seconds
            
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_meloetta_aria_wait(self):
        self.meloetta_timer -= 1
        self.y += math.sin(time.time() * 3) * 1.5
        self.update_position()
        
        if self.meloetta_timer <= 0:
            self.current_state = 'meloetta_aria_fire'
            self.meloetta_timer = 30
            
            # Fire notes
            if hasattr(self, 'mel_vfx_canvas'):
                for note in self.mel_drawn_notes:
                    tx = random.uniform(self.v_x + 50, self.v_x + self.v_width - 50) - self.v_x
                    ty = self.v_height - 10
                    dx = (tx - note['x']) / 45.0
                    dy = (ty - note['y']) / 45.0
                    self.mel_particles.append({'id': note['id'], 'vx': dx, 'vy': dy, 'life': 90, 'type': 'fired_note', 'decay': 45})
                self.mel_drawn_notes = []
                
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_meloetta_aria_fire(self):
        self.meloetta_timer -= 1
        if self.meloetta_timer <= 0:
            self.current_state = 'meloetta_aria_fly_down'
            self.meloetta_timer = 0
            self.meloetta_target_x = self.x
            self.meloetta_target_y = getattr(self, 'floor_y', self.default_floor_y)
        self.schedule_loop(33, self.physics_loop)
            
    def _fsm_meloetta_aria_fly_down(self):
        speed = 8.0
        self.meloetta_timer += 1
        dx = self.meloetta_target_x - self.x
        dy = self.meloetta_target_y - self.y
        dist = math.hypot(dx, dy)
        
        if dist < speed:
            self.x = self.meloetta_target_x
            self.y = self.meloetta_target_y
            self.current_state = 'idle'
            if hasattr(self, 'mel_vfx_win') and self.mel_vfx_win:
                self.mel_vfx_win.destroy()
                self.mel_vfx_win = None
        else:
            perp_x = -dy / dist
            if dist > 0:
                perp_y = dx / dist
            else:
                perp_y = 0
            wave = math.sin(self.meloetta_timer * 0.2) * 3.0
            self.x += (dx / dist) * speed + perp_x * wave
            self.y += (dy / dist) * speed + perp_y * wave
            
        self.update_position()
        self.schedule_loop(33, self.physics_loop)

    # --- PIROUETTE FORM (RED) ---
    def _fsm_meloetta_pirouette_walk(self):
        speed = 4.0
        reached = False
        
        target_floor = getattr(self, 'floor_y', self.default_floor_y)
        if hasattr(self, 'get_window_environment'):
            current_env, _ = self.get_window_environment()
            if current_env['hwnd']: target_floor = current_env['y']
            
        # If on a window, step off
        if target_floor < self.default_floor_y - 50:
            self.current_state = 'meloetta_pirouette_jump_off'
            self.v_y_velocity = -10
            self.v_x_velocity = 5.0 if self.is_facing_right else -5.0
            self.meloetta_target_y = self.default_floor_y
            self.schedule_loop(33, self.physics_loop)
            return
            
        if self.x + self.size_w/2 < self.meloetta_target_x - 10:
            self.is_facing_right = True
            self.x += speed
        elif self.x + self.size_w/2 > self.meloetta_target_x + 10:
            self.is_facing_right = False
            self.x -= speed
        else:
            reached = True
            
        self.update_position()
        
        if reached:
            self.current_state = 'meloetta_pirouette_dance'
            self.meloetta_timer = 0
            self.meloetta_spawn_timer = 45 # 1.5 seconds per note
            self.meloetta_orbit_angle = 0
            
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_meloetta_pirouette_jump_off(self):
        self.v_y_velocity += 2.0
        self.x += self.v_x_velocity
        self.y += self.v_y_velocity
        
        if self.y >= self.meloetta_target_y:
            self.y = self.meloetta_target_y
            self.current_state = 'meloetta_pirouette_walk'
            self.floor_y = self.default_floor_y
            
        self.update_position()
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_meloetta_pirouette_dance(self):
        self.meloetta_orbit_angle += 0.05
        self.meloetta_spawn_timer -= 1
        
        # Pirouette dancing movement (bounce and flip)
        target_floor = getattr(self, 'floor_y', getattr(self, 'default_floor_y', self.y))
        self.y = target_floor - abs(math.sin(self.meloetta_orbit_angle * 4)) * 30
        
        if int(self.meloetta_orbit_angle * 20) % 6 == 0:
            self.is_facing_right = not getattr(self, 'is_facing_right', True)
        self.update_position()
        
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        
        if self.meloetta_spawn_timer <= 0 and len(self.mel_drawn_notes) < 8:
            self.meloetta_spawn_timer = 45
            if hasattr(self, 'mel_vfx_canvas'):
                pid = self.mel_vfx_canvas.create_text(cx, cy, text="♪", font=("Arial", 20), fill="#FF5555")
                self.mel_drawn_notes.append({'id': pid, 'angle_offset': len(self.mel_drawn_notes) * (math.pi / 4)})
                # Particle explosion
                for _ in range(10):
                    vx = random.uniform(-3, 3)
                    vy = random.uniform(-3, 3)
                    pid_p = self.mel_vfx_canvas.create_rectangle(cx-2, cy-2, cx+2, cy+2, fill="#FF5555", outline="")
                    self.mel_particles.append({'id': pid_p, 'vx': vx, 'vy': vy, 'life': 15, 'type': 'explosion'})
                    
        # Update orbits
        for note in self.mel_drawn_notes:
            angle = self.meloetta_orbit_angle + note.get('angle_offset', 0)
            nx = cx + math.cos(angle) * 100
            ny = cy + math.sin(angle) * 40
            self.mel_vfx_canvas.coords(note['id'], nx, ny)
            
        if len(self.mel_drawn_notes) >= 8 and self.meloetta_spawn_timer <= -30:
            self.current_state = 'meloetta_pirouette_fire'
            self.meloetta_timer = 0
            
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_meloetta_pirouette_fire(self):
        target_floor = getattr(self, 'floor_y', getattr(self, 'default_floor_y', self.y))
        self.y = target_floor - abs(math.sin(time.time() * 5)) * 10
        self.update_position()
        
        self.meloetta_orbit_angle = getattr(self, 'meloetta_orbit_angle', 0) + 0.05
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        
        if hasattr(self, 'mel_vfx_canvas'):
            for note in self.mel_drawn_notes:
                angle = self.meloetta_orbit_angle + note.get('angle_offset', 0)
                nx = cx + math.cos(angle) * 100
                ny = cy + math.sin(angle) * 40
                self.mel_vfx_canvas.coords(note['id'], nx, ny)
        
        self.meloetta_timer -= 1
        if self.meloetta_timer <= 0:
            if not self.mel_drawn_notes:
                self.current_state = 'idle'
                self.schedule_loop(33, self.physics_loop)
                return
                
            note = self.mel_drawn_notes.pop(0)
            # Find random target
            target = None
            if hasattr(self, 'get_all_pets'):
                valid_targets = [p for p in self.get_all_pets() if getattr(p, 'pet_name', '') != self.pet_name and p.current_state != 'exiting' and not getattr(p, 'is_egg', False)]
                if valid_targets:
                    target = random.choice(valid_targets)
                    
            if hasattr(self, 'mel_vfx_canvas'):
                coords = self.mel_vfx_canvas.coords(note['id'])
                if coords:
                    if target:
                        tx = target.x - self.v_x + target.size_w/2
                        ty = target.y - self.v_y + target.size_h/2
                        dx = (tx - coords[0]) / 15.0
                        dy = (ty - coords[1]) / 15.0
                    else:
                        dx = random.uniform(-10, 10)
                        dy = random.uniform(-10, 10)
                    self.mel_particles.append({'id': note['id'], 'vx': dx, 'vy': dy, 'life': 15, 'type': 'missile', 'target': target})
            else:
                self.mel_vfx_canvas.delete(note['id'])
                
            self.meloetta_timer = 10
            
        # Update missiles
        for p in self.mel_particles:
            if p.get('type') == 'missile':
                target = p.get('target')
                if target and p['life'] == 1:
                    self.apply_meloetta_dance(target)
                    
        self.schedule_loop(33, self.physics_loop)

    def apply_meloetta_dance(self, target):
        # Cancel ongoing arts
        if target.current_state.startswith('dark_'): target.cancel_dark_arts()
        
        for prefix, cancel_func in [('mewtwo_', 'cancel_mewtwo_arts'), ('hooh_', 'cancel_hooh_arts'), ('kyogre_', 'cancel_kyogre_arts'), ('groudon_', 'cancel_groudon_arts'), ('lugia_', 'cancel_lugia_arts'), ('rayquaza_', 'cancel_rayquaza_arts'), ('dialga_', 'cancel_dialga_arts'), ('palkia_', 'cancel_palkia_arts'), ('giratina_', 'cancel_giratina_arts'), ('zekrom_', 'cancel_zekrom_arts'), ('reshiram_', 'cancel_reshiram_arts'), ('victini_', 'cancel_victini_arts'), ('sea_guardian_', 'cancel_sea_guardian_arts'), ('genesect_', 'cancel_genesect_arts')]:
            if target.current_state.startswith(prefix) and hasattr(target, cancel_func): getattr(target, cancel_func)()
            
        if target.current_state == 'bubbled' and hasattr(target, 'manage_bubble_vfx'):
            target.manage_bubble_vfx(False)
            if hasattr(target, 'show_bubble_burst_vfx'): target.show_bubble_burst_vfx()
            
        if target.current_state in ['tk_lifted', 'tk_channeling'] and hasattr(target, 'manage_tk_aura'):
            target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
            
        if target.current_state in ['digging_in', 'digging', 'digging_out']:
            target.canvas.itemconfig(target.canvas_image_id, state='normal')
            target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
            
        if not getattr(target, 'current_state', '') == 'dancing':
            if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
            target.current_state = 'dancing'
            target.surface_angle = 0
            if hasattr(target, 'is_climbing'): target.is_climbing = False
            if hasattr(target, 'climbing_surface'): target.climbing_surface = 'floor'
            if hasattr(target, 'gravity_inverted'): target.gravity_inverted = False
        if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
        target.current_state = 'dancing'
        target.dance_timer = int(15000 / 33) # 15 sec at 33ms
        target.dance_step_timer = 0
        target.dance_step = 0

        # Ensure VFX window for dance particles
        if not hasattr(target, 'mel_vfx_win') or not target.mel_vfx_win:
            if hasattr(target, '_init_meloetta_vfx'):
                target._init_meloetta_vfx()

    # --- DANCING LOGIC (Applied to victims) ---
    def _fsm_dancing(self):
        self.dance_timer -= 1
        self.dance_step_timer -= 1
        
        if self.dance_step_timer <= 0:
            self.dance_step = (self.dance_step + 1) % 6
            self.dance_step_timer = 15 # half second per step
            
            if self.dance_step == 0 or self.dance_step == 4:
                # Step right
                self.is_facing_right = True
                self.v_x_velocity = 5.0
                self.v_y_velocity = -3.0
            elif self.dance_step == 1 or self.dance_step == 3:
                # Step left
                self.is_facing_right = False
                self.v_x_velocity = -5.0
                self.v_y_velocity = -3.0
            elif self.dance_step == 2 or self.dance_step == 5:
                # Jump
                self.v_y_velocity = -10.0
                self.v_x_velocity = 0
                
        # Gravity
        target_floor = getattr(self, 'floor_y', self.default_floor_y)
        if hasattr(self, 'get_window_environment'):
            current_env, _ = self.get_window_environment()
            if current_env['hwnd']: target_floor = current_env['y']
            
        self.v_y_velocity += 2.0
        self.y += self.v_y_velocity
        if self.y >= target_floor:
            self.y = target_floor
            self.v_y_velocity = 0
            
        self.x += self.v_x_velocity
        self.v_x_velocity *= 0.8
        
        self.update_position()
        
        # Particles
        if random.random() < 0.1 and hasattr(self, 'mel_vfx_canvas'):
            cx = self.x - self.v_x + self.size_w/2 + random.uniform(-20, 20)
            cy = self.y - self.v_y + 10
            color = random.choice(["#FF5555", "#55FF55"])
            pid = self.mel_vfx_canvas.create_text(cx, cy, text="♪", font=("Arial", 14), fill=color)
            self.mel_particles.append({'id': pid, 'vx': 0, 'vy': -2, 'life': 20, 'type': 'dance_note'})
            
        if self.dance_timer <= 0:
            self.current_state = 'idle'
            if hasattr(self, 'mel_vfx_win') and self.mel_vfx_win:
                self.mel_vfx_win.destroy()
                self.mel_vfx_win = None
                
        self.schedule_loop(33, self.physics_loop)
