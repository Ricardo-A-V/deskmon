import math
import random
import tkinter as tk

class CresseliaMechanics:
    def trigger_cresselia_arts(self):
        if not getattr(self, 'get_all_pets', None): return
        
        self.current_state = 'cresselia_channeling'
        self.cresselia_timer = 100 
        
        self.schedule_loop(50, self.physics_loop)

    def cancel_cresselia_arts(self):
        for attr in ['cresselia_timer', 'cresselia_target_x', 'cresselia_target_y', 'blessing_timer', 'aurora_width', 'aurora_height', 'start_x', 'start_y', 'ascension_t']:
            if hasattr(self, attr): delattr(self, attr)

        self.canvas.delete("cresselia_vfx")
        self.canvas.itemconfig(self.canvas_image_id, state='normal')
        
        if hasattr(self, 'cresselia_aurora_win') and self.cresselia_aurora_win.winfo_exists():
            self.cresselia_aurora_win.destroy()

        if getattr(self, 'get_all_pets', None):
            for p in self.get_all_pets():
                if getattr(p, 'cresselia_master', None) == self:
                    p.cresselia_master = None
                    p.current_state = 'thrown' 
                    p.necrozma_bright_mod = 1.0 
                    p.v_x_velocity = 0.0
                    p.v_y_velocity = 0.0

        if self.current_state not in ['dragged', 'exiting']:
            self.climbing_surface = 'floor'
            self.anchored_hwnd = None
            self.anchored_rect = None
            
            self.current_state = 'thrown'
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0

    def _purge_victim_state(self, target):
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
        elif target.current_state.startswith('darkrai_') and hasattr(target, 'cancel_darkrai_arts'): target.cancel_darkrai_arts()
        elif target.current_state in ['regi_approach', 'regi_strike'] and hasattr(target, 'cancel_regi_arts'): target.cancel_regi_arts()
        elif target.current_state in ['jirachi_channeling', 'jirachi_vanished', 'jirachi_flyby'] and hasattr(target, 'cancel_jirachi_arts'): target.cancel_jirachi_arts()

    def _fsm_cresselia_channeling(self):
        if self.current_state != 'cresselia_channeling':
            self.cancel_cresselia_arts()
            self.schedule_loop(50, self.physics_loop)
            return
            
        self.cresselia_timer -= 1
        
        if self.cresselia_timer % 3 == 0:
            cx, cy = self.size_w / 2, self.size_h / 2
            color = random.choice(["#FF69B4", "#00FFFF", "#FFFACD"]) 
            pid = self.canvas.create_oval(cx-2, cy-2, cx+2, cy+2, fill=color, outline="", tags="cresselia_vfx")
            self.canvas.tag_lower(pid, self.canvas_image_id)
            
            angle = random.uniform(0, 2 * math.pi)
            
            def animate_pulse(step, p_id, current_dist):
                if self.current_state != 'cresselia_channeling' or not self.canvas.winfo_exists(): 
                    if self.canvas.winfo_exists(): self.canvas.delete(p_id)
                    return
                if step > 20: self.canvas.delete(p_id)
                else:
                    px = cx + math.cos(angle) * current_dist
                    py = cy + math.sin(angle) * current_dist
                    size = 2 + (step * 0.2)
                    self.canvas.coords(p_id, px-size, py-size, px+size, py+size)
                    self.schedule_loop(30, lambda: animate_pulse(step+1, p_id, current_dist + 3.0))
            
            animate_pulse(0, pid, 10.0)
            
        if self.cresselia_timer <= 0:
            self.current_state = 'cresselia_ascension'
            
            screen_w = self.window.winfo_screenwidth()
            screen_h = self.window.winfo_screenheight()
            mon_index = int((self.x - self.v_x) // screen_w)
            
            self.start_x = self.x
            self.start_y = self.y
            self.cresselia_target_x = self.v_x + (mon_index * screen_w) + (screen_w // 2) - (self.size_w // 2)
            self.cresselia_target_y = self.v_y + (screen_h // 8) - (self.size_h // 2)
            self.ascension_t = 0.0
            
        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def _fsm_cresselia_ascension(self):
        if self.current_state != 'cresselia_ascension':
            self.cancel_cresselia_arts()
            self.schedule_loop(50, self.physics_loop)
            return
            
        self.ascension_t += 0.02
        if self.ascension_t >= 1.0:
            self.ascension_t = 1.0
            self.x = self.cresselia_target_x
            self.y = self.cresselia_target_y
            self.current_state = 'cresselia_aurora'
            self.cresselia_timer = 400 
            self._spawn_aurora_field()
        else:
            t = self.ascension_t
            smooth_t = t * t * (3 - 2 * t) 
            
            base_x = self.start_x + (self.cresselia_target_x - self.start_x) * smooth_t
            base_y = self.start_y + (self.cresselia_target_y - self.start_y) * smooth_t
            
            curve_offset = math.sin(t * math.pi) * 150.0 
            
            self.x = base_x
            self.y = base_y - curve_offset
            self.is_facing_right = (self.cresselia_target_x - self.start_x) > 0
            
        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def _spawn_aurora_field(self):
        self.cresselia_aurora_win = tk.Toplevel(self.window.master)
        self.cresselia_aurora_win.overrideredirect(True)
        self.cresselia_aurora_win.attributes('-topmost', True) 
        
        TRANS = '#010101'
        self.cresselia_aurora_win.config(bg=TRANS)
        try: self.cresselia_aurora_win.wm_attributes('-transparentcolor', TRANS)
        except: pass
        
        self.aurora_width = self.v_width
        self.aurora_height = self.v_height // 10
        self.cresselia_aurora_win.geometry(f"{self.aurora_width}x{self.aurora_height}+{self.v_x}+{self.v_y}")
        
        self.aurora_canvas = tk.Canvas(self.cresselia_aurora_win, width=self.aurora_width, height=self.aurora_height, bg=TRANS, highlightthickness=0)
        self.aurora_canvas.pack()

    def _spawn_lunar_pulse(self, abs_x, abs_y):
        # Spawns a massive decoupled window to render the final blast without cropping
        pulse_win = tk.Toplevel(self.window.master)
        pulse_win.overrideredirect(True)
        pulse_win.attributes('-topmost', True)
        
        TRANS = '#010101'
        pulse_win.config(bg=TRANS)
        try: pulse_win.wm_attributes('-transparentcolor', TRANS)
        except: pass
        
        pulse_win.geometry(f"1200x1200+{int(abs_x - 600)}+{int(abs_y - 600)}")
        c = tk.Canvas(pulse_win, width=1200, height=1200, bg=TRANS, highlightthickness=0)
        c.pack()
        
        cx, cy = 600, 600
        
        # Dual-layer shockwave
        pid_outer = c.create_oval(cx-10, cy-10, cx+10, cy+10, outline="#00FFFF", width=8)
        pid_inner = c.create_oval(cx-5, cy-5, cx+5, cy+5, outline="#FF69B4", width=4)
        
        def animate_pulse(step, radius):
            if not pulse_win.winfo_exists(): return
            if step > 20:
                pulse_win.destroy()
                return
            
            # Rapid kinetic expansion (80px per frame)
            radius += 40.0
            
            c.coords(pid_outer, cx-radius, cy-radius, cx+radius, cy+radius)
            c.coords(pid_inner, cx-(radius*0.8), cy-(radius*0.8), cx+(radius*0.8), cy+(radius*0.8))
            
            pulse_win.after(30, lambda: animate_pulse(step + 1, radius))
            
        animate_pulse(0, 10.0)

    def _fsm_cresselia_aurora(self):
        if self.current_state != 'cresselia_aurora':
            self.cancel_cresselia_arts()
            self.schedule_loop(50, self.physics_loop)
            return
            
        self.cresselia_timer -= 1
        
        if hasattr(self, 'aurora_canvas') and self.aurora_canvas.winfo_exists() and self.cresselia_timer % 4 == 0:
            colors = ["#FFB6C1", "#E0FFFF", "#FFFACD", "#FFFFFF"] 
            
            for _ in range(random.randint(1, 2)): 
                px = random.uniform(0, self.aurora_width)
                size = random.choice([4, 6, 8])
                pid = self.aurora_canvas.create_oval(px, -10, px+size, -10+size, fill=random.choice(colors), outline="")
                
                speed_y = random.uniform(2.0, 5.0) 
                phase = random.uniform(0, math.pi * 2)
                amp = random.uniform(1.0, 3.0)
                
                def animate_dust(step, p_id, current_x, current_y, spd_y, ph, am, sz):
                    if not hasattr(self, 'aurora_canvas') or not self.aurora_canvas.winfo_exists(): return
                    
                    if current_y > self.aurora_height or step > 150: 
                        self.aurora_canvas.delete(p_id)
                    else:
                        drift = math.sin(step * 0.05 + ph) * am
                        current_x += drift
                        current_y += spd_y
                        self.aurora_canvas.coords(p_id, current_x, current_y, current_x+sz, current_y+sz)
                        self.aurora_canvas.after(30, lambda: animate_dust(step+1, p_id, current_x, current_y, spd_y, ph, am, sz))
                
                animate_dust(0, pid, px, -10, speed_y, phase, amp, size)
        
        if self.cresselia_timer % 10 == 0 and getattr(self, 'get_all_pets', None):
            for p in self.get_all_pets():
                if p != self and p.current_state not in ['exiting', 'falling_pokeball'] and not getattr(p, 'is_egg', False):
                    if p.current_state != 'cresselia_blessing':
                        if hasattr(self, '_purge_victim_state'): self._purge_victim_state(p)
                        
                        p.current_state = 'cresselia_blessing'
                        p.blessing_timer = self.cresselia_timer
                        p.cresselia_master = self
                        
                        # FIX: Triples base speed during the sprint injection
                        p.v_x_velocity = random.choice([-7.0, 7.0])
                        p.v_y_velocity = 0.0
                    else:
                        p.blessing_timer = self.cresselia_timer

        if self.cresselia_timer <= 0:
            self._spawn_lunar_pulse(self.x + self.size_w/2, self.y + self.size_h/2)
            self.cancel_cresselia_arts()
            self.schedule_loop(50, self.physics_loop)
            return
            
        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def _fsm_cresselia_blessing(self):
        if self.current_state != 'cresselia_blessing':
            self.necrozma_bright_mod = 1.0
            self.current_state = 'thrown'
            self.v_x_velocity = 0.0
            self.schedule_loop(50, self.physics_loop)
            return
            
        self.blessing_timer -= 1
        
        # FIX: Adjusted frequency modifier to 0.08 to force an extremely fluid fade in/out
        self.necrozma_bright_mod = 2.0 + (math.sin(self.blessing_timer * 0.08) * 1.5)

        self.is_facing_right = self.v_x_velocity > 0
        self.x += getattr(self, 'v_x_velocity', 0.0)
        
        if self.x <= self.v_x:
            self.x = self.v_x
            self.v_x_velocity *= -1.0
        elif self.x >= (self.v_x + self.v_width) - self.size_w:
            self.x = (self.v_x + self.v_width) - self.size_w
            self.v_x_velocity *= -1.0
            
        if getattr(self, 'is_flying', False):
            target_y = getattr(self, 'target_floor_y', self.default_floor_y)
            dy = target_y - self.y
            self.y += dy * 0.1 
        else:
            self.y = getattr(self, 'target_floor_y', self.default_floor_y)
            
        if self.blessing_timer <= 0:
            self.necrozma_bright_mod = 1.0
            self.current_state = 'thrown'
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            
        self.update_position()
        self.schedule_loop(50, self.physics_loop)