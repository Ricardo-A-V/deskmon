import math
import random

class IceMechanics:
    def check_ice_mechanic(self):
        if getattr(self, 'current_state', 'exiting') in ['exiting', 'dragged']: return
        
        if getattr(self, 'ice_cooldown', 0) == 0 and getattr(self, 'get_all_pets', None) and random.randint(1, 100) <= 10:
            target = None
            for other in self.get_all_pets():
                if other == self or getattr(other, 'is_egg', False) or other.current_state in ['exiting', 'dragged', 'poisoned', 'burning', 'frozen', 'asleep', 'paralyzed', 'webbed', 'bubbled', 'tk_lifted', 'dragon_fear', 'dragon_flee']: continue
                dist = math.hypot((other.x + other.size_w/2) - (self.x + self.size_w/2), (other.y + other.size_h/2) - (self.y + self.size_h/2))
                if dist < 600: 
                    target = other
                    break
            
            if target:
                self.ice_cooldown = self.get_type_cooldown(18000)
                def shoot_ice(x, y, tx, ty, steps_left=15, win=None, canvas=None, step_anim=0):
                    if getattr(self, 'current_state', 'exiting') == 'exiting':
                        if win: win.destroy()
                        return
                    if win is None:
                        import tkinter as tk
                        win = tk.Toplevel(self.window)
                        win.title("Deskmon_VFX")
                        win.overrideredirect(True)
                        win.attributes("-transparentcolor", "white")
                        win.attributes("-topmost", True)
                        canvas = tk.Canvas(win, bg='white', highlightthickness=0)
                        canvas.pack(fill='both', expand=True)
                        win.geometry(f"120x120+{int(x-60)}+{int(y-60)}")
                    
                    if steps_left <= 0:
                        if win: win.destroy()
                        if getattr(target, 'current_state', 'exiting') not in ['exiting', 'dragged']:
                            if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
                            target.current_state = 'frozen'
                            target.frozen_timer = 150
                            if hasattr(target, 'frozen_cube_loop'): target.frozen_cube_loop()
                        return
                        
                    canvas.delete('all')
                    colors = ["#00FFFF", "#87CEFA", "#FFFFFF", "#E0FFFF", "#00BFFF"]
                    
                    # Core
                    canvas.create_rectangle(45, 45, 75, 75, fill="#FFFFFF", outline="#00FFFF", width=4)
                    
                    for i in range(6):
                        angle = step_anim * 0.4 + (i * (2 * math.pi / 8))
                        dist = 20 + math.sin(step_anim * 0.3 + i) * 10
                        px = 60 + math.cos(angle) * dist
                        py = 60 + math.sin(angle) * dist
                        size = random.randint(6, 12)
                        canvas.create_polygon(
                            px, py-size, px+size, py, px, py+size, px-size, py,
                            fill=colors[i % len(colors)], outline="#00BFFF", width=2
                        )
                        

                    
                    nx = x + (tx - x) / steps_left
                    ny = y + (ty - y) / steps_left
                    win.geometry(f"120x120+{int(nx-60)}+{int(ny-60)}")
                    self.window.after(30, lambda: shoot_ice(nx, ny, tx, ty, steps_left - 1, win, canvas, step_anim + 1))
                
                shoot_ice(self.x + self.size_w/2, self.y + self.size_h/2, target.x + target.size_w/2, target.y + target.size_h/2)

    def _fsm_frozen(self):
        if getattr(self, 'current_state', 'exiting') == 'exiting': return
        
        if getattr(self, 'frozen_timer', 0) > 0:
            self.frozen_timer -= 1
            self.v_x_velocity = 0
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
            self.schedule_loop(20, self.physics_loop)
        else:
            self.canvas.delete('vfx_frozen_cube')
            if getattr(self, 'is_flying', False):
                self.floor_y = getattr(self, 'target_floor_y', self.y)
                self.current_state = 'ascending'
            else:
                self.current_state = 'idle'
            self.schedule_loop(20, self.physics_loop)

    def frozen_cube_loop(self):
        if getattr(self, 'current_state', '') not in ['frozen', 'dragged']:
            self.canvas.delete('vfx_frozen_cube')
            return
            
        self.canvas.delete('vfx_frozen_cube')
        cx = self.size_w / 2
        cy = self.size_h / 2
        s = min(self.size_w, self.size_h) / 2
        self.canvas.create_rectangle(cx-s, cy-s, cx+s, cy+s, outline="cyan", width=4, stipple="gray50", tags='vfx_frozen_cube')
        self.canvas.create_rectangle(cx-s-2, cy-s-2, cx+s+2, cy+s+2, outline="white", width=1, tags='vfx_frozen_cube')
        
        self.window.after(100, self.frozen_cube_loop)
