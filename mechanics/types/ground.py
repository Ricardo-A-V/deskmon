import random

class ExcavationMechanics:
    def _fsm_digging_in(self):
        self.dig_step += 1
        desplazamiento = self.dig_step * 3
        if getattr(self, 'gravity_inverted', False):
            self.canvas.coords(self.canvas_image_id, self.size_w//2, (self.size_h//2) - desplazamiento)
        else:
            self.canvas.coords(self.canvas_image_id, self.size_w//2, (self.size_h//2) + desplazamiento)
        
        if self.dig_step % 2 == 0:
            if hasattr(self, 'show_dirt_vfx'):
                self.show_dirt_vfx()
            
        if desplazamiento >= self.size_h // 2 + 10: 
            # Totally hidden under the Canvas limit
            self.current_state = 'digging'
            self.canvas.itemconfig(self.canvas_image_id, state='hidden')
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_digging(self):
        self.dig_timer -= 1
        
        # --- ORGANIC NAVIGATION ---
        if random.randint(1, 1000) <= 20:
            self.is_facing_right = not self.is_facing_right
        
        dig_speed = self.speed * 2

        # FIX: Strict and predictive clamping against sudden window resizing
        if getattr(self, 'anchored_rect', None):
            rect = self.anchored_rect
            
            # 1. Emergency clamping: If the window left it out, we force it inside
            if self.x > rect[2] - self.size_w:
                self.x = rect[2] - self.size_w
                self.is_facing_right = False
            elif self.x < rect[0]:
                self.x = rect[0]
                self.is_facing_right = True
            # 2. Standard predictive check: Bounce before exiting
            else:
                if self.is_facing_right and self.x + dig_speed > rect[2] - self.size_w:
                    self.is_facing_right = False
                elif not self.is_facing_right and self.x - dig_speed < rect[0]:
                    self.is_facing_right = True

        self.x += dig_speed if self.is_facing_right else -dig_speed
        
        if getattr(self, 'ghost_type', False):
            if self.x <= self.v_x - self.size_w: self.x = self.v_x + self.v_width
            elif self.x >= self.v_x + self.v_width: self.x = self.v_x - self.size_w
        else:
            if self.x <= self.v_x:
                self.x = self.v_x
                self.is_facing_right = True
            elif self.x >= (self.v_x + self.v_width) - self.size_w:
                self.x = (self.v_x + self.v_width) - self.size_w
                self.is_facing_right = False
        
        current_env, _ = self.get_window_environment()
        if getattr(self, 'anchored_hwnd', None):
            if not current_env['hwnd'] or current_env['hwnd'] != self.anchored_hwnd:
                self.anchored_hwnd = None
                self.canvas.itemconfig(self.canvas_image_id, state='normal')
                self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
                self.current_state = 'falling'
                self.v_y_velocity = 0.0
                self.update_position()
                self.schedule_loop(30, self.physics_loop)
                return
        
        if getattr(self, 'anchored_hwnd', None):
            self.y = getattr(self, 'anchored_rect', [0, 0, 0, 0])[3] + getattr(self, 'offset_y', 0) if getattr(self, 'gravity_inverted', False) else getattr(self, 'anchored_rect', [0, 0, 0, 0])[1] - self.size_h - getattr(self, 'offset_y', 0)
        else:
            self.y = self.v_y if getattr(self, 'gravity_inverted', False) else self.default_floor_y
        self.floor_y = self.y
        
        if self.dig_timer % 4 == 0:
            if hasattr(self, 'show_dirt_vfx'):
                self.show_dirt_vfx()
            
        if self.dig_timer <= 0:
            self.current_state = 'digging_out'
            self.canvas.itemconfig(self.canvas_image_id, state='normal')
            
        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def _fsm_digging_out(self):
        self.dig_step -= 1
        desplazamiento = self.dig_step * 3
        if getattr(self, 'gravity_inverted', False):
            self.canvas.coords(self.canvas_image_id, self.size_w//2, (self.size_h//2) - desplazamiento)
        else:
            self.canvas.coords(self.canvas_image_id, self.size_w//2, (self.size_h//2) + desplazamiento)
        
        if self.dig_step % 2 == 0:
            if hasattr(self, 'show_dirt_vfx'):
                self.show_dirt_vfx()
            
        if self.dig_step <= 0:
            self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
            self.current_state = 'idle'
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)
