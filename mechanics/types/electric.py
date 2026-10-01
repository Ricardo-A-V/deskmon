import random

class ElectricMechanics:
    def _fsm_paralyzed(self):
        self.para_timer -= 1
        self.v_x_velocity *= 0.95 
        self.x += self.v_x_velocity
        if getattr(self, 'ghost_type', False):
            if self.x <= self.v_x - self.size_w: self.x = self.v_x + self.v_width
            elif self.x >= self.v_x + self.v_width: self.x = self.v_x - self.size_w
        else:
            if self.x <= self.v_x:
                self.x = self.v_x
                self.v_x_velocity *= -0.7 
            elif self.x >= (self.v_x + self.v_width) - self.size_w:
                self.x = (self.v_x + self.v_width) - self.size_w
                self.v_x_velocity *= -0.7

        gravity = 4.0 if (getattr(self, "rock_type", False) or getattr(self, "steel_type", False)) else 1.5
        self.v_y_velocity += gravity
        self.y += self.v_y_velocity
        current_env, _ = self.get_window_environment()
        fall_tolerance = max(15, int(self.v_y_velocity) + 15) if self.v_y_velocity > 0 else 15
        physical_floor = current_env['y'] if self.y <= current_env['y'] + fall_tolerance else self.default_floor_y
        
        if self.y >= physical_floor:
            self.y = physical_floor
            self.v_y_velocity = 0.0
            self.v_x_velocity = 0.0 
            
        self.update_position()
        if self.para_timer <= 0:
            if getattr(self, 'is_flying', False):
                self.floor_y = getattr(self, 'target_floor_y', self.y)
                self.current_state = 'ascending'
            else:
                self.current_state = 'idle'
        self.schedule_loop(20, self.physics_loop)

    def para_vfx_loop(self):
        if getattr(self, 'current_state', '') not in ['paralyzed', 'dragged']: return
        if random.randint(1, 100) <= 50: 
            cx = self.size_w / 2
            cy = self.size_h / 2
            rx = cx + random.randint(-20, 20)
            ry = cy + random.randint(-20, 20)
            self.canvas.create_rectangle(rx-3, ry-3, rx+3, ry+3, fill="#FFFF00", outline="", tags="effect")
            self.canvas.create_rectangle(rx-1, ry-1, rx+1, ry+1, fill="#FFFFFF", outline="", tags="effect")
        self.window.after(100, self.para_vfx_loop)

    def check_electric_mechanic(self):
        if getattr(self, 'current_state', 'exiting') in ['exiting', 'dragged']: return
            
        if not hasattr(self, 'electric_charge'):
            self.electric_charge = 0
            
        if getattr(self, 'electric_cooldown', 0) == 0:
            if getattr(self, 'current_state', 'idle') in ['walking', 'idle']:
                if random.random() < 0.20:
                    self.electric_charge = min(5, self.electric_charge + 1)
                
        if self.electric_charge > 0:
            if random.random() < 0.3:
                cx = self.size_w / 2
                cy = self.size_h / 2
                rx = cx + random.randint(-20, 20)
                ry = cy + random.randint(-20, 20)
                self.canvas.create_rectangle(rx-2, ry-2, rx+2, ry+2, fill="#00FFFF", outline="", tags="effect")
                
        if getattr(self, 'electric_cooldown', 0) == 0 and self.electric_charge >= 5:
            if random.randint(1, 100) <= 10 and getattr(self, 'get_all_pets', None):
                targets = []
                for other in self.get_all_pets():
                    if other == self or getattr(other, 'is_egg', False) or other.current_state in ['exiting', 'dragged', 'poisoned', 'burning', 'frozen', 'asleep', 'paralyzed', 'webbed', 'bubbled', 'tk_lifted', 'dragon_fear', 'dragon_flee']: continue
                    dist = ((other.x - self.x)**2 + (other.y - self.y)**2)**0.5
                    if dist < 1500: 
                        targets.append(other)
                        
                if targets:
                    self.electric_cooldown = self.get_type_cooldown(18000)
                    target = random.choice(targets)
                    self.electric_charge = 0
                    
                    min_x = min(self.x + self.size_w/2, target.x + target.size_w/2) - 50
                    min_y = min(self.y + self.size_h/2, target.y + target.size_h/2) - 50
                    max_x = max(self.x + self.size_w/2, target.x + target.size_w/2) + 50
                    max_y = max(self.y + self.size_h/2, target.y + target.size_h/2) + 50
                    w = max_x - min_x
                    h = max_y - min_y
                    
                    import tkinter as tk
                    win = tk.Toplevel(self.window)
                    win.title("Deskmon_VFX")
                    win.overrideredirect(True)
                    win.attributes("-transparentcolor", "white")
                    win.attributes("-topmost", True)
                    canvas = tk.Canvas(win, bg='white', highlightthickness=0)
                    canvas.pack(fill='both', expand=True)
                    win.geometry(f"{int(w)}x{int(h)}+{int(min_x)}+{int(min_y)}")
                    
                    start_x = (self.x + self.size_w/2) - min_x
                    start_y = (self.y + self.size_h/2) - min_y
                    end_x = (target.x + target.size_w/2) - min_x
                    end_y = (target.y + target.size_h/2) - min_y
                    
                    import math
                    angle = math.atan2(end_y - start_y, end_x - start_x)
                    dist = math.hypot(end_x - start_x, end_y - start_y)
                    
                    # Generate exact Raikou-style fractal lightning points
                    pts = [(start_x, start_y)]
                    curr_dist = 0
                    curr_x, curr_y = start_x, start_y
                    
                    while curr_dist < dist:
                        step = random.uniform(20, 60)
                        if curr_dist + step > dist:
                            step = dist - curr_dist
                        curr_dist += step
                        curr_x += math.cos(angle + random.uniform(-0.8, 0.8)) * step
                        curr_y += math.sin(angle + random.uniform(-0.8, 0.8)) * step
                        if curr_dist >= dist:
                            curr_x, curr_y = end_x, end_y
                        pts.append((curr_x, curr_y))
                        
                    base_pts = [coord for pt in pts for coord in pt]
                    
                    def animate_lightning(step):
                        if step > 6:
                            win.destroy()
                            return
                        canvas.delete('all')
                        new_flat = []
                        for i in range(0, len(base_pts), 2):
                            if i == 0 or i == len(base_pts)-2:
                                new_flat.extend([base_pts[i], base_pts[i+1]])
                            else:
                                new_flat.extend([base_pts[i] + random.uniform(-12, 12), base_pts[i+1] + random.uniform(-12, 12)])
                                
                        new_width = random.choice([3, 5, 7])
                        color = random.choice(["#FFFF00", "#FFD700", "#FFFFFF"])
                        
                        if hasattr(self, '_draw_pixel_line'):
                            self._draw_pixel_line(canvas, new_flat, fill=color, width=new_width)
                        else:
                            canvas.create_line(new_flat, fill=color, width=new_width)
                            
                        win.after(50, lambda: animate_lightning(step + 1))
                        
                    win.after(50, lambda: animate_lightning(0))
                    
                    if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
                    target.current_state = 'paralyzed'
                    target.para_timer = 90
                    if hasattr(target, 'para_vfx_loop'): target.para_vfx_loop()
