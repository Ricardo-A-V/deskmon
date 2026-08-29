import math
import random
import tkinter as tk

class DarkraiMechanics:
    def trigger_darkrai_arts(self):
        if not getattr(self, 'get_all_pets', None): return
        
        self.current_state = 'darkrai_shadow_walk'
        self.dark_mode = True 
        try: self.window.attributes('-alpha', 0.6)
        except: pass
        
        # Calculates absolute monitor center to coordinate the ambush
        screen_w = self.window.winfo_screenwidth()
        mon_index = int((self.x - self.v_x) // screen_w)
        self.darkrai_target_x = self.v_x + (mon_index * screen_w) + (screen_w // 2) - (self.size_w // 2)
        self.darkrai_target_y = self.v_y + (self.window.winfo_screenheight() // 2) - (self.size_h // 2)
        
        self.schedule_loop(50, self.physics_loop)

    def cancel_darkrai_arts(self):
        for attr in ['darkrai_timer', 'darkrai_target_x', 'darkrai_target_y', 'nightmare_timer', 'aoe_radius']:
            if hasattr(self, attr): delattr(self, attr)

        self.canvas.delete("darkrai_vfx")
        self.dark_mode = False
        self.surface_angle = 0 
        self.canvas.itemconfig(self.canvas_image_id, state='normal')
        
        # Destroys the overlay canvas instantly
        if hasattr(self, 'darkrai_aoe_win') and self.darkrai_aoe_win.winfo_exists():
            self.darkrai_aoe_win.destroy()

        # Immediate release of all dominated FSMs
        if getattr(self, 'get_all_pets', None):
            for p in self.get_all_pets():
                if getattr(p, 'dark_master', None) == self:
                    p.dark_master = None
                    if hasattr(p, 'interrupt_current_state'): p.interrupt_current_state()
                    p.current_state = 'thrown' 
                    p.surface_angle = 0
                    p.nightmare_filter = False
                    p.v_x_velocity = 0.0
                    p.v_y_velocity = 0.0

        if self.current_state not in ['dragged', 'exiting']:
            self.climbing_surface = 'floor'
            self.anchored_hwnd = None
            self.anchored_rect = None
            try: self.window.attributes('-alpha', 1.0)
            except: pass
            
            # FIX: Uses 'thrown' instead of 'falling'. 
            # This perfectly emulates the user releasing the entity, 
            # allowing flying types to organically recover their altitude without hitting the ground.
            self.current_state = 'thrown'
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0

    def _fsm_darkrai_shadow_walk(self):
        if self.current_state != 'darkrai_shadow_walk':
            self.cancel_darkrai_arts()
            self.schedule_loop(50, self.physics_loop)
            return
            
        dx = self.darkrai_target_x - self.x
        dy = self.darkrai_target_y - self.y
        dist = math.hypot(dx, dy)
        
        # Dynamically updates sprite facing direction
        self.is_facing_right = dx > 0
        
        if dist < 5.0:
            self.x = self.darkrai_target_x
            self.y = self.darkrai_target_y
            
            self.current_state = 'darkrai_channeling'
            self.darkrai_timer = 60 # 3 seconds
            self.dark_mode = False 
            try: self.window.attributes('-alpha', 1.0)
            except: pass
            
            self._spawn_aoe_field()
        else:
            dx_step = dx * 0.05
            dy_step = dy * 0.05
            self.x += dx_step
            self.y += dy_step
            
            # Thick shadow trail generation opposing current momentum
            if random.randint(1, 100) <= 80:
                cx, cy = self.size_w / 2, self.size_h / 2
                size = random.choice([6, 8, 12])
                pid = self.canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill="#1A1A1A", outline="#4B0082", width=2, tags="darkrai_vfx")
                self.canvas.tag_lower(pid, self.canvas_image_id)
                
                def fade_shadow(step, p_id):
                    if self.current_state != 'darkrai_shadow_walk' or not self.canvas.winfo_exists(): return
                    if step > 15: self.canvas.delete(p_id)
                    else:
                        self.canvas.move(p_id, -dx_step * 1.5, -dy_step * 1.5)
                        self.schedule_loop(20, lambda: fade_shadow(step+1, p_id))
                fade_shadow(0, pid)
                
        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def _spawn_aoe_field(self):
        self.darkrai_aoe_win = tk.Toplevel(self.window.master)
        self.darkrai_aoe_win.overrideredirect(True)
        self.darkrai_aoe_win.attributes('-topmost', True) 
        
        TRANS = '#010101'
        self.darkrai_aoe_win.config(bg=TRANS)
        try: self.darkrai_aoe_win.wm_attributes('-transparentcolor', TRANS)
        except: pass
        
        cx_abs = self.x + (self.size_w / 2)
        cy_abs = self.y + (self.size_h / 2)
        self.darkrai_aoe_win.geometry(f"1000x1000+{int(cx_abs - 500)}+{int(cy_abs - 500)}")
        
        self.aoe_canvas = tk.Canvas(self.darkrai_aoe_win, width=1000, height=1000, bg=TRANS, highlightthickness=0)
        self.aoe_canvas.pack()

    def _render_spirals(self):
        if not hasattr(self, 'aoe_canvas') or not self.aoe_canvas.winfo_exists(): return
        
        for _ in range(3): 
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(400.0, 500.0)
            color = random.choice(["#4B0082", "#8A2BE2", "#1A1A1A"])
            
            pid = self.aoe_canvas.create_rectangle(0, 0, 0, 0, fill=color, outline="")
            
            def animate_spiral(step, p_id, current_angle, current_dist):
                if self.current_state not in ['darkrai_channeling', 'darkrai_aoe'] or not hasattr(self, 'aoe_canvas') or not self.aoe_canvas.winfo_exists(): return
                if current_dist <= 20.0:
                    self.aoe_canvas.delete(p_id)
                    return
                
                current_dist *= 0.85 
                current_angle += 0.5
                
                px = 500 + math.cos(current_angle) * current_dist
                py = 500 + math.sin(current_angle) * current_dist
                s = random.choice([4, 5, 7])
                
                self.aoe_canvas.coords(p_id, px-s, py-s, px+s, py+s)
                self.schedule_loop(20, lambda: animate_spiral(step+1, p_id, current_angle, current_dist))
                
            animate_spiral(0, pid, angle, distance)

    def _fsm_darkrai_channeling(self):
        if self.current_state != 'darkrai_channeling':
            self.cancel_darkrai_arts()
            self.schedule_loop(50, self.physics_loop)
            return
            
        self.darkrai_timer -= 1
        
        if self.darkrai_timer % 3 == 0:
            self._render_spirals()
            
        if self.darkrai_timer <= 0:
            self.current_state = 'darkrai_aoe'
            self.darkrai_timer = 400 # 20 seconds AOE phase
            self.aoe_radius = 0.0 
            
        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def _purge_victim_state(self, target):
        # Sweeps and sanitizes ongoing external FSM modifications to prevent visual ghosting
        if getattr(target, 'current_state', '') == 'attacking':
            target.attack_target = None

        if getattr(target, 'current_state', '') == 'bubbled':
            if hasattr(target, 'manage_bubble_vfx'): target.manage_bubble_vfx(False)
            if hasattr(target, 'show_bubble_burst_vfx'): target.show_bubble_burst_vfx()

        if getattr(target, 'current_state', '') in ['digging_in', 'digging', 'digging_out']:
            target.canvas.itemconfig(target.canvas_image_id, state='normal')
            target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)

        if getattr(target, 'current_state', '') == 'tk_channeling':
            if hasattr(target, 'manage_tk_aura'): target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
            if getattr(target, 'tk_target', None):
                t_targ = target.tk_target
                if hasattr(target, 'manage_tk_aura'):
                    t_w = t_targ.size_w if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size
                    t_h = t_targ.size_h if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size
                    target.manage_tk_aura(t_targ.canvas, t_w, t_h, False)
                if hasattr(t_targ, 'interrupt_current_state'): t_targ.interrupt_current_state()
                t_targ.current_state = 'falling'
                if hasattr(t_targ, 'tk_master'): t_targ.tk_master = None
            target.tk_target = None
        elif getattr(target, 'current_state', '') == 'tk_lifted':
            if hasattr(target, 'manage_tk_aura'): target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
            if getattr(target, 'tk_master', None):
                target.tk_master.tk_target = None
                if hasattr(target.tk_master, 'manage_tk_aura'): target.tk_master.manage_tk_aura(target.tk_master.canvas, target.tk_master.size_w, target.tk_master.size_h, False)
                target.tk_master.current_state = 'falling'
            target.tk_master = None

        if getattr(target, 'is_glitching', False):
            target.is_glitching = False
            target.glitch_teleports_left = 0
            target.glitch_cooldown = 12000
            try: target.window.attributes('-alpha', 1.0)
            except: pass

        # Legendary routing sweep
        if target.current_state.startswith('mewtwo_') and hasattr(target, 'cancel_mewtwo_arts'): target.cancel_mewtwo_arts()
        elif target.current_state in ['hooh_channeling', 'panic_run'] and hasattr(target, 'cancel_hooh_arts'): target.cancel_hooh_arts()
        elif target.current_state in ['lugia_channeling', 'lugia_dash'] and hasattr(target, 'cancel_lugia_arts'): target.cancel_lugia_arts()
        elif target.current_state == 'kyogre_channeling' and hasattr(target, 'cancel_kyogre_arts'): target.cancel_kyogre_arts()
        elif target.current_state == 'groudon_channeling' and hasattr(target, 'cancel_groudon_arts'): target.cancel_groudon_arts()
        elif target.current_state == 'rayquaza_channeling' and hasattr(target, 'cancel_rayquaza_arts'): target.cancel_rayquaza_arts()
        elif target.current_state == 'dialga_channeling' and hasattr(target, 'cancel_dialga_arts'): target.cancel_dialga_arts()
        elif target.current_state == 'palkia_channeling' and hasattr(target, 'cancel_palkia_arts'): target.cancel_palkia_arts()
        elif target.current_state.startswith('giratina_') and hasattr(target, 'cancel_giratina_arts'): target.cancel_giratina_arts()
        elif target.current_state.startswith('reshiram_') and hasattr(target, 'cancel_reshiram_arts'): target.cancel_reshiram_arts()
        elif target.current_state.startswith('zekrom_') and hasattr(target, 'cancel_zekrom_arts'): target.cancel_zekrom_arts()
        elif target.current_state == 'kyurem_channeling' and hasattr(target, 'cancel_kyurem_arts'): target.cancel_kyurem_arts()
        elif target.current_state == 'xerneas_channeling' and hasattr(target, 'cancel_xerneas_arts'): target.cancel_xerneas_arts()
        elif target.current_state == 'yveltal_channeling' and hasattr(target, 'cancel_yveltal_arts'): target.cancel_yveltal_arts()
        elif target.current_state in ['zygarde_channeling', 'zygarde50_channeling'] and hasattr(target, 'cancel_zygarde_arts'): target.cancel_zygarde_arts()
        elif target.current_state == 'solgaleo_channeling' and hasattr(target, 'cancel_solgaleo_arts'): target.cancel_solgaleo_arts()
        elif target.current_state == 'lunala_channeling' and hasattr(target, 'cancel_lunala_arts'): target.cancel_lunala_arts()
        elif target.current_state == 'necrozma_channeling' and hasattr(target, 'cancel_necrozma_arts'): target.cancel_necrozma_arts()
        elif target.current_state == 'zacian_channeling' and hasattr(target, 'cancel_zacian_arts'): target.cancel_zacian_arts()
        elif target.current_state == 'zamazenta_channeling' and hasattr(target, 'cancel_zamazenta_arts'): target.cancel_zamazenta_arts()
        elif target.current_state == 'eternatus_channeling' and hasattr(target, 'cancel_eternatus_arts'): target.cancel_eternatus_arts()
        elif target.current_state.startswith('koraidon_') and hasattr(target, 'cancel_koraidon_arts'): target.cancel_koraidon_arts()
        elif target.current_state.startswith('miraidon_') and hasattr(target, 'cancel_miraidon_arts'): target.cancel_miraidon_arts()
        elif target.current_state == 'bird_channeling' and hasattr(target, 'cancel_bird_arts'): target.cancel_bird_arts()
        elif target.current_state in ['mew_channeling', 'mew_bounce', 'mew_tethered'] and hasattr(target, 'cancel_mew_arts'): target.cancel_mew_arts()
        elif target.current_state.startswith('beast_') and hasattr(target, 'cancel_beast_arts'): target.cancel_beast_arts()
        elif target.current_state in ['celebi_channeling', 'celebi_wait', 'celebi_freeze', 'celebi_revert_flight'] and hasattr(target, 'cancel_celebi_arts'): target.cancel_celebi_arts()
        elif target.current_state in ['regi_approach', 'regi_strike'] and hasattr(target, 'cancel_regi_arts'): target.cancel_regi_arts()
        elif target.current_state in ['jirachi_channeling', 'jirachi_vanished', 'jirachi_flyby'] and hasattr(target, 'cancel_jirachi_arts'): target.cancel_jirachi_arts()

    def _fsm_darkrai_aoe(self):
        if self.current_state != 'darkrai_aoe':
            self.cancel_darkrai_arts()
            self.schedule_loop(50, self.physics_loop)
            return
            
        self.darkrai_timer -= 1
        
        if self.darkrai_timer % 3 == 0:
            self._render_spirals()
            
        if self.aoe_radius < 400.0:
            self.aoe_radius += 4.0
            
        if hasattr(self, 'aoe_canvas') and self.aoe_canvas.winfo_exists():
            for _ in range(4):
                angle = random.uniform(0, 2 * math.pi)
                px = 500 + math.cos(angle) * self.aoe_radius
                py = 500 + math.sin(angle) * self.aoe_radius
                size = random.choice([2, 3])
                pid = self.aoe_canvas.create_rectangle(px-size, py-size, px+size, py+size, fill="#8A2BE2", outline="")
                
                def fade_aoe(step, p_id):
                    if not self.aoe_canvas.winfo_exists(): return
                    if step > 10: self.aoe_canvas.delete(p_id)
                    else:
                        self.aoe_canvas.move(p_id, 0, -2) 
                        self.aoe_canvas.after(30, lambda: fade_aoe(step+1, p_id))
                fade_aoe(0, pid)
        
        cx = self.x + (self.size_w / 2)
        cy = self.y + (self.size_h / 2)
        
        if getattr(self, 'get_all_pets', None):
            for p in self.get_all_pets():
                if p != self and p.current_state not in ['exiting', 'falling_pokeball'] and not getattr(p, 'is_egg', False) and not getattr(p, 'is_dragging', False):
                    pcx = p.x + (p.size_w / 2)
                    pcy = p.y + (p.size_h / 2)
                    
                    dx = cx - pcx
                    dy = cy - pcy
                    dist = max(1.0, math.hypot(dx, dy))
                    
                    if p.current_state != 'darkrai_nightmare':
                        # Applies sanity check and purges prior mechanics to avoid superposition
                        if p.current_state != 'dragged':
                            self._purge_victim_state(p)
                            
                        if dist <= self.aoe_radius:
                            if hasattr(p, 'cancel_darkrai_arts'): p.cancel_darkrai_arts() 
                            if hasattr(p, 'interrupt_current_state'): p.interrupt_current_state()
                            p.current_state = 'darkrai_nightmare'
                            p.nightmare_timer = self.darkrai_timer 
                            p.nightmare_filter = True 
                            p.dark_master = self
                            
                            p.v_x_velocity = -(dx / dist) * 2.5
                            p.v_y_velocity = -(dy / dist) * 2.5
                        else:
                            if hasattr(p, 'interrupt_current_state'): p.interrupt_current_state()
                            p.current_state = 'dragged'
                            p.dark_master = self
                            p.x += (dx / dist) * 6.0
                            p.y += (dy / dist) * 6.0
                            p.update_position()

        if self.darkrai_timer <= 0:
            self._spawn_teleport_explosion(self.x, self.y)
            self.cancel_darkrai_arts()
            self.schedule_loop(50, self.physics_loop)
            return
            
        self.schedule_loop(50, self.physics_loop)

    def _fsm_darkrai_nightmare(self):
        if self.current_state != 'darkrai_nightmare':
            self.surface_angle = 0
            self.nightmare_filter = False
            self.current_state = 'thrown'
            self.v_x_velocity = 0.0
            self.schedule_loop(50, self.physics_loop)
            return
            
        self.nightmare_timer -= 1

        self.surface_angle = (getattr(self, 'surface_angle', 0) + 5) % 360
        self.x += getattr(self, 'v_x_velocity', 0.0)
        self.y += getattr(self, 'v_y_velocity', 0.0)
        
        if self.x <= self.v_x:
            self.x = self.v_x
            self.v_x_velocity *= -1.0
        elif self.x >= (self.v_x + self.v_width) - self.size_w:
            self.x = (self.v_x + self.v_width) - self.size_w
            self.v_x_velocity *= -1.0
            
        if self.y <= self.v_y:
            self.y = self.v_y
            self.v_y_velocity *= -1.0
        elif self.y >= getattr(self, 'target_floor_y', self.default_floor_y):
            self.y = getattr(self, 'target_floor_y', self.default_floor_y)
            self.v_y_velocity *= -1.0
            
        if self.nightmare_timer <= 0:
            self.surface_angle = 0
            self.nightmare_filter = False
            self.current_state = 'thrown'
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            
        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def _spawn_teleport_explosion(self, abs_x, abs_y):
        exp_win = tk.Toplevel(self.window.master)
        exp_win.overrideredirect(True)
        exp_win.attributes('-topmost', True)
        
        TRANS = '#010101'
        exp_win.config(bg=TRANS)
        try: exp_win.wm_attributes('-transparentcolor', TRANS)
        except: pass
        
        exp_win.geometry(f"{self.size_w}x{self.size_h}+{int(abs_x)}+{int(abs_y)}")
        c = tk.Canvas(exp_win, width=self.size_w, height=self.size_h, bg=TRANS, highlightthickness=0)
        c.pack()
        
        cx = self.size_w / 2
        cy = self.size_h / 2
        
        particles = []
        for _ in range(40):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(5.0, 15.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.choice([3, 5, 7])
            color = random.choice(["#4B0082", "#1A1A1A", "#8A2BE2", "#000000"])
            pid = c.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline="")
            particles.append({'id': pid, 'x': cx, 'y': cy, 'vx': vx, 'vy': vy})
            
        def animate_exp(step):
            if not exp_win.winfo_exists(): return
            if step > 20:
                exp_win.destroy()
                return
            for p in particles:
                p['x'] += p['vx']
                p['y'] += p['vy']
                p['vx'] *= 0.85 
                p['vy'] *= 0.85
                c.coords(p['id'], p['x']-2, p['y']-2, p['x']+2, p['y']+2)
            exp_win.after(30, lambda: animate_exp(step + 1))
            
        animate_exp(0)