import math
import random
import tkinter as tk
from PIL import Image, ImageTk

def init_volcanion_arts(self):
    if getattr(self, 'current_state', '') == 'dragged':
        return
        
    self.current_state = 'volcanion_channeling'
    self.volcanion_timer = 90  # 3 seconds at 30 ticks/s
    self.volcanion_targets = []
    
    self.is_global_mechanic = True
    
    # Store references to PIL images and PhotoImages to prevent GC
    self.volcanion_red_cache = {}
    
    # Init steam window
    _init_volcanion_vfx(self)
    
def cancel_volcanion_arts(self):
    if not str(getattr(self, 'current_state', '')).startswith('volcanion_'):
        return
        
    self.current_state = 'idle'
    self.is_global_mechanic = False
    
    # Release victims
    for t in getattr(self, 'volcanion_targets', []):
        t.is_being_pushed = False
        if t.current_state == 'volcanion_victim':
            if hasattr(t, 'interrupt_current_state'): t.interrupt_current_state()
            t.current_state = 'idle'
            
    self.volcanion_targets = []
    
    if hasattr(self, 'volcanion_vfx_win'):
        try: self.volcanion_vfx_win.destroy()
        except: pass
        self.volcanion_vfx_win = None

def _init_volcanion_vfx(self):
    if hasattr(self, 'volcanion_vfx_win') and self.volcanion_vfx_win and self.volcanion_vfx_win.winfo_exists():
        return
        
    self.volcanion_vfx_win = tk.Toplevel(self.window.master)
    self.volcanion_vfx_win.title("volcanion_vfx")
    self.volcanion_vfx_win.overrideredirect(True)
    self.volcanion_vfx_win.attributes('-topmost', True)
    TRANS_COLOR = '#010101'
    self.volcanion_vfx_win.config(bg=TRANS_COLOR)
    try: self.volcanion_vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
    except: pass
    self.volcanion_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
    
    self.volcanion_canvas = tk.Canvas(self.volcanion_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
    self.volcanion_canvas.pack(fill="both", expand=True)
    self.volcanion_particles = []
    self.volcanion_explosions = []
    
    # Start the global VFX loop for particles and victim heating
    self.schedule_loop(30, lambda: _volcanion_global_loop(self))

def _spawn_volcanion_particle(self, x, y, vx, vy, lifetime, color, size=4):
    p = self.volcanion_canvas.create_rectangle(x-size, y-size, x+size, y+size, fill=color, outline="")
    self.volcanion_particles.append({
        'id': p, 'x': x, 'y': y, 'vx': vx, 'vy': vy, 'life': lifetime, 'max_life': lifetime, 'color': color, 'size': size
    })

def _fsm_volcanion_channeling(self):
    self.volcanion_timer -= 1
    
    # Emit steam
    if self.volcanion_timer % 2 == 0:
        my_cx = self.x - self.v_x + self.size_w/2
        my_cy = self.y - self.v_y + self.size_h/2
        _spawn_volcanion_particle(self, my_cx, my_cy - 20, random.uniform(-2, 2), random.uniform(-4, -1), 45, "#DDDDDD", size=random.randint(4, 8))
        
    if self.volcanion_timer <= 0:
        # Pick 2 targets
        valid_targets = [p for p in self.get_all_pets() if p != self and not getattr(p, 'is_egg', False) and p.current_state in ['idle', 'walking', 'socializing'] and getattr(p, 'climbing_surface', 'floor') == 'floor']
        random.shuffle(valid_targets)
        self.volcanion_targets = valid_targets[:2]
        
        for t in self.volcanion_targets:
            if hasattr(t, 'interrupt_current_state'): t.interrupt_current_state()
            t.current_state = 'volcanion_victim'
            t.volcanion_burn = 450  # 15 seconds at 30 ticks
            
        self.current_state = 'volcanion_shooting'
        self.volcanion_timer = 150  # 5 seconds
    self.schedule_loop(30, self.physics_loop)

def _fsm_volcanion_shooting(self):
    self.volcanion_timer -= 1
    my_cx = self.x - self.v_x + self.size_w/2
    my_cy = self.y - self.v_y + self.size_h/2
    
    for target in self.volcanion_targets:
        if target.current_state != 'volcanion_victim':
            continue
            
        # Target position
        t_cx = target.x - target.v_x + getattr(target, 'size_w', 64)/2
        t_cy = target.y - target.v_y + getattr(target, 'size_h', 64)/2
        
        # Shoot water
        dx = t_cx - my_cx
        dy = t_cy - my_cy
        dist = max(1, math.sqrt(dx**2 + dy**2))
        
        # Water particle stream
        if self.volcanion_timer % 3 == 0:
            speed = 25.0
            vx = (dx / dist) * speed + random.uniform(-1, 1)
            vy = (dy / dist) * speed + random.uniform(-1, 1)
            life = int(dist / speed) + 5
            _spawn_volcanion_particle(self, my_cx, my_cy, vx, vy, life, "#4682B4", size=random.randint(6, 10))
            
        # Push target
        push_force = 1.5
        target.v_x_velocity += (dx / dist) * push_force
        target.v_y_velocity += (dy / dist) * 2.5  # Stronger Y push to overcome gravity
        if target.x <= target.v_x or target.x >= target.v_x + target.v_width - getattr(target, 'size_w', 64):
            target.v_x_velocity = 0 # stop push at edge
            
    if self.volcanion_timer <= 0:
        # Steam explosion
        for _ in range(50):
            angle = random.uniform(0, 2*math.pi)
            speed = random.uniform(2, 8)
            _spawn_volcanion_particle(self, my_cx, my_cy, math.cos(angle)*speed, math.sin(angle)*speed, 60, "#FFFFFF", size=random.randint(4, 10))
            
        self.current_state = 'idle'
        self.is_global_mechanic = False
        for t in self.volcanion_targets:
            if t.current_state == 'volcanion_victim':
                if hasattr(t, 'interrupt_current_state'): t.interrupt_current_state()
                t.current_state = 'idle'
        self.volcanion_targets = []
    
    self.schedule_loop(30, self.physics_loop)

def _volcanion_global_loop(self):
    if not hasattr(self, 'volcanion_vfx_win') or not self.volcanion_vfx_win:
        return
        
    keep_alive = False
    
    # Process particles
    for p in self.volcanion_particles[:]:
        p['life'] -= 1
        if p['life'] <= 0:
            self.volcanion_canvas.delete(p['id'])
            self.volcanion_particles.remove(p)
        else:
            self.volcanion_canvas.move(p['id'], p['vx'], p['vy'])
            keep_alive = True
            
    # Process victims (even after Volcanion is idle)
    for p in self.get_all_pets():
        if getattr(p, 'volcanion_burn', 0) > 0:
            p.volcanion_burn -= 1
            keep_alive = True
            
            # Emit steam from victim
            if random.random() < 0.1:
                size_w = getattr(p, 'size_w', 64)
                size_h = getattr(p, 'size_h', 64)
                my_cx = p.x - self.v_x + size_w/2
                my_cy = p.y - self.v_y + size_h/2
                _spawn_volcanion_particle(self, my_cx, my_cy, random.uniform(-1, 1), random.uniform(-3, -1), 30, "#DDDDDD", size=random.randint(3, 6))
                
    if keep_alive or self.current_state in ['volcanion_channeling', 'volcanion_shooting']:
        self.schedule_loop(30, lambda: _volcanion_global_loop(self))
    else:
        # Cleanup completely
        self.volcanion_red_cache.clear()
        try: self.volcanion_vfx_win.destroy()
        except: pass
        self.volcanion_vfx_win = None
