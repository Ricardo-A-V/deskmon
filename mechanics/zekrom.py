import random
import math
import tkinter as tk

class ZekromMechanics:
    def cancel_zekrom_arts(self):
        for attr in ['zekrom_phase', 'zekrom_timer', 'zekrom_vfx_active', 'zekrom_target_x', 'zekrom_target_y', 'zekrom_vx', 'zekrom_vy', 'zekrom_pulse']:
            if hasattr(self, attr): delattr(self, attr)

        self.canvas.delete("vfx_zekrom")
        self.canvas.itemconfig(self.canvas_image_id, state='normal')

        if self.current_state not in ['dragged', 'exiting']:
            if getattr(self, 'is_flying', False):
                self.floor_y = getattr(self, 'target_floor_y', self.y)
                self.current_state = 'ascending'
            else:
                self.current_state = 'falling'

    def _fsm_zekrom_channeling(self):
        if not hasattr(self, 'zekrom_phase'):
            self.zekrom_phase = 0
            self.zekrom_timer = 0
            self.zekrom_vfx_active = True
            self.zekrom_vfx_radius = 0.0
            self.zekrom_pulse = 0.0
            
            self.canvas.itemconfig(self.canvas_image_id, state='hidden')
            self.zekrom_aura_loop()
            
        target_y = self.v_y + (self.v_height * 0.25) 

        if self.zekrom_phase == 0:
            self.y -= 2.0
            self.zekrom_vfx_radius = min(1.0, self.zekrom_vfx_radius + 0.02)
            
            if self.y <= target_y:
                self.y = target_y
                self.zekrom_phase = 1
                self.zekrom_timer = 60 

        elif self.zekrom_phase == 1:
            self.zekrom_timer -= 1
            # FIX: Incremento reducido de 0.2 a 0.05 para una flotación mucho más lenta y pesada
            self.fly_amplitude = getattr(self, 'fly_amplitude', 0) + 0.05 
            self.y = target_y + math.sin(self.fly_amplitude) * 10
            
            if self.zekrom_timer <= 0:
                self.zekrom_phase = 2
                self.zekrom_timer = 15 
                
                self.zekrom_target_x = random.randint(self.v_x + 50, self.v_x + self.v_width - self.size_w - 50)
                self.zekrom_target_y = self.default_floor_y
                
                self.is_facing_right = (self.zekrom_target_x > self.x)
                
                dx = self.x - self.zekrom_target_x
                dy = self.y - self.zekrom_target_y
                dist = max(1.0, math.sqrt(dx**2 + dy**2))
                self.zekrom_vx = (dx / dist) * 2.0
                self.zekrom_vy = (dy / dist) * 2.0

        elif self.zekrom_phase == 2:
            self.zekrom_timer -= 1
            self.x += self.zekrom_vx
            self.y += self.zekrom_vy
            
            if self.zekrom_timer <= 0:
                self.zekrom_phase = 3
                
                dx = self.zekrom_target_x - self.x
                dy = self.zekrom_target_y - self.y
                dist = max(1.0, math.sqrt(dx**2 + dy**2))
                
                dash_speed = 90.0 
                self.zekrom_vx = (dx / dist) * dash_speed
                self.zekrom_vy = (dy / dist) * dash_speed

        elif self.zekrom_phase == 3:
            self.x += self.zekrom_vx
            self.y += self.zekrom_vy
            
            current_env, _ = self.get_window_environment()
            physical_floor = current_env['y'] if self.y <= current_env['y'] + 45 else self.default_floor_y
            
            if self.y >= physical_floor:
                self.y = physical_floor
                self.trigger_landing_shake()
                
                self.canvas.itemconfig(self.canvas_image_id, state='normal')
                self.zekrom_vfx_active = False
                self.canvas.delete("vfx_zekrom")
                
                self.zekrom_explode()
                
                self.current_state = 'idle'
                self.zekrom_cooldown = 72000 
                for attr in ['zekrom_phase', 'zekrom_timer', 'zekrom_vfx_active', 'zekrom_vx', 'zekrom_vy', 'zekrom_pulse']:
                    if hasattr(self, attr): delattr(self, attr)

        self.update_position()
        self.schedule_loop(30, self.physics_loop) 

    def zekrom_aura_loop(self):
        if getattr(self, 'current_state', 'exiting') == 'exiting': return
        if not getattr(self, 'zekrom_vfx_active', False): return

        self.canvas.delete("vfx_zekrom")
        cx = self.size_w / 2
        cy = self.size_h / 2
        
        # Aumentamos el margen de seguridad a 5 píxeles para que la expansión exterior no choque con los bordes de la ventana
        max_r = (min(self.size_w, self.size_h) / 2) - 5 
        base_radius_mult = getattr(self, 'zekrom_vfx_radius', 1.0)
        
        r1_base = max_r * base_radius_mult
        
        if r1_base > 5:
            self.zekrom_pulse = getattr(self, 'zekrom_pulse', 0) + 0.15
            
            # Pulso exterior leve (3% de variación)
            outer_pulse_mod = math.sin(self.zekrom_pulse) * 0.05
            r1 = max_r * (base_radius_mult + outer_pulse_mod)
            
            # Pulso interior inestable y notorio (10% de variación)
            inner_pulse_mod = math.sin(self.zekrom_pulse) * 0.05
            r2 = r1 * (0.85 + inner_pulse_mod)
            r3 = r1 * (0.60 + inner_pulse_mod)
            
            self.canvas.create_oval(cx-r1, cy-r1, cx+r1, cy+r1, fill="#008B8B", outline="#008B8B", tags="vfx_zekrom")
            self.canvas.create_oval(cx-r2, cy-r2, cx+r2, cy+r2, fill="#00FFFF", outline="#00FFFF", tags="vfx_zekrom")
            self.canvas.create_oval(cx-r3, cy-r3, cx+r3, cy+r3, fill="#FFFFFF", outline="#FFFFFF", tags="vfx_zekrom")
            
            for _ in range(3):
                a1 = random.uniform(0, 2*math.pi)
                a2 = random.uniform(0, 2*math.pi)
                lr1 = random.uniform(r2, r1)
                lr2 = random.uniform(r2, r1)
                self.canvas.create_line(cx+math.cos(a1)*lr1, cy+math.sin(a1)*lr1, cx+math.cos(a2)*lr2, cy+math.sin(a2)*lr2, fill="#FFFFFF", width=3, tags="vfx_zekrom")

        self.window.after(40, self.zekrom_aura_loop)

    def zekrom_explode(self):
        impact_radius = 800 
        self.trigger_global_shockwave(impact_radius)

        particles = []
        cx = self.size_w / 2
        cy = self.size_h / 2
        for _ in range(40):
            angle = random.uniform(0, 2*math.pi)
            speed = random.uniform(20.0, 45.0)
            pid = self.canvas.create_line(cx, cy, cx+math.cos(angle)*15, cy+math.sin(angle)*15, fill="#00FFFF", width=4, tags="vfx_zekrom_exp")
            particles.append({'id': pid, 'vx': math.cos(angle)*speed, 'vy': math.sin(angle)*speed, 'life': 12})
            
        def animate_local_explosion():
            if getattr(self, 'current_state', 'exiting') == 'exiting': return
            alive = 0
            for p in particles:
                if p['life'] > 0:
                    self.canvas.move(p['id'], p['vx'], p['vy'])
                    p['vx'] *= 0.80
                    p['vy'] *= 0.80
                    p['life'] -= 1
                    alive += 1
                else:
                    self.canvas.delete(p['id'])
            if alive > 0: self.window.after(30, animate_local_explosion)
        animate_local_explosion()

        if getattr(self, 'get_all_pets', None):
            for target in self.get_all_pets():
                # FIX ESTRUCTURAL: Ignorar siempre a los huevos
                if target != self and target.current_state != 'exiting' and not getattr(target, 'is_egg', False):
                    dist = math.sqrt((self.x - target.x)**2 + (self.y - target.y)**2)
                    if dist <= impact_radius:
                        self.apply_paralysis(target)

    def trigger_global_shockwave(self, max_radius):
        wave_win = tk.Toplevel(self.window.master)
        wave_win.title("VFX_Zekrom_Ignore")
        wave_win.overrideredirect(True)
        wave_win.attributes('-topmost', True)
        
        TRANS_COLOR = '#010101'
        wave_win.config(bg=TRANS_COLOR)
        try: wave_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass
        
        win_size = max_radius * 2
        center_x = int(self.x + self.size_w/2 - win_size/2)
        center_y = int(self.y + self.size_h/2 - win_size/2)
        wave_win.geometry(f"{win_size}x{win_size}+{center_x}+{center_y}")
        
        w_canvas = tk.Canvas(wave_win, width=win_size, height=win_size, bg=TRANS_COLOR, highlightthickness=0)
        w_canvas.pack()
        
        state = {'radius': 10.0, 'alpha_width': 25.0}
        
        def animate_wave():
            if not wave_win.winfo_exists(): return
            
            w_canvas.delete("wave")
            state['radius'] += 45.0 
            state['alpha_width'] *= 0.85 
            
            if state['radius'] >= max_radius or state['alpha_width'] < 1.0:
                wave_win.destroy()
                return
                
            r = state['radius']
            cx = win_size / 2
            cy = win_size / 2
            
            w_canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline="#00FFFF", width=int(state['alpha_width']), tags="wave")
            wave_win.after(20, animate_wave)
            
        animate_wave()

    def apply_paralysis(self, target):
        if target.current_state.startswith('dark_'): target.cancel_dark_arts()
        elif target.current_state == 'tk_channeling':
            target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
            if getattr(target, 'tk_target', None):
                t_targ = target.tk_target
                target.manage_tk_aura(t_targ.canvas, t_targ.size_w if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size, t_targ.size_h if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size, False)
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
        elif target.current_state in ['digging_in', 'digging', 'digging_out']:
            target.canvas.itemconfig(target.canvas_image_id, state='normal')
            target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
            
        if getattr(target, 'is_glitching', False):
            target.is_glitching = False
            target.glitch_teleports_left = 0
            
        for prefix, cancel_func in [('mewtwo_', 'cancel_mewtwo_arts'), ('hooh_', 'cancel_hooh_arts'), ('kyogre_', 'cancel_kyogre_arts'), ('groudon_', 'cancel_groudon_arts'), ('lugia_', 'cancel_lugia_arts'), ('rayquaza_', 'cancel_rayquaza_arts'), ('dialga_', 'cancel_dialga_arts'), ('palkia_', 'cancel_palkia_arts'), ('giratina_', 'cancel_giratina_arts')]:
            if target.current_state.startswith(prefix) and hasattr(target, cancel_func): getattr(target, cancel_func)()

        target.canvas.itemconfig(target.canvas_image_id, state='normal')
        try: target.window.attributes('-alpha', 1.0)
        except: pass

        target.current_state = 'zekrom_paralyzed'
        target.zekrom_para_timer = 300 
        target.v_x_velocity = 0.0
        target.v_y_velocity = 0.0
        
        target.zekrom_para_vfx_loop()

    def _fsm_zekrom_paralyzed(self):
        self.zekrom_para_timer -= 1
        
        gravity = 4.0 if getattr(self, 'heavy_fall', False) else 1.5
        self.v_y_velocity += gravity
        self.y += self.v_y_velocity
        
        current_env, _ = self.get_window_environment()
        physical_floor = current_env['y'] if self.y <= current_env['y'] + 15 else self.default_floor_y
        
        if self.y >= physical_floor:
            self.y = physical_floor
            self.v_y_velocity = 0.0
            
        self.update_position()
        
        if self.zekrom_para_timer <= 0:
            self.canvas.delete("vfx_para")
            if getattr(self, 'is_flying', False):
                self.floor_y = self.y
                self.current_state = 'ascending'
            else:
                self.current_state = 'idle'
                
        # FIX LÓGICO: Forzar la ejecución del bucle independientemente del estado para no matar el FSM
        self.schedule_loop(50, self.physics_loop)

    def zekrom_para_vfx_loop(self):
        if getattr(self, 'current_state', '') != 'zekrom_paralyzed': 
            self.canvas.delete("vfx_para")
            return
            
        self.canvas.delete("vfx_para")
        if random.randint(1, 100) <= 30: 
            cx = self.size_w / 2
            cy = self.size_h / 2
            rx = cx + random.randint(-20, 20)
            ry = cy + random.randint(-20, 20)
            self.canvas.create_line(rx-5, ry-5, rx+5, ry+5, fill="#FFFF00", width=2, tags="vfx_para")
            self.canvas.create_line(rx+5, ry-5, rx-5, ry+5, fill="#FFFF00", width=2, tags="vfx_para")
            
        self.window.after(100, self.zekrom_para_vfx_loop)