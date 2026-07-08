import random
import math
import os

class DarkArtsMechanics:
    def cancel_dark_arts(self):
        self.dark_mode = False
        self.canvas.itemconfig(self.canvas_image_id, state='normal')
        self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
        try: self.window.attributes('-alpha', 1.0)
        except: pass
        
        # Only change to falling if not being dragged in this exact millisecond
        if self.current_state not in ['dragged', 'exiting']:
            self.current_state = 'falling'
        
        target = getattr(self, 'dark_target', None)
        self.dark_target = None # Prevent infinite recursion
        if target and target.window.winfo_exists():
            target.dark_master = None 
            target.canvas.itemconfig(target.canvas_image_id, state='normal')
            target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
            try: target.window.attributes('-alpha', 1.0)
            except: pass
            if target.current_state not in ['dragged', 'exiting']:
                target.current_state = 'falling'
            
        master = getattr(self, 'dark_master', None)
        self.dark_master = None 
        if master and master.window.winfo_exists():
            master.cancel_dark_arts()

    def _fsm_dark_victim_frozen(self):
        self.schedule_loop(50, self.physics_loop) 

    def _fsm_dark_dash(self):
        target = getattr(self, 'dark_target', None)
        if not target or target.current_state != 'dark_victim_frozen' or not target.window.winfo_exists():
            self.cancel_dark_arts()
            self.schedule_loop(30, self.physics_loop) 
            return

        self.is_facing_right = (target.x > self.x)
        dist_x = abs(self.x - target.x)
        dist_y = target.y - self.y
        dash_speed = self.speed * 4
        
        if dist_x > dash_speed:
            self.x += dash_speed if self.is_facing_right else -dash_speed
            # FIX: Mathematical interpolation. Y axis advances proportionally to X axis.
            self.y += (dist_y / dist_x) * dash_speed
        else:
            self.x = target.x 
            self.y = target.y 
            self.current_state = 'dark_sink'
            target.current_state = 'dark_victim_sink'
            self.dark_step = 0
            target.dark_step = 0
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_dark_sink(self):
        self.dark_step += 1
        displacement = self.dark_step * 5
        
        # FIX: Reverse visual direction to hide in the ceiling
        if getattr(self, 'gravity_inverted', False):
            self.canvas.coords(self.canvas_image_id, self.size_w//2, (self.size_h//2) - displacement)
        else:
            self.canvas.coords(self.canvas_image_id, self.size_w//2, (self.size_h//2) + displacement)
            
        if displacement >= self.size_h // 2 + 10:
            self.current_state = 'dark_hidden'
            self.canvas.itemconfig(self.canvas_image_id, state='hidden')
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_dark_victim_sink(self):
        self.dark_step += 1
        displacement = self.dark_step * 5
        
        if getattr(self, 'gravity_inverted', False):
            self.canvas.coords(self.canvas_image_id, self.size_w//2, (self.size_h//2) - displacement)
        else:
            self.canvas.coords(self.canvas_image_id, self.size_w//2, (self.size_h//2) + displacement)
            
        if displacement >= self.size_h // 2 + 10:
            self.current_state = 'dark_victim_hidden'
            self.canvas.itemconfig(self.canvas_image_id, state='hidden')
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_dark_victim_hidden(self):
        self.schedule_loop(50, self.physics_loop) 

    def _fsm_dark_hidden(self):
        target = getattr(self, 'dark_target', None)
        if not target or not target.window.winfo_exists() or target.current_state not in ['dark_victim_sink', 'dark_victim_hidden']:
            self.cancel_dark_arts()
            self.schedule_loop(30, self.physics_loop) 
            return

        if target.current_state == 'dark_victim_sink':
            self.schedule_loop(30, self.physics_loop)
            return

        if not getattr(self, 'dark_timer_started', False):
            self.dark_timer = 20 
            self.dark_timer_started = True

        self.dark_timer -= 1
        if self.dark_timer <= 0:
            self.dark_timer_started = False
            
            self.x = random.randint(self.v_x + 50, self.v_x + self.v_width - self.size_w - 50)
            
            # FIX: The scanner starts from the opposite side of the screen depending on gravity
            self.y = self.default_floor_y if getattr(self, 'gravity_inverted', False) else self.v_y 
            current_env, _ = self.get_window_environment()
            
            if current_env['hwnd']:
                self.anchored_hwnd = current_env['hwnd']
                self.anchored_rect = current_env['rect']
                if getattr(self, 'gravity_inverted', False):
                    self.floor_y = self.anchored_rect[3] + getattr(self, 'offset_y', 0)
                else:
                    self.floor_y = self.anchored_rect[1] - self.size_h - getattr(self, 'offset_y', 0)
            else:
                self.anchored_hwnd = None
                self.anchored_rect = None
                self.floor_y = self.v_y if getattr(self, 'gravity_inverted', False) else self.default_floor_y
            
            self.y = self.floor_y
            self.is_facing_right = random.choice([True, False])
            
            target.anchored_hwnd = self.anchored_hwnd
            target.anchored_rect = getattr(self, 'anchored_rect', None)
            target.floor_y = self.floor_y
            target.y = target.floor_y
            
            if self.is_facing_right:
                target.x = self.x + self.size_w - 20
                target.is_facing_right = False
            else:
                target.x = self.x - target.size_w + 20
                target.is_facing_right = True
            
            self.current_state = 'dark_emerge'
            target.current_state = 'dark_victim_emerge'
            self.dark_step = (self.size_h // 2 + 10) // 4
            target.dark_step = (target.size_h // 2 + 10) // 4
            
            self.canvas.itemconfig(self.canvas_image_id, state='normal')
            target.canvas.itemconfig(target.canvas_image_id, state='normal')
            self.dark_alpha = 0.0
            target.dark_alpha = 0.0
            
        self.update_position()
        if target: target.update_position()
        self.schedule_loop(50, self.physics_loop)

    def _fsm_dark_emerge(self):
        target = getattr(self, 'dark_target', None)
        if not target or not target.window.winfo_exists() or target.current_state not in ['dark_victim_emerge', 'thrown', 'falling']:
            self.cancel_dark_arts()
            self.schedule_loop(30, self.physics_loop) 
            return

        if self.dark_step > 0:
            self.dark_step -= 1
            displacement = self.dark_step * 4
            
            if getattr(self, 'gravity_inverted', False):
                self.canvas.coords(self.canvas_image_id, self.size_w//2, (self.size_h//2) - max(0, displacement))
            else:
                self.canvas.coords(self.canvas_image_id, self.size_w//2, (self.size_h//2) + max(0, displacement))
            
            self.dark_alpha = min(0.7, self.dark_alpha + 0.05)
            try: self.window.attributes('-alpha', self.dark_alpha)
            except: pass
        
        if self.dark_step <= 0:
            self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
            
            if target.current_state == 'dark_victim_emerge' and target.dark_step > 0:
                self.schedule_loop(30, self.physics_loop)
                return
                
            self.current_state = 'dark_throw'
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_dark_victim_emerge(self):
        if self.dark_step > 0:
            self.dark_step -= 1
            displacement = self.dark_step * 4
            
            if getattr(self, 'gravity_inverted', False):
                self.canvas.coords(self.canvas_image_id, self.size_w//2, (self.size_h//2) - max(0, displacement))
            else:
                self.canvas.coords(self.canvas_image_id, self.size_w//2, (self.size_h//2) + max(0, displacement))
            
            self.dark_alpha = min(1.0, self.dark_alpha + 0.05)
            try: self.window.attributes('-alpha', self.dark_alpha)
            except: pass
        
        if self.dark_step <= 0:
            self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_dark_throw(self):
        target = getattr(self, 'dark_target', None)
        self.dark_mode = False
        try: self.window.attributes('-alpha', 1.0)
        except: pass
        self.current_state = 'idle'
        self.dark_target = None
        
        if target and target.window.winfo_exists():
            target.dark_master = None
            try: target.window.attributes('-alpha', 1.0)
            except: pass
            
            target.current_state = 'thrown'
            push_dir = 1 if self.is_facing_right else -1
            
            target.v_x_velocity = push_dir * random.uniform(40.0, 60.0)
            # FIX: Parametric inversion of the throw (towards the room floor)
            if getattr(self, 'gravity_inverted', False):
                target.v_y_velocity = random.uniform(20.0, 30.0) 
            else:
                target.v_y_velocity = random.uniform(-20.0, -30.0) 
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

