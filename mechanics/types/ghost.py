import random

class GhostMechanics:
    def schedule_glitch_teleport(self):
        if not getattr(self, 'is_glitching', False) or self.current_state == 'exiting':
            return
            
        # If the user grabs it or it is involved in telekinesis, we pause the jumps
        if self.current_state in ['dragged', 'tk_controlled', 'tk_lifted']:
            self.schedule_loop(500, self.schedule_glitch_teleport)
            return
            
        if getattr(self, 'glitch_teleports_left', 0) > 0:
            self.glitch_teleports_left -= 1
            
            # Chaotic teleportation: New X coordinate
            self.x = random.randint(self.v_x, self.v_x + self.v_width - self.size_w)
            
            if getattr(self, 'is_flying', False):
                self.y = random.randint(self.v_y, self.default_floor_y)
                self.floor_y = self.y
            else:
                self.y = self.default_floor_y if getattr(self, 'gravity_inverted', False) else self.v_y 
                current_env, _ = self.get_window_environment()
                
                if current_env['hwnd']:
                    self.anchored_hwnd = current_env['hwnd']
                    self.anchored_rect = current_env['rect']
                    self.floor_y = current_env['y']
                    self.y = self.floor_y
                else:
                    self.anchored_hwnd = None
                    self.anchored_rect = None
                    self.floor_y = self.v_y if getattr(self, 'gravity_inverted', False) else self.default_floor_y
                    self.y = self.floor_y
                
            self.update_position()
            
            # Schedule the next interference between 1.5 and 3 seconds
            self.schedule_loop(random.randint(1500, 3000), self.schedule_glitch_teleport)
        else:
            # End of phase
            self.is_glitching = False
            self.has_genesect_glitch = False
            self.ghost_cooldown = self.get_type_cooldown(18000)
            try: self.window.attributes('-alpha', 1.0)
            except: pass
