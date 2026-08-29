import random
import math
import tkinter as tk

class ZygardeMechanics:
    def cancel_zygarde_arts(self):
        if hasattr(self, 'zygarde_win') and self.zygarde_win and self.zygarde_win.winfo_exists():
            self.zygarde_win.destroy()
            self.zygarde_win = None

        for attr in ['zygarde_phase', 'zygarde_timer', 'zygarde_hit_targets', 'zygarde_projectiles', 'zygarde50_phase', 'zygarde50_timer', 'zygarde50_attack_cd', 'zygarde50_shake', 'z50_particles']:
            if hasattr(self, attr): delattr(self, attr)

        self.canvas.delete("vfx_z50_aura")
        self.canvas.itemconfig(self.canvas_image_id, state='normal')
        self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)

        if self.current_state not in ['dragged', 'exiting']:
            self.current_state = 'falling'
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0

    # ==========================================
    # 10% PHASE (DOG) - HORIZONTAL INTERCEPTOR
    # ==========================================
    def _fsm_zygarde_channeling(self):
        if not hasattr(self, 'zygarde_phase'):
            self.zygarde_phase = 0
            self.zygarde_timer = 40 
            self.zygarde_hit_targets = set()
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0

        if self.zygarde_phase == 0:
            self.zygarde_timer -= 1
            crop_amount = int((1.0 - (self.zygarde_timer / 40.0)) * self.size_h)
            self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2 + crop_amount)
            
            if self.zygarde_timer % 4 == 0: self.spawn_zygarde_dirt_vfx(is_green=True)
            if self.zygarde_timer <= 0:
                self.zygarde_phase = 1
                self.zygarde_timer = 40 
                self.canvas.itemconfig(self.canvas_image_id, state='hidden')

        elif self.zygarde_phase == 1:
            self.zygarde_timer -= 1
            if self.zygarde_timer <= 0:
                self.zygarde_phase = 2
                self.canvas.itemconfig(self.canvas_image_id, state='normal')
                self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
                
                self.is_facing_right = random.choice([True, False])
                self.y = self.default_floor_y
                if self.is_facing_right:
                    self.x = self.v_x - self.size_w
                    self.v_x_velocity = 25.0
                else:
                    self.x = self.v_x + self.v_width
                    self.v_x_velocity = -25.0

        elif self.zygarde_phase == 2:
            self.x += self.v_x_velocity
            self.zygarde_scan_and_intercept()
            if (self.is_facing_right and self.x > self.v_x + self.v_width) or (not self.is_facing_right and self.x < self.v_x - self.size_w):
                self.zygarde_phase = 3
                self.zygarde_timer = 40 
                self.v_x_velocity = 0.0

        elif self.zygarde_phase == 3:
            self.zygarde_timer -= 1
            if self.zygarde_timer <= 0:
                self.zygarde_phase = 4
                self.zygarde_timer = 40
                self.x = random.randint(self.v_x + 50, self.v_x + self.v_width - 50 - self.size_w)
                self.y = self.default_floor_y
                self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2 + self.size_h)
                self.canvas.itemconfig(self.canvas_image_id, state='normal')

        elif self.zygarde_phase == 4:
            self.zygarde_timer -= 1
            crop_amount = int((self.zygarde_timer / 40.0) * self.size_h)
            self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2 + crop_amount)
            
            if self.zygarde_timer % 4 == 0: self.spawn_zygarde_dirt_vfx(is_green=True)
            if self.zygarde_timer <= 0:
                self.cancel_zygarde_arts()
                self.current_state = 'idle'
                self.zygarde_cooldown = 72000 

        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def zygarde_scan_and_intercept(self):
        if not getattr(self, 'get_all_pets', None): return
        for target in self.get_all_pets():
            if target == self or target.current_state in ['exiting', 'dragged'] or getattr(target, 'is_egg', False): continue
            if id(target) in self.zygarde_hit_targets: continue
            if abs(self.x - target.x) < 40:
                self.zygarde_hit_targets.add(id(target))
                is_climber = getattr(target, 'climbing_surface', 'floor') != 'floor'
                target_floor = getattr(target, 'floor_y', target.default_floor_y)
                
                is_airborne = False
                if getattr(target, 'is_flying', False): is_airborne = True
                elif target.current_state in ['falling', 'thrown', 'jumping_arc', 'legendary_bounce', 'falling_legendary', 'falling_pokeball'] and target.y < target_floor - 5:
                    is_airborne = True
                    
                if is_airborne and not is_climber:
                    self.execute_thousand_arrows(target, burst_mode=False)
                else:
                    self.execute_lands_wrath(target)


    # ==========================================
    # 50% PHASE (SNAKE) - GLOBAL ARTILLERY
    # ==========================================
    def _fsm_zygarde50_channeling(self):
        if not hasattr(self, 'zygarde50_phase'):
            self.zygarde50_phase = 0
            self.zygarde50_timer = 40 
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0

        if self.zygarde50_phase == 0:
            self.zygarde50_timer -= 1
            crop_amount = int((1.0 - (self.zygarde50_timer / 40.0)) * self.size_h)
            self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2 + crop_amount)
            if self.zygarde50_timer % 4 == 0: self.spawn_zygarde_dirt_vfx(is_green=True)
            
            if self.zygarde50_timer <= 0:
                self.zygarde50_phase = 1
                self.zygarde50_timer = 40 
                self.canvas.itemconfig(self.canvas_image_id, state='hidden')
                
                try:
                    import win32api
                    import win32con
                    monitor = win32api.MonitorFromPoint((int(self.x), int(self.y)), win32con.MONITOR_DEFAULTTONEAREST)
                    mon_info = win32api.GetMonitorInfo(monitor)
                    mon_rect = mon_info['Monitor'] 
                    self.x = mon_rect[0] + ((mon_rect[2] - mon_rect[0]) // 2) - (self.size_w // 2)
                except:
                    self.x = self.v_x + (self.v_width // 2) - (self.size_w // 2)
                    
                self.y = self.default_floor_y
                self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2 + self.size_h)

        elif self.zygarde50_phase == 1:
            self.canvas.itemconfig(self.canvas_image_id, state='normal')
            self.zygarde50_timer -= 1
            crop_amount = int((self.zygarde50_timer / 40.0) * self.size_h)
            self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2 + crop_amount)
            if self.zygarde50_timer % 4 == 0: self.spawn_zygarde_dirt_vfx(is_green=True)
            
            if self.zygarde50_timer <= 0:
                self.zygarde50_phase = 2
                self.zygarde50_timer = 600 
                self.zygarde50_attack_cd = random.randint(10, 30) 
                
                self.create_zygarde_global_canvas()
                self.zygarde50_aura_loop()

        elif self.zygarde50_phase == 2:
            self.zygarde50_timer -= 1
            self.zygarde50_attack_cd -= 1
            
            # VIBRATION CONTROL (Kinetic Feedback)
            if getattr(self, 'zygarde50_shake', 0) > 0:
                self.zygarde50_shake -= 1
                ox = random.choice([-4, 0, 4])
                oy = random.choice([-3, 0, 3])
                self.canvas.coords(self.canvas_image_id, (self.size_w//2) + ox, (self.size_h//2) + oy)
            else:
                self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)

            # Continuous instantiation of the cellular aura
            if self.zygarde50_timer % 3 == 0:
                self.spawn_zygarde50_aura_particles()

            if self.zygarde50_attack_cd <= 0:
                self.zygarde50_attack_cd = random.randint(10, 30)
                self.zygarde50_fire_random_artillery()
                
            if self.zygarde50_timer <= 0:
                self.cancel_zygarde_arts()
                self.current_state = 'idle'
                self.zygarde_cooldown = 72000 

        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def spawn_zygarde50_aura_particles(self):
        # Protects against memory leaks if the state collapses
        if getattr(self, 'current_state', '') != 'zygarde50_channeling': return
        
        cx = self.size_w / 2
        cy = self.size_h / 2
        
        for _ in range(random.randint(1, 2)):
            r = random.uniform(2.0, 4.5)
            px = cx + random.uniform(-self.size_w * 0.35, self.size_w * 0.35)
            py = cy + random.uniform(-self.size_h * 0.3, self.size_h * 0.4)
            
            # Strict trigonometric construction of a hexagon
            pts = [
                px, py-r, px+r*0.86, py-r*0.5, px+r*0.86, py+r*0.5,
                px, py+r, px-r*0.86, py+r*0.5, px-r*0.86, py-r*0.5
            ]
            
            color = random.choice(["#39FF14", "#00FF00"])
            pid = self.canvas.create_polygon(pts, fill=color, outline=color, tags="vfx_z50_aura")
            
            if not hasattr(self, 'z50_particles'): self.z50_particles = []
            
            # Cells ascend as if they were gravitational energy
            self.z50_particles.append({
                'id': pid, 
                'vx': random.uniform(-0.8, 0.8), 
                'vy': random.uniform(-3.5, -1.0), 
                'life': random.randint(15, 30)
            })

    def zygarde50_aura_loop(self):
        # Isolated loop to handle aura physics
        if getattr(self, 'current_state', '') != 'zygarde50_channeling':
            self.canvas.delete("vfx_z50_aura")
            return

        if not hasattr(self, 'z50_particles'): self.z50_particles = []
        
        alive = []
        for p in self.z50_particles:
            if p['life'] > 0:
                self.canvas.move(p['id'], p['vx'], p['vy'])
                
                # Stochastic drift injection (light snaking movement)
                p['vx'] += random.uniform(-0.3, 0.3)
                p['life'] -= 1
                alive.append(p)
            else:
                self.canvas.delete(p['id'])
                
        self.z50_particles = alive
        self.window.after(50, self.zygarde50_aura_loop)

    def zygarde50_fire_random_artillery(self):
        if not getattr(self, 'get_all_pets', None): return
        
        valid_targets = [p for p in self.get_all_pets() if p != self and p.current_state not in ['exiting', 'dragged'] and not getattr(p, 'is_egg', False)]
        if not valid_targets: return
        
        target = random.choice(valid_targets)
        
        # Flips Zygarde to face its victim
        self.is_facing_right = target.x > self.x
        
        is_climber = getattr(target, 'climbing_surface', 'floor') != 'floor'
        is_airborne = False
        
        if getattr(target, 'is_flying', False) and target.current_state != 'zygarde_grounded':
            is_airborne = True
        elif target.current_state in ['falling', 'thrown', 'jumping_arc', 'legendary_bounce', 'falling_legendary', 'falling_pokeball'] and target.y < getattr(target, 'floor_y', target.default_floor_y) - 5:
            is_airborne = True
            
        # Executes Thousand Arrows if flying freely, otherwise Land's Wrath
        if is_airborne and not is_climber:
            self.execute_thousand_arrows(target, burst_mode=True)
        else:
            self.execute_lands_wrath(target)


    # ==========================================
    # WEAPONRY AND VFX ENGINE
    # ==========================================
    def execute_thousand_arrows(self, target, burst_mode=False):
        if not hasattr(self, 'zygarde_win') or not self.zygarde_win:
            self.create_zygarde_global_canvas()
            
        start_x = self.x + self.size_w/2 - self.v_x
        
        # In normal mode, they spawn from the feet. In burst mode (50%), they spawn from its geometric center.
        start_y = (self.y + self.size_h/2 - self.v_y) if burst_mode else (self.y + self.size_h - self.v_y)
        
        for _ in range(6):
            if burst_mode:
                vx = random.uniform(-20, 20)
                vy = random.uniform(-20, 20)
                offset_x, offset_y = random.uniform(-20, 20), random.uniform(-20, 20)
            else:
                vx = random.uniform(-5, 5)
                vy = random.uniform(-15, -25)
                offset_x, offset_y = random.uniform(-30, 30), 0
                
            self.zygarde_projectiles.append({
                'type': 'arrow', 'target': target,
                'x': start_x + offset_x, 'y': start_y + offset_y,
                'vx': vx, 'vy': vy
            })
            
        self.zygarde_vfx_engine()

    def execute_lands_wrath(self, target):
        if not hasattr(self, 'zygarde_win') or not self.zygarde_win:
            self.create_zygarde_global_canvas()
            
        surface = getattr(target, 'climbing_surface', 'floor')
        tcx = target.x + target.size_w/2 - self.v_x
        tcy = target.y + target.size_h/2 - self.v_y
        
        launch_vx = 0.0
        launch_vy = 0.0
        p_x, p_y = tcx, tcy
        pillar_dir = 'up'
        
        if surface in ['wall_l', 'screen_l']:
            launch_vx = random.uniform(25.0, 35.0)
            launch_vy = random.uniform(-10.0, -20.0)
            p_x = target.x - self.v_x
            p_y = tcy
            pillar_dir = 'right'
        elif surface in ['wall_r', 'screen_r']:
            launch_vx = random.uniform(-35.0, -25.0)
            launch_vy = random.uniform(-10.0, -20.0)
            p_x = target.x + target.size_w - self.v_x
            p_y = tcy
            pillar_dir = 'left'
        elif surface in ['ceiling', 'screen_ceiling']:
            launch_vx = random.uniform(-15.0, 15.0)
            launch_vy = random.uniform(20.0, 30.0) 
            p_x = tcx
            p_y = target.y - self.v_y
            pillar_dir = 'down'
        else:
            launch_vx = random.uniform(-8.0, 8.0)
            target_height = random.uniform(self.v_height * 0.25, self.v_height * 0.75)
            launch_vy = -math.sqrt(3.0 * target_height)
            p_x = tcx
            p_y = target.y + target.size_h + getattr(target, 'offset_y', -6) - self.v_y
            pillar_dir = 'up'
            
        self.zygarde_projectiles.append({
            'type': 'pillar', 'target': target,
            'x': p_x, 'y': p_y,
            'vx': launch_vx, 'vy': launch_vy,
            'dir': pillar_dir,
            'life': 10, 'max_life': 10
        })
        self.zygarde_vfx_engine()

    def spawn_zygarde_dirt_vfx(self, is_green=False):
        colors = ["#39FF14", "#00FF00", "#124E13"] if is_green else ["#5C4033", "#8B5A2B", "#CD853F"]
        cx = self.size_w / 2
        cy = self.size_h - 10
        for _ in range(3):
            px = cx + random.uniform(-15, 15)
            py = cy + random.uniform(-5, 5)
            size = random.choice([3, 4, 5])
            color = random.choice(colors)
            pid = self.canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color, tags="vfx_z_dirt")
            if not hasattr(self, 'z_particles'): self.z_particles = []
            self.z_particles.append({'id': pid, 'vx': random.uniform(-2, 2), 'vy': random.uniform(-4, -1), 'life': 15})
        self.zygarde_dirt_vfx_loop()

    def zygarde_dirt_vfx_loop(self):
        if not hasattr(self, 'z_particles'): return
        alive = []
        for p in self.z_particles:
            if p['life'] > 0:
                self.canvas.move(p['id'], p['vx'], p['vy'])
                p['vy'] += 0.5 
                p['life'] -= 1
                alive.append(p)
            else:
                self.canvas.delete(p['id'])
        self.z_particles = alive
        if self.z_particles:
            self.window.after(50, self.zygarde_dirt_vfx_loop)

    def create_zygarde_global_canvas(self):
        self.zygarde_win = tk.Toplevel(self.window.master)
        self.zygarde_win.title("VFX_Zygarde_Ignore")
        self.zygarde_win.overrideredirect(True)
        self.zygarde_win.attributes('-topmost', True)
        
        TRANS_COLOR = '#010101'
        self.zygarde_win.config(bg=TRANS_COLOR)
        try: self.zygarde_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass

        self.zygarde_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        self.zygarde_canvas = tk.Canvas(self.zygarde_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
        self.zygarde_canvas.pack()
        self.zygarde_win.lift() 
        self.zygarde_projectiles = []

    def zygarde_vfx_engine(self):
        if not hasattr(self, 'zygarde_win') or not self.zygarde_win: return
        self.zygarde_win.lift() 
        self.zygarde_canvas.delete("vfx_z_proj")
        
        alive = []
        for p in self.zygarde_projectiles:
            if p['type'] == 'arrow':
                target_cx = p['target'].x + p['target'].target_w/2 if hasattr(p['target'], 'target_w') else p['target'].x + p['target'].size_w/2 - self.v_x
                target_cy = p['target'].y + p['target'].target_h/2 if hasattr(p['target'], 'target_h') else p['target'].y + p['target'].size_h/2 - self.v_y
                
                dx = target_cx - p['x']
                dy = target_cy - p['y']
                dist = math.hypot(dx, dy)
                
                if dist > 0:
                    p['vx'] += (dx / dist) * 6.0
                    p['vy'] += (dy / dist) * 6.0
                
                speed = math.hypot(p['vx'], p['vy'])
                if speed > 45.0:
                    p['vx'] = (p['vx'] / speed) * 45.0
                    p['vy'] = (p['vy'] / speed) * 45.0
                    
                p['x'] += p['vx']
                p['y'] += p['vy']
                
                r = 12
                pts = [
                    p['x'], p['y']-r, p['x']+r*0.86, p['y']-r*0.5, p['x']+r*0.86, p['y']+r*0.5,
                    p['x'], p['y']+r, p['x']-r*0.86, p['y']+r*0.5, p['x']-r*0.86, p['y']-r*0.5
                ]
                self.zygarde_canvas.create_polygon(pts, fill="#39FF14", outline="#00FF00", tags="vfx_z_proj")
                
                if math.hypot(p['x'] - target_cx, p['y'] - target_cy) < 60:
                    self.apply_zygarde_grounded(p['target'])
                    continue 
                
                if p['y'] > -100 and p['y'] < self.v_height + 100: alive.append(p)
                
            elif p['type'] == 'pillar':
                p['life'] -= 1
                progress = 1.0 - (p['life'] / p['max_life'])
                
                try: p['target'].window.attributes('-topmost', False)
                except: pass
                
                max_len = 150 
                cur_len = max_len * progress
                bw = 40 
                
                if p['dir'] == 'up':
                    self.zygarde_canvas.create_rectangle(p['x']-bw/2, p['y']-cur_len, p['x']+bw/2, p['y'], fill="#5C4033", outline="#3b281f", width=2, tags="vfx_z_proj")
                elif p['dir'] == 'down':
                    self.zygarde_canvas.create_rectangle(p['x']-bw/2, p['y'], p['x']+bw/2, p['y']+cur_len, fill="#5C4033", outline="#3b281f", width=2, tags="vfx_z_proj")
                elif p['dir'] == 'right':
                    self.zygarde_canvas.create_rectangle(p['x'], p['y']-bw/2, p['x']+cur_len, p['y']+bw/2, fill="#5C4033", outline="#3b281f", width=2, tags="vfx_z_proj")
                elif p['dir'] == 'left':
                    self.zygarde_canvas.create_rectangle(p['x']-cur_len, p['y']-bw/2, p['x'], p['y']+bw/2, fill="#5C4033", outline="#3b281f", width=2, tags="vfx_z_proj")
                
                if p['life'] <= 0:
                    self.zygarde_force_launch(p['target'], p['vx'], p['vy'])
                    
                    self.zygarde50_shake = 10 
                    
                    for _ in range(15):
                        ex, ey = p['x'], p['y']
                        if p['dir'] == 'up': ey -= cur_len/2
                        elif p['dir'] == 'down': ey += cur_len/2
                        elif p['dir'] == 'right': ex += cur_len/2
                        elif p['dir'] == 'left': ex -= cur_len/2
                        
                        self.zygarde_projectiles.append({
                            'type': 'dirt', 'x': ex, 'y': ey,
                            'vx': random.uniform(-10, 10), 'vy': random.uniform(-12, -2), 'life': 20
                        })
                else:
                    alive.append(p)
                    
            elif p['type'] == 'dirt':
                p['x'] += p['vx']
                p['y'] += p['vy']
                p['vy'] += 0.8 
                p['life'] -= 1
                size = random.choice([3, 5, 7])
                color = random.choice(["#5C4033", "#8B5A2B", "#CD853F"])
                self.zygarde_canvas.create_rectangle(p['x']-size, p['y']-size, p['x']+size, p['y']+size, fill=color, outline=color, tags="vfx_z_proj")
                
                if p['life'] > 0: alive.append(p)

        self.zygarde_projectiles = alive
        if self.zygarde_projectiles or getattr(self, 'current_state', '') in ['zygarde_channeling', 'zygarde50_channeling']:
            self.window.after(30, self.zygarde_vfx_engine)

    # ==========================================
    # PHYSICAL RESOLUTION
    # ==========================================
    def apply_zygarde_grounded(self, target):
        if target.current_state.startswith('dark_'): target.cancel_dark_arts()
        if getattr(target, 'is_glitching', False):
            target.is_glitching = False
            target.glitch_teleports_left = 0
            
        target.canvas.itemconfig(target.canvas_image_id, state='normal')
        if hasattr(target, 'dark_mode'): target.dark_mode = False
        try: target.window.attributes('-alpha', 1.0)
        except: pass
            
        if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
        target.current_state = 'zygarde_grounded'
        target.zygarde_grounded_timer = 200 
        target.zygarde_impact_done = False 
        target.zygarde_grounded_vfx_loop()

    def _fsm_zygarde_grounded(self):
        if self.v_y_velocity < 0: self.v_y_velocity = 0.0
        self.v_y_velocity += 1.5
        self.y += self.v_y_velocity
        
        current_env, _ = self.get_window_environment()
        physical_floor = current_env['y'] if self.y <= current_env['y'] + 15 else self.default_floor_y
        
        if self.y >= physical_floor:
            self.y = physical_floor
            self.v_y_velocity = 0.0
            
            if not getattr(self, 'zygarde_impact_done', False):
                self.zygarde_impact_done = True
                if not hasattr(self, 'z_target_particles'): self.z_target_particles = []
                
                cx, cy = self.size_w / 2, self.size_h - 5
                for _ in range(10):
                    color = random.choice(["#5C4033", "#8B5A2B", "#CD853F"])
                    pid = self.canvas.create_rectangle(cx, cy, cx+5, cy+5, fill=color, outline=color, tags="vfx_z_g_dirt")
                    self.z_target_particles.append({'id': pid, 'vx': random.uniform(-6, 6), 'vy': random.uniform(-8, -2), 'life': 15, 'type': 'dirt'})
        
        self.zygarde_grounded_timer -= 1
        if self.zygarde_grounded_timer <= 0:
            self.canvas.delete("vfx_z_grounded")
            self.canvas.delete("vfx_z_g_dirt")
            
            if hasattr(self, 'dark_mode'): self.dark_mode = False
            try: self.window.attributes('-alpha', 1.0)
            except: pass
            
            if getattr(self, 'is_flying', False):
                self.floor_y = self.y 
                self.current_state = 'ascending'
            else:
                self.current_state = 'idle'
                
        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def zygarde_grounded_vfx_loop(self):
        if getattr(self, 'current_state', '') != 'zygarde_grounded':
            self.canvas.delete("vfx_z_grounded")
            self.canvas.delete("vfx_z_g_dirt")
            return

        if not hasattr(self, 'z_target_particles'): self.z_target_particles = []

        if getattr(self, 'zygarde_impact_done', False) and random.randint(1, 100) <= 40:
            cx, cy = self.size_w / 2, self.size_h / 2
            px = cx + random.uniform(-self.size_w * 0.4, self.size_w * 0.4)
            py = cy + random.uniform(0, self.size_h * 0.4)
            
            color = random.choice(["#39FF14", "#00FF00"])
            pid = self.canvas.create_rectangle(px, py, px+3, py+3, fill=color, outline=color, tags="vfx_z_grounded")
            self.z_target_particles.append({'id': pid, 'vx': random.uniform(-0.5, 0.5), 'vy': random.uniform(-3.0, -1.0), 'life': 25, 'type': 'aura'})

        alive = []
        for p in self.z_target_particles:
            if p['life'] > 0:
                self.canvas.move(p['id'], p['vx'], p['vy'])
                if p['type'] == 'dirt': p['vy'] += 0.5 
                p['life'] -= 1
                alive.append(p)
            else:
                self.canvas.delete(p['id'])
        self.z_target_particles = alive
        self.window.after(50, self.zygarde_grounded_vfx_loop)

    def zygarde_force_launch(self, target, vx, vy):
        if target.current_state.startswith('dark_'): target.cancel_dark_arts()
        if getattr(target, 'is_glitching', False):
            target.is_glitching = False
            target.glitch_teleports_left = 0
            
        for prefix, cancel_func in [('mewtwo_', 'cancel_mewtwo_arts'), ('hooh_', 'cancel_hooh_arts'), ('kyogre_', 'cancel_kyogre_arts'), ('groudon_', 'cancel_groudon_arts'), ('lugia_', 'cancel_lugia_arts'), ('rayquaza_', 'cancel_rayquaza_arts'), ('dialga_', 'cancel_dialga_arts'), ('palkia_', 'cancel_palkia_arts'), ('giratina_', 'cancel_giratina_arts'), ('zekrom_', 'cancel_zekrom_arts'), ('reshiram_', 'cancel_reshiram_arts'), ('kyurem_', 'cancel_kyurem_arts'), ('xerneas_', 'cancel_xerneas_arts'), ('yveltal_', 'cancel_yveltal_arts')]:
            if target.current_state.startswith(prefix) and hasattr(target, cancel_func): getattr(target, cancel_func)()

        target.canvas.itemconfig(target.canvas_image_id, state='normal')
        if hasattr(target, 'dark_mode'): target.dark_mode = False 
        try: target.window.attributes('-topmost', True)
        except: pass
        try: target.window.attributes('-alpha', 1.0)
        except: pass
        
        target.canvas.delete("vfx_z_grounded")
        target.canvas.delete("vfx_z_g_dirt")

        surface = getattr(target, 'climbing_surface', 'floor')
        if surface in ['wall_l', 'screen_l']: target.x += 30
        elif surface in ['wall_r', 'screen_r']: target.x -= 30
        elif surface in ['ceiling', 'screen_ceiling']: target.y += 30
        else: target.y -= 40
        
        target.climbing_surface = 'floor' 
        target.surface_angle = 180 if getattr(target, 'gravity_inverted', False) else 0
        
        target.v_x_velocity = vx
        target.v_y_velocity = vy
        
        # FLIGHT RECOVERY FIX
        if getattr(target, 'is_flying', False):
            if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
            target.current_state = 'zygarde_launched_flyer'
        else:
            if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
            target.current_state = 'zygarde_launched' 
        
    def _fsm_zygarde_launched(self):
        self.v_y_velocity += 1.5 
        self.y += self.v_y_velocity
        self.x += self.v_x_velocity
        
        if getattr(self, 'can_screen_wrap', False):
            if self.x <= self.v_x - self.size_w: self.x = self.v_x + self.v_width
            elif self.x >= self.v_x + self.v_width: self.x = self.v_x - self.size_w
        else:
            if self.x <= self.v_x:
                self.x = self.v_x
                self.v_x_velocity *= -0.8
            elif self.x >= (self.v_x + self.v_width) - self.size_w:
                self.x = (self.v_x + self.v_width) - self.size_w
                self.v_x_velocity *= -0.8

        current_env, _ = self.get_window_environment()
        physical_floor = current_env['y'] if self.y <= current_env['y'] + 15 else self.default_floor_y
        
        if self.v_y_velocity > 0 and self.y >= physical_floor:
            self.y = physical_floor
            self.v_y_velocity = 0.0
            self.v_x_velocity = 0.0
            
            if getattr(self, 'heavy_fall', False):
                self.trigger_landing_shake()
            else:
                self.current_state = 'idle'
            
        self.update_position()
        self.schedule_loop(20, self.physics_loop)
        
    def _fsm_zygarde_launched_flyer(self):
        self.v_y_velocity += 1.5 
        self.y += self.v_y_velocity
        self.x += self.v_x_velocity
        
        if getattr(self, 'can_screen_wrap', False):
            if self.x <= self.v_x - self.size_w: self.x = self.v_x + self.v_width
            elif self.x >= self.v_x + self.v_width: self.x = self.v_x - self.size_w
        else:
            if self.x <= self.v_x:
                self.x = self.v_x
                self.v_x_velocity *= -0.8
            elif self.x >= (self.v_x + self.v_width) - self.size_w:
                self.x = (self.v_x + self.v_width) - self.size_w
                self.v_x_velocity *= -0.8

        # FIX: Instead of crashing, when vertical inertia becomes falling, gently resume flight.
        if self.v_y_velocity > 0:
            self.v_y_velocity = 0.0
            self.v_x_velocity = 0.0
            self.floor_y = self.y
            self.current_state = 'ascending'
            
        self.update_position()
        self.schedule_loop(20, self.physics_loop)