import random
import math
import tkinter as tk

class DiancieMechanics:
    def start_diancie_mechanic(self):
        if getattr(self, 'current_state', '') in ['dragged', 'exiting']: return
        if getattr(self, 'diancie_cooldown', 0) > 0: return
        if hasattr(self, 'is_global_mechanic_active') and self.is_global_mechanic_active(): return

        name = self.pet_name.lower().replace("_", "").replace("-", "")
        if name not in ["diancie", "diancie1"]: return

        self.diancie_cooldown = 120000
        self.current_state = 'diancie_charging'
        self.diancie_timer = 100

        self._init_diancie_vfx()
        self.schedule_loop(30, self.physics_loop)

    def _init_diancie_vfx(self):
        if hasattr(self, 'diancie_vfx_win') and self.diancie_vfx_win and self.diancie_vfx_win.winfo_exists():
            return
            
        self.diancie_vfx_win = tk.Toplevel(self.window.master)
        self.diancie_vfx_win.overrideredirect(True)
        self.diancie_vfx_win.attributes('-topmost', True)
        TRANS_COLOR = '#010101'
        self.diancie_vfx_win.config(bg=TRANS_COLOR)
        try: self.diancie_vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass
        self.diancie_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        
        self.diancie_canvas = tk.Canvas(self.diancie_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
        self.diancie_canvas.pack(fill="both", expand=True)
        
        self.diancie_crystals = []
        self.diancie_particles = []
        self.diancie_frozen_pets = []
        self.diancie_diamonds = []

    def _cleanup_diancie_vfx(self):
        if hasattr(self, 'diancie_vfx_win') and self.diancie_vfx_win and self.diancie_vfx_win.winfo_exists():
            self.diancie_vfx_win.destroy()
            self.diancie_vfx_win = None
            
        for attr in ['diancie_timer', 'diancie_crystals', 'diancie_particles', 'diancie_frozen_pets', 'diancie_diamonds']:
            if hasattr(self, attr): delattr(self, attr)

    def cancel_diancie_arts(self):
        if getattr(self, 'current_state', '') in ['diancie_charging', 'diancie_flying_up', 'diancie_crystallizing', 'diancie_shooting']:
            self.current_state = 'diancie_returning'
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            
        self.diancie_crystals = [] 
        self.diancie_timer = 0
        
        if not getattr(self, 'diancie_frozen_pets', []) and not getattr(self, 'diancie_diamonds', []):
            self._cleanup_diancie_vfx()

    def _fsm_diancie_charging(self):
        self.diancie_timer -= 1
        
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        
        floor_cy = self.default_floor_y - self.v_y + self.size_h
        start_x = cx + random.uniform(-60, 60)
        start_y = floor_cy
        
        dx = cx - start_x
        dy = cy - start_y
        dist = max(1, math.sqrt(dx**2 + dy**2))
        vx = (dx / dist) * 6
        vy = (dy / dist) * 6
        
        color = random.choice(["#FFB6C1", "#FF69B4", "#FF1493"])
        self._spawn_diancie_particle(start_x, start_y, vx, vy, int(dist/6), color)
        
        self._update_diancie_vfx()
        
        if self.diancie_timer <= 0:
            self.current_state = 'diancie_flying_up'
            import win32api
            try:
                monitor_info = win32api.GetMonitorInfo(win32api.MonitorFromPoint((int(self.x + self.size_w/2), int(self.y + self.size_h/2))))
                work_area = monitor_info.get("Work")
                self.diancie_target_x = work_area[0] + (work_area[2] - work_area[0]) / 2 - self.size_w/2
                self.diancie_target_y = work_area[1] + (work_area[3] - work_area[1]) / 4 - self.size_h/2
            except:
                self.diancie_target_x = self.v_x + self.v_width / 2 - self.size_w/2
                self.diancie_target_y = self.v_y + self.v_height / 4 - self.size_h/2

        self.schedule_loop(30, self.physics_loop)

    def _fsm_diancie_flying_up(self):
        dx = self.diancie_target_x - self.x
        dy = self.diancie_target_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist < 10:
            self.current_state = 'diancie_crystallizing'
            self.diancie_timer = 233
            self.diancie_crystal_health = 3
        else:
            self.v_x_velocity = (dx / dist) * 8.0
            self.v_y_velocity = (dy / dist) * 8.0
            self.x += self.v_x_velocity
            self.y += self.v_y_velocity
            self.is_facing_right = self.v_x_velocity > 0
            
            color = random.choice(["#FFB6C1", "#FF69B4", "#FF1493"])
            self._spawn_diancie_particle(self.x - self.v_x + self.size_w/2, self.y - self.v_y + self.size_h/2, 
                                         random.uniform(-1, 1), random.uniform(-1, 1), 20, color)
            
        self.update_position()
        self._update_diancie_vfx()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_diancie_crystallizing(self):
        self.diancie_timer -= 1
        
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        
        if self.diancie_timer % 30 == 0 and len(self.diancie_crystals) < 8:
            pts = []
            angle_offset = random.uniform(0, 2*math.pi)
            for i in range(5):
                r = random.uniform(20, 50)
                a = angle_offset + (i / 5) * 2 * math.pi
                pts.append({'r': r, 'a': a})
            
            self.diancie_crystals.append({
                'cx': cx + random.uniform(-30, 30),
                'cy': cy + random.uniform(-30, 30),
                'pts': pts,
                'growth': 0.0,
                'color': random.choice(["#FFB6C1", "#FF69B4", "#FF1493"])
            })
            
        for c in self.diancie_crystals:
            if c['growth'] < 1.0:
                c['growth'] += 0.0075
                
        self._update_diancie_vfx()
        
        if self.diancie_timer <= 0:
            self.current_state = 'diancie_shooting'
            self.diancie_timer = 40
            self.diancie_shots_fired = 0
            if hasattr(self, 'diancie_vfx_win'):
                self.diancie_manage_frozen_loop()
            
        self.schedule_loop(30, self.physics_loop)

    def _fsm_diancie_shooting(self):
        self.diancie_timer -= 1
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        
        if self.diancie_timer <= 0:
            if self.diancie_shots_fired >= 3:
                for _ in range(50):
                    color = random.choice(["#FFB6C1", "#FF69B4", "#FF1493"])
                    self._spawn_diancie_particle(cx, cy, random.uniform(-10, 10), random.uniform(-10, 10), 30, color)
                
                self.current_state = 'diancie_returning'
                self.diancie_crystals = []
                self.schedule_loop(30, self.physics_loop)
                return
                
            valid_targets = [p for p in self.get_all_pets() if p != self and p.current_state not in ['exiting', 'dragged', 'diancie_frozen'] and not getattr(p, 'is_egg', False)]
            if valid_targets:
                target = random.choice(valid_targets)
                tcx = target.x - self.v_x + getattr(target, 'size_w', 64)/2
                tcy = target.y - self.v_y + getattr(target, 'size_h', 64)/2
                
                dx = tcx - cx
                dy = tcy - cy
                dist = max(1, math.sqrt(dx**2 + dy**2))
                vx = (dx / dist) * 20.0
                vy = (dy / dist) * 20.0
                
                self.diancie_diamonds.append({
                    'x': cx, 'y': cy, 'vx': vx, 'vy': vy, 'target': target, 'life': 200
                })
                
                self.diancie_shots_fired += 1
                self.diancie_timer = 40
                
                if self.diancie_crystals:
                    c = self.diancie_crystals.pop(0)
                    for _ in range(10):
                        color = random.choice(["#FFB6C1", "#FF69B4", "#FF1493"])
                        self._spawn_diancie_particle(c['cx'], c['cy'], random.uniform(-5, 5), random.uniform(-5, 5), 20, color)
            else:
                self.diancie_shots_fired = 3
                self.diancie_timer = 0
                
        self.schedule_loop(30, self.physics_loop)

    def diancie_manage_frozen_loop(self):
        if not hasattr(self, 'diancie_vfx_win') or not self.diancie_vfx_win or not self.diancie_vfx_win.winfo_exists():
            return
            
        all_done = True
        for d in self.diancie_diamonds[:]:
            target = d['target']
            tcx = getattr(target, 'x', 0) - getattr(self, 'v_x', 0) + getattr(target, 'size_w', 64)/2
            tcy = getattr(target, 'y', 0) - getattr(self, 'v_y', 0) + getattr(target, 'size_h', 64)/2
            
            dx = tcx - d['x']
            dy = tcy - d['y']
            dist_to_target = max(1, math.sqrt(dx**2 + dy**2))
            d['vx'] = (dx / dist_to_target) * 80.0
            d['vy'] = (dy / dist_to_target) * 80.0
            
            d['x'] += d['vx']
            d['y'] += d['vy']
            d['life'] -= 1
            
            color = random.choice(["#FFB6C1", "#FF69B4", "#FFFFFF"])
            self._spawn_diancie_particle(d['x'], d['y'], random.uniform(-2, 2), random.uniform(-2, 2), random.randint(10, 15), color)
            
            if dist_to_target <= 80 or d['life'] <= 0:
                self.diancie_diamonds.remove(d)
                if dist_to_target <= 80 and getattr(target, 'current_state', '') not in ['exiting', 'dragged', 'despawning_wild']:
                    if target.current_state in ['teleporting_out', 'teleporting_in']:
                        try: target.window.attributes('-alpha', 1.0)
                        except: pass
                    if target.current_state == 'tk_channeling' and hasattr(target, 'manage_tk_aura'):
                        target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
                        tk_t = getattr(target, 'tk_target', None)
                        if tk_t:
                            t_w = tk_t.size_w if tk_t.__class__.__name__ == 'DesktopPet' else tk_t.size
                            t_h = tk_t.size_h if tk_t.__class__.__name__ == 'DesktopPet' else tk_t.size
                            if hasattr(target, 'manage_tk_aura'): target.manage_tk_aura(tk_t.canvas, t_w, t_h, False)
                            if hasattr(tk_t, 'interrupt_current_state'): tk_t.interrupt_current_state()
                            tk_t.current_state = 'falling'
                            tk_t.tk_master = None
                        target.tk_target = None
                    if target.current_state == 'tk_lifted':
                        if hasattr(target, 'manage_tk_aura'): target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
                        tk_m = getattr(target, 'tk_master', None)
                        if tk_m and tk_m.current_state == 'tk_channeling':
                            if hasattr(tk_m, 'interrupt_current_state'): tk_m.interrupt_current_state()
                            tk_m.current_state = 'idle'
                            if hasattr(tk_m, 'manage_tk_aura'): tk_m.manage_tk_aura(tk_m.canvas, tk_m.size_w, tk_m.size_h, False)
                            tk_m.tk_target = None
                        target.tk_master = None
                    if target.current_state == 'bubbled' and hasattr(target, 'manage_bubble_vfx'):
                        target.manage_bubble_vfx(False)
                        target.show_bubble_burst_vfx()
                    if target.current_state in ['digging', 'digging_in', 'digging_out']:
                        target.canvas.itemconfig(target.canvas_image_id, state='normal')
                        target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
                    if target.current_state == 'regirock_embedded':
                        target.surface_angle = 0
                        target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
                    
                    if target.current_state.startswith('dark_') and hasattr(target, 'cancel_dark_arts'): target.cancel_dark_arts()
                    if target.current_state.startswith('mewtwo_') and hasattr(target, 'cancel_mewtwo_arts'): target.cancel_mewtwo_arts()
                    if target.current_state.startswith('meloetta_') and hasattr(target, 'cancel_meloetta_arts'): target.cancel_meloetta_arts()
                    if target.current_state in ['hooh_channeling', 'panic_run'] and hasattr(target, 'cancel_hooh_arts'): target.cancel_hooh_arts()
                    if target.current_state in ['lugia_channeling', 'lugia_dash'] and hasattr(target, 'cancel_lugia_arts'): target.cancel_lugia_arts()
                    if target.current_state == 'kyogre_channeling' and hasattr(target, 'cancel_kyogre_arts'): target.cancel_kyogre_arts()
                    if target.current_state == 'groudon_channeling' and hasattr(target, 'cancel_groudon_arts'): target.cancel_groudon_arts()
                    if target.current_state in ['diancie_charging', 'diancie_flying_up', 'diancie_crystallizing', 'diancie_shooting'] and hasattr(target, 'cancel_diancie_arts'): target.cancel_diancie_arts()
                    if target.current_state == 'rayquaza_channeling' and hasattr(target, 'cancel_rayquaza_arts'): target.cancel_rayquaza_arts()
                    if target.current_state.startswith('giratina_') and hasattr(target, 'cancel_giratina_arts'): target.cancel_giratina_arts()
                    if target.current_state.startswith('reshiram_') and hasattr(target, 'cancel_reshiram_arts'): target.cancel_reshiram_arts()
                    if target.current_state.startswith('heatran_') and hasattr(target, 'cancel_heatran_arts'): target.cancel_heatran_arts()
                    if target.current_state.startswith('zekrom_') and hasattr(target, 'cancel_zekrom_arts'): target.cancel_zekrom_arts()
                    if target.current_state.startswith('sea_guardian_') and hasattr(target, 'cancel_sea_guardian_arts'): target.cancel_sea_guardian_arts()
                    
                    if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
                    target.current_state = 'diancie_frozen'
                    target.diancie_frozen_timer = 500 
                    
                    pts = []
                    for i in range(6):
                        r = random.uniform(40, 60)
                        a = (i / 6) * 2 * math.pi
                        pts.append({'r': r, 'a': a})
                        
                    self.diancie_frozen_pets.append({
                        'pet': target,
                        'pts': pts,
                        'color': "#FF69B4",
                        'opacity': 0.3
                    })
                    
                    for _ in range(60):
                        color = random.choice(["#FFB6C1", "#FF69B4", "#FF1493", "#FFFFFF"])
                        self._spawn_diancie_particle(tcx, tcy, random.uniform(-12, 12), random.uniform(-12, 12), random.randint(20, 40), color)

        for f in self.diancie_frozen_pets[:]:
            pet = f['pet']
            if not getattr(pet, 'window', None) or not pet.window.winfo_exists() or getattr(pet, 'current_state', '') in ['dragged', 'exiting', 'despawning_wild']:
                tcx = getattr(pet, 'x', 0) - self.v_x + getattr(pet, 'size_w', 64)/2
                tcy = getattr(pet, 'y', 0) - self.v_y + getattr(pet, 'size_h', 64)/2
                for _ in range(80):
                    color = random.choice(["#FFB6C1", "#FF69B4", "#FF1493", "#FFFFFF"])
                    self._spawn_diancie_particle(tcx, tcy, random.uniform(-15, 15), random.uniform(-15, 15), random.randint(25, 50), color)
                self.diancie_frozen_pets.remove(f)
                continue
                
            if getattr(pet, 'diancie_frozen_timer', 0) > 0:
                pet.diancie_frozen_timer -= 1
                all_done = False
                if getattr(pet, 'is_flying', False) or getattr(pet, 'is_climbing', False) or pet.y < getattr(pet, 'default_floor_y', 0):
                    pet.v_y_velocity += getattr(pet, 'gravity', 1.5)
                    pet.v_y_velocity = min(pet.v_y_velocity, 15.0)
                    pet.y += pet.v_y_velocity
                    
                    target_floor = pet.default_floor_y
                    if hasattr(pet, 'get_window_environment'):
                        env, _ = pet.get_window_environment()
                        if env['hwnd'] and pet.y <= env['y'] + 30:
                            target_floor = env['y']
                            
                    if pet.y >= target_floor:
                        pet.y = target_floor
                        pet.v_y_velocity = 0
                else:
                    pet.v_y_velocity = 0
                
                pet.v_x_velocity = 0
                pet.update_position()
            else:
                if pet.current_state == 'diancie_frozen':
                    if hasattr(pet, 'interrupt_current_state'): pet.interrupt_current_state()
                    pet.current_state = 'falling'
                tcx = pet.x - self.v_x + getattr(pet, 'size_w', 64)/2
                tcy = pet.y - self.v_y + getattr(pet, 'size_h', 64)/2
                for _ in range(80):
                    color = random.choice(["#FFB6C1", "#FF69B4", "#FF1493", "#FFFFFF"])
                    self._spawn_diancie_particle(tcx, tcy, random.uniform(-15, 15), random.uniform(-15, 15), random.randint(25, 50), color)
                self.diancie_frozen_pets.remove(f)
                
        self._update_diancie_vfx()
        
        if all_done and not self.diancie_particles and not getattr(self, 'diancie_diamonds', []) and getattr(self, 'current_state', '') != 'diancie_shooting':
            self._cleanup_diancie_vfx()
        else:
            if hasattr(self, 'diancie_vfx_win') and self.diancie_vfx_win and self.diancie_vfx_win.winfo_exists():
                self.diancie_vfx_win.after(30, self.diancie_manage_frozen_loop)

    def _spawn_diancie_particle(self, cx, cy, vx, vy, life, color):
        if not hasattr(self, 'diancie_canvas'): return
        size = random.choice([2, 4, 6])
        pid = self.diancie_canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline="", tags="diancie_vfx")
        self.diancie_particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': life, 'max_life': life, 'max_size': size})

    def _update_diancie_vfx(self):
        if not hasattr(self, 'diancie_canvas') or not self.diancie_canvas.winfo_exists(): return
        self.diancie_canvas.delete("crystal")
        self.diancie_canvas.delete("diamond")
        
        G = 4
        for c in self.diancie_crystals:
            cx = round(c['cx'] / G) * G
            cy = round(c['cy'] / G) * G
            poly = []
            for p in c['pts']:
                r = p['r'] * c['growth']
                x = round((cx + math.cos(p['a']) * r) / G) * G
                y = round((cy + math.sin(p['a']) * r) / G) * G
                poly.extend([x, y])
            if len(poly) >= 6:
                self.diancie_canvas.create_polygon(poly, outline=c['color'], fill="", width=3, tags="crystal")
                self.diancie_canvas.create_polygon(poly, fill=c['color'], stipple="gray25", tags="crystal")

        for d in self.diancie_diamonds:
            cx = d['x']
            cy = d['y']
            angle = math.atan2(d['vy'], d['vx'])
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            
            base_pts = [
                (18, 0),
                (0, 12),
                (-18, 0),
                (0, -12)
            ]
            
            poly = []
            for bx, by in base_pts:
                rx = bx * cos_a - by * sin_a
                ry = bx * sin_a + by * cos_a
                poly.append(round((cx + rx) / G) * G)
                poly.append(round((cy + ry) / G) * G)
                
            self.diancie_canvas.create_polygon(poly, fill="#FFFFFF", outline="#FF1493", width=2, tags="diamond")
            
        for f in self.diancie_frozen_pets:
            pet = f['pet']
            if pet.current_state != 'diancie_frozen': continue
            cx = pet.x - getattr(self, 'v_x', 0) + getattr(pet, 'size_w', 64)/2
            cy = pet.y - getattr(self, 'v_y', 0) + getattr(pet, 'size_h', 64)/2
            cx = round(cx / G) * G
            cy = round(cy / G) * G
            poly = []
            for p in f['pts']:
                r = p['r']
                x = round((cx + math.cos(p['a']) * r) / G) * G
                y = round((cy + math.sin(p['a']) * r) / G) * G
                poly.extend([x, y])
            if len(poly) >= 6:
                self.diancie_canvas.create_polygon(poly, outline="#FF1493", fill="#FF69B4", stipple="gray25", width=4, tags="crystal")

        new_parts = []
        for p in self.diancie_particles:
            p['life'] -= 1
            if p['life'] > 0:
                self.diancie_canvas.move(p['id'], p['vx'], p['vy'])
                ratio = p['life'] / p['max_life']
                new_size = max(1, int(p['max_size'] * ratio))
                coords = self.diancie_canvas.coords(p['id'])
                if coords:
                    cx = (coords[0] + coords[2])/2
                    cy = (coords[1] + coords[3])/2
                    self.diancie_canvas.coords(p['id'], cx-new_size, cy-new_size, cx+new_size, cy+new_size)
                new_parts.append(p)
            else:
                self.diancie_canvas.delete(p['id'])
        self.diancie_particles = new_parts

    def _fsm_diancie_returning(self):
        target_y = getattr(self, 'target_floor_y', self.default_floor_y)
        dy = target_y - self.y
        if abs(dy) < 5:
            self.y = target_y
            self.current_state = 'idle'
        else:
            self.y += math.copysign(3.0, dy)
            self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_diancie_frozen(self):
        self.schedule_loop(30, self.physics_loop)
