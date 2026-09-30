import random
import math
import tkinter as tk
import time

class UrshifuMechanics:
    def start_urshifu_mechanic(self):
        if getattr(self, 'current_state', '') in ['dragged', 'exiting']: return
        if getattr(self, 'urshifu_cooldown', 0) > 0: return
        if hasattr(self, 'is_global_mechanic_active') and self.is_global_mechanic_active(): return

        name = self.pet_name.lower().replace("_", "").replace("-", "")
        if name not in ["urshifu", "urshifu1"]: return

        self.current_state = 'urshifu_charging'
        self.urshifu_timer = 90 # 3 seconds (30ms * 90 = 2.7s ~ 3s)
        self.urshifu_cooldown = 120000 # 1 hour at 30ms
        self.urshifu_form = name
        
        # single strike = urshifu, rapid strike = urshifu1
        self.urshifu_is_rapid = (name == "urshifu1")
        
        self.urshifu_grab_target = None
        self._find_urshifu_grab_target()

        self._init_urshifu_vfx()
        self.schedule_loop(30, self.physics_loop)

    def _init_urshifu_vfx(self):
        if hasattr(self, 'urshifu_vfx_win') and self.urshifu_vfx_win and self.urshifu_vfx_win.winfo_exists():
            return
            
        self.urshifu_vfx_win = tk.Toplevel(self.window.master)
        self.urshifu_vfx_win.overrideredirect(True)
        self.urshifu_vfx_win.attributes('-topmost', True)
        TRANS_COLOR = '#010101'
        self.urshifu_vfx_win.config(bg=TRANS_COLOR)
        try: self.urshifu_vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass
        self.urshifu_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        
        self.urshifu_canvas = tk.Canvas(self.urshifu_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
        self.urshifu_canvas.pack(fill="both", expand=True)
        self.urshifu_particles = []

    def cancel_urshifu_arts(self):
        if hasattr(self, 'urshifu_vfx_win') and self.urshifu_vfx_win and self.urshifu_vfx_win.winfo_exists():
            self.urshifu_vfx_win.destroy()
            self.urshifu_vfx_win = None
            
        target = getattr(self, 'urshifu_grab_target', None)
        if target and target.current_state in ['urshifu_victim_vibrating', 'tk_controlled']:
            target.current_state = 'falling'
            target.canvas.itemconfig(target.canvas_image_id, state='normal')
            
        for attr in ['urshifu_timer', 'urshifu_grab_target', 'urshifu_is_rapid', 'urshifu_canvas', 'urshifu_particles', 'urshifu_punch_count']:
            if hasattr(self, attr): delattr(self, attr)

        if self.current_state not in ['dragged', 'exiting']:
            self.current_state = 'falling'
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0

    def _find_urshifu_grab_target(self):
        self.urshifu_grab_target = None
        if hasattr(self, 'get_all_pets'):
            valid_targets = [p for p in self.get_all_pets() if p != self and p.current_state not in ['exiting', 'dragged', 'thrown'] and not getattr(p, 'is_egg', False)]
            if valid_targets:
                self.urshifu_grab_target = random.choice(valid_targets)
                self.urshifu_grab_target.current_state = 'tk_controlled'

    def _fsm_urshifu_charging(self):
        self.urshifu_timer -= 1
        
        my_cx = self.x - self.v_x + self.size_w/2
        my_cy = self.y - self.v_y + self.size_h/2
        
        # Generates vertical rectangular particles from the ground (less frequency)
        if self.urshifu_timer % 3 == 0:
            color = "#00BFFF" if self.urshifu_is_rapid else "#FF4500"
            ground_y = my_cy + self.size_h/2
            px = my_cx + random.uniform(-40, 40)
            py = ground_y + random.uniform(-10, 10)
            vy = random.uniform(-6, -2)
            
            self.spawn_urshifu_particle(px, py, 0, vy, 20, color, shape="rect")
            
        self._update_urshifu_vfx()
        
        if self.urshifu_timer <= 0:
            color = "#00BFFF" if self.urshifu_is_rapid else "#FF4500"
            # Small explosion of particles
            for _ in range(40):
                angle = random.uniform(0, 2*math.pi)
                speed = random.uniform(4, 10)
                self.spawn_urshifu_particle(my_cx, my_cy, math.cos(angle)*speed, math.sin(angle)*speed, 15, color, shape="square")
                
            self.current_state = 'urshifu_dashing'
            if not self.urshifu_grab_target:
                self.cancel_urshifu_arts()
            self.schedule_loop(30, self.physics_loop)
            return

        self.schedule_loop(30, self.physics_loop)

    def _fsm_urshifu_dashing(self):
        target = getattr(self, 'urshifu_grab_target', None)
        if not target or target.current_state in ['dragged', 'falling_pokeball', 'exiting']:
            self.cancel_urshifu_arts()
            self.schedule_loop(30, self.physics_loop)
            return

        tx = target.x + getattr(target, 'size_w', 64)/2
        ty = target.y + getattr(target, 'size_h', 64)/2
        
        my_cx = self.x + self.size_w/2
        my_cy = self.y + self.size_h/2
        
        dx = tx - my_cx
        dy = ty - my_cy
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist < 40:
            # Reached target
            if self.urshifu_is_rapid:
                self.current_state = 'urshifu_punching_rapid'
                self.urshifu_timer = 210 # 7 seconds
                self.urshifu_punch_count = 0
            else:
                self.current_state = 'urshifu_punching_single'
                self.urshifu_timer = 90 # 3 seconds vibrating
                
                # Single hit effect (large impact + explosion)
                color = "#FF4500"
                self.spawn_urshifu_impact(my_cx - self.v_x, my_cy - self.v_y, color, large=True)
                
                for _ in range(50):
                    angle = random.uniform(0, 2*math.pi)
                    speed = random.uniform(6, 15)
                    self.spawn_urshifu_particle(my_cx - self.v_x, my_cy - self.v_y, math.cos(angle)*speed, math.sin(angle)*speed, 20, color, shape="square")
                    
                target.current_state = 'urshifu_victim_vibrating'
                
        else:
            target_vx = (dx / dist) * 25.0
            target_vy = (dy / dist) * 25.0
            
            self.v_x_velocity = target_vx
            self.v_y_velocity = target_vy
            
            self.x += self.v_x_velocity
            self.y += self.v_y_velocity
            self.is_facing_right = self.v_x_velocity > 0
            
        self.update_position()
        self._update_urshifu_vfx()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_urshifu_punching_single(self):
        target = getattr(self, 'urshifu_grab_target', None)
        if not target or target.current_state not in ['urshifu_victim_vibrating', 'tk_controlled', 'falling']:
            self.cancel_urshifu_arts()
            self.schedule_loop(30, self.physics_loop)
            return
            
        self.urshifu_timer -= 1
        
        # Vibrate target
        if self.urshifu_timer % 2 == 0:
            target.x += random.randint(-5, 5)
            target.y += random.randint(-5, 5)
            target.update_position()
            
        self._update_urshifu_vfx()
        
        if self.urshifu_timer <= 0:
            # Push far away in the direction of the hit, and slightly upwards
            target.current_state = 'thrown'
            
            # Direction from Urshifu to Target
            dx = (target.x + getattr(target, 'size_w', 64)/2) - (self.x + self.size_w/2)
            direction = 1 if dx >= 0 else -1
            
            if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
            target.v_x_velocity = direction * 120.0
            target.v_y_velocity = -60.0 # Push vertically upwards
            
            self.cancel_urshifu_arts()
            self.schedule_loop(30, self.physics_loop)
            return
            
        self.schedule_loop(30, self.physics_loop)

    def _fsm_urshifu_punching_rapid(self):
        target = getattr(self, 'urshifu_grab_target', None)
        if not target or target.current_state in ['dragged', 'falling_pokeball', 'exiting']:
            self.cancel_urshifu_arts()
            self.schedule_loop(30, self.physics_loop)
            return
            return
            
        self.urshifu_timer -= 1
        
        my_cx = self.x + self.size_w/2
        my_cy = self.y + self.size_h/2
        
        if self.urshifu_timer % 5 == 0:
            self.urshifu_punch_count += 1
            
            # Push towards center to keep them on screen
            center_x = self.v_x + self.v_width / 2
            center_y = self.v_y + self.v_height / 2
            dx_c = center_x - (target.x + getattr(target, 'size_w', 64)/2)
            dy_c = center_y - (target.y + getattr(target, 'size_h', 64)/2)
            angle_to_center = math.atan2(dy_c, dx_c)
            
            # Mix random push with push towards center
            push_angle = random.uniform(0, 2*math.pi)
            if random.random() < 0.4: push_angle = angle_to_center
            
            # Move target slightly (double distance)
            target.x += math.cos(push_angle) * 30.0
            target.y += math.sin(push_angle) * 30.0
            
            # Clamp to screen
            target.x = max(self.v_x + 50, min(self.v_x + self.v_width - 50 - getattr(target, 'size_w', 64), target.x))
            target.y = max(self.v_y + 50, min(self.v_y + self.v_height - 50 - getattr(target, 'size_h', 64), target.y))
            target.update_position()
            
            # Follow target
            tcx = target.x + getattr(target, 'size_w', 64)/2
            tcy = target.y + getattr(target, 'size_h', 64)/2
            self.x = tcx - self.size_w/2 - math.cos(push_angle)*30.0
            self.y = tcy - self.size_h/2 - math.sin(push_angle)*30.0
            self.is_facing_right = math.cos(push_angle) > 0
            self.update_position()
            
            # Punch effect and small explosion
            color = "#00BFFF"
            px, py = self.x - self.v_x + self.size_w/2, self.y - self.v_y + self.size_h/2
            self.spawn_urshifu_impact(px, py, color, large=False)
            
            for _ in range(8):
                ang = random.uniform(0, 2*math.pi)
                spd = random.uniform(2, 6)
                self.spawn_urshifu_particle(px, py, math.cos(ang)*spd, math.sin(ang)*spd, 10, color, shape="square")
            
        self._update_urshifu_vfx()
        
        if self.urshifu_timer <= 0:
            # Last punch pushes further
            center_x = self.v_x + self.v_width / 2
            center_y = self.v_y + self.v_height / 2
            dx_c = center_x - (target.x + getattr(target, 'size_w', 64)/2)
            dy_c = center_y - (target.y + getattr(target, 'size_h', 64)/2)
            push_angle = math.atan2(dy_c, dx_c) # push towards center so they bounce
            
            if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
            target.current_state = 'thrown'
            target.v_x_velocity = math.cos(push_angle) * 100.0
            target.v_y_velocity = math.sin(push_angle) * 100.0
            
            color = "#00BFFF"
            px, py = self.x - self.v_x + self.size_w/2, self.y - self.v_y + self.size_h/2
            self.spawn_urshifu_impact(px, py, color, large=True)
            
            for _ in range(30):
                ang = random.uniform(0, 2*math.pi)
                spd = random.uniform(4, 12)
                self.spawn_urshifu_particle(px, py, math.cos(ang)*spd, math.sin(ang)*spd, 15, color, shape="square")
            
            self.cancel_urshifu_arts()
            self.schedule_loop(30, self.physics_loop)
            return
            
        self.schedule_loop(30, self.physics_loop)
        
    def _fsm_urshifu_victim_vibrating(self):
        # Victim state handled mostly by urshifu, just stay active
        self.schedule_loop(30, self.physics_loop)

    def spawn_urshifu_particle(self, cx, cy, vx, vy, life, color, shape="square"):
        if not hasattr(self, 'urshifu_canvas'): return
        
        if shape == "rect":
            pid = self.urshifu_canvas.create_rectangle(cx-2, cy-10, cx+2, cy+10, fill=color, outline="", tags="urshifu_vfx")
        else:
            size = random.choice([3, 4, 6])
            pid = self.urshifu_canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline="", tags="urshifu_vfx")
            
        self.urshifu_particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': life, 'max_life': life, 'shape': shape})

    def spawn_urshifu_impact(self, cx, cy, color, large=False):
        if not hasattr(self, 'urshifu_canvas'): return
        
        radius_in = 20 if large else 10
        radius_out = 40 if large else 20
        
        inner = self._draw_pixel_circle_bbox(self.urshifu_canvas, cx-radius_in, cy-radius_in, cx+radius_in, cy+radius_in, fill="white", outline="", tags="urshifu_vfx")
        outer = self._draw_pixel_circle_bbox(self.urshifu_canvas, cx-radius_out, cy-radius_out, cx+radius_out, cy+radius_out, outline=color, width=4 if large else 2, tags="urshifu_vfx")
        
        self.urshifu_particles.append({'id': inner, 'type': 'explosion', 'life': 10, 'bbox': (cx-radius_in, cy-radius_in, cx+radius_in, cy+radius_in), 'color': "white", 'large': large})
        self.urshifu_particles.append({'id': outer, 'type': 'explosion_ring', 'life': 10, 'bbox': (cx-radius_out, cy-radius_out, cx+radius_out, cy+radius_out), 'color': color, 'large': large})

    def _update_urshifu_vfx(self):
        if not hasattr(self, 'urshifu_canvas') or not self.urshifu_canvas.winfo_exists(): return
        
        new_parts = []
        for p in self.urshifu_particles:
            p['life'] -= 1
            if p['life'] > 0:
                if p.get('type') == 'explosion':
                    b = p['bbox']
                    expand = 4 if p.get('large') else 2
                    p['bbox'] = (b[0]-expand, b[1]-expand, b[2]+expand, b[3]+expand)
                    self.urshifu_canvas.delete(p['id'])
                    p['id'] = self._draw_pixel_circle_bbox(self.urshifu_canvas, *p['bbox'], fill=p['color'], outline="", tags="urshifu_vfx")
                    new_parts.append(p)
                elif p.get('type') == 'explosion_ring':
                    b = p['bbox']
                    expand = 6 if p.get('large') else 3
                    width = 4 if p.get('large') else 2
                    p['bbox'] = (b[0]-expand, b[1]-expand, b[2]+expand, b[3]+expand)
                    self.urshifu_canvas.delete(p['id'])
                    p['id'] = self._draw_pixel_circle_bbox(self.urshifu_canvas, *p['bbox'], outline=p['color'], width=width, tags="urshifu_vfx")
                    new_parts.append(p)
                else:
                    self.urshifu_canvas.move(p['id'], p['vx'], p['vy'])
                    new_parts.append(p)
            else:
                self.urshifu_canvas.delete(p['id'])
        self.urshifu_particles = new_parts
