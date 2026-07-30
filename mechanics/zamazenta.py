import os
import math
import random
import tkinter as tk

class ZamazentaMechanics:
    def cancel_zamazenta_arts(self):
        # Immediate memory release for all VFX overlays to prevent leakages
        if hasattr(self, 'zam_canvas') and self.zam_canvas and self.zam_canvas.winfo_exists():
            self.zam_canvas.destroy()
            self.zam_canvas = None
            
        if hasattr(self, 'zam_win') and self.zam_win and self.zam_win.winfo_exists():
            self.zam_win.destroy()
            self.zam_win = None

        if hasattr(self, 'zam_vfx_win') and self.zam_vfx_win and self.zam_vfx_win.winfo_exists():
            self.zam_vfx_win.destroy()
            self.zam_vfx_win = None

        for attr in ['zam_phase', 'zam_timer', 'zam_speed', 'zam_pushed_pets', 'zam_particles']:
            if hasattr(self, attr): delattr(self, attr)

        try: self.window.attributes('-alpha', 1.0)
        except: pass

        if self.current_state not in ['dragged', 'exiting']:
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.1 
            self.anchored_hwnd = None
            
            if getattr(self, 'is_flying', False):
                self.floor_y = self.y
                self.current_state = 'ascending'
            else:
                self.current_state = 'walking'

    def _fsm_zamazenta_channeling(self):
        if not hasattr(self, 'zam_phase'):
            self.zam_phase = 0
            self.zam_timer = 60 
            self.zam_speed = 1.0 
            self.zam_pushed_pets = set() 
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            self.is_facing_right = (self.x < self.v_x + self.v_width / 2)
            
            if self.pet_name.lower().replace("_", "").replace("-", "") == "zamazenta":
                self.pet_name = "zamazenta_1"
                self.pet_data["species"] = "zamazenta_1"
                from entities.animator import DesktopPetAnimator
                anim_dir = os.path.join(self.base_dir, "game_env", "pets", "zamazenta_1")
                if self.is_shiny and os.path.exists(os.path.join(anim_dir, "shiny")):
                    anim_dir = os.path.join(anim_dir, "shiny")
                self.animator = DesktopPetAnimator(
                    self.canvas, self.config.get("images", {}), 
                    (self.size_w, self.size_h), (self.size_w, self.size_h), anim_dir
                )
                self.play_shiny_sound()
            
            self.setup_zam_vfx_layer()

        if self.zam_phase == 0:
            self.zam_timer -= 1
            
            self.spawn_absorption_particle()
            self.process_zam_particles()
            self.apply_zam_gravity()
            
            if self.zam_timer <= 0:
                self.zam_phase = 1
                self.zam_timer = 5 
                self.spawn_burst_particles()
                self.spawn_zamazenta_shield()

        elif self.zam_phase == 1:
            self.process_zam_particles()
            self.apply_zam_gravity()
            
            self.zam_timer -= 1
            if self.zam_timer <= 0:
                self.zam_phase = 2
                
                # Absolute purge forces structural clean-up of any lingering pre-dash artifacts 
                if hasattr(self, 'zam_vfx_canvas') and self.zam_vfx_canvas:
                    for p in self.zam_particles:
                        if p['mode'] in ['absorb', 'burst']:
                            self.zam_vfx_canvas.delete(p['id'])
                self.zam_particles = [p for p in self.zam_particles if p['mode'] not in ['absorb', 'burst']]

        elif self.zam_phase == 2:
            self.process_zam_particles()
            self.apply_zam_gravity()
            
            if random.random() < 0.6:
                self.spawn_zam_trail_particle()

            self.zam_speed += 0.25 
            if self.zam_speed > 35.0: self.zam_speed = 35.0
            
            self.x += self.zam_speed if self.is_facing_right else -self.zam_speed
            
            shield_width = 120
            shield_h = self.v_height // 8
            shield_y_top = (self.y + self.size_h) - shield_h
            
            arc_depth = shield_width * 0.4
            max_thickness = shield_width * 0.15
            visual_front_offset = int(arc_depth + max_thickness)
            
            if self.is_facing_right:
                s_left = self.x + self.size_w
                s_right = s_left + visual_front_offset
                win_x = s_left
            else:
                s_right = self.x
                s_left = s_right - visual_front_offset
                win_x = s_right - shield_width
            
            if hasattr(self, 'zam_win') and self.zam_win.winfo_exists():
                self.zam_win.geometry(f"{shield_width}x{shield_h}+{int(win_x)}+{int(shield_y_top)}")

            if getattr(self, 'get_all_pets', None):
                for p in self.get_all_pets():
                    if p == self or getattr(p, 'is_egg', False) or p.current_state in ['exiting', 'dragged', 'zamazenta_channeling']:
                        continue
                    
                    p_bottom = p.y + p.size_h
                    if p_bottom > shield_y_top and p.y < shield_y_top + shield_h:
                        if self.is_facing_right:
                            if p.x <= s_right and p.x + p.size_w >= s_left:
                                p.x = s_right
                                p.is_facing_right = True
                                if getattr(p, 'v_x_velocity', 0) < 0: p.v_x_velocity *= -1
                                self.zam_pushed_pets.add(p)
                                
                                p.climbing_surface = 'floor'
                                p.surface_angle = 180 if getattr(p, 'gravity_inverted', False) else 0
                                p.anchored_hwnd = None
                                
                        else:
                            if p.x + p.size_w >= s_left and p.x <= s_right:
                                p.x = s_left - p.size_w
                                p.is_facing_right = False
                                if getattr(p, 'v_x_velocity', 0) > 0: p.v_x_velocity *= -1
                                self.zam_pushed_pets.add(p)
                                
                                p.climbing_surface = 'floor'
                                p.surface_angle = 180 if getattr(p, 'gravity_inverted', False) else 0
                                p.anchored_hwnd = None

            hit_edge = False
            if self.is_facing_right and s_right >= self.v_x + self.v_width:
                self.x = self.v_x + self.v_width - self.size_w - visual_front_offset
                hit_edge = True
            elif not self.is_facing_right and s_left <= self.v_x:
                self.x = self.v_x + visual_front_offset
                hit_edge = True

            if hit_edge:
                self.zam_phase = 3
                self.zam_timer = 15
                
                exp_x = s_right if self.is_facing_right else s_left
                exp_y = shield_y_top + shield_h/2
                self.spawn_zam_explosion(exp_x, exp_y)
                
                bounce_dir = -1 if self.is_facing_right else 1
                for p in self.zam_pushed_pets:
                    if p.window.winfo_exists():
                        p.current_state = 'thrown'
                        p.v_x_velocity = random.uniform(80.0, 110.0) * bounce_dir
                        p.v_y_velocity = random.uniform(-40.0, -60.0)
                        p.climbing_surface = 'floor'
                        p.surface_angle = 180 if getattr(p, 'gravity_inverted', False) else 0
                        p.anchored_hwnd = None
                self.zam_pushed_pets.clear()
                
                if hasattr(self, 'zam_win') and self.zam_win and self.zam_win.winfo_exists():
                    self.zam_win.destroy()
                    self.zam_win = None

        elif self.zam_phase == 3:
            self.process_zam_particles()
            self.zam_timer -= 1
            if self.zam_timer <= 0:
                self.zamazenta_cooldown = 72000
                self.cancel_zamazenta_arts()

        self.update_position()
        
        if hasattr(self, 'zam_vfx_win') and self.zam_vfx_win and self.zam_vfx_win.winfo_exists():
            dim = max(self.size_w, self.size_h) + 200
            self.zam_vfx_win.geometry(f"{dim}x{dim}+{int(self.x - 100)}+{int(self.y - 100)}")
            
        self.schedule_loop(50, self.physics_loop)
        
    def apply_zam_gravity(self):
        gravity = 4.0 if getattr(self, 'heavy_fall', False) and self.v_y_velocity >= -0.5 else 1.5
        self.v_y_velocity += gravity
        self.y += self.v_y_velocity
        
        current_env, _ = self.get_window_environment()
        fall_tolerance = max(15, int(self.v_y_velocity) + 15) if self.v_y_velocity > 0 else 15
        physical_floor = current_env['y'] if self.y <= current_env['y'] + fall_tolerance else self.default_floor_y
        
        if self.v_y_velocity > 0 and self.y >= physical_floor:
            self.y = physical_floor
            self.v_y_velocity = 0
            if current_env['hwnd']:
                self.anchored_hwnd = current_env['hwnd']
                self.anchored_rect = current_env['rect']
            else:
                self.anchored_hwnd = None
        elif self.y < physical_floor - 15:
            self.anchored_hwnd = None

    def setup_zam_vfx_layer(self):
        self.zam_particles = []
        self.zam_vfx_win = tk.Toplevel(self.window.master)
        self.zam_vfx_win.title("VFX_Zam_Energy")
        self.zam_vfx_win.overrideredirect(True)
        self.zam_vfx_win.attributes('-topmost', True)
        
        TRANS = '#010101'
        self.zam_vfx_win.config(bg=TRANS)
        try: self.zam_vfx_win.wm_attributes('-transparentcolor', TRANS)
        except: pass
        
        dim = max(self.size_w, self.size_h) + 200
        self.zam_vfx_win.geometry(f"{dim}x{dim}+{int(self.x - 100)}+{int(self.y - 100)}")
        self.zam_vfx_canvas = tk.Canvas(self.zam_vfx_win, width=dim, height=dim, bg=TRANS, highlightthickness=0)
        self.zam_vfx_canvas.pack()

    def spawn_absorption_particle(self):
        dim = max(self.size_w, self.size_h) + 200
        cx, cy = dim // 2, dim // 2
        
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(80, 120)
        px = cx + math.cos(angle) * dist
        py = cy + math.sin(angle) * dist
        
        color = random.choice(["#E74C3C", "#C0392B", "#1A237E", "#283593"])
        size = random.choice([2, 3])
        
        pid = self.zam_vfx_canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color)
        
        speed = random.uniform(3.0, 6.0)
        vx = -math.cos(angle) * speed
        vy = -math.sin(angle) * speed
        
        self.zam_particles.append({'id': pid, 'x': px, 'y': py, 'vx': vx, 'vy': vy, 'life': 20, 'mode': 'absorb'})

    def spawn_burst_particles(self):
        dim = max(self.size_w, self.size_h) + 200
        cx, cy = dim // 2, dim // 2
        
        for _ in range(40):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(8.0, 15.0)
            px, py = cx, cy
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = random.choice(["#E74C3C", "#C0392B", "#1A237E", "#283593"])
            size = random.choice([3, 4])
            
            pid = self.zam_vfx_canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color)
            self.zam_particles.append({'id': pid, 'x': px, 'y': py, 'vx': vx, 'vy': vy, 'life': 15, 'mode': 'burst'})

    def spawn_zam_trail_particle(self):
        if not hasattr(self, 'zam_vfx_canvas') or not self.zam_vfx_canvas: return
        
        dim = max(self.size_w, self.size_h) + 200
        cx, cy = dim // 2, dim // 2
        
        offset_x = -self.size_w/2 if self.is_facing_right else self.size_w/2
        px = cx + offset_x + random.uniform(-10, 10)
        py = cy + self.size_h/2 - random.uniform(5, 20)
        
        color = random.choice(["#E74C3C", "#C0392B", "#F1C40F"])
        size = random.choice([1, 2])
        
        pid = self.zam_vfx_canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color)
        
        vx = random.uniform(-1.0, 1.0)
        vy = random.uniform(-0.5, 0.5)
        
        self.zam_particles.append({'id': pid, 'x': px, 'y': py, 'vx': vx, 'vy': vy, 'life': random.randint(15, 25), 'mode': 'trail'})

    def process_zam_particles(self):
        # Unified lifecycle evaluation prevents orphaned particles from lingering indefinitely due to skipped updates.
        if not hasattr(self, 'zam_vfx_canvas') or not self.zam_vfx_canvas: return
        
        alive = []
        for p in self.zam_particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1
            
            # Differential physics logic executed without blocking the particle's internal decay clock
            if p['mode'] == "burst":
                p['vx'] *= 0.85
                p['vy'] *= 0.85
            elif p['mode'] == "trail":
                parallax_shift = self.zam_speed if self.is_facing_right else -self.zam_speed
                p['x'] -= parallax_shift
                p['vy'] -= 0.1
            
            if p['life'] > 0:
                self.zam_vfx_canvas.coords(p['id'], p['x']-2, p['y']-2, p['x']+2, p['y']+2)
                alive.append(p)
            else:
                self.zam_vfx_canvas.delete(p['id'])
                
        self.zam_particles = alive

    def spawn_zamazenta_shield(self):
        self.zam_win = tk.Toplevel(self.window.master)
        self.zam_win.title("VFX_Zamazenta_Ignore")
        self.zam_win.overrideredirect(True)
        self.zam_win.attributes('-topmost', True)
        
        TRANS_COLOR = '#010101'
        self.zam_win.config(bg=TRANS_COLOR)
        try: self.zam_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass

        shield_width = 120
        shield_h = self.v_height // 8
        self.zam_canvas = tk.Canvas(self.zam_win, width=shield_width, height=shield_h, bg=TRANS_COLOR, highlightthickness=0)
        self.zam_canvas.pack()
        
        points = []
        arc_depth = shield_width * 0.4
        max_thickness = shield_width * 0.15
        
        for i in range(31):
            t = i / 30.0
            x = int(arc_depth * math.sin(t * math.pi) + max_thickness)
            y = int(shield_h * t)
            
            if not self.is_facing_right:
                x = shield_width - x
                
            points.append(x)
            points.append(y)
            
        for i in range(30, -1, -1):
            t = i / 30.0
            current_thickness = max_thickness * math.sin(t * math.pi)
            x = int(arc_depth * math.sin(t * math.pi) + max_thickness - current_thickness)
            y = int(shield_h * t)
            
            if not self.is_facing_right:
                x = shield_width - x
                
            points.append(x)
            points.append(y)
            
        self.zam_canvas.create_polygon(points, fill="#E74C3C", outline="#F1C40F", width=2)

    def spawn_zam_explosion(self, cx, cy):
        if not hasattr(self, 'get_all_pets'): return
        
        vfx_win = tk.Toplevel(self.window.master)
        vfx_win.title("VFX_Explosion_Ignore")
        vfx_win.overrideredirect(True)
        vfx_win.attributes('-topmost', True)
        
        TRANS_COLOR = '#010101'
        vfx_win.config(bg=TRANS_COLOR)
        try: vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass
        
        vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        cv = tk.Canvas(vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
        cv.pack()
        
        ox = cx - self.v_x
        oy = cy - self.v_y
        
        exp_state = {'radius': 20.0, 'width': 50.0}
        def animate():
            try:
                cv.delete("all")
                exp_state['radius'] += 75.0
                exp_state['width'] *= 0.65 
                
                if exp_state['width'] < 1.0:
                    vfx_win.destroy()
                    return 
                    
                r = exp_state['radius']
                w = int(exp_state['width'])
                cv.create_oval(ox-r, oy-r, ox+r, oy+r, outline="#E74C3C", width=w)
                cv.create_oval(ox-r*0.8, oy-r*0.8, ox+r*0.8, oy+r*0.8, outline="#F1C40F", width=max(1, w//2))
                
                self.window.after(30, animate)
            except: pass
            
        animate()