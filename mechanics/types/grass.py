import random
import math

class GrassMechanics:
    def check_grass_mechanic(self):
        if getattr(self, 'grass_cooldown', 0) == 0 and __import__('random').randint(1, 100) <= 10:
            target_found = False
            if getattr(self, 'get_all_pets', None):
                for other in self.get_all_pets():
                    if other == self or getattr(other, 'is_egg', False) or other.current_state in ['exiting', 'dragged', 'poisoned', 'burning', 'frozen', 'asleep', 'paralyzed', 'webbed', 'bubbled', 'tk_lifted', 'dragon_fear', 'dragon_flee', 'flying']: continue
                    dist = __import__('math').hypot((other.x + other.size_w/2) - (self.x + self.size_w/2), (other.y + other.size_h/2) - (self.y + self.size_h/2))
                    if dist < 1000:
                        target_found = True
                        break
                        
            if target_found:
                self.grass_cooldown = 18000
                
                import tkinter as tk
                win = tk.Toplevel(self.window)
                win.title("Deskmon_VFX")
                win.overrideredirect(True)
                win.attributes("-transparentcolor", "white")
                win.attributes("-topmost", True)
                canvas = tk.Canvas(win, bg='white', highlightthickness=0)
                canvas.pack(fill='both', expand=True)
                
                direction = 1 if getattr(self, 'is_facing_right', True) else -1
                
                c_w, c_h = 1000, 800
                start_x = self.x + self.size_w/2
                start_y = self.y + self.size_h/2
                
                win.geometry(f"{c_w}x{c_h}+{int(start_x - c_w/2)}+{int(start_y - c_h/2)}")
                
                cloud = {
                    'win': win,
                    'canvas': canvas,
                    'x': start_x - c_w/2,
                    'y': start_y - c_h/2,
                    'life': 100,
                    'spores': []
                }
                
                for _ in range(25):
                    cloud['spores'].append({
                        'cx': c_w/2 + direction * 20 + __import__('random').randint(-15, 15),
                        'cy': c_w/2 - 100 + __import__('random').randint(-15, 15),
                        'vx': direction * __import__('random').uniform(4, 7),
                        'vy': __import__('random').uniform(-1.5, 1.5),
                        'color': __import__('random').choice(['#7CFC00', '#ADFF2F', '#32CD32'])
                    })
                
                def animate_cloud(c):
                    if not c['win'].winfo_exists(): return
                    
                    c['life'] -= 1
                    if c['life'] <= 0:
                        c['win'].destroy()
                        return
                        
                    c['canvas'].delete('all')
                    
                    for spore in c['spores']:
                        spore['cx'] += spore['vx']
                        spore['cy'] += spore['vy']
                        r = max(0.5, 5.0 * (c['life'] / 100.0))
                        c['canvas'].create_rectangle(
                            spore['cx'] - r, spore['cy'] - r,
                            spore['cx'] + r, spore['cy'] + r,
                            fill=spore['color'], outline=''
                        )
                        
                        global_x = c['x'] + spore['cx']
                        global_y = c['y'] + spore['cy']
                        
                        if getattr(self, 'get_all_pets', None):
                            for other in self.get_all_pets():
                                if other == self or getattr(other, 'is_egg', False) or other.current_state in ['exiting', 'dragged', 'poisoned', 'burning', 'frozen', 'asleep', 'paralyzed', 'webbed', 'bubbled', 'tk_lifted', 'dragon_fear', 'dragon_flee', 'flying']: continue
                                dx = other.x + other.size_w/2 - global_x
                                dy = other.y + other.size_h/2 - global_y
                                if __import__('math').hypot(dx, dy) < 40:
                                    if hasattr(other, 'interrupt_current_state'): other.interrupt_current_state()
                                    other.current_state = 'asleep'
                                    other.asleep_timer = 600
                                    break
                                    
                    self.window.after(30, lambda: animate_cloud(c))
                
                animate_cloud(cloud)
    def _fsm_asleep(self):
        self.asleep_timer -= 1
        self.v_x_velocity = 0
        gravity = 4.0 if (getattr(self, "rock_type", False) or getattr(self, "steel_type", False)) else 1.5
        self.v_y_velocity += gravity
        self.y += self.v_y_velocity
        
        current_env, _ = self.get_window_environment()
        fall_tolerance = max(15, int(self.v_y_velocity) + 15) if self.v_y_velocity > 0 else 15
        physical_floor = current_env['y'] if self.y <= current_env['y'] + fall_tolerance else self.default_floor_y
        
        if self.y >= physical_floor:
            self.y = physical_floor
            self.v_y_velocity = 0.0
            
        self.update_position()
        
        if self.asleep_timer % 30 == 0:
            if not hasattr(self, 'zzz_particles'): self.zzz_particles = []
            self.zzz_particles.append({'x': self.size_w/2, 'y': self.size_h/2 - 10, 'life': 40})
            
        if hasattr(self, 'zzz_particles'):
            alive_z = []
            for z in self.zzz_particles:
                z['y'] -= 1.5
                z['x'] += math.sin(z['life'] * 0.2) * 2
                z['life'] -= 1
                if z['life'] > 0:
                    alive_z.append(z)
                    x, y = z['x'], z['y']
                    self.canvas.create_line(x-6, y-6, x+6, y-6, fill="white", width=2, tags="effect")
                    self.canvas.create_line(x+6, y-6, x-6, y+6, fill="white", width=2, tags="effect")
                    self.canvas.create_line(x-6, y+6, x+6, y+6, fill="white", width=2, tags="effect")
            self.zzz_particles = alive_z
            
        if self.asleep_timer <= 0:
            if getattr(self, 'is_flying', False):
                self.floor_y = getattr(self, 'target_floor_y', self.y)
                self.current_state = 'ascending'
            else:
                self.current_state = 'idle'
                
        self.schedule_loop(20, self.physics_loop)
