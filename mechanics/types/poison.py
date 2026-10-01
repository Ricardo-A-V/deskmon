import random

class PoisonMechanics:
    def check_poison_mechanic(self):
        if not hasattr(self, 'poison_puddles'):
            self.poison_puddles = []
            
        if getattr(self, 'poison_cooldown', 0) == 0 and random.randint(1, 100) <= 10:
            self.poison_cooldown = self.get_type_cooldown(18000)
            
            if self.y >= getattr(self, "default_floor_y", self.y) - 10:
                import tkinter as tk
                win = tk.Toplevel(self.window)
                win.title("Deskmon_VFX")
                win.overrideredirect(True)
                win.attributes("-transparentcolor", "white")
                win.attributes("-topmost", True)
                canvas = tk.Canvas(win, bg='white', highlightthickness=0)
                canvas.pack(fill='both', expand=True)
                
                start_x = self.x + self.size_w/2
                start_y = self.y + self.size_h/2
                
                # Throw sludge bomb in a random direction
                target_x = start_x + random.choice([-1, 1]) * random.randint(150, 400)
                target_x = max(self.v_x + 50, min(target_x, self.v_x + getattr(self, 'v_width', 1920) - 50))
                floor_y = getattr(self, "default_floor_y", self.y) + self.size_h + 15
                
                def create_puddle(px, py):
                    p_win = tk.Toplevel(self.window)
                    p_win.title("Deskmon_VFX")
                    p_win.overrideredirect(True)
                    p_win.attributes("-transparentcolor", "white")
                    p_win.attributes("-topmost", True)
                    p_canvas = tk.Canvas(p_win, bg='white', highlightthickness=0)
                    p_canvas.pack(fill='both', expand=True)
                    p_win.geometry(f"80x40+{int(px - 40)}+{int(py - 40)}")
                    
                    def animate_puddle(step):
                        if not p_win.winfo_exists(): return
                        p_canvas.delete('all')
                        
                        p_canvas.create_rectangle(10, 10, 70, 30, fill="#4B0082", outline="")
                        p_canvas.create_rectangle(5, 15, 75, 25, fill="#4B0082", outline="")
                        p_canvas.create_rectangle(20, 15, 60, 25, fill="#800080", outline="")
                        p_canvas.create_rectangle(25, 10, 55, 30, fill="#800080", outline="")
                        
                        b1_y = 20 - ((step // 2) % 5)
                        b2_y = 15 - (((step // 2)+2) % 6)
                        p_canvas.create_rectangle(30, b1_y, 40, b1_y+5, fill="#9932CC", outline="")
                        p_canvas.create_rectangle(45, b2_y, 50, b2_y+5, fill="#9932CC", outline="")
                        
                        p_win.after(200, lambda: animate_puddle(step + 1))
                        
                    p_win.after(50, lambda: animate_puddle(0))
                    self.window.after(15000, p_win.destroy)
                    
                    self.poison_puddles.append({
                        'x': px, 'y': py, 'life': 450
                    })
                
                def animate_bomb(step):
                    if not win.winfo_exists(): return
                    
                    total_steps = 30
                    if step > total_steps:
                        create_puddle(target_x, floor_y)
                        win.destroy()
                        return
                    
                    t = step / total_steps
                    curr_x = start_x + (target_x - start_x) * t
                    arc = 4 * 100 * t * (1 - t)
                    curr_y = start_y + (floor_y - start_y) * t - arc
                    
                    win.geometry(f"40x40+{int(curr_x - 20)}+{int(curr_y - 20)}")
                    canvas.delete('all')
                    
                    canvas.create_rectangle(10, 10, 30, 30, fill="#800080", outline="")
                    canvas.create_rectangle(5, 15, 35, 25, fill="#800080", outline="")
                    canvas.create_rectangle(15, 5, 25, 35, fill="#800080", outline="")
                    canvas.create_rectangle(12, 12, 28, 28, fill="#4B0082", outline="")
                    
                    for _ in range(3):
                        ox = random.randint(10, 30)
                        oy = random.randint(25, 35)
                        canvas.create_rectangle(ox-2, oy-2, ox+2, oy+2, fill="#9932CC", outline="")
                    
                    win.after(30, lambda: animate_bomb(step + 1))
                    
                animate_bomb(0)
        alive_puddles = []
        for p in self.poison_puddles:
            p['life'] -= 1
            if p['life'] > 0:
                alive_puddles.append(p)
                
        self.poison_puddles = alive_puddles
        
        if getattr(self, 'get_all_pets', None):
            for other in self.get_all_pets():
                if other == self or getattr(other, 'is_egg', False) or other.current_state in ['exiting', 'dragged', 'poisoned', 'burning', 'frozen', 'asleep', 'paralyzed', 'webbed', 'bubbled', 'tk_lifted', 'dragon_fear', 'dragon_flee']: continue
                for p in self.poison_puddles:
                    dx = abs((other.x + other.size_w/2) - p['x'])
                    dy = abs((other.y + other.size_h) - p['y'])
                    if dx < 60 and dy < 25:
                        if hasattr(other, 'interrupt_current_state'): other.interrupt_current_state()
                        other.current_state = 'poisoned'
                        other.poisoned_timer = 450
                        break

    def _fsm_poisoned(self):
        self.poisoned_timer -= 1
        if not hasattr(self, 'poison_direction_timer'):
            self.poison_direction_timer = 0
            
        self.poison_direction_timer -= 1
        if self.poison_direction_timer <= 0:
            self.poison_direction_timer = random.randint(30, 90)
            self.is_facing_right = not self.is_facing_right
            
        direction = 1 if self.is_facing_right else -1
        self.x += direction * self.speed * 0.3
        
        gravity = 4.0 if (getattr(self, "rock_type", False) or getattr(self, "steel_type", False)) else 1.5
        self.v_y_velocity = getattr(self, 'v_y_velocity', 0) + gravity
        self.y += self.v_y_velocity
        
        current_env, _ = self.get_window_environment()
        fall_tolerance = max(15, int(self.v_y_velocity) + 15) if self.v_y_velocity > 0 else 15
        physical_floor = current_env['y'] if self.y <= current_env['y'] + fall_tolerance else self.default_floor_y
        
        if self.y >= physical_floor:
            self.y = physical_floor
            self.v_y_velocity = 0.0
            
        self.update_position()
        
        # Proper floating bubbles
        if not hasattr(self, 'poison_bubbles'): self.poison_bubbles = []
        
        if random.randint(1, 100) <= 20:
            cx = self.size_w / 2
            cy = self.size_h
            rx = cx + random.randint(-int(self.size_w/2), int(self.size_w/2))
            ry = cy - random.randint(10, 40)
            pid1 = self.canvas.create_rectangle(rx-4, ry-4, rx+4, ry+4, fill="#8A2BE2", outline="")
            pid2 = self.canvas.create_rectangle(rx-2, ry-2, rx+2, ry+2, fill="#DDA0DD", outline="")
            self.poison_bubbles.append({'id1': pid1, 'id2': pid2, 'x': rx, 'y': ry, 'life': 40})
            
        alive = []
        for b in self.poison_bubbles:
            b['life'] -= 1
            if b['life'] <= 0:
                self.canvas.delete(b['id1'])
                self.canvas.delete(b['id2'])
            else:
                b['y'] -= 2
                import math
                b['x'] += math.sin(b['life'] * 0.3) * 1.5
                self.canvas.coords(b['id1'], b['x']-4, b['y']-4, b['x']+4, b['y']+4)
                self.canvas.coords(b['id2'], b['x']-2, b['y']-2, b['x']+2, b['y']+2)
                alive.append(b)
        self.poison_bubbles = alive
        
        if self.poisoned_timer <= 0:
            delattr(self, 'poison_direction_timer')
            for b in self.poison_bubbles:
                self.canvas.delete(b['id1'])
                self.canvas.delete(b['id2'])
            self.poison_bubbles = []
            
            if getattr(self, 'is_flying', False):
                self.floor_y = getattr(self, 'target_floor_y', self.y)
                self.current_state = 'ascending'
            else:
                self.current_state = 'idle'
                
        self.schedule_loop(20, self.physics_loop)
