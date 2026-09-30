import os
import math
import random
import tkinter as tk

class MewMechanics:
    def cancel_mew_arts(self):
        if hasattr(self, 'mew_vfx_win') and self.mew_vfx_win and self.mew_vfx_win.winfo_exists():
            self.mew_vfx_win.destroy()
            self.mew_vfx_win = None

        for victim in getattr(self, 'mew_victims', []):
            if victim.window.winfo_exists() and getattr(victim, 'current_state', '') == 'mew_tethered':
                # Force gravity drop for victims instead of teleports
                if hasattr(victim, 'interrupt_current_state'): victim.interrupt_current_state()
                victim.current_state = 'thrown'
                victim.surface_angle = 0
                victim.mew_master = None

        for attr in ['mew_timer', 'mew_phase', 'mew_vx', 'mew_vy', 'mew_victims', 'mew_orbit_particles', 'mew_trail_particles']:
            if hasattr(self, attr): delattr(self, attr)

        self.surface_angle = 0

        if self.current_state not in ['dragged', 'exiting']:
            # Forcing ballistic physics drops Mew exactly from the popping coordinate
            self.current_state = 'thrown'
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            self.schedule_loop(50, self.physics_loop)

    def trigger_mew_arts(self):
        self._setup_mew_vfx_layer()
        self.mew_phase = 0
        self.mew_timer = 90 
        self.mew_trail_particles = []
        
        self.mew_orbit_particles = []
        for _ in range(25): 
            self.mew_orbit_particles.append({
                'angle': random.uniform(0, 2 * math.pi),
                'dist': random.uniform(80, 180),
                'size': random.randint(2, 5),
                'speed_mod': random.uniform(0.8, 1.2)
            })

        self.mew_victims = []
        self.current_state = 'mew_channeling'
        self.v_x_velocity = 0.0
        self.v_y_velocity = 0.0
        self.schedule_loop(30, self.physics_loop)

    def _setup_mew_vfx_layer(self):
        if hasattr(self, 'mew_vfx_win') and self.mew_vfx_win and self.mew_vfx_win.winfo_exists():
            self.mew_vfx_canvas.delete("all")
            return
            
        self.mew_vfx_win = tk.Toplevel(self.window.master)
        self.mew_vfx_win.title("VFX_Mew")
        self.mew_vfx_win.overrideredirect(True)
        self.mew_vfx_win.attributes('-topmost', True)
        
        TRANS = '#010101'
        self.mew_vfx_win.config(bg=TRANS)
        try: self.mew_vfx_win.wm_attributes('-transparentcolor', TRANS)
        except: pass
        
        self.mew_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.mew_vfx_win.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x00080000 | 0x00000020)
        except: pass

        self.mew_vfx_canvas = tk.Canvas(self.mew_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS, highlightthickness=0)
        self.mew_vfx_canvas.pack()

    def _fsm_mew_channeling(self):
        self.mew_timer -= 1
        
        self.fly_amplitude = getattr(self, 'fly_amplitude', 0) + 0.1
        self.y += math.sin(self.fly_amplitude) * 2.0
        
        if not hasattr(self, 'mew_vfx_canvas') or not self.mew_vfx_canvas: return
        self.mew_vfx_canvas.delete("mew_orbit")
        
        abs_cx = self.x - self.v_x + self.size_w / 2
        abs_cy = self.y - self.v_y + self.size_h / 2
        
        progress = 1.0 - (self.mew_timer / 90.0)
        # Polynomial formula for extreme acceleration curve
        base_angular_velocity = 0.02 + (progress ** 4) * 1.5 
        
        for p in self.mew_orbit_particles:
            p['angle'] += base_angular_velocity * p['speed_mod']
            current_dist = p['dist'] * (1.0 - progress * 0.7) 
            
            px = abs_cx + math.cos(p['angle']) * current_dist
            py = abs_cy + math.sin(p['angle']) * current_dist
            
            color = random.choice(["#FF69B4", "#FFB6C1", "#FFFFFF", "#FF1493"])
            self.mew_vfx_canvas.create_rectangle(px-p['size'], py-p['size'], px+p['size'], py+p['size'], fill=color, outline="", tags="mew_orbit")
        
        if self.mew_timer <= 0:
            self.mew_vfx_canvas.delete("mew_orbit")
            self.mew_phase = 1
            self.mew_timer = 1200 
            self.current_state = 'mew_bounce'
            
            angle = random.uniform(0, 2 * math.pi)
            speed = 10.0
            self.mew_vx = math.cos(angle) * speed
            self.mew_vy = math.sin(angle) * speed
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_mew_bounce(self):
        self.mew_timer -= 1
        
        self.x += self.mew_vx
        self.y += self.mew_vy
        
        # Smooth inner rotation
        self.surface_angle = (getattr(self, 'surface_angle', 0) + 2) % 360
        
        hit_wall = False
        if self.x <= self.v_x:
            self.x = self.v_x
            self.mew_vx *= -1
            hit_wall = True
        elif self.x >= (self.v_x + self.v_width) - self.size_w:
            self.x = (self.v_x + self.v_width) - self.size_w
            self.mew_vx *= -1
            hit_wall = True
            
        if self.y <= self.v_y:
            self.y = self.v_y
            self.mew_vy *= -1
            hit_wall = True
        elif self.y >= (self.v_y + self.v_height) - self.size_h:
            self.y = (self.v_y + self.v_height) - self.size_h
            self.mew_vy *= -1
            hit_wall = True
            
        self.is_facing_right = (self.mew_vx > 0)
        
        abs_cx = self.x - self.v_x + self.size_w / 2
        abs_cy = self.y - self.v_y + self.size_h / 2
        bubble_radius = max(self.size_w, self.size_h) * 0.6
        
        if hasattr(self, 'mew_vfx_canvas'):
            self.mew_vfx_canvas.delete("mew_master_bubble")
            
            # Vectorial Hollow Bubble rendering bypasses PIL Chroma Key Opacity restrictions
            self._draw_pixel_circle_bbox(self.mew_vfx_canvas, abs_cx-bubble_radius, abs_cy-bubble_radius, abs_cx+bubble_radius, abs_cy+bubble_radius, outline="#FF69B4", width=4, tags="mew_master_bubble")
            self._draw_pixel_circle_bbox(self.mew_vfx_canvas, abs_cx-bubble_radius+4, abs_cy-bubble_radius+4, abs_cx+bubble_radius-4, abs_cy+bubble_radius-4, outline="#FFB6C1", width=1, tags="mew_master_bubble")
            
            # Simulated gloss reflections
            self.mew_vfx_canvas.create_arc(abs_cx-bubble_radius+10, abs_cy-bubble_radius+10, abs_cx+bubble_radius-10, abs_cy+bubble_radius-10, start=45, extent=45, outline="#FFFFFF", width=3, style=tk.ARC, tags="mew_master_bubble")
            self.mew_vfx_canvas.create_arc(abs_cx-bubble_radius+10, abs_cy-bubble_radius+10, abs_cx+bubble_radius-10, abs_cy+bubble_radius-10, start=225, extent=20, outline="#FFFFFF", width=2, style=tk.ARC, tags="mew_master_bubble")

            if self.mew_timer % 3 == 0:
                self.mew_trail_particles.append({
                    'x': abs_cx + random.uniform(-bubble_radius/2, bubble_radius/2),
                    'y': abs_cy + random.uniform(-bubble_radius/2, bubble_radius/2),
                    'size': random.randint(4, 10),
                    'life': 20
                })
                
            self._process_mew_trail()
        
        # Collision scan - Fixed exclusion parameter to capture victims regardless of Mew's global lock
        if getattr(self, 'get_all_pets', None):
            for p in self.get_all_pets():
                if p != self and p not in self.mew_victims and p.current_state not in ['exiting', 'dragged', 'mew_tethered']:
                    if not getattr(p, 'is_egg', False):
                        dist = math.hypot((self.x + self.size_w/2) - (p.x + p.size_w/2), (self.y + self.size_h/2) - (p.y + p.size_h/2))
                        if dist < max(self.size_w, self.size_h) * 1.5: 
                            self._capture_mew_victim(p)
                            
        self._update_mew_tethers()
        
        if self.mew_timer <= 0:
            self._execute_mew_pop()
            self.cancel_mew_arts()
            return

        self.update_position()
        self.schedule_loop(30, self.physics_loop)
        
    def _process_mew_trail(self):
        if not hasattr(self, 'mew_vfx_canvas') or not self.mew_vfx_canvas: return
        self.mew_vfx_canvas.delete("mew_trail")
        
        alive = []
        for t in self.mew_trail_particles:
            t['life'] -= 1
            t['size'] *= 0.9 
            if t['life'] > 0:
                self.mew_vfx_canvas.create_rectangle(t['x']-t['size'], t['y']-t['size'], t['x']+t['size'], t['y']+t['size'], outline="#FF69B4", width=2, tags="mew_trail")
                alive.append(t)
        self.mew_trail_particles = alive

    def _capture_mew_victim(self, target):
        if target.current_state.startswith('dark_') and hasattr(target, 'cancel_dark_arts'): target.cancel_dark_arts()
        if target.current_state.startswith('mewtwo_') and hasattr(target, 'cancel_mewtwo_arts'): target.cancel_mewtwo_arts()
        if target.current_state == 'bubbled': 
            if hasattr(target, 'manage_bubble_vfx'): target.manage_bubble_vfx(False)
            if hasattr(target, 'show_bubble_burst_vfx'): target.show_bubble_burst_vfx()
        if target.current_state in ['digging_in', 'digging', 'digging_out']:
            target.canvas.itemconfig(target.canvas_image_id, state='normal')
            target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
            
        if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
        target.current_state = 'mew_tethered'
        target.mew_master = self
        target.anchored_hwnd = None
        target.v_x_velocity = 0.0
        target.v_y_velocity = 0.0
        
        target.mew_tether_angle = random.uniform(0, 2 * math.pi)
        target.mew_tether_length = random.uniform(150, 300)
        
        self.mew_victims.append(target)
        
    def _update_mew_tethers(self):
        if not hasattr(self, 'mew_vfx_canvas') or not self.mew_vfx_canvas: return
        self.mew_vfx_canvas.delete("mew_tether")
        self.mew_vfx_canvas.delete("mew_victim_bubble")
        
        abs_mx = self.x + self.size_w / 2
        abs_my = self.y + self.size_h / 2
        
        active_victims = []
        for victim in self.mew_victims:
            if victim.window.winfo_exists() and getattr(victim, 'current_state', '') == 'mew_tethered':
                
                victim.mew_tether_angle += 0.02
                target_x = abs_mx + math.cos(victim.mew_tether_angle) * victim.mew_tether_length - victim.size_w / 2
                target_y = abs_my + math.sin(victim.mew_tether_angle) * victim.mew_tether_length - victim.size_h / 2
                
                victim.x += (target_x - victim.x) * 0.2
                victim.y += (target_y - victim.y) * 0.2
                
                victim.surface_angle = (getattr(victim, 'surface_angle', 0) + 5) % 360
                victim.update_position()
                
                vfx_mx = abs_mx - self.v_x
                vfx_my = abs_my - self.v_y
                vfx_vx = victim.x + victim.size_w / 2 - self.v_x
                vfx_vy = victim.y + victim.size_h / 2 - self.v_y
                
                # --- DNA TETHER GENERATION MATRIX ---
                # Calculates direct spatial vector to align the sine wave projection
                dx = vfx_vx - vfx_mx
                dy = vfx_vy - vfx_my
                dist = math.hypot(dx, dy)
                
                if dist > 0:
                    angle = math.atan2(dy, dx)
                    perp_angle = angle + (math.pi / 2) # Establishes orthogonal axis for helix width
                    
                    amplitude = 6.0
                    frequency = 0.08
                    
                    # Offsets sine phase via global timer to force visual scrolling towards the victim
                    phase = self.mew_timer * -0.4
                    
                    segment_length = 10
                    num_segments = int(dist / segment_length)
                    
                    prev_h1_x, prev_h1_y = vfx_mx, vfx_my
                    prev_h2_x, prev_h2_y = vfx_mx, vfx_my
                    
                    for i in range(1, num_segments + 1):
                        t = i / num_segments
                        base_x = vfx_mx + (dx * t)
                        base_y = vfx_my + (dy * t)
                        
                        sine_val = math.sin((i * segment_length * frequency) + phase)
                        offset = sine_val * amplitude
                        
                        # Generates mirrored nodes to construct the dual backbones
                        h1_x = base_x + math.cos(perp_angle) * offset
                        h1_y = base_y + math.sin(perp_angle) * offset
                        h2_x = base_x - math.cos(perp_angle) * offset
                        h2_y = base_y - math.sin(perp_angle) * offset
                        
                        # Renders genetic base pairs (rungs) conditionally to prevent visual clutter
                        if abs(sine_val) > 0.8:
                            self.mew_vfx_canvas.create_line(h1_x, h1_y, h2_x, h2_y, fill="#FFB6C1", width=1, tags="mew_tether")
                            
                        self.mew_vfx_canvas.create_line(prev_h1_x, prev_h1_y, h1_x, h1_y, fill="#FF69B4", width=2, tags="mew_tether")
                        self.mew_vfx_canvas.create_line(prev_h2_x, prev_h2_y, h2_x, h2_y, fill="#C71585", width=2, tags="mew_tether")
                        
                        prev_h1_x, prev_h1_y = h1_x, h1_y
                        prev_h2_x, prev_h2_y = h2_x, h2_y
                # ------------------------------------
                
                vr = max(victim.size_w, victim.size_h) * 0.5
                self._draw_pixel_circle_bbox(self.mew_vfx_canvas, vfx_vx-vr, vfx_vy-vr, vfx_vx+vr, vfx_vy+vr, outline="#FF69B4", width=2, tags="mew_victim_bubble")
                self.mew_vfx_canvas.create_arc(vfx_vx-vr+5, vfx_vy-vr+5, vfx_vx+vr-5, vfx_vy+vr-5, start=45, extent=45, outline="#FFFFFF", width=2, style=tk.ARC, tags="mew_victim_bubble")

                active_victims.append(victim)
        self.mew_victims = active_victims
        
    def _execute_mew_pop(self):
        if not hasattr(self, 'mew_vfx_canvas') or not self.mew_vfx_canvas: return
        cx = self.x - self.v_x + self.size_w / 2
        cy = self.y - self.v_y + self.size_h / 2
        
        pop_particles = []
        for _ in range(40):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(5.0, 25.0)
            pop_particles.append({
                'x': cx,
                'y': cy,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': 20,
                'size': random.randint(3, 8)
            })
            
        def animate_pop():
            if not hasattr(self, 'mew_vfx_canvas') or not self.mew_vfx_canvas: return
            self.mew_vfx_canvas.delete("mew_pop")
            alive = []
            for p in pop_particles:
                p['x'] += p['vx']
                p['y'] += p['vy']
                p['vx'] *= 0.85
                p['vy'] *= 0.85
                p['size'] *= 0.9
                p['life'] -= 1
                if p['life'] > 0:
                    color = random.choice(["#FF69B4", "#FFFFFF", "#FFB6C1"])
                    self.mew_vfx_canvas.create_rectangle(p['x']-p['size'], p['y']-p['size'], p['x']+p['size'], p['y']+p['size'], fill=color, outline="", tags="mew_pop")
                    alive.append(p)
            pop_particles[:] = alive
            if pop_particles:
                self.mew_vfx_canvas.after(30, animate_pop)
            else:
                self.mew_vfx_canvas.delete("all")
                
        animate_pop()
        
    def _fsm_mew_tethered(self):
        self.schedule_loop(50, self.physics_loop)