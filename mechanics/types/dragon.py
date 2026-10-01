import random

class DragonMechanics:
    def check_dragon_mechanic(self):
        if getattr(self, 'current_state', 'exiting') in ['exiting', 'dragged', 'dragon_fear', 'dragon_flee', 'webbed']:
            return

        if getattr(self, 'dragon_cooldown', 0) == 0 and random.randint(1, 100) <= 10:
            self.dragon_cooldown = self.get_type_cooldown(18000)
            self._do_dragon_roar()

    def _do_dragon_roar(self):
        if getattr(self, 'current_state', 'exiting') == 'exiting': return
        
        import tkinter as tk
        win = tk.Toplevel(self.window)
        win.title("Deskmon_VFX")
        win.overrideredirect(True)
        win.attributes("-transparentcolor", "white")
        win.attributes("-topmost", True)
        canvas = tk.Canvas(win, bg='white', highlightthickness=0)
        canvas.pack(fill='both', expand=True)
        
        wx = self.x + self.size_w/2 - 200
        wy = self.y + self.size_h/2 - 200
        win.geometry(f"400x400+{int(wx)}+{int(wy)}")
        
        def animate_roar(step):
            if step > 12:
                win.destroy()
                return
            canvas.delete('all')
            r = 20 + step * 15
            coords = [
                200 - r*0.4, 200 - r, 200 + r*0.4, 200 - r, 200 + r, 200 - r*0.4, 200 + r, 200 + r*0.4,
                200 + r*0.4, 200 + r, 200 - r*0.4, 200 + r, 200 - r, 200 + r*0.4, 200 - r, 200 - r*0.4
            ]
            canvas.create_polygon(coords, outline='#8A2BE2', fill='', width=6)
            if step > 2:
                r2 = r - 30
                coords2 = [
                    200 - r2*0.4, 200 - r2, 200 + r2*0.4, 200 - r2, 200 + r2, 200 - r2*0.4, 200 + r2, 200 + r2*0.4,
                    200 + r2*0.4, 200 + r2, 200 - r2*0.4, 200 + r2, 200 - r2, 200 + r2*0.4, 200 - r2, 200 - r2*0.4
                ]
                canvas.create_polygon(coords2, outline='#BA55D3', fill='', width=4)
                
            self.window.after(40, lambda: animate_roar(step + 1))
            
        self.window.after(50, lambda: animate_roar(0))
            
        if getattr(self, 'get_all_pets', None):
            for other in self.get_all_pets():
                if other == self or getattr(other, 'is_egg', False) or other.current_state in ['exiting', 'dragged', 'poisoned', 'burning', 'frozen', 'asleep', 'paralyzed', 'webbed', 'bubbled', 'tk_lifted', 'dragon_fear', 'dragon_flee']: continue
                
                dist = ((other.x - self.x)**2 + (other.y - self.y)**2)**0.5
                if dist < 400:
                    if hasattr(other, 'interrupt_current_state'): other.interrupt_current_state()
                    other.current_state = 'dragon_fear'
                    other.dragon_fear_timer = 60

    def _fsm_dragon_fear(self):
        self.dragon_fear_timer -= 1
        self.x += random.choice([-2, 2])
        self.y += random.choice([-2, 2])
        self.update_position()
        if hasattr(self, 'animator'):
            self.animator.update_animation('walking', getattr(self, 'is_facing_right', True), self.canvas_image_id, True, getattr(self, 'frame_rate_active', 60))
        
        if self.dragon_fear_timer <= 0:
            self.current_state = 'dragon_flee'
            self.dragon_flee_timer = 60
        self.schedule_loop(30, self.physics_loop)
        
    def _fsm_dragon_flee(self):
        self.dragon_flee_timer -= 1
        if not hasattr(self, 'flee_direction'):
            self.flee_direction = random.choice([-1, 1])
            self.is_facing_right = (self.flee_direction == 1)
            
        # Slower speed
        self.x += self.flee_direction * self.speed * 1.5
        
        if getattr(self, 'is_flying', False):
            pass
        else:
            gravity = 4.0 if (getattr(self, "rock_type", False) or getattr(self, "steel_type", False)) else 1.5
            self.v_y_velocity = getattr(self, 'v_y_velocity', 0) + gravity
        
        # Screen edge jump
        if self.x <= self.v_x:
            self.x = self.v_x
            if self.y >= getattr(self, "default_floor_y", self.y) - 15:
                self.v_y_velocity = -12.0
        elif self.x >= self.v_x + getattr(self, 'v_width', 1920) - self.size_w:
            self.x = self.v_x + getattr(self, 'v_width', 1920) - self.size_w
            if self.y >= getattr(self, "default_floor_y", self.y) - 15:
                self.v_y_velocity = -12.0
                
        self.y += self.v_y_velocity
        
        current_env, _ = self.get_window_environment()
        fall_tolerance = max(15, int(self.v_y_velocity) + 15) if self.v_y_velocity > 0 else 15
        physical_floor = current_env['y'] if self.y <= current_env['y'] + fall_tolerance else self.default_floor_y
        
        if self.y >= physical_floor:
            self.y = physical_floor
            self.v_y_velocity = 0.0
            
        self.update_position()
        if hasattr(self, 'animator'):
            self.animator.update_animation('walking', getattr(self, 'is_facing_right', True), self.canvas_image_id, True, getattr(self, 'frame_rate_active', 60))
        
        if self.dragon_flee_timer <= 0:
            delattr(self, 'flee_direction')
            if getattr(self, 'is_flying', False):
                self.floor_y = getattr(self, 'target_floor_y', self.y)
                self.current_state = 'ascending'
            else:
                self.current_state = 'idle'
                
        self.schedule_loop(20, self.physics_loop)
