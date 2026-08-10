import random
import math
import tkinter as tk
import time

class VictiniMechanics:
    def start_victini_mechanic(self):
        if getattr(self, 'current_state', '') in ['dragged', 'exiting']: return
        if getattr(self, 'victini_cooldown', 0) > 0: return
        if hasattr(self, 'is_global_mechanic_active') and self.is_global_mechanic_active(ignore_victini=True): return

        name = self.pet_name.lower().replace("_", "").replace("-", "")
        if name != "victini": return

        self.current_state = 'victini_channeling'
        self.victini_timer = 90 # 3 seconds
        self.victini_cooldown = 108000 # 1 hour
        self.vic_particles = []
        self.vic_angle = 0
        
        self.schedule_loop(33, self.physics_loop)

    def _fsm_victini_channeling(self):
        self.victini_timer -= 1
        self.vic_angle += 0.2
        
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        
        px = cx + math.cos(self.vic_angle) * 40
        py = cy + math.sin(self.vic_angle) * 40
        self.spawn_victini_particle(px, py, 0, -2, life=20, p_type="fire")
        
        if self.victini_timer <= 0:
            self.current_state = 'victini_flying'
            self.victini_timer = 210 # 7 seconds
            self.v_x_velocity = random.choice([-5, 5])
            self.v_y_velocity = -5
            
        self.schedule_loop(33, self.physics_loop)

    def _fsm_victini_flying(self):
        self.victini_timer -= 1
        
        self.v_x_velocity += math.sin(self.vic_angle) * 0.5
        self.v_y_velocity += math.cos(self.vic_angle * 0.7) * 0.3
        self.vic_angle += 0.1
        
        self.v_x_velocity = max(-8, min(8, self.v_x_velocity))
        self.v_y_velocity = max(-6, min(6, self.v_y_velocity))
        
        self.x += self.v_x_velocity
        self.y += self.v_y_velocity
        
        self.is_facing_right = self.v_x_velocity > 0
        
        if self.x < self.v_x + 50: self.v_x_velocity = abs(self.v_x_velocity)
        elif self.x > self.v_x + self.v_width - self.size_w - 50: self.v_x_velocity = -abs(self.v_x_velocity)
        
        if self.y < self.v_y + 50: self.v_y_velocity = abs(self.v_y_velocity)
        elif self.y > self.v_y + self.v_height - self.size_h - 100: self.v_y_velocity = -abs(self.v_y_velocity)
        
        self._spawn_victini_v_shape()
        
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        if self.victini_timer % 2 == 0:
            self.spawn_victini_particle(cx, cy, 0, 0, life=15, p_type="trail")
            
        self.update_position()
        
        if self.victini_timer <= 0:
            target = None
            if hasattr(self, 'get_all_pets'):
                valid_targets = [p for p in self.get_all_pets() if p != self and p.current_state not in ['exiting', 'dragged'] and not getattr(p, 'is_egg', False)]
                if valid_targets:
                    target = random.choice(valid_targets)
                    
            if target:
                self.vic_target = target
            else:
                self.vic_target = {'x': self.v_x + self.v_width/2, 'y': self.v_y + self.v_height - 100}
                
            self.current_state = 'victini_dash'
            
        self.schedule_loop(33, self.physics_loop)
        
    def _spawn_victini_v_shape(self):
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + 10 # Just above head
        
        self.spawn_victini_particle(cx - 20, cy - 40, 0, 0, 5, p_type="fire")
        self.spawn_victini_particle(cx - 15, cy - 30, 0, 0, 5, p_type="fire")
        self.spawn_victini_particle(cx - 10, cy - 20, 0, 0, 5, p_type="fire")
        self.spawn_victini_particle(cx - 5, cy - 10, 0, 0, 5, p_type="fire")
        
        self.spawn_victini_particle(cx + 20, cy - 40, 0, 0, 5, p_type="fire")
        self.spawn_victini_particle(cx + 15, cy - 30, 0, 0, 5, p_type="fire")
        self.spawn_victini_particle(cx + 10, cy - 20, 0, 0, 5, p_type="fire")
        self.spawn_victini_particle(cx + 5, cy - 10, 0, 0, 5, p_type="fire")
        
        self.spawn_victini_particle(cx, cy, 0, 0, 5, p_type="fire")

    def _fsm_victini_dash(self):
        tx = getattr(self.vic_target, 'x', self.vic_target.get('x', 0) if isinstance(self.vic_target, dict) else 0)
        ty = getattr(self.vic_target, 'y', self.vic_target.get('y', 0) if isinstance(self.vic_target, dict) else 0)
        
        dx = tx - self.x
        dy = ty - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist < 40:
            self.current_state = 'victini_impact'
            self.schedule_loop(33, self.physics_loop)
            return
            
        target_speed = 45.0
        target_vx = (dx / dist) * target_speed
        target_vy = (dy / dist) * target_speed
        
        # Smooth interpolation to simulate graceful acceleration and turning
        self.v_x_velocity += (target_vx - self.v_x_velocity) * 0.12
        self.v_y_velocity += (target_vy - self.v_y_velocity) * 0.12
        
        self.x += self.v_x_velocity
        self.y += self.v_y_velocity
        self.is_facing_right = self.v_x_velocity > 0
        
        self._spawn_victini_v_shape()
        self.spawn_victini_particle(self.x - self.v_x + self.size_w/2, self.y - self.v_y + self.size_h/2, 0, 0, 15, p_type="trail")
        
        self.update_position()
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_victini_impact(self):
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        
        for _ in range(30):
            # V explosion pattern
            if random.random() < 0.5:
                vx = -random.uniform(3, 8)
                vy = -random.uniform(5, 12)
            else:
                vx = random.uniform(3, 8)
                vy = -random.uniform(5, 12)
        self.trigger_victini_explosion()
            
        impact_radius = 400
        if hasattr(self, 'get_all_pets'):
            for target in self.get_all_pets():
                if target != self and target.current_state != 'exiting' and not getattr(target, 'is_egg', False):
                    dt = math.sqrt((self.x - target.x)**2 + (self.y - target.y)**2)
                    if dt <= impact_radius:
                        if hasattr(self, 'apply_burn'):
                            self.apply_burn(target)
                        
        self.current_state = 'thrown' if getattr(self, 'is_flying', False) else 'falling'
        self.schedule_loop(33, self.physics_loop)

    def spawn_victini_particle(self, cx, cy, vx, vy, life, p_type="fire"):
        if not hasattr(self, 'vic_vfx_win') or not self.vic_vfx_win or not self.vic_vfx_win.winfo_exists():
            self._init_vic_vfx()
            
        color = random.choice(["#E74C3C", "#E67E22", "#F1C40F", "#FF5733"])
        size = random.choice([4, 6, 8])
        
        pid = self.vic_vfx_canvas.create_oval(cx-size, cy-size, cx+size, cy+size, fill=color, outline="")
        if not hasattr(self, 'vic_particles'): self.vic_particles = []
        self.vic_particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': life, 'max_life': life, 'max_size': size, 'type': p_type})

    def _init_vic_vfx(self):
        self.vic_vfx_win = tk.Toplevel(self.window.master)
        self.vic_vfx_win.overrideredirect(True)
        self.vic_vfx_win.attributes('-topmost', True)
        TRANS_COLOR = '#010101'
        self.vic_vfx_win.config(bg=TRANS_COLOR)
        try: self.vic_vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass
        self.vic_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        self.vic_vfx_canvas = tk.Canvas(self.vic_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
        self.vic_vfx_canvas.pack()
        self.vic_particles = []
        self._start_victini_particle_loop()

    def _start_victini_particle_loop(self):
        if not hasattr(self, 'vic_particle_loop_running') or not self.vic_particle_loop_running:
            self.vic_particle_loop_running = True
            self._victini_particle_loop()
            
    def _victini_particle_loop(self):
        if hasattr(self, 'vic_vfx_win') and self.vic_vfx_win and self.vic_vfx_win.winfo_exists():
            self._process_victini_particles()
            if getattr(self, 'vic_particles', []) or getattr(self, 'current_state', '').startswith('victini_'):
                self.window.after(33, self._victini_particle_loop)
            else:
                self.vic_vfx_win.destroy()
                self.vic_vfx_win = None
                self.vic_particle_loop_running = False
        else:
            self.vic_particle_loop_running = False

    def _process_victini_particles(self):
        if not hasattr(self, 'vic_vfx_win') or not self.vic_vfx_win: return
        alive = []
        for p in self.vic_particles:
            p['life'] -= 1
            if p['life'] > 0:
                if p['type'] == "explosion":
                    p['vy'] += 0.5
                self.vic_vfx_canvas.move(p['id'], p['vx'], p['vy'])
                
                # Smoothly shrink the particle to simulate fading
                coords = self.vic_vfx_canvas.coords(p['id'])
                if coords:
                    cx = (coords[0] + coords[2]) / 2
                    cy = (coords[1] + coords[3]) / 2
                    r = p['max_size'] * (p['life'] / p['max_life'])
                    self.vic_vfx_canvas.coords(p['id'], cx-r, cy-r, cx+r, cy+r)
                    
                alive.append(p)
            else:
                self.vic_vfx_canvas.delete(p['id'])
                
        self.vic_particles = alive

    def cancel_victini_arts(self):
        if hasattr(self, 'vic_vfx_win') and self.vic_vfx_win:
            self.vic_vfx_win.destroy()
            self.vic_vfx_win = None
        self.vic_particles = []
        if getattr(self, 'current_state', '').startswith('victini_'):
            self.current_state = 'thrown' if getattr(self, 'is_flying', False) else 'falling'

    def trigger_victini_explosion(self):
        impact_radius = 600
        wave_win = tk.Toplevel(self.window.master)
        wave_win.title("VFX_VicWave_Ignore")
        wave_win.overrideredirect(True)
        wave_win.attributes('-topmost', True)
        
        TRANS_COLOR = '#010101'
        wave_win.config(bg=TRANS_COLOR)
        try: wave_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass
        
        win_size = impact_radius * 2
        center_x = int(self.x + self.size_w/2 - win_size/2)
        center_y = int(self.y + self.size_h/2 - win_size/2)
        wave_win.geometry(f"{win_size}x{win_size}+{center_x}+{center_y}")
        
        w_canvas = tk.Canvas(wave_win, width=win_size, height=win_size, bg=TRANS_COLOR, highlightthickness=0)
        w_canvas.pack()
        
        state = {'radius': 10.0, 'alpha_width': 50.0, 'v_scale': 1.0}
        
        if hasattr(self, 'trigger_landing_shake'):
            self.trigger_landing_shake()
            
        # Spawn massive fast flying spark debris
        for _ in range(80):
            vx = random.uniform(-25, 25)
            vy = random.uniform(-25, 25)
            self.spawn_victini_particle(self.x - self.v_x + self.size_w/2, self.y - self.v_y + self.size_h/2, vx, vy, life=50, p_type="explosion")
        
        def animate_wave():
            if not wave_win.winfo_exists(): return
            w_canvas.delete("wave")
            state['radius'] += 45.0
            state['alpha_width'] *= 0.85
            state['v_scale'] += 0.3
            
            if state['radius'] >= impact_radius or state['alpha_width'] < 1.0:
                wave_win.destroy()
                return
                
            r = state['radius']
            cx = win_size / 2
            cy = win_size / 2
            
            # Expanding blast rings
            w_canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline="#E74C3C", width=int(state['alpha_width']), tags="wave")
            w_canvas.create_oval(cx-r*0.8, cy-r*0.8, cx+r*0.8, cy+r*0.8, outline="#F1C40F", width=int(state['alpha_width']*0.8), tags="wave")
            
            # Massive Expanding V - Multi-layered for fiery effect
            vs = state['v_scale'] * 35
            aw = int(state['alpha_width'])
            
            colors = [("#C0392B", 2.5), ("#E67E22", 1.8), ("#F1C40F", 1.0), ("#FFFFFF", 0.4)]
            for col, w_mult in colors:
                w_canvas.create_line(cx, cy, cx - vs, cy - vs*1.5, fill=col, width=int(max(1, aw * w_mult)), capstyle=tk.ROUND, tags="wave")
                w_canvas.create_line(cx, cy, cx + vs, cy - vs*1.5, fill=col, width=int(max(1, aw * w_mult)), capstyle=tk.ROUND, tags="wave")
            
            wave_win.after(20, animate_wave)
            
        animate_wave()
