import random
import math
import tkinter as tk
import time

class SeaGuardiansMechanics:
    def start_sea_guardian_mechanic(self):
        if getattr(self, 'current_state', '') in ['dragged', 'exiting']: return
        
        # Cooldown check
        if getattr(self, 'sg_cooldown', 0) > 0:
            return
            
        # Global mechanic block
        if hasattr(self, 'is_global_mechanic_active') and self.is_global_mechanic_active(ignore_sea_guardians=True):
            return

        name = self.pet_name.lower().replace("-", "").replace("_", "")
        if "manaphy" in name:
            self.sea_guardian_jumps = 20
        elif "phione" in name:
            self.sea_guardian_jumps = 10
        else:
            return

        self.current_state = 'sea_guardian_absorb'
        self.surface_angle = 0
        self.sg_timer = 60 # 2 seconds
        
        # 1 hour cooldown (3600 seconds * 30 frames/sec)
        self.sg_cooldown = 108000 

    def _fsm_sea_guardian_absorb(self):
        if not hasattr(self, 'sg_timer'): return
        if self.sg_timer > 0:
            self.sg_timer -= 1
            if random.random() < 0.3:
                cx = self.x - self.v_x + self.size_w/2
                cy = self.y - self.v_y + self.size_h
                px = cx + random.randint(-40, 40)
                py = self.v_height - 5
                vx = (cx - px) / 10.0
                vy = (cy - py) / 10.0
                self.spawn_water_particle(px, py, vx, vy, life=15)
            self.schedule_loop(33, self.physics_loop)
        else:
            self.current_state = 'sea_guardian_big_jump'
            g = 1.2
            h = self.v_height * 0.75
            self.v_y_velocity = -math.sqrt(2 * g * h)
            self.v_x_velocity = random.uniform(-15, 15)
            self.sg_gravity = g
            self.schedule_loop(33, self.physics_loop)

    def _fsm_sea_guardian_big_jump(self):
        self.v_y_velocity += self.sg_gravity
        self.x += self.v_x_velocity
        self.y += self.v_y_velocity
        
        self.surface_angle = (-math.degrees(math.atan2(self.v_y_velocity, self.v_x_velocity)) - 90) % 360
        self.is_facing_right = self.v_x_velocity > 0
        
        if random.random() < 0.5:
            self.spawn_water_trail()

        self.update_position()
        
        if self.v_y_velocity > 0 and self.y > self.v_y + self.v_height:
            splash_x = (self.x - self.v_x + self.size_w/2) - (self.v_x_velocity * 2)
            self.splash_at(splash_x, self.v_height - 10)
            self.current_state = 'sea_guardian_wait'
            self.sg_timer = 30
            
        self.schedule_loop(33, self.physics_loop)

    def _fsm_sea_guardian_wait(self):
        if not hasattr(self, 'sg_timer'): return
        if self.sg_timer > 0:
            self.sg_timer -= 1
            self.schedule_loop(33, self.physics_loop)
        else:
            if self.sea_guardian_jumps > 0:
                self.sea_guardian_jumps -= 1
                self.start_small_jump(is_last=(self.sea_guardian_jumps == 0))
            else:
                self.cancel_sea_guardian_arts()

    def start_small_jump(self, is_last=False):
        self.current_state = 'sea_guardian_last_jump' if is_last else 'sea_guardian_jump'
        
        surface = random.choice([0, 1, 2])
        g = 1.5
        self.sg_gravity = g
        
        if surface == 0: # bottom
            self.x = self.v_x + random.randint(self.size_w, self.v_width - self.size_w)
            self.y = self.v_y + self.v_height + self.size_h
            # A bit more vertical height for bottom jumps
            h = random.uniform(self.v_height * 0.4, self.v_height * 0.7)
            self.v_y_velocity = -math.sqrt(2 * g * h)
            self.v_x_velocity = random.uniform(15, 30) if random.random() < 0.5 else random.uniform(-30, -15)
            self.splash_at(self.x - self.v_x + self.size_w/2, self.v_height - 10)
        elif surface == 1: # left
            self.x = self.v_x - self.size_w
            self.y = self.v_y + random.randint(self.size_h, self.v_height - self.size_h)
            self.v_x_velocity = random.uniform(25, 45)
            self.v_y_velocity = random.uniform(-15, -5)
            self.splash_at(10, self.y - self.v_y + self.size_h/2)
        else: # right
            self.x = self.v_x + self.v_width + self.size_w
            self.y = self.v_y + random.randint(self.size_h, self.v_height - self.size_h)
            self.v_x_velocity = random.uniform(-45, -25)
            self.v_y_velocity = random.uniform(-15, -5)
            self.splash_at(self.v_width - 10, self.y - self.v_y + self.size_h/2)
            
        self.schedule_loop(33, self.physics_loop)

    def _fsm_sea_guardian_last_jump(self):
        self.v_y_velocity += self.sg_gravity
        self.x += self.v_x_velocity
        self.y += self.v_y_velocity
        
        self.surface_angle = (-math.degrees(math.atan2(self.v_y_velocity, self.v_x_velocity)) - 90) % 360
        self.is_facing_right = self.v_x_velocity > 0
        
        if random.random() < 0.5:
            self.spawn_water_trail()
            
        self.update_position()
        
        if self.v_y_velocity >= 0:
            self.current_state = 'sea_guardian_braking'
            
        self.schedule_loop(33, self.physics_loop)

    def _fsm_sea_guardian_braking(self):
        # Brake horizontally smoothly
        self.v_x_velocity *= 0.85
        
        # Float down gently
        self.v_y_velocity += self.sg_gravity * 0.2
        self.v_y_velocity *= 0.90
        
        self.x += self.v_x_velocity
        self.y += self.v_y_velocity
        self.surface_angle = 0
        
        self.update_position()
        
        if abs(self.v_x_velocity) < 1.0:
            self.v_x_velocity = 0
            self.cancel_sea_guardian_arts()
            
        self.schedule_loop(33, self.physics_loop)

    def _fsm_sea_guardian_jump(self):
        self.v_y_velocity += self.sg_gravity
        self.x += self.v_x_velocity
        self.y += self.v_y_velocity
        
        self.surface_angle = (-math.degrees(math.atan2(self.v_y_velocity, self.v_x_velocity)) - 90) % 360
        self.is_facing_right = self.v_x_velocity > 0
        
        if random.random() < 0.5:
            self.spawn_water_trail()
            
        self.update_position()
        
        exited = False
        cx = (self.x - self.v_x + self.size_w/2) - (self.v_x_velocity * 2)
        cy = (self.y - self.v_y + self.size_h/2) - (self.v_y_velocity * 2)
        
        if self.v_y_velocity > 0 and self.y > self.v_y + self.v_height:
            self.splash_at(cx, self.v_height - 10)
            exited = True
        elif self.v_x_velocity < 0 and self.x + self.size_w < self.v_x:
            self.splash_at(10, cy)
            exited = True
        elif self.v_x_velocity > 0 and self.x > self.v_x + self.v_width:
            self.splash_at(self.v_width - 10, cy)
            exited = True
            
        if exited:
            self.current_state = 'sea_guardian_wait'
            self.sg_timer = 30
            
        self.schedule_loop(33, self.physics_loop)

    def spawn_water_trail(self):
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        self.spawn_water_particle(cx, cy, 0, 0, 15, tag="sg_trail")
        
    def splash_at(self, x, y):
        for _ in range(10):
            vx = random.uniform(-5, 5)
            vy = random.uniform(-5, 0)
            self.spawn_water_particle(x, y, vx, vy, random.randint(15, 30))

    def spawn_water_particle(self, cx, cy, vx, vy, life, tag="sg_particle"):
        if not hasattr(self, 'sg_vfx_win') or not self.sg_vfx_win or not self.sg_vfx_win.winfo_exists():
            self._init_sg_vfx()
        
        colors = ["#4D94FF", "#0055FF", "#B3D1FF", "#00BFFF"]
        color = random.choice(colors)
        size = random.choice([2, 3])
        pid = self.sg_vfx_canvas.create_oval(cx-size, cy-size, cx+size, cy+size, fill=color, outline="")
        self.sg_particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': life, 'max_life': life, 'tag': tag})
        if len(self.sg_particles) == 1:
            self._process_sg_particles()

    def _init_sg_vfx(self):
        self.sg_vfx_win = tk.Toplevel(self.window.master)
        self.sg_vfx_win.overrideredirect(True)
        self.sg_vfx_win.attributes('-topmost', True)
        TRANS_COLOR = '#010101'
        self.sg_vfx_win.config(bg=TRANS_COLOR)
        try: self.sg_vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass
        self.sg_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        self.sg_vfx_canvas = tk.Canvas(self.sg_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
        self.sg_vfx_canvas.pack()
        self.sg_particles = []

    def _process_sg_particles(self):
        if not hasattr(self, 'sg_vfx_win') or not self.sg_vfx_win: return
        alive = []
        for p in self.sg_particles:
            p['life'] -= 1
            if p['life'] > 0:
                p['vy'] += 0.2
                self.sg_vfx_canvas.move(p['id'], p['vx'], p['vy'])
                alive.append(p)
            else:
                self.sg_vfx_canvas.delete(p['id'])
                
        self.sg_particles = alive
        if self.sg_particles:
            self.schedule_loop(33, self._process_sg_particles)
        else:
            if hasattr(self, 'sg_vfx_win') and self.sg_vfx_win:
                self.sg_vfx_win.destroy()
                self.sg_vfx_win = None

    def cancel_sea_guardian_arts(self):
        if hasattr(self, 'sg_vfx_win') and self.sg_vfx_win:
            self.sg_vfx_win.destroy()
            self.sg_vfx_win = None
        self.surface_angle = 0
        if getattr(self, 'current_state', '').startswith('sea_guardian_'):
            self.current_state = 'thrown' if getattr(self, 'is_flying', False) else 'falling'
