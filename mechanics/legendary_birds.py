import os
import math
import random
import tkinter as tk

class LegendaryBirdsMechanics:
    def cancel_bird_arts(self):
        # Destroys the unified VFX layer to prevent DWM memory leaks
        if hasattr(self, 'bird_vfx_win') and self.bird_vfx_win and self.bird_vfx_win.winfo_exists():
            self.bird_vfx_win.destroy()
            self.bird_vfx_win = None

        for attr in ['bird_timer', 'bird_phase', 'bird_type', 'bird_particles', 'bird_pillar_xs']:
            if hasattr(self, attr): delattr(self, attr)

        if self.current_state not in ['dragged', 'exiting']:
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            
            if getattr(self, 'is_flying', False):
                self.floor_y = getattr(self, 'target_floor_y', self.y)
                self.current_state = 'ascending'
            else:
                self.current_state = 'falling'
                
            # Critical Engine Fix: Restarts the physics loop to prevent FSM deadlocks
            self.schedule_loop(50, self.physics_loop)

    def trigger_bird_arts(self):
        name = self.pet_name.lower().replace("_", "").replace("-", "")
        if name in ["articuno", "articuno1"]: self.bird_type = "articuno"
        elif name in ["zapdos", "zapdos1"]: self.bird_type = "zapdos"
        elif name in ["moltres", "moltres1"]: self.bird_type = "moltres"
        else: return

        self._setup_bird_vfx_layer()
        
        self.bird_phase = 0
        self.bird_timer = 60 
        self.current_state = 'bird_channeling'
        self.v_x_velocity = 0.0
        self.v_y_velocity = 0.0
        
        self.schedule_loop(30, self.physics_loop)

    def _setup_bird_vfx_layer(self):
        self.bird_particles = []
        if hasattr(self, 'bird_vfx_win') and self.bird_vfx_win and self.bird_vfx_win.winfo_exists():
            self.bird_vfx_canvas.delete("all")
            return
            
        self.bird_vfx_win = tk.Toplevel(self.window.master)
        self.bird_vfx_win.title("VFX_Legendary_Birds")
        self.bird_vfx_win.overrideredirect(True)
        self.bird_vfx_win.attributes('-topmost', True)
        
        TRANS = '#010101'
        self.bird_vfx_win.config(bg=TRANS)
        try: self.bird_vfx_win.wm_attributes('-transparentcolor', TRANS)
        except: pass
        
        self.bird_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        
        # Injects WS_EX_TRANSPARENT into Windows API to bypass mouse hit-tests
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.bird_vfx_win.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x00080000 | 0x00000020)
        except: pass

        self.bird_vfx_canvas = tk.Canvas(self.bird_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS, highlightthickness=0)
        self.bird_vfx_canvas.pack()

    def _spawn_bird_absorption(self):
        if not hasattr(self, 'bird_vfx_canvas'): return
        
        # Relative coordinates mapping based on the active viewport offset
        cx = self.x - self.v_x + self.size_w / 2
        cy = self.y - self.v_y + self.size_h / 2
        
        for _ in range(2):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(80, 150)
            px = cx + math.cos(angle) * dist
            py = cy + math.sin(angle) * dist
            
            if self.bird_type == "articuno":
                color = random.choice(["#E0FFFF", "#ADD8E6", "#87CEFA", "#FFFFFF"])
            elif self.bird_type == "zapdos":
                color = random.choice(["#FFFF00", "#FFD700", "#FFA500", "#FFFFFF"])
            else: 
                color = random.choice(["#FF4500", "#FF0000", "#E74C3C", "#F1C40F"])
                
            size = random.choice([2, 3, 4])
            speed = random.uniform(8.0, 15.0)
            vx = -math.cos(angle) * speed
            vy = -math.sin(angle) * speed
            
            pid = self.bird_vfx_canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color)
            self.bird_particles.append({'id': pid, 'x': px, 'y': py, 'vx': vx, 'vy': vy, 'life': 10, 'size': size, 'type': 'absorb'})

    def _execute_bird_explosion(self):
        if not hasattr(self, 'bird_vfx_canvas'): return
        cx = self.x - self.v_x + self.size_w / 2
        cy = self.y - self.v_y + self.size_h / 2
        
        for _ in range(30):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(10.0, 25.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            if self.bird_type == "articuno":
                color = random.choice(["#E0FFFF", "#ADD8E6", "#FFFFFF"])
            elif self.bird_type == "zapdos":
                color = random.choice(["#FFFF00", "#FFA500", "#FFFFFF"])
            else:
                color = random.choice(["#FF4500", "#FF0000", "#F1C40F"])
                
            size = random.choice([3, 4, 5])
            pid = self.bird_vfx_canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline=color)
            self.bird_particles.append({'id': pid, 'x': cx, 'y': cy, 'vx': vx, 'vy': vy, 'life': 15, 'size': size, 'type': 'explode'})

    def _spawn_pillar_particles(self):
        if not hasattr(self, 'bird_vfx_canvas'): return
        
        self.bird_vfx_canvas.delete("bird_lightning")
        
        for px in self.bird_pillar_xs:
            # Rendering must be local to the Canvas. Removing self.v_x to avoid double translation geometry failure.
            render_x = px
            
            if self.bird_type == "articuno":
                # Particle emission throttled to maintain CPU performance
                if self.bird_timer % 3 == 0:
                    ox = render_x + random.uniform(-45, 45)
                    oy = -20
                    s = random.choice([6, 8, 10])
                    vy = random.uniform(25.0, 45.0)
                    color = random.choice(["#E0FFFF", "#ADD8E6", "#FFFFFF"])
                    
                    pid = self.bird_vfx_canvas.create_polygon(
                        ox, oy-s, ox+s, oy, ox, oy+s, ox-s, oy,
                        fill=color, outline="#87CEEB", tags="bird_pillar"
                    )
                    self.bird_particles.append({'id': pid, 'x': ox, 'y': oy, 'vx': 0.0, 'vy': vy, 'life': 45, 'size': s, 'type': 'pillar'})
                    
            elif self.bird_type == "moltres":
                if self.bird_timer % 3 == 0:
                    ox = render_x + random.uniform(-45, 45)
                    oy = self.v_height + 20
                    s = random.choice([4, 6, 8])
                    vy = random.uniform(-25.0, -45.0)
                    color = random.choice(["#FF4500", "#FF0000", "#F1C40F", "#E67E22"])
                    
                    pid = self.bird_vfx_canvas.create_rectangle(
                        ox-s, oy-s, ox+s, oy+s, fill=color, outline=color, tags="bird_pillar"
                    )
                    self.bird_particles.append({'id': pid, 'x': ox, 'y': oy, 'vx': 0.0, 'vy': vy, 'life': 45, 'size': s, 'type': 'pillar'})
                    
            elif self.bird_type == "zapdos":
                if random.randint(1, 100) <= 40:
                    w = random.choice([5, 10, 20])
                    color = random.choice(["#FFFF00", "#FFFFFF", "#FFD700"])
                    self.bird_vfx_canvas.create_line(
                        render_x + random.randint(-30, 30), 0, 
                        render_x + random.randint(-30, 30), self.v_height, 
                        fill=color, width=w, tags="bird_lightning"
                    )

    def _process_bird_particles(self):
        if not hasattr(self, 'bird_vfx_canvas') or not self.bird_vfx_canvas: return
        alive = []
        for p in getattr(self, 'bird_particles', []):
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1
            
            if p['type'] == 'explode':
                p['vx'] *= 0.85
                p['vy'] *= 0.85
                
            if p['life'] > 0:
                if p.get('type') == 'pillar' and self.bird_type == "articuno":
                    s = p['size']
                    self.bird_vfx_canvas.coords(p['id'], p['x'], p['y']-s, p['x']+s, p['y'], p['x'], p['y']+s, p['x']-s, p['y'])
                else:
                    self.bird_vfx_canvas.coords(p['id'], p['x']-p['size'], p['y']-p['size'], p['x']+p['size'], p['y']+p['size'])
                alive.append(p)
            else:
                self.bird_vfx_canvas.delete(p['id'])
        self.bird_particles = alive

    def _fsm_bird_channeling(self):
        if self.bird_phase == 0:
            self.bird_timer -= 1
            self._spawn_bird_absorption()
            self._process_bird_particles()
            
            if getattr(self, 'is_flying', False):
                self.fly_amplitude = getattr(self, 'fly_amplitude', 0) + 0.1
                self.y = getattr(self, 'target_floor_y', self.default_floor_y) + math.sin(self.fly_amplitude) * 5
                
            if self.bird_timer <= 0:
                self._execute_bird_explosion()
                self.bird_phase = 1
                self.bird_timer = 25 
                
        elif self.bird_phase == 1:
            self.bird_timer -= 1
            self._process_bird_particles()
            
            if self.bird_timer <= 0:
                self.bird_phase = 2
                self.bird_timer = 90 
                
                self.bird_pillar_xs = []
                for _ in range(3):
                    self.bird_pillar_xs.append(random.randint(100, self.v_width - 100))

        elif self.bird_phase == 2:
            self.bird_timer -= 1
            self._spawn_pillar_particles()
            self._process_bird_particles()
            
            # Hitbox assessment synced accurately to visual rendering duration
            self._apply_bird_hitboxes()
            
            if self.bird_timer <= 0:
                self.cancel_bird_arts()
                return

        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _apply_bird_hitboxes(self):
        if not getattr(self, 'get_all_pets', None): return
        
        for p in self.get_all_pets():
            if p == self or getattr(p, 'is_egg', False) or p.current_state in ['exiting', 'dragged']: 
                continue
            
            if self.bird_type == "articuno" and p.current_state == 'kyurem_frozen': continue
            if self.bird_type == "zapdos" and p.current_state == 'zekrom_paralyzed': continue
            if self.bird_type == "moltres" and p.current_state == 'reshiram_burn': continue
            
            px_center = p.x + (p.size_w / 2)
            
            hit = False
            for pillar_x in self.bird_pillar_xs:
                # The hitbox strictly demands absolute OS coordinates for physical spatial alignment
                absolute_pillar_x = pillar_x + self.v_x
                if abs(px_center - absolute_pillar_x) < 70: 
                    hit = True
                    break
                    
            if hit:
                if self.bird_type == "articuno" and hasattr(self, 'apply_freeze'):
                    self.apply_freeze(p)
                elif self.bird_type == "zapdos" and hasattr(self, 'apply_paralysis'):
                    self.apply_paralysis(p)
                elif self.bird_type == "moltres" and hasattr(self, 'apply_burn'):
                    self.apply_burn(p)