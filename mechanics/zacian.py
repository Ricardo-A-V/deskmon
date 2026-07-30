import os
import math
import random
import tkinter as tk

class ZacianMechanics:
    def cancel_zacian_arts(self):
        # Clears UI overlays immediately to free memory resources
        if hasattr(self, 'zacian_canvas') and self.zacian_canvas and self.zacian_canvas.winfo_exists():
            self.zacian_canvas.destroy()
            self.zacian_canvas = None

        if hasattr(self, 'zacian_vfx_win') and self.zacian_vfx_win and self.zacian_vfx_win.winfo_exists():
            self.zacian_vfx_win.destroy()
            self.zacian_vfx_win = None

        for attr in ['zacian_phase', 'zacian_timer', 'zacian_start_x', 'zacian_start_y', 'zacian_target_x', 'zacian_target_y', 'zacian_dash_dx', 'zacian_dash_dy', 'zacian_particles']:
            if hasattr(self, attr): delattr(self, attr)

        try: self.window.attributes('-alpha', 1.0)
        except: pass

        if self.current_state not in ['dragged', 'exiting']:
            self.v_x_velocity = 0.0
            self.anchored_hwnd = None
            
            if getattr(self, 'is_flying', False):
                self.floor_y = self.y
                self.current_state = 'ascending'
            else:
                # Propels the entity upwards to force the collision engine to recalculate the physical floor
                self.current_state = 'thrown'
                self.v_y_velocity = -15.0

    def _fsm_zacian_channeling(self):
        if not hasattr(self, 'zacian_phase'):
            self.zacian_phase = 0
            self.zacian_timer = 60 
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            self.setup_zacian_vfx_layer()

        if self.zacian_phase == 0:
            self.zacian_timer -= 1
            
            self.spawn_zacian_absorption_particle()
            self.process_zacian_particles()
            self.apply_zacian_gravity()
            
            if self.zacian_timer <= 0:
                self.zacian_phase = 1
                self.zacian_timer = 10 
                
                target = None
                max_dist = -1
                
                if getattr(self, 'get_all_pets', None):
                    for p in self.get_all_pets():
                        if p != self and p.current_state not in ['exiting', 'dragged'] and not getattr(p, 'is_egg', False):
                            dist = math.hypot(p.x - self.x, p.y - self.y)
                            if dist > max_dist:
                                max_dist = dist
                                target = p
                                
                if target:
                    self.zacian_target_x = target.x + target.size_w / 2
                    self.zacian_target_y = target.y + target.size_h / 2
                else:
                    self.zacian_target_x = random.randint(self.v_x, self.v_x + self.v_width)
                    self.zacian_target_y = random.randint(self.v_y, self.v_y + self.v_height)

                self.zacian_start_x = self.x + self.size_w / 2
                self.zacian_start_y = self.y + self.size_h / 2
                
                total_dx = self.zacian_target_x - self.zacian_start_x
                total_dy = self.zacian_target_y - self.zacian_start_y
                
                self.zacian_dash_dx = total_dx / 10.0
                self.zacian_dash_dy = total_dy / 10.0
                
                self.is_facing_right = (total_dx > 0)
                self.anchored_hwnd = None
                
                if hasattr(self, 'zacian_vfx_win') and self.zacian_vfx_win:
                    self.zacian_vfx_win.destroy()
                    self.zacian_vfx_win = None
                
                self.spawn_zacian_slash_vfx()

        elif self.zacian_phase == 1:
            self.zacian_timer -= 1
            
            self.x += self.zacian_dash_dx
            self.y += self.zacian_dash_dy
            
            if self.zacian_timer <= 0:
                self.zacian_phase = 2
                self.zacian_timer = 5 
                
                self.zacian_calculate_hitbox()
                
                if hasattr(self, 'zacian_canvas') and self.zacian_canvas and self.zacian_canvas.winfo_exists():
                    self.zacian_canvas.destroy()
                    self.zacian_canvas = None

        elif self.zacian_phase == 2:
            self.zacian_timer -= 1
            if self.zacian_timer <= 0:
                self.zacian_cooldown = 72000
                
                if self.pet_name.lower().replace("_", "").replace("-", "") == "zacian":
                    self.pet_name = "zacian_1"
                    self.pet_data["species"] = "zacian_1"
                    
                    from entities.animator import DesktopPetAnimator
                    anim_dir = os.path.join(self.base_dir, "game_env", "pets", "zacian_1")
                    if self.is_shiny and os.path.exists(os.path.join(anim_dir, "shiny")):
                        anim_dir = os.path.join(anim_dir, "shiny")
                    
                    self.animator = DesktopPetAnimator(
                        self.canvas, self.config.get("images", {}), 
                        (self.size_w, self.size_h), (self.size_w, self.size_h), anim_dir
                    )
                
                self.cancel_zacian_arts()
                # REMOVED: `return` statement has been purged. The asynchronous thread will now correctly proceed.

        self.update_position()
        
        if hasattr(self, 'zacian_vfx_win') and self.zacian_vfx_win and self.zacian_vfx_win.winfo_exists():
            dim = max(self.size_w, self.size_h) + 200
            self.zacian_vfx_win.geometry(f"{dim}x{dim}+{int(self.x - 100)}+{int(self.y - 100)}")
            
        self.schedule_loop(50, self.physics_loop)

    def apply_zacian_gravity(self):
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

    def setup_zacian_vfx_layer(self):
        self.zacian_particles = []
        self.zacian_vfx_win = tk.Toplevel(self.window.master)
        self.zacian_vfx_win.title("VFX_Zacian_Energy")
        self.zacian_vfx_win.overrideredirect(True)
        self.zacian_vfx_win.attributes('-topmost', True)
        
        TRANS = '#010101'
        self.zacian_vfx_win.config(bg=TRANS)
        try: self.zacian_vfx_win.wm_attributes('-transparentcolor', TRANS)
        except: pass
        
        dim = max(self.size_w, self.size_h) + 200
        self.zacian_vfx_win.geometry(f"{dim}x{dim}+{int(self.x - 100)}+{int(self.y - 100)}")
        self.zacian_vfx_canvas = tk.Canvas(self.zacian_vfx_win, width=dim, height=dim, bg=TRANS, highlightthickness=0)
        self.zacian_vfx_canvas.pack()

    def spawn_zacian_absorption_particle(self):
        dim = max(self.size_w, self.size_h) + 200
        cx, cy = dim // 2, dim // 2
        
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(80, 120)
        px = cx + math.cos(angle) * dist
        py = cy + math.sin(angle) * dist
        
        color = random.choice(["#ADD8E6", "#87CEFA", "#FFCCCB", "#F08080"])
        size = random.choice([2, 3])
        
        pid = self.zacian_vfx_canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color)
        
        speed = random.uniform(3.0, 6.0)
        vx = -math.cos(angle) * speed
        vy = -math.sin(angle) * speed
        
        self.zacian_particles.append({'id': pid, 'x': px, 'y': py, 'vx': vx, 'vy': vy, 'life': 20})

    def process_zacian_particles(self):
        if not hasattr(self, 'zacian_vfx_canvas') or not self.zacian_vfx_canvas: return
        
        alive = []
        for p in self.zacian_particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1
            
            if p['life'] > 0:
                self.zacian_vfx_canvas.coords(p['id'], p['x']-2, p['y']-2, p['x']+2, p['y']+2)
                alive.append(p)
            else:
                self.zacian_vfx_canvas.delete(p['id'])
                
        self.zacian_particles = alive

    def spawn_zacian_slash_vfx(self):
        self.zacian_win = tk.Toplevel(self.window.master)
        self.zacian_win.title("VFX_Zacian_Ignore")
        self.zacian_win.overrideredirect(True)
        self.zacian_win.attributes('-topmost', True)
        
        TRANS_COLOR = '#010101'
        self.zacian_win.config(bg=TRANS_COLOR)
        try: self.zacian_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass

        self.zacian_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        self.zacian_canvas = tk.Canvas(self.zacian_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
        self.zacian_canvas.pack()
        
        sx = self.zacian_start_x - self.v_x
        sy = self.zacian_start_y - self.v_y
        ex = self.zacian_target_x - self.v_x
        ey = self.zacian_target_y - self.v_y
        
        self.zacian_canvas.create_line(sx, sy, ex, ey, fill="#E0F7FA", width=18, capstyle=tk.ROUND)
        self.zacian_canvas.create_line(sx, sy, ex, ey, fill="#B2EBF2", width=10, capstyle=tk.ROUND)
        self.zacian_canvas.create_line(sx, sy, ex, ey, fill="#FFFFFF", width=4, capstyle=tk.ROUND)

    def zacian_calculate_hitbox(self):
        if not getattr(self, 'get_all_pets', None): return
        
        sx = self.zacian_start_x
        sy = self.zacian_start_y
        ex = self.zacian_target_x
        ey = self.zacian_target_y
        
        line_dx = ex - sx
        line_dy = ey - sy
        line_length_sq = line_dx**2 + line_dy**2
        
        hit_targets = []
        
        for target in self.get_all_pets():
            if target == self or target.current_state in ['exiting', 'dragged', 'zacian_channeling'] or getattr(target, 'is_egg', False): 
                continue
                
            tcx = target.x + target.size_w / 2
            tcy = target.y + target.size_h / 2
            
            if line_length_sq == 0:
                dist = math.hypot(tcx - sx, tcy - sy)
            else:
                t = max(0, min(1, ((tcx - sx) * line_dx + (tcy - sy) * line_dy) / line_length_sq))
                proj_x = sx + t * line_dx
                proj_y = sy + t * line_dy
                dist = math.hypot(tcx - proj_x, tcy - proj_y)
                
            if dist < 60:
                dist_to_start = math.hypot(tcx - sx, tcy - sy)
                hit_targets.append({'target': target, 'dist': dist_to_start, 'tcx': tcx})

        hit_targets.sort(key=lambda item: item['dist'])

        for index, item in enumerate(hit_targets):
            target = item['target']
            tcx = item['tcx']
            
            push_dir = 1 if tcx > sx else -1
            mult = 1 if not getattr(target, 'gravity_inverted', False) else -1
            
            delay_ms = (index + 1) * 500
            
            self.apply_zacian_stun(target, delay_ms, push_dir, mult)

    def apply_zacian_stun(self, target, delay_ms, push_dir, mult):
        prev_state = getattr(target, 'current_state', '')
        
        target.current_state = 'zacian_stunned'
        target.v_x_velocity = 0.0
        target.v_y_velocity = 0.0
        target.anchored_hwnd = None
        
        # 1. Safely interrupt channel logic without relying on the current_state string post-assignment
        if prev_state.startswith('dark_') and hasattr(target, 'cancel_dark_arts'): target.cancel_dark_arts()
        elif prev_state.startswith('mewtwo_') and hasattr(target, 'cancel_mewtwo_arts'): target.cancel_mewtwo_arts()
        elif prev_state in ['hooh_channeling', 'panic_run'] and hasattr(target, 'cancel_hooh_arts'): target.cancel_hooh_arts()
        elif prev_state in ['lugia_channeling', 'lugia_dash'] and hasattr(target, 'cancel_lugia_arts'): target.cancel_lugia_arts()

        if prev_state == 'tk_channeling' and hasattr(target, 'manage_tk_aura'):
            target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
            if getattr(target, 'tk_target', None):
                t_targ = target.tk_target
                target.manage_tk_aura(t_targ.canvas, t_targ.size_w if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size, t_targ.size_h if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size, False)
                t_targ.current_state = 'falling'
                if hasattr(t_targ, 'tk_master'): t_targ.tk_master = None
            target.tk_target = None
        elif prev_state == 'tk_lifted' and hasattr(target, 'manage_tk_aura'):
            target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
            if getattr(target, 'tk_master', None):
                target.tk_master.tk_target = None
                target.tk_master.manage_tk_aura(target.tk_master.canvas, target.tk_master.size_w, target.tk_master.size_h, False)
                target.tk_master.current_state = 'falling'
            target.tk_master = None

        # 2. Universal graphical purge to prevent leftover rendering flags
        target.dark_mode = False
        target.is_glitching = False
        target.glitch_teleports_left = 0
        target.glitch_cooldown = 12000
        
        try: target.window.attributes('-alpha', 1.0)
        except: pass
        
        if hasattr(target, 'canvas') and hasattr(target, 'canvas_image_id'):
            target.canvas.itemconfig(target.canvas_image_id, state='normal')

        self.zacian_vibration_loop(target, delay_ms, push_dir, mult)

    def zacian_vibration_loop(self, target, time_left, push_dir, mult):
        if not target.window.winfo_exists() or target.current_state != 'zacian_stunned':
            if target.window.winfo_exists():
                target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
            return
            
        if time_left <= 0:
            target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
            
            target_is_soft = not getattr(target, 'heavy_fall', False) or not getattr(target, 'aggressive', False)
            if getattr(self, 'heavy_fall', False) and target_is_soft:
                target.current_state = 'landing_shake'
                target.shake_timer = 25 
                target.v_x_velocity = 0.0
                target.v_y_velocity = 0.0
            else:
                target.current_state = 'thrown'
                target.v_x_velocity = 85.0 * push_dir 
                target.v_y_velocity = -35.0 * mult    
                target.climbing_surface = 'floor'
                target.surface_angle = 180 if getattr(target, 'gravity_inverted', False) else 0
                
                self.spawn_zacian_sparks(target, push_dir)
            return

        offset_x = random.choice([-6, -3, 0, 3, 6])
        offset_y = random.choice([-6, -3, 0, 3, 6])
        target.canvas.coords(target.canvas_image_id, (target.size_w//2) + offset_x, (target.size_h//2) + offset_y)
        
        target.window.after(30, lambda: self.zacian_vibration_loop(target, time_left - 30, push_dir, mult))

    def spawn_zacian_sparks(self, target, push_dir):
        if not target.window.winfo_exists() or getattr(target, 'current_state', 'exiting') == 'exiting': return
        
        particles = []
        cx = target.size_w // 2
        cy = target.size_h // 2
        
        for _ in range(random.randint(15, 25)):
            base_angle = 0 if push_dir > 0 else math.pi
            angle = base_angle + random.uniform(-math.pi/3, math.pi/3)
            
            speed = random.uniform(8.0, 16.0)
            vx = math.cos(angle) * speed
            vy = (math.sin(angle) * speed) - random.uniform(4.0, 8.0)
            
            size = random.choice([2, 3])
            color = random.choice(["#FFFFFF", "#FFFFAA", "#FFD700", "#F1C40F"])
            
            pid = target.canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline=color, tags="vfx_z_spark")
            particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': random.randint(12, 22)})
            
        def animate_sparks():
            if not target.window.winfo_exists() or getattr(target, 'current_state', 'exiting') == 'exiting': return
            alive = 0
            for p in particles:
                if p['life'] > 0:
                    target.canvas.move(p['id'], p['vx'], p['vy'])
                    p['vx'] *= 0.85 
                    p['vy'] += 1.2 
                    p['life'] -= 1
                    alive += 1
                elif p['life'] == 0:
                    target.canvas.delete(p['id'])
                    p['life'] = -1
                    
            if alive > 0:
                target.window.after(30, animate_sparks)
                
        animate_sparks()