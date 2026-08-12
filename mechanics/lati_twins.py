import random
import math
import tkinter as tk

class LatiTwinsMechanics:
    def cancel_lati_arts(self):
        if hasattr(self, 'lati_vfx_win') and self.lati_vfx_win and self.lati_vfx_win.winfo_exists():
            self.lati_vfx_win.destroy()
            self.lati_vfx_win = None
            
        for attr in ['lati_timer', 'lati_dashes', 'lati_vfx_win', 'lati_canvas', 'lati_particles', 'lati_spiral_angle', 'lati_spiral_radius', 'lati_spiral_cx', 'lati_spiral_cy']:
            if hasattr(self, attr): delattr(self, attr)

        self.surface_angle = 0
        if self.current_state not in ['dragged', 'exiting']:
            self.current_state = 'falling'
            self.v_y_velocity = 0

    def _fsm_lati_channeling(self):
        if not hasattr(self, 'lati_timer'):
            self.lati_timer = 100 # 3.3 seconds
            self.v_y_velocity = 0
            
            # Setup VFX window
            current_env, _ = self.get_window_environment()
            self.lati_vfx_win = tk.Toplevel(self.window.master)
            self.lati_vfx_win.title("VFX_Lati_Ignore")
            self.lati_vfx_win.overrideredirect(True)
            self.lati_vfx_win.attributes('-topmost', True)
            TRANS_COLOR = '#010101'
            self.lati_vfx_win.config(bg=TRANS_COLOR)
            try: self.lati_vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
            except: pass
            
            self.lati_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
            self.lati_canvas = tk.Canvas(self.lati_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
            self.lati_canvas.pack()
            self.lati_particles = []
            self.lati_vfx_loop()
            
        self.lati_timer -= 1
        
        # Add inward particles
        if self.lati_timer % 2 == 0:
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(100, 200)
            cx = self.x - self.v_x + self.size_w/2
            cy = self.y - self.v_y + self.size_h/2
            spawn_x = cx + math.cos(angle) * dist
            spawn_y = cy + math.sin(angle) * dist
            
            color = "#E91E63" if "latias" in self.pet_name.lower() else "#2196F3"
            if "latias" not in self.pet_name.lower() and "latios" not in self.pet_name.lower():
                color = "#E91E63" # fallback
                
            self.lati_particles.append({
                'id': self.lati_canvas.create_rectangle(spawn_x-3, spawn_y-3, spawn_x+3, spawn_y+3, fill=color, outline=color, tags="pt"),
                'x': spawn_x, 'y': spawn_y,
                'target_x': cx, 'target_y': cy,
                'speed': random.uniform(4.0, 8.0)
            })
            
        if self.lati_timer <= 0:
            self.current_state = 'lati_spiral'
            self.lati_spiral_angle = 0.0
            self.lati_spiral_radius_x = 50.0
            self.lati_spiral_radius_y = 20.0
            self.lati_spiral_cx = self.x
            self.lati_spiral_cy = self.y
            self.is_facing_right = True
            
        self.update_position()
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_lati_spiral(self):
        # 2 loops = 4pi, flatten oval
        self.lati_spiral_angle += 0.15
        self.lati_spiral_radius_x += 24.0
        self.lati_spiral_radius_y += 1.5
        
        new_x = self.lati_spiral_cx + math.cos(self.lati_spiral_angle) * self.lati_spiral_radius_x
        new_y = self.lati_spiral_cy + math.sin(self.lati_spiral_angle) * self.lati_spiral_radius_y
        
        self.is_facing_right = new_x > self.x
        self.x = new_x
        self.y = new_y
        
        # Add trail
        color = "#E91E63" if "latias" in self.pet_name.lower() else "#2196F3"
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        self.lati_particles.append({
            'id': self.lati_canvas.create_rectangle(cx-6, cy-6, cx+6, cy+6, fill=color, outline=color, tags="pt"),
            'x': cx, 'y': cy, 'type': 'trail', 'life': 30
        })
        
        # Check if off-screen laterally
        if (self.x < self.v_x - self.size_w or self.x > self.v_x + self.v_width) and self.lati_spiral_radius_x > 300:
            self.current_state = 'lati_dash_wait'
            self.lati_timer = 30 # 1 second
            self.lati_dashes = 0
            
        self.update_position()
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_lati_dash_wait(self):
        self.x = -1000
        self.y = -1000
        self.update_position()
        
        self.lati_timer -= 1
        if self.lati_timer <= 0:
            if self.lati_dashes >= 10:
                self.current_state = 'lati_return'
                # Setup return approach
                self.x = self.v_x - self.size_w
                self.y = getattr(self, 'target_floor_y', self.v_y + 100)
                self.v_x_velocity = 20.0
                self.is_facing_right = True
                self.surface_angle = 0
                if hasattr(self, 'lati_vfx_win') and self.lati_vfx_win:
                    self.lati_vfx_win.destroy()
                    self.lati_vfx_win = None
            else:
                self.current_state = 'lati_dash'
                self.lati_dashes += 1
                # Setup random straight line from edge to opposite half edge
                edge = random.choice(['top', 'bottom', 'left', 'right'])
                if edge == 'top':
                    self.x = self.v_x + random.randint(0, self.v_width)
                    self.y = self.v_y - self.size_h
                    target_x = self.v_x + random.randint(0, self.v_width)
                    target_y = self.v_y + self.v_height + self.size_h
                elif edge == 'bottom':
                    self.x = self.v_x + random.randint(0, self.v_width)
                    self.y = self.v_y + self.v_height + self.size_h
                    target_x = self.v_x + random.randint(0, self.v_width)
                    target_y = self.v_y - self.size_h
                elif edge == 'left':
                    self.x = self.v_x - self.size_w
                    self.y = self.v_y + random.randint(0, self.v_height)
                    target_x = self.v_x + self.v_width + self.size_w
                    target_y = self.v_y + random.randint(0, self.v_height)
                else: # right
                    self.x = self.v_x + self.v_width + self.size_w
                    self.y = self.v_y + random.randint(0, self.v_height)
                    target_x = self.v_x - self.size_w
                    target_y = self.v_y + random.randint(0, self.v_height)
                    
                dx = target_x - self.x
                dy = target_y - self.y
                dist = math.hypot(dx, dy)
                speed = 120.0
                self.lati_dash_vx = (dx / dist) * speed
                self.lati_dash_vy = (dy / dist) * speed
                
                angle = math.degrees(math.atan2(dy, dx))
                # Force right-facing and use pure negative angle rotation
                self.is_facing_right = True
                self.surface_angle = -angle
                
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_lati_dash(self):
        self.x += self.lati_dash_vx
        self.y += self.lati_dash_vy
        
        # Trail
        color = "#E91E63" if "latias" in self.pet_name.lower() else "#2196F3"
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        
        for _ in range(4):
            self.lati_particles.append({
                'id': self.lati_canvas.create_rectangle(cx-6, cy-6, cx+6, cy+6, fill=color, outline=color, tags="pt"),
                'x': cx + random.randint(-20, 20), 'y': cy + random.randint(-20, 20), 'type': 'trail', 'life': 30
            })
            
        # Collision detection (excluding eggs and other latis)
        global_cx = self.x + self.size_w/2
        global_cy = self.y + self.size_h/2
        if getattr(self, 'get_all_pets', None):
            for p in self.get_all_pets():
                if p != self and p.current_state not in ['exiting', 'dragged', 'thrown'] and not getattr(p, 'is_egg', False) and "lati" not in p.pet_name.lower():
                    pcx = p.x + p.size_w/2
                    pcy = p.y + p.size_h/2
                    dist = math.hypot(global_cx - pcx, global_cy - pcy)
                    if dist < (self.size_w + p.size_w)/2.0:
                        p.current_state = 'thrown'
                        p.v_x_velocity = self.lati_dash_vx * 1.2 + random.uniform(-10, 10)
                        p.v_y_velocity = self.lati_dash_vy * 0.8 - 40.0
                        
                        # Add explosion ring
                        inner = self._draw_pixel_circle_bbox(self.lati_canvas, pcx-self.v_x-10, pcy-self.v_y-10, pcx-self.v_x+10, pcy-self.v_y+10, fill="white", outline="", tags="pt")
                        outer = self._draw_pixel_circle_bbox(self.lati_canvas, pcx-self.v_x-20, pcy-self.v_y-20, pcx-self.v_x+20, pcy-self.v_y+20, outline=color, width=4, tags="pt")
                        self.lati_particles.append({'id': inner, 'type': 'explosion', 'life': 10, 'bbox': (pcx-self.v_x-10, pcy-self.v_y-10, pcx-self.v_x+10, pcy-self.v_y+10), 'color': "white"})
                        self.lati_particles.append({'id': outer, 'type': 'explosion_ring', 'life': 10, 'bbox': (pcx-self.v_x-20, pcy-self.v_y-20, pcx-self.v_x+20, pcy-self.v_y+20), 'color': color})
                        
                        if hasattr(p, 'play_sound'):
                            try: p.play_sound("hit.wav")
                            except: pass
        
        # Check off-screen
        if self.x < self.v_x - self.size_w*2 or self.x > self.v_x + self.v_width + self.size_w*2 or \
           self.y < self.v_y - self.size_h*2 or self.y > self.v_y + self.v_height + self.size_h*2:
            self.current_state = 'lati_dash_wait'
            self.lati_timer = 30 # 1 sec delay
            
        self.update_position()
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_lati_return(self):
        self.x += self.v_x_velocity
        self.v_x_velocity *= 0.9 # Brake
        
        if self.v_x_velocity < 2.0:
            self.current_state = 'idle'
            self.lati_cooldown = 72000
            self.v_x_velocity = 0
            
        self.update_position()
        self.schedule_loop(33, self.physics_loop)
        
    def lati_vfx_loop(self):
        if self.current_state not in ['lati_channeling', 'lati_spiral', 'lati_dash_wait', 'lati_dash', 'lati_return']: return
        if not hasattr(self, 'lati_vfx_win') or not self.lati_vfx_win or not self.lati_vfx_win.winfo_exists(): return
        
        alive = []
        for p in self.lati_particles:
            if p.get('type') == 'trail':
                if p['life'] > 0:
                    p['life'] -= 1
                    size = max(1, p['life']/5.0)
                    self.lati_canvas.coords(p['id'], p['x']-size, p['y']-size, p['x']+size, p['y']+size)
                    alive.append(p)
                else:
                    self.lati_canvas.delete(p['id'])
            elif p.get('type') == 'explosion':
                if p['life'] > 0:
                    p['life'] -= 1
                    b = p['bbox']
                    p['bbox'] = (b[0]-2, b[1]-2, b[2]+2, b[3]+2)
                    self.lati_canvas.delete(p['id'])
                    p['id'] = self._draw_pixel_circle_bbox(self.lati_canvas, *p['bbox'], fill=p['color'], outline="", tags="pt")
                    alive.append(p)
                else:
                    self.lati_canvas.delete(p['id'])
            elif p.get('type') == 'explosion_ring':
                if p['life'] > 0:
                    p['life'] -= 1
                    b = p['bbox']
                    p['bbox'] = (b[0]-3, b[1]-3, b[2]+3, b[3]+3)
                    self.lati_canvas.delete(p['id'])
                    p['id'] = self._draw_pixel_circle_bbox(self.lati_canvas, *p['bbox'], outline=p['color'], width=4, tags="pt")
                    alive.append(p)
                else:
                    self.lati_canvas.delete(p['id'])
            else:
                # Inward channel
                dx = p['target_x'] - p['x']
                dy = p['target_y'] - p['y']
                dist = math.hypot(dx, dy)
                if dist > p['speed']:
                    p['x'] += (dx/dist) * p['speed']
                    p['y'] += (dy/dist) * p['speed']
                    self.lati_canvas.coords(p['id'], p['x']-3, p['y']-3, p['x']+3, p['y']+3)
                    alive.append(p)
                else:
                    self.lati_canvas.delete(p['id'])
                    
        self.lati_particles = alive
        self.window.after(33, self.lati_vfx_loop)
