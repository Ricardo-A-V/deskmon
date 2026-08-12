import random
import math
import tkinter as tk

class HeatranMechanics:
    def cancel_heatran_arts(self):
        if hasattr(self, 'hea_vfx_win') and self.hea_vfx_win and self.hea_vfx_win.winfo_exists():
            self.hea_vfx_win.destroy()
            self.hea_vfx_win = None
            
        for attr in ['hea_phase', 'hea_timer', 'hea_rocks', 'hea_rocks_dropped', 'hea_total_rocks', 'hea_rock_timer']:
            if hasattr(self, attr): delattr(self, attr)

        if self.current_state not in ['dragged', 'exiting']:
            self.climbing_surface = 'floor'
            self.surface_angle = 0
            self.current_state = 'falling'

    def _fsm_heatran_jump_down(self):
        vel_y = getattr(self, 'v_y_velocity', 0)
        self.y += vel_y
        self.v_y_velocity = vel_y + 1.2 # Gravity

        if self.y >= self.default_floor_y:
            self.y = self.default_floor_y
            self.v_y_velocity = 0
            if hasattr(self, 'trigger_landing_shake'):
                self.trigger_landing_shake()
            self.trigger_heatran_dirt_particles(self.x + self.size_w/2, self.y + self.size_h, 20)
            self.current_state = 'heatran_channeling'
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_heatran_channeling(self):
        if not hasattr(self, 'hea_phase'):
            self.hea_phase = 0
            self.hea_timer = 166 # 5 seconds
            
        self.hea_timer -= 1
        
        if self.hea_timer % 55 == 0:
            self.trigger_heatran_explosion(self.x + self.size_w/2, self.y + self.size_h/2)
            
        if self.hea_timer <= 0:
            self.current_state = 'heatran_positioning'
            self.hea_phase = 'find_edge'
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)
        
    def _fsm_heatran_positioning(self):
        speed = self.speed * 2
            
        if self.hea_phase == 'find_edge':
            if not hasattr(self, 'hea_target_edge'):
                self.hea_target_edge = random.choice(['left', 'right'])
                
            if self.hea_target_edge == 'left':
                self.x -= speed
                self.is_facing_right = False
                if self.x <= self.v_x:
                    self.x = self.v_x
                    self.hea_phase = 'climb'
                    self.climbing_surface = 'wall_l'
                    self.surface_angle = 270
            else:
                self.x += speed
                self.is_facing_right = True
                if self.x >= self.v_x + self.v_width - self.size_w:
                    self.x = self.v_x + self.v_width - self.size_w
                    self.hea_phase = 'climb'
                    self.climbing_surface = 'wall_r'
                    self.surface_angle = 90
                    
        elif self.hea_phase == 'climb':
            self.y -= speed
            if self.y <= self.v_y:
                self.y = self.v_y
                self.hea_phase = 'center'
                self.climbing_surface = 'ceiling'
                self.surface_angle = 180
                
        elif self.hea_phase == 'center':
            target_x = self.v_x + self.v_width/2 - self.size_w/2
            if self.x < target_x:
                self.x += speed
                self.is_facing_right = False
                if self.x >= target_x:
                    self.x = target_x
                    self.hea_phase = 'done'
            else:
                self.x -= speed
                self.is_facing_right = True
                if self.x <= target_x:
                    self.x = target_x
                    self.hea_phase = 'done'
                    
        if self.hea_phase == 'done':
            self.current_state = 'heatran_storm'
            self.hea_timer = 33 # 1 sec wait
            self.hea_storm_center_x = self.x
            self.hea_storm_center_y = self.y
            self.hea_rocks_dropped = 0
            self.hea_total_rocks = random.randint(8, 12)
            self.hea_rock_timer = random.randint(33, 100)
            self.hea_rocks = []
            
            self.hea_vfx_win = tk.Toplevel(self.window.master)
            self.hea_vfx_win.title("VFX_HeatranStorm_Ignore")
            self.hea_vfx_win.overrideredirect(True)
            self.hea_vfx_win.attributes('-topmost', True)
            TRANS_COLOR = '#010101'
            self.hea_vfx_win.config(bg=TRANS_COLOR)
            try: self.hea_vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
            except: pass
            
            self.hea_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
            self.hea_canvas = tk.Canvas(self.hea_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
            self.hea_canvas.pack()
            self.heatran_storm_vfx_loop()
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)
        
    def _fsm_heatran_storm(self):
        if self.hea_timer > 0:
            self.hea_timer -= 1
        else:
            # Vibrate constrained to center
            self.x = self.hea_storm_center_x + random.randint(-3, 3)
            self.y = self.hea_storm_center_y + random.randint(-2, 2)
            
            self.hea_rock_timer -= 1
            if self.hea_rock_timer <= 0 and self.hea_rocks_dropped < self.hea_total_rocks:
                self.hea_rocks_dropped += 1
                self.hea_rock_timer = random.randint(33, 100)
                
                spawn_x = random.randint(self.v_x + 10, self.v_x + self.v_width - 10)
                spawn_y = self.v_y - 20
                
                rock = {
                    'id': self._draw_pixel_circle_bbox(self.hea_canvas, spawn_x-24-self.v_x, spawn_y-24-self.v_y, spawn_x+24-self.v_x, spawn_y+24-self.v_y, fill="#795548", outline="#3E2723", width=2, tags="rock"),
                    'x': spawn_x - self.v_x, 'y': spawn_y - self.v_y,
                    'vx': random.uniform(-1, 1),
                    'vy': random.uniform(5, 10),
                    'trail': []
                }
                self.hea_rocks.append(rock)
                
            if self.hea_rocks_dropped >= self.hea_total_rocks and len(self.hea_rocks) == 0:
                if hasattr(self, 'hea_vfx_win') and self.hea_vfx_win:
                    self.hea_vfx_win.destroy()
                    self.hea_vfx_win = None
                self.current_state = 'heatran_falling'
                self.climbing_surface = 'floor'
                
        self.update_position()
        self.schedule_loop(30, self.physics_loop)
        
    def heatran_storm_vfx_loop(self):
        if self.current_state != 'heatran_storm': return
        if not hasattr(self, 'hea_vfx_win') or not self.hea_vfx_win or not self.hea_vfx_win.winfo_exists(): return
        
        alive_rocks = []
        self.hea_canvas.delete("trail")
        
        for rock in self.hea_rocks:
            self.hea_canvas.move(rock['id'], rock['vx'], rock['vy'])
            rock['x'] += rock['vx']
            rock['y'] += rock['vy']
            rock['vy'] += 0.3 # gravity
            
            rock['trail'].append({'x': rock['x'] + random.randint(-24, 24), 'y': rock['y'] + random.randint(-24, 24) - 10, 'life': 12})
            
            alive_trail = []
            for t in rock['trail']:
                if t['life'] > 0:
                    t['y'] -= 1 
                    size = t['life'] / 2
                    color = random.choice(["#E67E22", "#F1C40F", "#C0392B"])
                    self.hea_canvas.create_rectangle(t['x']-size, t['y']-size, t['x']+size, t['y']+size, fill=color, outline=color, tags="trail")
                    t['life'] -= 1
                    alive_trail.append(t)
            rock['trail'] = alive_trail
            
            global_rock_x = self.v_x + rock['x']
            global_rock_y = self.v_y + rock['y']
            
            hit = False
            if getattr(self, 'get_all_pets', None):
                for p in self.get_all_pets():
                    if p != self and p.current_state not in ['exiting', 'dragged', 'reshiram_burn'] and not getattr(p, 'is_egg', False):
                        if (global_rock_x > p.x and global_rock_x < p.x + p.size_w and
                            global_rock_y > p.y and global_rock_y < p.y + p.size_h):
                            if hasattr(self, 'apply_burn'):
                                self.apply_burn(p)
                            hit = True
                            
            if rock['y'] < self.v_height + 50 and not hit:
                alive_rocks.append(rock)
            else:
                self.hea_canvas.delete(rock['id'])
                
        self.hea_rocks = alive_rocks
        self.window.after(30, self.heatran_storm_vfx_loop)
        
    def _fsm_heatran_falling(self):
        self.y += 15.0
        self.surface_angle = 0
        current_env, _ = self.get_window_environment()
        floor = current_env['y'] if self.y <= current_env['y'] + 15 else self.default_floor_y
        
        if self.y >= floor:
            self.y = floor
            if hasattr(self, 'trigger_landing_shake'):
                self.trigger_landing_shake()
            self.trigger_heatran_dirt_particles(self.x + self.size_w/2, self.y + self.size_h, 30)
            self.current_state = 'idle'
            self.heatran_cooldown = 72000 
            for attr in ['hea_phase', 'hea_timer', 'hea_rocks', 'hea_rocks_dropped', 'hea_total_rocks', 'hea_rock_timer']:
                if hasattr(self, attr): delattr(self, attr)
                
        self.update_position()
        self.schedule_loop(30, self.physics_loop)
        
    def trigger_heatran_explosion(self, cx, cy):
        exp_win = tk.Toplevel(self.window.master)
        exp_win.title("VFX_HeatranExp_Ignore")
        exp_win.overrideredirect(True)
        exp_win.attributes('-topmost', True)
        TRANS_COLOR = '#010101'
        exp_win.config(bg=TRANS_COLOR)
        try: exp_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass
        
        size = 200
        exp_win.geometry(f"{size}x{size}+{int(cx-size/2)}+{int(cy-size/2)}")
        c = tk.Canvas(exp_win, width=size, height=size, bg=TRANS_COLOR, highlightthickness=0)
        c.pack()
        
        state = {'radius': 10.0, 'alpha': 20}
        
        def anim():
            if not exp_win.winfo_exists(): return
            c.delete("exp")
            state['radius'] += 10
            state['alpha'] -= 1
            
            if state['alpha'] <= 0 or state['radius'] >= size/2:
                exp_win.destroy()
                return
                
            r = state['radius']
            self._draw_pixel_circle_bbox(c, size/2-r, size/2-r, size/2+r, size/2+r, outline="#E74C3C", width=state['alpha'], tags="exp")
            self._draw_pixel_circle_bbox(c, size/2-r*0.8, size/2-r*0.8, size/2+r*0.8, size/2+r*0.8, outline="#E67E22", width=max(1, state['alpha']-5), tags="exp")
            
            exp_win.after(30, anim)
            
        anim()
        
    def trigger_heatran_dirt_particles(self, cx, cy, count):
        d_win = tk.Toplevel(self.window.master)
        d_win.title("VFX_HeatranDirt_Ignore")
        d_win.overrideredirect(True)
        d_win.attributes('-topmost', True)
        TRANS_COLOR = '#010101'
        d_win.config(bg=TRANS_COLOR)
        try: d_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass
        
        size = 300
        d_win.geometry(f"{size}x{size}+{int(cx-size/2)}+{int(cy-size/2)}")
        c = tk.Canvas(d_win, width=size, height=size, bg=TRANS_COLOR, highlightthickness=0)
        c.pack()
        
        particles = []
        for _ in range(count):
            particles.append({
                'x': size/2, 'y': size/2,
                'vx': random.uniform(-8, 8),
                'vy': random.uniform(-10, -2),
                'life': random.randint(15, 30),
                'color': random.choice(["#795548", "#5D4037", "#8D6E63", "#3E2723"])
            })
            
        def anim():
            if not d_win.winfo_exists(): return
            c.delete("dirt")
            alive = []
            for p in particles:
                if p['life'] > 0:
                    p['x'] += p['vx']
                    p['y'] += p['vy']
                    p['vy'] += 0.8 
                    psize = random.randint(3, 6)
                    c.create_rectangle(p['x']-psize, p['y']-psize, p['x']+psize, p['y']+psize, fill=p['color'], outline=p['color'], tags="dirt")
                    p['life'] -= 1
                    alive.append(p)
            
            if len(alive) > 0:
                particles.clear()
                particles.extend(alive)
                d_win.after(30, anim)
            else:
                d_win.destroy()
                
        anim()
