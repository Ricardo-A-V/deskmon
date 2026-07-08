import random
import math
import os

class RayquazaMechanics:
    def cancel_rayquaza_arts(self):
        for attr in ['rayquaza_phase', 'rayquaza_start_x', 'rayquaza_end_x', 'rayquaza_target_y', 'rayquaza_global_timer', 'rayquaza_sweeps_done', 'rayquaza_sweeps_total', 'rayquaza_sweep_duration']:
            if hasattr(self, attr): delattr(self, attr)
            
        if self.current_state not in ['dragged', 'exiting']:
            if getattr(self, 'is_flying', False):
                self.floor_y = self.y
                self.current_state = 'ascending'
            else:
                self.current_state = 'falling'
                
        targets = getattr(self, 'rayquaza_targets', [])
        self.rayquaza_targets = []
        for target in targets:
            if target and target.window.winfo_exists():
                target.rayquaza_master = None
                if target.current_state == 'rayquaza_cyclone_victim' and target.current_state not in ['dragged', 'exiting']:
                    target.current_state = 'falling'
                    
        master = getattr(self, 'rayquaza_master', None)
        self.rayquaza_master = None
        if master and master.window.winfo_exists():
            master.cancel_rayquaza_arts()

    def _fsm_rayquaza_channeling(self):
        if not hasattr(self, 'rayquaza_start_x'):
            # FIX: Extremes at 1/8 (12.5%) and 7/8 (87.5%) of screen
            is_left = random.choice([True, False])
            self.rayquaza_start_x = self.v_x + (self.v_width * 0.125) if is_left else self.v_x + (self.v_width * 0.875)
            self.rayquaza_end_x = self.v_x + (self.v_width * 0.875) if is_left else self.v_x + (self.v_width * 0.125)
            self.rayquaza_target_y = self.v_y + (self.v_height * 0.15) 

        if getattr(self, 'rayquaza_phase', 0) == 0:
            target_x = self.rayquaza_start_x - (self.size_w // 2)
            dx = target_x - self.x
            dy = self.rayquaza_target_y - self.y
            dist = math.sqrt(dx**2 + dy**2)

            self.is_facing_right = (dx > 0)
            fly_speed = self.speed * 2.5
            
            if dist > fly_speed:
                self.x += (dx/dist) * fly_speed
                self.y += (dy/dist) * fly_speed
            else:
                self.x = target_x
                self.y = self.rayquaza_target_y
                self.rayquaza_phase = 1
                
                self.rayquaza_timer = self.rayquaza_sweep_duration 
                self.rayquaza_global_timer = 0 # Constant master chronometer for victims
                
                self.is_facing_right = (self.rayquaza_end_x > self.rayquaza_start_x)
                
                active_targets = []
                for target in getattr(self, 'rayquaza_targets', []):
                    if target and target.window.winfo_exists() and target.current_state not in ['exiting', 'dragged', 'spawning_wild', 'despawning_wild', 'falling_pokeball', 'falling_egg']:
                        
                        if target.current_state.startswith('dark_'): target.cancel_dark_arts()
                        elif target.current_state.startswith('mewtwo_'): target.cancel_mewtwo_arts()
                        elif target.current_state in ['hooh_channeling', 'panic_run']: target.cancel_hooh_arts()
                        elif target.current_state in ['kyogre_channeling', 'deluge_float']: target.cancel_kyogre_arts()
                        elif target.current_state == 'groudon_channeling': target.cancel_groudon_arts()
                        elif target.current_state in ['lugia_channeling', 'lugia_dash']: target.cancel_lugia_arts()
                        elif target.current_state == 'tk_channeling':
                            target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
                            if getattr(target, 'tk_target', None):
                                if getattr(target.tk_target, 'current_state', '') in ['tk_controlled', 'tk_lifted']:
                                    t_targ = target.tk_target
                                    t_w = t_targ.size_w if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size
                                    t_h = t_targ.size_h if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size
                                    target.manage_tk_aura(t_targ.canvas, t_w, t_h, False)
                                    t_targ.current_state = 'falling'
                                    if hasattr(t_targ, 'tk_master'): t_targ.tk_master = None
                            target.tk_target = None
                        elif target.current_state == 'tk_lifted':
                            target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
                            if getattr(target, 'tk_master', None):
                                target.tk_master.tk_target = None
                                target.tk_master.manage_tk_aura(target.tk_master.canvas, target.tk_master.size_w, target.tk_master.size_h, False)
                                target.tk_master.current_state = 'falling'
                            target.tk_master = None
                        elif target.current_state == 'bubbled':
                            target.manage_bubble_vfx(False)
                            target.show_bubble_burst_vfx()

                        if getattr(target, 'is_glitching', False):
                            target.is_glitching = False
                            target.glitch_teleports_left = 0
                            target.glitch_cooldown = 12000

                        target.canvas.itemconfig(target.canvas_image_id, state='normal')
                        target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
                        try: target.window.attributes('-alpha', 1.0)
                        except: pass
                        
                        target.current_state = 'rayquaza_cyclone_victim'
                        target.rayquaza_master = self
                        target.rayquaza_angle_offset = random.uniform(0, 2 * math.pi)
                        target.anchored_hwnd = None
                        active_targets.append(target)
                self.rayquaza_targets = active_targets

        elif self.rayquaza_phase == 1:
            self.rayquaza_timer -= 1
            self.rayquaza_global_timer += 1
            
            progress = (self.rayquaza_sweep_duration - self.rayquaza_timer) / float(self.rayquaza_sweep_duration)
            current_target_x = self.rayquaza_start_x + (self.rayquaza_end_x - self.rayquaza_start_x) * progress - (self.size_w // 2)
            
            self.x = current_target_x
            
            # MATHEMATICAL FIX: Pronounced oscillation. (80 px travel at soft 0.05 pace)
            self.y = self.rayquaza_target_y + math.sin(self.rayquaza_global_timer * 0.05) * 80.0
            
            if self.rayquaza_timer % 3 == 0:
                self.show_emerald_cyclone_vfx(is_master=True)

            if self.rayquaza_timer <= 0:
                self.rayquaza_sweeps_done += 1
                
                if self.rayquaza_sweeps_done >= self.rayquaza_sweeps_total:
                    for target in getattr(self, 'rayquaza_targets', []):
                        if target and target.window.winfo_exists():
                            target.rayquaza_master = None
                            if target.current_state == 'rayquaza_cyclone_victim':
                                target.current_state = 'thrown'
                                target.v_y_velocity = random.uniform(-5.0, 5.0) 
                                target.v_x_velocity = random.uniform(-40.0, 40.0) 
                                
                    self.rayquaza_targets = []
                    if getattr(self, 'is_flying', False):
                        self.floor_y = self.y 
                        self.current_state = 'ascending'
                    else:
                        self.current_state = 'falling'
                        
                    for attr in ['rayquaza_phase', 'rayquaza_start_x', 'rayquaza_end_x', 'rayquaza_target_y', 'rayquaza_global_timer', 'rayquaza_sweeps_done', 'rayquaza_sweeps_total', 'rayquaza_sweep_duration']:
                        if hasattr(self, attr): delattr(self, attr)
                else:
                    self.rayquaza_start_x, self.rayquaza_end_x = self.rayquaza_end_x, self.rayquaza_start_x
                    self.is_facing_right = (self.rayquaza_end_x > self.rayquaza_start_x)
                    self.rayquaza_sweep_duration = max(30, int(self.rayquaza_sweep_duration * 0.85))
                    self.rayquaza_timer = self.rayquaza_sweep_duration

        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_rayquaza_cyclone_victim(self):
        master = getattr(self, 'rayquaza_master', None)
        if not master or master.current_state != 'rayquaza_channeling' or not master.window.winfo_exists():
            if self.current_state not in ['dragged', 'exiting']:
                self.current_state = 'falling'
            self.schedule_loop(30, self.physics_loop)
            return

        elapsed = getattr(master, 'rayquaza_global_timer', 0)
        
        m_cx = master.x + master.size_w / 2
        m_cy = master.y + master.size_h / 2
        
        # Adjusted so max ring doesn't exceed inertia limits
        radius_x = max(200.0, (self.v_width * 0.4) - (elapsed * 1.5))
        radius_y = max(30.0, 100.0 - (elapsed * 0.2)) 
        
        angular_speed = 0.02 + (elapsed * 0.0003)
        self.rayquaza_angle_offset += angular_speed
        
        target_x = m_cx + math.cos(self.rayquaza_angle_offset) * radius_x - self.size_w / 2
        target_y = m_cy + math.sin(self.rayquaza_angle_offset) * radius_y - self.size_h / 2 + 80 
        
        # PHYSICAL FIX: 'Rubber-banding' elimination.
        # Read how fast Rayquaza is going on this particular trip
        sweep_dur = getattr(master, 'rayquaza_sweep_duration', 120)
        
        # If Rayquaza accelerates (sweep_dur drops), multiplier goes up to 400%
        speed_multiplier = 120.0 / float(max(1, sweep_dur)) 
        
        base_pull = min(0.15, 0.02 + (elapsed * 0.0005))
        
        # Vectorial separation of tensors:
        # Ultra-aggressive X pull so they don't fall behind (up to 90% instant anchor)
        pull_strength_x = min(0.9, base_pull * speed_multiplier * 1.5) 
        # Soft Y pull to maintain organic levitation feel
        pull_strength_y = min(0.3, base_pull * speed_multiplier) 
        
        self.x += (target_x - self.x) * pull_strength_x
        self.y += (target_y - self.y) * pull_strength_y
            
        if elapsed % 5 == 0:
            self.show_emerald_cyclone_vfx(is_master=False)

        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def show_emerald_cyclone_vfx(self, is_master=False):
        if getattr(self, 'current_state', 'exiting') == 'exiting': return
        particles = []
        cx = self.size_w // 2
        cy = self.size_h // 2
        
        count = random.randint(5, 8) if is_master else random.randint(2, 4)
        
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(5.0, 10.0) if is_master else random.uniform(3.0, 6.0)
            
            # Flattened projection to pair with orbital ellipse
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * (speed * 0.3) - 1.0
            
            size = random.choice([2, 3])
            color = random.choice(["#2ECC71", "#27AE60", "#1ABC9C", "#58D68D", "#A9DFBF"])
            
            pid = self.canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline=color, tags="vfx_emerald")
            particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': random.randint(10, 20)})
            
        def animate_cyclone():
            if getattr(self, 'current_state', 'exiting') == 'exiting': return
            alive_count = 0
            for p in particles:
                if p['life'] > 0:
                    self.canvas.move(p['id'], p['vx'], p['vy'])
                    
                    p['vx'] *= 0.85
                    p['vy'] -= 0.5 
                    
                    p['life'] -= 1
                    alive_count += 1
                elif p['life'] == 0:
                    self.canvas.delete(p['id'])
                    p['life'] = -1
                    
            if alive_count > 0:
                self.schedule_loop(30, animate_cyclone)
                
        animate_cyclone()

