import random
import math
import tkinter as tk
import time

class HoopaMechanics:
    def start_hoopa_mechanic(self):
        if getattr(self, 'current_state', '') in ['dragged', 'exiting']: return
        if getattr(self, 'hoopa_cooldown', 0) > 0: return
        if hasattr(self, 'is_global_mechanic_active') and self.is_global_mechanic_active(): return

        name = self.pet_name.lower().replace("_", "").replace("-", "")
        if name not in ["hoopa", "hoopa1"]: return

        self.current_state = 'hoopa_channeling'
        self.hoopa_timer = 90 # 3 seconds
        self.hoopa_cooldown = 120000 # 1 hour at 30ms
        self.hoopa_form = name
        
        self.hoopa_ring_targets = []
        num_pairs = 1 if name == "hoopa" else 2
        
        # Generate ring positions
        for _ in range(num_pairs):
            while True:
                tx1 = self.v_x + random.randint(100, self.v_width - 100)
                ty1 = self.v_y + random.randint(100, self.v_height - 200)
                tx2 = self.v_x + random.randint(100, self.v_width - 100)
                ty2 = self.v_y + random.randint(100, self.v_height - 200)
                dist = math.sqrt((tx1 - tx2)**2 + (ty1 - ty2)**2)
                if dist >= self.v_width / 3.0:
                    self.hoopa_ring_targets.append({'x': tx1, 'y': ty1})
                    self.hoopa_ring_targets.append({'x': tx2, 'y': ty2})
                    break
            
        self.hoopa_target_index = 0
        self.hoopa_rings = []
        self.hoopa_float_angle = 0.0
        
        # Init VFX window
        self._init_hoopa_vfx()
        self.schedule_loop(30, self.physics_loop)

    def _init_hoopa_vfx(self):
        if hasattr(self, 'hoopa_vfx_win') and self.hoopa_vfx_win and self.hoopa_vfx_win.winfo_exists():
            return
            
        self.hoopa_vfx_win = tk.Toplevel(self.window.master)
        self.hoopa_vfx_win.overrideredirect(True)
        self.hoopa_vfx_win.attributes('-topmost', True)
        TRANS_COLOR = '#010101'
        self.hoopa_vfx_win.config(bg=TRANS_COLOR)
        try: self.hoopa_vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass
        self.hoopa_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        
        self.hoopa_canvas = tk.Canvas(self.hoopa_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
        self.hoopa_canvas.pack(fill="both", expand=True)
        self.hoopa_particles = []

    def cancel_hoopa_arts(self):
        if hasattr(self, 'hoopa_vfx_win') and self.hoopa_vfx_win and self.hoopa_vfx_win.winfo_exists():
            self.hoopa_vfx_win.destroy()
            self.hoopa_vfx_win = None
            
        for attr in ['hoopa_timer', 'hoopa_ring_targets', 'hoopa_target_index', 'hoopa_rings', 'hoopa_float_angle', 'hoopa_canvas', 'hoopa_particles']:
            if hasattr(self, attr): delattr(self, attr)

        if self.current_state not in ['dragged', 'exiting']:
            self.floor_y = getattr(self, 'y', 0)
            self.current_state = 'ascending'
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0

    def _fsm_hoopa_channeling(self):
        self.hoopa_timer -= 1
        
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        
        # Absorb golden particles
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(80, 150)
        px = cx + math.cos(angle) * dist
        py = cy + math.sin(angle) * dist
        
        vx = (cx - px) * 0.1
        vy = (cy - py) * 0.1
        self.spawn_hoopa_particle(px, py, vx, vy, 10, "#FFD700")
        
        self._update_hoopa_vfx()
        
        if self.hoopa_timer <= 0:
            self.current_state = 'hoopa_flying'
            
        self.schedule_loop(30, self.physics_loop)

    def _fsm_hoopa_flying(self):
        if self.hoopa_target_index >= len(self.hoopa_ring_targets):
            if self.hoopa_form == "hoopa1":
                self.current_state = 'hoopa_grab_target'
                self._find_hoopa_grab_target()
            else:
                self.floor_y = self.y
                self.current_state = 'ascending'
                self.v_x_velocity = 0.0
                self.v_y_velocity = 0.0
                # Start global ring loop
                self.hoopa_ring_lifetime = 600 # 20 seconds
                self._hoopa_global_ring_loop()
            self.schedule_loop(30, self.physics_loop)
            return
            
        target = self.hoopa_ring_targets[self.hoopa_target_index]
        tx = target['x']
        ty = target['y']
        
        my_cx = self.x + self.size_w/2
        my_cy = self.y + self.size_h/2
        
        dx = tx - my_cx
        dy = ty - my_cy
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist < 40:
            # Reached point, create ring
            self._create_hoopa_ring(tx, ty)
            self.hoopa_target_index += 1
            # Add particle explosion
            for _ in range(30):
                angle = random.uniform(0, 2*math.pi)
                speed = random.uniform(2, 8)
                self.spawn_hoopa_particle(tx - self.v_x, ty - self.v_y, math.cos(angle)*speed, math.sin(angle)*speed, 20, "#FFD700")
        else:
            # Floaty graceful movement
            target_vx = (dx / dist) * 18.0
            target_vy = (dy / dist) * 18.0
            
            self.v_x_velocity += (target_vx - self.v_x_velocity) * 0.08
            self.v_y_velocity += (target_vy - self.v_y_velocity) * 0.08
            
            self.hoopa_float_angle += 0.15
            self.x += self.v_x_velocity + math.cos(self.hoopa_float_angle) * 4
            self.y += self.v_y_velocity + math.sin(self.hoopa_float_angle * 0.8) * 4
            self.is_facing_right = self.v_x_velocity > 0
            
        self.update_position()
        self._update_hoopa_vfx()
        self.schedule_loop(30, self.physics_loop)

    def _create_hoopa_ring(self, x, y):
        # Pair index: 0 goes to 1, 1 to 0, 2 to 3, 3 to 2
        idx = len(self.hoopa_rings)
        pair_idx = idx + 1 if idx % 2 == 0 else idx - 1
        
        self.hoopa_rings.append({
            'x': x - self.v_x, 
            'y': y - self.v_y, 
            'pair_idx': pair_idx,
            'radius': 0,
            'target_radius': 60,
            'growth': 0
        })

    def _find_hoopa_grab_target(self):
        self.hoopa_grab_target = None
        if hasattr(self, 'get_all_pets'):
            valid_targets = [p for p in self.get_all_pets() if p != self and p.current_state not in ['exiting', 'dragged', 'thrown'] and not getattr(p, 'is_egg', False)]
            if valid_targets:
                self.hoopa_grab_target = random.choice(valid_targets)
                self.hoopa_grab_target.current_state = 'tk_controlled'

    def _fsm_hoopa_grab_target(self):
        if not hasattr(self, 'hoopa_grab_target') or not self.hoopa_grab_target:
            self.current_state = 'falling'
            self.hoopa_ring_lifetime = 600
            self._hoopa_global_ring_loop()
            self.schedule_loop(30, self.physics_loop)
            return
            
        tx = self.hoopa_grab_target.x + getattr(self.hoopa_grab_target, 'size_w', 64)/2
        ty = self.hoopa_grab_target.y + getattr(self.hoopa_grab_target, 'size_h', 64)/2
        
        my_cx = self.x + self.size_w/2
        my_cy = self.y + self.size_h/2
        
        dx = tx - my_cx
        dy = ty - my_cy
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist < 60:
            # Grabbed
            self.current_state = 'hoopa_throw'
            self.hoopa_timer = 15 # Delay before throw
            # Grab particles
            for _ in range(20):
                angle = random.uniform(0, 2*math.pi)
                speed = random.uniform(2, 6)
                self.spawn_hoopa_particle(my_cx - self.v_x, my_cy - self.v_y, math.cos(angle)*speed, math.sin(angle)*speed, 15, "#800080")
        else:
            target_vx = (dx / dist) * 22.0
            target_vy = (dy / dist) * 22.0
            self.v_x_velocity += (target_vx - self.v_x_velocity) * 0.15
            self.v_y_velocity += (target_vy - self.v_y_velocity) * 0.15
            self.x += self.v_x_velocity
            self.y += self.v_y_velocity
            self.is_facing_right = self.v_x_velocity > 0
            
        self.update_position()
        self._update_hoopa_vfx()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_hoopa_throw(self):
        target = getattr(self, 'hoopa_grab_target', None)
        if not target:
            self.current_state = 'falling'
            self.hoopa_ring_lifetime = 600
            self._hoopa_global_ring_loop()
            self.schedule_loop(30, self.physics_loop)
            return
            
        self.hoopa_timer -= 1
        
        my_cx = self.x + self.size_w/2
        my_cy = self.y + self.size_h/2
        target.x = my_cx - getattr(target, 'size_w', 64)/2
        target.y = my_cy - getattr(target, 'size_h', 64)/2
        target.update_position()
        
        if self.hoopa_timer <= 0:
            # Throw towards a random ring
            ring = random.choice(self.hoopa_rings)
            dx = (ring['x'] + self.v_x) - my_cx
            dy = (ring['y'] + self.v_y) - my_cy
            dist = math.sqrt(dx**2 + dy**2)
            
            target.current_state = 'thrown'
            target.hoopa_thrown = True
            if dist > 0:
                target.v_x_velocity = (dx / dist) * 95.0
                target.v_y_velocity = (dy / dist) * 95.0
            
            # Throw particles
            for _ in range(30):
                angle = random.uniform(0, 2*math.pi)
                speed = random.uniform(4, 12)
                self.spawn_hoopa_particle(my_cx - self.v_x, my_cy - self.v_y, math.cos(angle)*speed, math.sin(angle)*speed, 20, "#FF1493")
                
            self.hoopa_grab_target = None
            self.floor_y = self.y
            self.current_state = 'ascending'
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            self.hoopa_ring_lifetime = 600
            self._hoopa_global_ring_loop()
            
        self.update_position()
        self._update_hoopa_vfx()
        self.schedule_loop(30, self.physics_loop)

    def _hoopa_global_ring_loop(self):
        if not hasattr(self, 'hoopa_vfx_win') or not self.hoopa_vfx_win or not self.hoopa_vfx_win.winfo_exists():
            return
            
        self.hoopa_ring_lifetime -= 1
        
        if self.hoopa_ring_lifetime <= 0:
            if not getattr(self, 'hoopa_rings_dying', False):
                self.hoopa_rings_dying = True
                for r in self.hoopa_rings:
                    r['target_radius'] = 0
            
            all_gone = True
            for r in self.hoopa_rings:
                if r['radius'] > 2:
                    all_gone = False
                    break
            
            if all_gone:
                if not getattr(self, 'hoopa_final_popped', False):
                    self.hoopa_final_popped = True
                    self.hoopa_final_timer = 20
                    for r in self.hoopa_rings:
                        for _ in range(20):
                            angle = random.uniform(0, 2*math.pi)
                            speed = random.uniform(2, 6)
                            self.spawn_hoopa_particle(r['x'], r['y'], math.cos(angle)*speed, math.sin(angle)*speed, 15, "#FFD700")
                
                self.hoopa_final_timer -= 1
                if self.hoopa_final_timer <= 0:
                    self.cancel_hoopa_arts()
                    return
        else:
            # Check ring collisions only while rings are active
            if hasattr(self, 'get_all_pets'):
                for p in self.get_all_pets():
                    if p.current_state in ['exiting', 'dragged']: continue
                    
                    if getattr(p, 'hoopa_ring_cd', 0) > 0:
                        p.hoopa_ring_cd -= 1
                        continue
                        
                    p_cx = p.x - self.v_x + getattr(p, 'size_w', 64)/2
                    p_cy = p.y - self.v_y + getattr(p, 'size_h', 64)/2
                    
                    for idx, r in enumerate(self.hoopa_rings):
                        if r['radius'] < 30: continue
                        dist = math.sqrt((p_cx - r['x'])**2 + (p_cy - r['y'])**2)
                        
                        # Hitbox exactly matches the outer border of the ring
                        if dist < r['radius']:
                            pair = self.hoopa_rings[r['pair_idx']]
                            if pair['radius'] < 30: continue
                            
                            p.x = pair['x'] + self.v_x - getattr(p, 'size_w', 64)/2
                            p.y = pair['y'] + self.v_y - getattr(p, 'size_h', 64)/2
                            p.hoopa_ring_cd = 30
                            p.hoopa_thrown = False
                            p.update_position()
                            
                            for ring_idx in [idx, r['pair_idx']]:
                                ring = self.hoopa_rings[ring_idx]
                                for _ in range(15):
                                    angle = random.uniform(0, 2*math.pi)
                                    speed = random.uniform(2, 8)
                                    self.spawn_hoopa_particle(ring['x'], ring['y'], math.cos(angle)*speed, math.sin(angle)*speed, 15, "#FFD700")
                            break

        self._update_hoopa_vfx()
        self.window.after(30, self._hoopa_global_ring_loop)

    def spawn_hoopa_particle(self, cx, cy, vx, vy, life, color):
        if not hasattr(self, 'hoopa_canvas'): return
        size = random.choice([3, 4, 6])
        pid = self.hoopa_canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline="", tags="hoopa_vfx")
        self.hoopa_particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': life, 'max_life': life, 'max_size': size})

    def _update_hoopa_vfx(self):
        if not hasattr(self, 'hoopa_canvas') or not self.hoopa_canvas.winfo_exists(): return
        self.hoopa_canvas.delete("ring")
        
        for r in self.hoopa_rings:
            # 1 second to grow -> approx 33 ticks
            diff = r['target_radius'] - r['radius']
            r['radius'] += diff * 0.15
            
            if r['radius'] > 2:
                G = 4
                steps = max(24, int(r['radius'] * 2))
                
                def get_pixelated_polygon(cx, cy, radius):
                    pts = []
                    last_x, last_y = None, None
                    for i in range(steps + 1):
                        a = (i / steps) * 2 * math.pi
                        x = round((cx + math.cos(a) * radius) / G) * G
                        y = round((cy + math.sin(a) * radius) / G) * G
                        if last_x is not None and (x != last_x or y != last_y):
                            if x != last_x and y != last_y:
                                pts.extend([last_x, y])
                            pts.extend([x, y])
                        elif last_x is None:
                            pts.extend([x, y])
                        last_x, last_y = x, y
                    return pts

                outer_pts = get_pixelated_polygon(r['x'], r['y'], r['radius'])
                inner_pts = get_pixelated_polygon(r['x'], r['y'], r['radius'] * 0.8)
                
                w = max(2, int(r['radius']*0.15))
                self.hoopa_canvas.create_polygon(outer_pts, outline="#FFD700", fill="", width=w, tags="ring")
                self.hoopa_canvas.create_polygon(inner_pts, outline="#800080", fill="", width=2, tags="ring")

        new_parts = []
        for p in self.hoopa_particles:
            p['life'] -= 1
            if p['life'] > 0:
                self.hoopa_canvas.move(p['id'], p['vx'], p['vy'])
                ratio = p['life'] / p['max_life']
                new_size = max(1, int(p['max_size'] * ratio))
                coords = self.hoopa_canvas.coords(p['id'])
                if coords:
                    cx = (coords[0] + coords[2])/2
                    cy = (coords[1] + coords[3])/2
                    self.hoopa_canvas.coords(p['id'], cx-new_size, cy-new_size, cx+new_size, cy+new_size)
                new_parts.append(p)
            else:
                self.hoopa_canvas.delete(p['id'])
        self.hoopa_particles = new_parts
