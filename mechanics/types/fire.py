import math
import random
import time

class FireMechanics:
    def check_fire_mechanic(self):
        if not hasattr(self, 'fire_puddles'):
            self.fire_puddles = []
            self.fire_trail_timer = 0
            
        if getattr(self, 'fire_cooldown', 0) == 0 and self.current_state in ['idle', 'walking', 'running'] and random.randint(1, 100) <= 10:
            self.fire_cooldown = self.get_type_cooldown(18000)
            self.fire_trail_timer = 150 
            
        if self.fire_trail_timer > 0:
            self.fire_trail_timer -= 1
            if self.fire_trail_timer % 15 == 0:
                cx, cy = self.x + self.size_w/2, self.y + self.size_h
                
                def draw_fire(c, step=0):
                    c.delete('all')
                    if step > 20: return 
                    
                    colors = ["#FF4500", "#FFA500", "#FFD700"]
                    for i in range(3):
                        w = 8 - i * 2
                        h = 15 - i * 4 + random.randint(-3, 3)
                        offset_x = random.randint(-2, 2)
                        offset_y = random.randint(-2, 2)
                        c.create_rectangle(
                            20 - w + offset_x, 30 - h + offset_y,
                            20 + w + offset_x, 30 + offset_y,
                            fill=colors[i], outline=""
                        )
                    c.after(150, lambda: draw_fire(c, step + 1))
                    
                if hasattr(self, 'spawn_static_vfx'):
                    win = self.spawn_static_vfx(cx - 20, cy - 40, 40, 40, lambda c: draw_fire(c, 0), 4000)
                    
                self.fire_puddles.append({'expires': time.time() + 4, 'x': cx, 'y': cy})
            
        current_time = time.time()
        alive_puddles = []
        for p in self.fire_puddles:
            if current_time < p['expires']:
                alive_puddles.append(p)
        self.fire_puddles = alive_puddles
        
        if getattr(self, 'get_all_pets', None):
            for other in self.get_all_pets():
                if other == self or getattr(other, 'is_egg', False) or other.current_state in ['exiting', 'dragged', 'poisoned', 'burning', 'frozen', 'asleep', 'paralyzed', 'webbed', 'bubbled', 'tk_lifted', 'dragon_fear', 'dragon_flee']: continue
                for p in self.fire_puddles:
                    dx = abs((other.x + other.size_w/2) - p['x'])
                    dy = abs((other.y + other.size_h) - p['y'])
                    if dx < 50 and dy < 25:
                        if hasattr(other, 'interrupt_current_state'): other.interrupt_current_state()
                        other.current_state = 'burning'
                        other.burning_timer = 250
                        break

    def _fsm_burning(self):
        # Pause burning_timer at 1 to handle dissipation phase internally
        if self.burning_timer > 1:
            self.burning_timer -= 1
            self.burn_dissipating = False
        elif self.burning_timer == 1:
            if not getattr(self, 'burn_dissipating', False):
                self.burn_dissipating = True
                self.burn_dissipate_timer = 250 # 5 seconds dissipation
            
            if self.burn_dissipate_timer > 0:
                self.burn_dissipate_timer -= 1
            else:
                self.burning_timer = 0
        
        # Panic running
        if not hasattr(self, 'burn_direction'):
            self.burn_direction = random.choice([-1, 1])
            self.burn_dir_timer = random.randint(10, 30)
            self.is_facing_right = (self.burn_direction == 1)
            
        self.burn_dir_timer -= 1
        if self.burn_dir_timer <= 0:
            self.burn_direction = random.choice([-1, 1])
            self.burn_dir_timer = random.randint(10, 30)
            self.is_facing_right = (self.burn_direction == 1)
            
        speed_mult = 2.0
        if getattr(self, 'burn_dissipating', False):
            # Speed transitions from 2.0 (start of dissipation) to 1.0 (end of dissipation)
            progress = self.burn_dissipate_timer / 250.0
            speed_mult = 1.0 + progress
            
        self.x += self.burn_direction * self.speed * speed_mult
        
        if self.x <= self.v_x:
            self.x = self.v_x
            self.burn_direction = 1
            self.is_facing_right = True
        elif self.x >= self.v_x + self.v_width - self.size_w:
            self.x = self.v_x + self.v_width - self.size_w
            self.burn_direction = -1
            self.is_facing_right = False
        
        if getattr(self, 'is_flying', False):
            # Panic run in the air without falling
            pass
        else:
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
        
        # Manually update animation since we bypass _fsm_active
        if hasattr(self, 'animator'):
            self.animator.update_animation('walking', getattr(self, 'is_facing_right', True), self.canvas_image_id, True, getattr(self, 'frame_rate_active', 60))

        
        # Fire particles floating UP
        if not hasattr(self, 'burn_particles'): self.burn_particles = []
        
        spawn_chance = 40
        if getattr(self, 'burn_dissipating', False):
            # Particle count decreases over 5 seconds
            spawn_chance = int(40 * (self.burn_dissipate_timer / 250.0))
            
        if random.randint(1, 100) <= spawn_chance:
            cx = self.size_w / 2
            cy = self.size_h / 2
            rx = cx + random.randint(-15, 15)
            ry = cy + random.randint(-10, 20)
            
            if getattr(self, 'burn_dissipating', False):
                progress = self.burn_dissipate_timer / 250.0
                # Transition to mainly smoke
                if random.random() > progress:
                    # Smoke colors
                    color = random.choice(["#555555", "#777777", "#999999", "#888888"])
                else:
                    # Fire colors
                    color = random.choice(["#FF4500", "#FFA500", "#FFD700"])
            else:
                color = random.choice(["#FF4500", "#FFA500", "#FFD700"])
                
            pid = self.canvas.create_rectangle(rx-3, ry-3, rx+3, ry+3, fill=color, outline="")
            self.burn_particles.append({'id': pid, 'x': rx, 'y': ry, 'life': 20, 'color': color})
            
        alive = []
        for p in self.burn_particles:
            p['life'] -= 1
            if p['life'] <= 0:
                self.canvas.delete(p['id'])
            else:
                p['y'] -= 4
                p['x'] += random.randint(-2, 2)
                s = 1 + (p['life'] // 5)
                self.canvas.coords(p['id'], p['x']-s, p['y']-s, p['x']+s, p['y']+s)
                alive.append(p)
        self.burn_particles = alive
        
        if self.burning_timer <= 0:
            delattr(self, 'burn_direction')
            if getattr(self, 'burn_dissipating', False):
                self.burn_dissipating = False
                
            for p in self.burn_particles:
                self.canvas.delete(p['id'])
            self.burn_particles = []
            
            if getattr(self, 'is_flying', False):
                self.floor_y = getattr(self, 'target_floor_y', self.y)
                self.current_state = 'ascending'
            else:
                self.current_state = 'idle'
                
        self.schedule_loop(20, self.physics_loop)

