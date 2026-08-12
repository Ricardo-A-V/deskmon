import math
import random
import tkinter as tk

class LegendaryGeniesMechanics:
    def _clear_victim_state(self, target):
        if target.current_state == 'bubbled':
            if hasattr(target, 'manage_bubble_vfx'): target.manage_bubble_vfx(False)
            if hasattr(target, 'show_bubble_burst_vfx'): target.show_bubble_burst_vfx()
            
        if target.current_state == 'tk_lifted':
            if hasattr(target, 'manage_tk_aura'): target.manage_tk_aura(target.canvas, getattr(target, 'size_w', 50), getattr(target, 'size_h', 50), False)
            master = getattr(target, 'tk_master', None)
            if master and master.current_state == 'tk_channeling':
                master.current_state = 'idle'
                if hasattr(master, 'manage_tk_aura'): master.manage_tk_aura(master.canvas, getattr(master, 'size_w', 50), getattr(master, 'size_h', 50), False)
                master.tk_target = None
            target.tk_master = None
            
        if target.current_state in ['digging_in', 'digging', 'digging_out', 'regirock_embedded', 'embedded']:
            target.canvas.itemconfig(target.canvas_image_id, state='normal')
            target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
            if hasattr(target, 'dig_hole_win') and target.dig_hole_win:
                target.dig_hole_win.destroy()
                target.dig_hole_win = None
                
        state = target.current_state
        if state.startswith('dark_'):
            if hasattr(target, 'cancel_dark_arts'): target.cancel_dark_arts()
        elif state.startswith('mewtwo_'):
            if hasattr(target, 'cancel_mewtwo_arts'): target.cancel_mewtwo_arts()
        elif state.startswith('meloetta_'):
            if hasattr(target, 'cancel_meloetta_arts'): target.cancel_meloetta_arts()
        elif state in ['hooh_channeling', 'panic_run']:
            if hasattr(target, 'cancel_hooh_arts'): target.cancel_hooh_arts()
        elif state in ['lugia_channeling', 'lugia_dash']:
            if hasattr(target, 'cancel_lugia_arts'): target.cancel_lugia_arts()
        elif state == 'kyogre_channeling':
            if hasattr(target, 'cancel_kyogre_arts'): target.cancel_kyogre_arts()
        elif state == 'groudon_channeling':
            if hasattr(target, 'cancel_groudon_arts'): target.cancel_groudon_arts()
        elif state == 'rayquaza_channeling':
            if hasattr(target, 'cancel_rayquaza_arts'): target.cancel_rayquaza_arts()
        elif state.startswith('giratina_'):
            if hasattr(target, 'cancel_giratina_arts'): target.cancel_giratina_arts()
        elif state.startswith('reshiram_'):
            if hasattr(target, 'cancel_reshiram_arts'): target.cancel_reshiram_arts()
        elif state.startswith('heatran_'):
            if hasattr(target, 'cancel_heatran_arts'): target.cancel_heatran_arts()
        elif state == 'celebi_frozen':
            if hasattr(target, 'cancel_celebi_arts'): target.cancel_celebi_arts()
        elif state.startswith('cresselia_'):
            if hasattr(target, 'cancel_cresselia_arts'): target.cancel_cresselia_arts()
        elif state.startswith('lake_'):
            if hasattr(target, 'cancel_lake_arts'): target.cancel_lake_arts()
        elif state.startswith('beast_'):
            if hasattr(target, 'cancel_beast_arts'): target.cancel_beast_arts()
        elif state.startswith('bird_'):
            if hasattr(target, 'cancel_bird_arts'): target.cancel_bird_arts()
        elif state.startswith('genie_'):
            if hasattr(target, 'cancel_genie_arts'): target.cancel_genie_arts()
        elif state == 'regirock_embedded':
            if hasattr(target, 'cancel_regi_arts'): target.cancel_regi_arts()
            
        target.is_sleeping = False
        target.is_glitching = False
        target.is_frozen = False
        target.is_paralyzed = False
        
        if hasattr(target, 'tapu_field_timeout'):
            if hasattr(target, 'original_speed'):
                target.speed = target.original_speed
            delattr(target, 'tapu_field_timeout')
            
        target.anchored_hwnd = None
        target.climbing_surface = 'floor'
        target.v_x_velocity = 0.0
        target.v_y_velocity = 0.0
        
    def cancel_genie_arts(self):
        if hasattr(self, 'genie_vfx_win') and self.genie_vfx_win and self.genie_vfx_win.winfo_exists():
            self.genie_vfx_win.destroy()
            self.genie_vfx_win = None

        for attr in ['genie_timer', 'genie_phase', 'genie_type', 'genie_particles', 'genie_target', 'genie_sphere', 'genie_tornadoes', 'genie_angle']:
            if hasattr(self, attr): delattr(self, attr)

        self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)

        if self.current_state not in ['dragged', 'exiting']:
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            if getattr(self, 'is_flying', False):
                self.current_state = 'idle'
            else:
                self.current_state = 'falling'

        if getattr(self, 'genie_type', '') == 'tornadus':
            for target in self.get_all_pets():
                if getattr(target, 'current_state', '') == 'tornadus_victim' and getattr(target, 'tornadus_master', None) == self:
                    target.current_state = 'falling'
                    target.surface_angle = 0
                    target.tornadus_master = None

    def trigger_genie_arts(self):
        if not getattr(self, 'get_all_pets', None): return
        
        excluded_states = ['exiting', 'dragged', 'spawning_wild', 'despawning_wild', 'falling_pokeball', 'falling_egg']
        valid_targets = [p for p in self.get_all_pets() if p != self and p.current_state not in excluded_states and not getattr(p, 'is_egg', False)]
        
        if not valid_targets: return
        
        name = self.pet_name.lower().replace("_", "").replace("-", "")
        if name in ["tornadus", "tornadus1"]: self.genie_type = "tornadus"
        elif name in ["thundurus", "thundurus1"]: self.genie_type = "thundurus"
        elif name in ["landorus", "landorus1"]: self.genie_type = "landorus"
        elif name in ["enamorus", "enamorus1"]: self.genie_type = "enamorus"
        else: return

        self.genie_target = random.choice(valid_targets)
        self._setup_genie_vfx_layer()
        self.genie_phase = 0
        self.genie_timer = 75
        self.genie_particles = []
        self.genie_tornadoes = []
        self.genie_angle = 0.0
        self.current_state = 'genie_channeling'
        self.v_x_velocity = 0.0
        self.v_y_velocity = 0.0
        self.schedule_loop(50, self.physics_loop)

    def _setup_genie_vfx_layer(self):
        self.genie_particles = []
        if hasattr(self, 'genie_vfx_win') and self.genie_vfx_win and self.genie_vfx_win.winfo_exists():
            self.genie_vfx_canvas.delete("all")
            return
            
        self.genie_vfx_win = tk.Toplevel(self.window.master)
        self.genie_vfx_win.overrideredirect(True)
        self.genie_vfx_win.attributes('-topmost', True)
        
        TRANS = '#010101'
        self.genie_vfx_win.config(bg=TRANS)
        try: self.genie_vfx_win.wm_attributes('-transparentcolor', TRANS)
        except: pass
        
        self.genie_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.genie_vfx_win.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x00080000 | 0x00000020)
        except: pass

        self.genie_vfx_canvas = tk.Canvas(self.genie_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS, highlightthickness=0)
        self.genie_vfx_canvas.pack()

    def _get_genie_colors(self):
        if self.genie_type == "tornadus": return ["#00FF00", "#7CFC00", "#FFFFFF"]
        elif self.genie_type == "thundurus": return ["#FFFF00", "#00FFFF", "#E0FFFF"]
        elif self.genie_type == "landorus": return ["#FFA500", "#8B4513", "#FF8C00"]
        elif self.genie_type == "enamorus": return ["#FF69B4", "#FF1493", "#FFB6C1"]
        return ["#FFFFFF"]

    def _fsm_genie_channeling(self):
        self.genie_timer -= 1
        
        if not hasattr(self, 'genie_vfx_canvas') or not self.genie_vfx_canvas: 
            self.schedule_loop(50, self.physics_loop)
            return
            
        cx = self.x - self.v_x + self.size_w / 2
        cy = self.y - self.v_y + self.size_h / 2

        self.genie_angle += 0.2

        if self.genie_timer > 30:
            colors = self._get_genie_colors()
            for _ in range(4):
                spawn_angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(150, 250)
                px = cx + math.cos(spawn_angle) * dist
                py = cy + math.sin(spawn_angle) * dist
                
                tangent_angle = spawn_angle + (math.pi / 2.5) 
                speed = random.uniform(8, 15)
                vx = math.cos(tangent_angle) * speed
                vy = math.sin(tangent_angle) * speed
                
                size = random.uniform(1.5, 4.0)
                color = random.choice(colors)
                
                pid = self.genie_vfx_canvas.create_oval(px-size, py-size, px+size, py+size, fill=color, outline="")
                self.genie_particles.append({'id': pid, 'x': px, 'y': py, 'vx': vx, 'vy': vy, 'life': 30, 'size': size, 'color': color, 'type': 'spiral_in'})
        
        alive = []
        for p in self.genie_particles:
            p['life'] -= 1
            if p['type'] == 'spiral_in':
                dx = cx - p['x']
                dy = cy - p['y']
                dist = math.hypot(dx, dy)
                if dist > 5:
                    pull_factor = 0.2
                    p['vx'] += (dx/dist * 15 - p['vx']) * pull_factor
                    p['vy'] += (dy/dist * 15 - p['vy']) * pull_factor
                
                p['x'] += p['vx']
                p['y'] += p['vy']
                
                p['size'] *= 0.95
                s = p['size']
                self.genie_vfx_canvas.coords(p['id'], p['x']-s, p['y']-s, p['x']+s, p['y']+s)
            
            if p['life'] > 0 and p.get('size', 1.0) > 0.5:
                alive.append(p)
            else:
                self.genie_vfx_canvas.delete(p['id'])
        self.genie_particles = alive
        
        if self.genie_timer <= 0:
            self.current_state = 'genie_shoot'
            self.genie_timer = 20
            
            for p in self.genie_particles:
                self.genie_vfx_canvas.delete(p['id'])
            self.genie_particles = []

            colors = self._get_genie_colors()
            for _ in range(25):
                spawn_angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(5, 12)
                vx = math.cos(spawn_angle) * speed
                vy = math.sin(spawn_angle) * speed
                size = random.uniform(2, 5)
                color = random.choice(colors)
                pid = self.genie_vfx_canvas.create_oval(cx-size, cy-size, cx+size, cy+size, fill=color, outline="")
                self.genie_particles.append({'id': pid, 'x': cx, 'y': cy, 'vx': vx, 'vy': vy, 'life': 15, 'size': size, 'color': color, 'type': 'explosion'})
            
            target = getattr(self, 'genie_target', None)
            tx = cx
            ty = cy
            if target and target.window.winfo_exists() and target.current_state != 'exiting':
                tx = target.x - target.v_x + target.size_w / 2
                ty = target.y - target.v_y + target.size_h / 2
                
            dist = math.hypot(tx - cx, ty - cy)
            speed = 5.0 
            vx = (tx - cx) / dist * speed if dist > 0 else 0
            vy = (ty - cy) / dist * speed if dist > 0 else 0
                
            self.genie_sphere = {'x': cx, 'y': cy, 'vx': vx, 'vy': vy, 'life': 80, 'speed': speed}
            
        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def _fsm_genie_shoot(self):
        if not hasattr(self, 'genie_vfx_canvas'): 
            self.schedule_loop(50, self.physics_loop)
            return
        
        sp = getattr(self, 'genie_sphere', None)
        hit = False

        if sp and sp['life'] > 0:
            target = getattr(self, 'genie_target', None)
            
            if target and target.window.winfo_exists() and target.current_state not in ['exiting', 'dragged']:
                tx = target.x - target.v_x + target.size_w / 2
                ty = target.y - target.v_y + target.size_h / 2
                dx = tx - sp['x']
                dy = ty - sp['y']
                dist = math.hypot(dx, dy)
                
                if dist > 0:
                    sp['speed'] = min(sp['speed'] + 3.0, 60.0) 
                    turn_factor = 0.2 
                    
                    target_vx = (dx / dist) * sp['speed']
                    target_vy = (dy / dist) * sp['speed']
                    
                    sp['vx'] += (target_vx - sp['vx']) * turn_factor
                    sp['vy'] += (target_vy - sp['vy']) * turn_factor
            
            sp['x'] += sp['vx']
            sp['y'] += sp['vy']
            sp['life'] -= 1
            
            colors = self._get_genie_colors()
            
            for _ in range(8):
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(0, 15)
                px = sp['x'] + math.cos(angle) * dist
                py = sp['y'] + math.sin(angle) * dist
                size = random.uniform(3, 7)
                color = random.choice(colors)
                pid = self.genie_vfx_canvas.create_oval(px-size, py-size, px+size, py+size, fill=color, outline="")
                self.genie_particles.append({'id': pid, 'x': px, 'y': py, 'vx': sp['vx']*0.5 + random.uniform(-3,3), 'vy': sp['vy']*0.5 + random.uniform(-3,3), 'life': 5, 'size': size, 'type': 'core'})
            
            for _ in range(6):
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(5, 30)
                px = sp['x'] + math.cos(angle) * dist
                py = sp['y'] + math.sin(angle) * dist
                size = random.uniform(2.0, 4.5)
                color = random.choice(colors)
                
                tvx = -sp['vx'] * random.uniform(0.1, 0.5) + random.uniform(-2, 2)
                tvy = -sp['vy'] * random.uniform(0.1, 0.5) + random.uniform(-2, 2)
                pid = self.genie_vfx_canvas.create_oval(px-size, py-size, px+size, py+size, fill=color, outline="")
                self.genie_particles.append({'id': pid, 'x': px, 'y': py, 'vx': tvx, 'vy': tvy, 'life': 15, 'size': size, 'color': color, 'type': 'trail'})
            
            for target_pet in self.get_all_pets():
                if target_pet == self or getattr(target_pet, 'is_egg', False) or target_pet.current_state in ['exiting', 'dragged']: continue
                tx = target_pet.x - target_pet.v_x + target_pet.size_w / 2
                ty = target_pet.y - target_pet.v_y + target_pet.size_h / 2
                if math.hypot(tx - sp['x'], ty - sp['y']) < target_pet.size_w/2 + 30:
                    hit = True
                    break
            
            if hit or sp['life'] <= 0:
                sp['life'] = 0
                self._genie_impact(sp['x'], sp['y'])
                
                if self.genie_type == "tornadus":
                    self.current_state = 'genie_wait_tornado'
                    self.genie_timer = 300 
                else:
                    self.current_state = 'genie_finish'
                    self.genie_timer = 60 
        
        alive = []
        for p in self.genie_particles:
            p['life'] -= 1
            if p['type'] == 'core':
                p['x'] += p['vx']
                p['y'] += p['vy']
                p['size'] *= 0.7 
                s = p['size']
                self.genie_vfx_canvas.coords(p['id'], p['x']-s, p['y']-s, p['x']+s, p['y']+s)
            elif p['type'] == 'trail':
                p['x'] += p['vx']
                p['y'] += p['vy']
                p['size'] *= 0.85 
                s = p['size']
                self.genie_vfx_canvas.coords(p['id'], p['x']-s, p['y']-s, p['x']+s, p['y']+s)
            elif p['type'] == 'explosion':
                p['x'] += p['vx']
                p['y'] += p['vy']
                p['size'] *= 0.9 
                s = p['size']
                self.genie_vfx_canvas.coords(p['id'], p['x']-s, p['y']-s, p['x']+s, p['y']+s)

            if p['life'] > 0 and p.get('size', 1.0) > 0.5:
                alive.append(p)
            else:
                self.genie_vfx_canvas.delete(p['id'])
        self.genie_particles = alive

        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def _fsm_genie_wait_tornado(self):
        self.genie_timer -= 1
        if not hasattr(self, 'genie_vfx_canvas'): 
            self.schedule_loop(50, self.physics_loop)
            return
        
        alive = []
        for p in self.genie_particles:
            p['life'] -= 1
            if p['type'] == 'tornado_part':
                if p['life'] > 0:
                    p['angle'] += 0.4
                    px = p['cx'] + math.cos(p['angle']) * p['dist']
                    py = p['cy'] + math.sin(p['angle']) * p['dist']
                    s = p.get('size', 2)
                    self.genie_vfx_canvas.coords(p['id'], px-s, py-s, px+s, py+s)
                    alive.append(p)
                else:
                    self.genie_vfx_canvas.delete(p['id'])
            elif p['type'] == 'explosion':
                if p['life'] > 0:
                    p['x'] += p['vx']
                    p['y'] += p['vy']
                    p['size'] = p.get('size', 2) * 0.95
                    s = p['size']
                    self.genie_vfx_canvas.coords(p['id'], p['x']-s, p['y']-s, p['x']+s, p['y']+s)
                    alive.append(p)
                else:
                    self.genie_vfx_canvas.delete(p['id'])
            elif p['type'] in ['core', 'trail']:
                if p['life'] > 0:
                    p['x'] += p['vx']
                    p['y'] += p['vy']
                    p['size'] = p.get('size', 2) * 0.8
                    s = p['size']
                    self.genie_vfx_canvas.coords(p['id'], p['x']-s, p['y']-s, p['x']+s, p['y']+s)
                    if s > 0.5: alive.append(p)
                    else: self.genie_vfx_canvas.delete(p['id'])
                else:
                    self.genie_vfx_canvas.delete(p['id'])
            else:
                if p['life'] > 0: alive.append(p)
                else: self.genie_vfx_canvas.delete(p['id'])
                    
        self.genie_particles = alive
        
        t_alive = []
        for t in self.genie_tornadoes:
            t['life'] -= 1
            if t['life'] > 0:
                t['x'] += t['vx']
                t['y'] += t['vy']
                
                if random.random() < 0.1:
                    t['vx'] = random.uniform(-3, 3)
                    t['vy'] = random.uniform(-3, 3)
                    
                colors = self._get_genie_colors()
                for _ in range(2):
                    pid = self.genie_vfx_canvas.create_oval(0, 0, 0, 0, fill=random.choice(colors), outline="")
                    self.genie_particles.append({'id': pid, 'cx': t['x'], 'cy': t['y'], 'angle': random.uniform(0, 2*math.pi), 'dist': random.uniform(20, 80), 'size': random.randint(3, 6), 'life': 20, 'type': 'tornado_part'})
                
                for target in self.get_all_pets():
                    if target == self or getattr(target, 'is_egg', False) or target.current_state in ['exiting', 'dragged']: continue
                    
                    tx = target.x - target.v_x + target.size_w / 2
                    ty = target.y - target.v_y + target.size_h / 2
                    dist = math.hypot(tx - t['x'], ty - t['y'])
                    
                    if dist < 200:
                        self._clear_victim_state(target)
                        target.current_state = 'tornadus_victim'
                        target.tornadus_master = self
                        
                        if not hasattr(target, 'tornadus_angle'):
                            target.tornadus_angle = random.uniform(0, 2*math.pi)
                            target.tornadus_dist = dist
                            
                        target.tornadus_angle += 0.2
                        target.tornadus_dist = max(10, target.tornadus_dist * 0.95)
                        
                        new_tx = t['x'] + math.cos(target.tornadus_angle) * target.tornadus_dist
                        new_ty = t['y'] + math.sin(target.tornadus_angle) * target.tornadus_dist
                        
                        target.x = new_tx + target.v_x - target.size_w / 2
                        target.y = new_ty + target.v_y - target.size_h / 2
                        
                        target.surface_angle = (getattr(target, 'surface_angle', 0) + 25) % 360

                t_alive.append(t)
                
        self.genie_tornadoes = t_alive

        if self.genie_timer <= 0:
            self.cancel_genie_arts()
            self.schedule_loop(50, self.physics_loop)
            return
            
        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def _fsm_genie_finish(self):
        self.genie_timer -= 1
        if not hasattr(self, 'genie_vfx_canvas'): 
            self.schedule_loop(50, self.physics_loop)
            return
        
        alive = []
        for p in self.genie_particles:
            p['life'] -= 1
            if p['type'] == 'explosion':
                if p['life'] > 0:
                    p['x'] += p['vx']
                    p['y'] += p['vy']
                    p['size'] = p.get('size', 2) * 0.92
                    s = p['size']
                    self.genie_vfx_canvas.coords(p['id'], p['x']-s, p['y']-s, p['x']+s, p['y']+s)
                    if s > 0.5: alive.append(p)
                    else: self.genie_vfx_canvas.delete(p['id'])
                else:
                    self.genie_vfx_canvas.delete(p['id'])
            elif p['type'] == 'lightning':
                if p['life'] > 0:
                    new_flat = []
                    for i, (bx, by) in enumerate(p['base_pts']):
                        if i == 0: 
                            new_flat.extend([bx, by])
                        else:
                            new_flat.extend([bx + random.uniform(-20, 20), by + random.uniform(-20, 20)])
                    self.genie_vfx_canvas.coords(p['id'], *new_flat)
                    w = max(1, p.get('w', 2) - 1)
                    p['w'] = w
                    self.genie_vfx_canvas.itemconfig(p['id'], width=w, fill=random.choice(["#FFFFFF", p['color']]))
                    if w > 1: alive.append(p)
                    else: self.genie_vfx_canvas.delete(p['id'])
                else:
                    self.genie_vfx_canvas.delete(p['id'])
            elif p['type'] in ['core', 'trail']:
                if p['life'] > 0:
                    p['x'] += p['vx']
                    p['y'] += p['vy']
                    p['size'] = p.get('size', 2) * 0.8
                    s = p['size']
                    self.genie_vfx_canvas.coords(p['id'], p['x']-s, p['y']-s, p['x']+s, p['y']+s)
                    if s > 0.5: alive.append(p)
                    else: self.genie_vfx_canvas.delete(p['id'])
                else:
                    self.genie_vfx_canvas.delete(p['id'])
            else:
                if p['life'] > 0:
                    alive.append(p)
                else:
                    self.genie_vfx_canvas.delete(p['id'])
                    
        self.genie_particles = alive
        
        if self.genie_timer <= 0 and len(self.genie_particles) == 0:
            self.cancel_genie_arts()
            self.schedule_loop(50, self.physics_loop)
            return
            
        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def _genie_impact(self, ix, iy):
        colors = self._get_genie_colors()
        
        for _ in range(50):
            vx = random.uniform(-15, 15)
            vy = random.uniform(-15, 15)
            size = random.uniform(4, 9)
            pid = self.genie_vfx_canvas.create_oval(ix-size, iy-size, ix+size, iy+size, fill=random.choice(colors), outline="")
            self.genie_particles.append({'id': pid, 'x': ix, 'y': iy, 'vx': vx, 'vy': vy, 'size': size, 'life': 40, 'type': 'explosion'})
        
        if self.genie_type == "tornadus":
            self.genie_tornadoes.append({'x': ix, 'y': iy, 'vx': random.uniform(-2, 2), 'vy': random.uniform(-2, 2), 'life': 300})
            
        elif self.genie_type == "thundurus":
            for _ in range(15):
                angle = random.uniform(0, 2 * math.pi)
                dist = 220
                pts = [(ix, iy)]
                curr_dist = 0
                curr_x, curr_y = ix, iy
                
                while curr_dist < dist:
                    step = random.uniform(30, 80)
                    curr_dist += step
                    curr_x += math.cos(angle + random.uniform(-1.0, 1.0)) * step
                    curr_y += math.sin(angle + random.uniform(-1.0, 1.0)) * step
                    pts.append((curr_x, curr_y))
                    
                w = random.choice([3, 5, 8])
                color = random.choice(colors)
                
                flat_pts = [coord for pt in pts for coord in pt]
                pid = self.genie_vfx_canvas.create_line(*flat_pts, fill=color, width=w)
                self.genie_particles.append({
                    'id': pid, 'base_pts': pts, 'color': color, 'w': w, 
                    'life': 8, 'type': 'lightning' 
                })
                
            for target in self.get_all_pets():
                if target == self or getattr(target, 'is_egg', False) or target.current_state in ['exiting', 'dragged']: continue
                tx = target.x - target.v_x + target.size_w / 2
                ty = target.y - target.v_y + target.size_h / 2
                if math.hypot(tx - ix, ty - iy) <= 220:
                    self._clear_victim_state(target)
                    if hasattr(target, 'zekrom_para_vfx_loop'):
                        target.current_state = 'zekrom_paralyzed'
                        target.zekrom_para_timer = 400
                        target.zekrom_para_vfx_loop()
                        
        elif self.genie_type == "landorus":
            for target in self.get_all_pets():
                if target == self or getattr(target, 'is_egg', False) or target.current_state in ['exiting', 'dragged']: continue
                tx = target.x - target.v_x + target.size_w / 2
                ty = target.y - target.v_y + target.size_h / 2
                if math.hypot(tx - ix, ty - iy) <= 200:
                    self._clear_victim_state(target)
                    target.current_state = 'landorus_thrown'
                    target.v_x_velocity = random.uniform(15, 30) * (1 if tx > ix else -1)
                    target.v_y_velocity = random.uniform(-30, -20)
                    target.surface_angle = 180

        elif self.genie_type == "enamorus":
            for target in self.get_all_pets():
                if target == self or getattr(target, 'is_egg', False) or target.current_state in ['exiting', 'dragged']: continue
                tx = target.x - target.v_x + target.size_w / 2
                ty = target.y - target.v_y + target.size_h / 2
                if math.hypot(tx - ix, ty - iy) <= 200:
                    self._clear_victim_state(target)
                    target.current_state = 'enamorus_joy'
                    target.enamorus_joy_timer = 200
                    target.v_y_velocity = -20.0
                    if hasattr(target, 'show_heart_vfx'):
                        target.show_heart_vfx()

    def _fsm_tornadus_victim(self):
        if not getattr(self, 'tornadus_master', None) or self.tornadus_master.current_state != 'genie_wait_tornado':
            self.current_state = 'falling'
            self.surface_angle = 0
            
        self.update_position()
        self.schedule_loop(50, self.physics_loop)
        
    def _fsm_landorus_thrown(self):
        self.v_y_velocity += 2.0
        self.y += self.v_y_velocity
        self.x += getattr(self, 'v_x_velocity', 0.0)
        
        if getattr(self, 'can_screen_wrap', False):
            if self.x <= self.v_x - self.size_w: self.x = self.v_x + self.v_width
            elif self.x >= self.v_x + self.v_width: self.x = self.v_x - self.size_w
        else:
            hit_wall = False
            if self.x <= self.v_x:
                self.x = self.v_x
                self.v_x_velocity = 0
                hit_wall = True
                wall_surface = 'wall_l'
            elif self.x >= (self.v_x + self.v_width) - self.size_w:
                self.x = (self.v_x + self.v_width) - self.size_w
                self.v_x_velocity = 0
                hit_wall = True
                wall_surface = 'wall_r'
                
            if hit_wall:
                self.v_y_velocity = 0
                if hasattr(self, '_embed_victim'):
                    self._embed_victim(wall_surface)
                else:
                    self.current_state = 'regirock_embedded'
                    self.surface_angle = 90 if wall_surface == 'wall_l' else 270
                    self.update_position()
                    self.schedule_loop(50, self.physics_loop)
                return
                
        current_env, _ = self.get_window_environment()
        physical_floor = current_env['y'] if self.y <= current_env['y'] + 15 else self.default_floor_y
        
        if self.v_y_velocity > 0 and self.y >= physical_floor:
            self.y = physical_floor
            self.floor_y = physical_floor
            self.v_x_velocity = 0
            self.v_y_velocity = 0
            
            if hasattr(self, '_embed_victim'):
                self._embed_victim()
            else:
                self.current_state = 'regirock_embedded'
                self.surface_angle = 180
                self.y = self.default_floor_y + (self.size_h // 2)
                self.update_position()
                self.schedule_loop(50, self.physics_loop)
            return
                
        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def _fsm_enamorus_joy(self):
        self.enamorus_joy_timer = getattr(self, 'enamorus_joy_timer', 0) - 1
        
        self.v_y_velocity += 1.5
        self.y += self.v_y_velocity
        self.x += getattr(self, 'v_x_velocity', 0.0)
        
        current_env, _ = self.get_window_environment()
        physical_floor = current_env['y'] if self.y <= current_env['y'] + 15 else self.default_floor_y
        
        if self.v_y_velocity > 0 and self.y >= physical_floor:
            self.y = physical_floor
            self.v_y_velocity = 0
            
            if self.enamorus_joy_timer > 0:
                self.v_y_velocity = -random.uniform(15.0, 25.0)
                self.v_x_velocity = random.uniform(-8.0, 8.0)
                if hasattr(self, 'show_heart_vfx'):
                    self.show_heart_vfx()
            else:
                self.current_state = 'idle'
                self.v_x_velocity = 0
                
        self.update_position()
        self.schedule_loop(50, self.physics_loop)
