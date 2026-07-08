import random
import math
import tkinter as tk

class ReshiramMechanics:
    def cancel_reshiram_arts(self):
        # Destruir proyectil externo si existe
        if hasattr(self, 'res_win') and self.res_win and self.res_win.winfo_exists():
            self.res_win.destroy()
            self.res_win = None

        for attr in ['res_phase', 'res_timer', 'res_target_x', 'res_target_y', 'res_vx', 'res_vy', 'res_pulse']:
            if hasattr(self, attr): delattr(self, attr)

        if self.current_state not in ['dragged', 'exiting']:
            if getattr(self, 'is_flying', False):
                self.floor_y = getattr(self, 'target_floor_y', self.y)
                self.current_state = 'ascending'
            else:
                self.current_state = 'falling'

    def _fsm_reshiram_channeling(self):
        if not hasattr(self, 'res_phase'):
            self.res_phase = 0
            self.res_timer = 0
            self.res_pulse = 0.0
            self.res_vfx_radius = 0.0
            
            # 1. Spawn de la ventana independiente para el proyectil esférico
            self.res_win = tk.Toplevel(self.window.master)
            self.res_win.overrideredirect(True)
            self.res_win.attributes('-topmost', True)
            TRANS_COLOR = '#010101'
            self.res_win.config(bg=TRANS_COLOR)
            try: self.res_win.wm_attributes('-transparentcolor', TRANS_COLOR)
            except: pass
            
            self.res_size = 250 
            self.res_canvas = tk.Canvas(self.res_win, width=self.res_size, height=self.res_size, bg=TRANS_COLOR, highlightthickness=0)
            self.res_canvas.pack()
            
            # Coordenadas iniciales: Centro de Reshiram
            self.res_x = self.x + self.size_w / 2 - self.res_size / 2
            self.res_y = self.y + self.size_h / 2 - self.res_size / 2
            self.res_win.geometry(f"{self.res_size}x{self.res_size}+{int(self.res_x)}+{int(self.res_y)}")
            
            self.res_particles = []
            self.reshiram_sphere_loop()
            
        # 2. Reshiram se queda inmóvil recargando
        self.v_x_velocity = 0.0
        self.v_y_velocity = 0.0
        if not getattr(self, 'is_flying', False):
            current_env, _ = self.get_window_environment()
            physical_floor = current_env['y'] if self.y <= current_env['y'] + 15 else self.default_floor_y
            if self.y < physical_floor:
                self.y += 4.0
                if self.y > physical_floor: self.y = physical_floor
        
        # 3. Línea Temporal del Proyectil (Esfera)
        target_y = self.v_y + (self.v_height * 0.25) - self.res_size / 2

        if self.res_phase == 0:
            self.res_y -= 4.0 
            self.res_vfx_radius = min(1.0, self.res_vfx_radius + 0.02)
            
            if self.res_y <= target_y:
                self.res_y = target_y
                self.res_phase = 1
                self.res_timer = 60 

        elif self.res_phase == 1:
            self.res_timer -= 1
            self.fly_amplitude = getattr(self, 'fly_amplitude', 0) + 0.05 
            self.res_y = target_y + math.sin(self.fly_amplitude) * 10
            
            if self.res_timer <= 0:
                self.res_phase = 2
                self.res_timer = 15 
                
                self.res_target_x = random.randint(self.v_x + 50, self.v_x + self.v_width - self.res_size - 50)
                self.res_target_y = self.default_floor_y - self.res_size / 2
                
                self.is_facing_right = (self.res_target_x > self.x)
                
                dx = self.res_x - self.res_target_x
                dy = self.res_y - self.res_target_y
                dist = max(1.0, math.sqrt(dx**2 + dy**2))
                self.res_vx = (dx / dist) * 2.0
                self.res_vy = (dy / dist) * 2.0

        elif self.res_phase == 2:
            self.res_timer -= 1
            self.res_x += self.res_vx
            self.res_y += self.res_vy
            
            if self.res_timer <= 0:
                self.res_phase = 3
                
                dx = self.res_target_x - self.res_x
                dy = self.res_target_y - self.res_y
                dist = max(1.0, math.sqrt(dx**2 + dy**2))
                
                dash_speed = 90.0 
                self.res_vx = (dx / dist) * dash_speed
                self.res_vy = (dy / dist) * dash_speed

        elif self.res_phase == 3:
            self.res_x += self.res_vx
            self.res_y += self.res_vy
            
            sphere_feet_y = self.res_y + self.res_size - 50
            if sphere_feet_y >= self.default_floor_y:
                self.trigger_landing_shake()
                self.reshiram_explode()
                
                if hasattr(self, 'res_win') and self.res_win:
                    self.res_win.destroy()
                    self.res_win = None
                
                self.current_state = 'idle'
                self.reshiram_cooldown = 72000 
                for attr in ['res_phase', 'res_timer', 'res_vx', 'res_vy', 'res_pulse']:
                    if hasattr(self, attr): delattr(self, attr)

        # Mover la sub-ventana si existe
        if hasattr(self, 'res_win') and self.res_win and self.res_win.winfo_exists():
            self.res_win.geometry(f"+{int(self.res_x)}+{int(self.res_y)}")

        self.update_position()
        self.schedule_loop(30, self.physics_loop) 

    def reshiram_sphere_loop(self):
        if getattr(self, 'current_state', 'exiting') != 'reshiram_channeling': return
        if not hasattr(self, 'res_win') or not self.res_win or not self.res_win.winfo_exists(): return

        self.res_canvas.delete("vfx_res")
        cx = self.res_size / 2
        cy = self.res_size / 2
        
        max_r = (self.res_size / 2) - 20 
        base_radius_mult = getattr(self, 'res_vfx_radius', 1.0)
        
        r1_base = max_r * base_radius_mult
        
        if r1_base > 5:
            self.res_pulse = getattr(self, 'res_pulse', 0) + 0.15
            
            outer_pulse_mod = math.sin(self.res_pulse) * 0.05
            r1 = max_r * (base_radius_mult + outer_pulse_mod)
            
            inner_pulse_mod = math.sin(self.res_pulse) * 0.05
            r2 = r1 * (0.85 + inner_pulse_mod)
            r3 = r1 * (0.60 + inner_pulse_mod)
            
            # Anillos de fuego solar
            self.res_canvas.create_oval(cx-r1, cy-r1, cx+r1, cy+r1, fill="#C0392B", outline="#C0392B", tags="vfx_res")
            self.res_canvas.create_oval(cx-r2, cy-r2, cx+r2, cy+r2, fill="#E67E22", outline="#E67E22", tags="vfx_res")
            self.res_canvas.create_oval(cx-r3, cy-r3, cx+r3, cy+r3, fill="#F1C40F", outline="#F1C40F", tags="vfx_res")
            
            # Emisión de partículas de fuego ascendentes
            for _ in range(4):
                angle = random.uniform(math.pi + 0.2, 2 * math.pi - 0.2)
                dist = random.uniform(0, r1)
                px = cx + math.cos(angle) * dist
                py = cy + math.sin(angle) * dist
                speed = random.uniform(2.0, 7.0)
                size = random.choice([3, 4, 5])
                color = random.choice(["#E74C3C", "#E67E22", "#F1C40F", "#D35400"])
                
                pid = self.res_canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color, tags="vfx_res_part")
                self.res_particles.append({'id': pid, 'vx': math.cos(angle)*speed*0.5, 'vy': -speed, 'life': 15})

        alive = []
        for p in self.res_particles:
            if p['life'] > 0:
                self.res_canvas.move(p['id'], p['vx'], p['vy'])
                p['life'] -= 1
                alive.append(p)
            else:
                self.res_canvas.delete(p['id'])
        self.res_particles = alive

        self.window.after(40, self.reshiram_sphere_loop)

    def reshiram_explode(self):
        impact_radius = 800 
        self.trigger_reshiram_shockwave(impact_radius)

        if getattr(self, 'get_all_pets', None):
            for target in self.get_all_pets():
                if target != self and target.current_state != 'exiting':
                    dist = math.sqrt((self.res_target_x - target.x)**2 + (self.res_target_y - target.y)**2)
                    if dist <= impact_radius:
                        self.apply_burn(target)

    def trigger_reshiram_shockwave(self, max_radius):
        wave_win = tk.Toplevel(self.window.master)
        wave_win.overrideredirect(True)
        wave_win.attributes('-topmost', True)
        
        TRANS_COLOR = '#010101'
        wave_win.config(bg=TRANS_COLOR)
        try: wave_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass
        
        win_size = max_radius * 2
        center_x = int(self.res_x + self.res_size/2 - win_size/2)
        center_y = int(self.res_y + self.res_size/2 - win_size/2)
        wave_win.geometry(f"{win_size}x{win_size}+{center_x}+{center_y}")
        
        w_canvas = tk.Canvas(wave_win, width=win_size, height=win_size, bg=TRANS_COLOR, highlightthickness=0)
        w_canvas.pack()
        
        state = {'radius': 10.0, 'alpha_width': 35.0}
        
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
            
            # Múltiples anillos de fuego para la onda expansiva
            w_canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline="#C0392B", width=int(state['alpha_width']), tags="wave")
            w_canvas.create_oval(cx-r*0.9, cy-r*0.9, cx+r*0.9, cy+r*0.9, outline="#E67E22", width=int(state['alpha_width']*0.8), tags="wave")
            
            wave_win.after(20, animate_wave)
            
        animate_wave()

    def apply_burn(self, target):
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
            
        for prefix, cancel_func in [('mewtwo_', 'cancel_mewtwo_arts'), ('hooh_', 'cancel_hooh_arts'), ('kyogre_', 'cancel_kyogre_arts'), ('groudon_', 'cancel_groudon_arts'), ('lugia_', 'cancel_lugia_arts'), ('rayquaza_', 'cancel_rayquaza_arts'), ('dialga_', 'cancel_dialga_arts'), ('palkia_', 'cancel_palkia_arts'), ('giratina_', 'cancel_giratina_arts'), ('zekrom_', 'cancel_zekrom_arts'), ('reshiram_', 'cancel_reshiram_arts')]:
            if target.current_state.startswith(prefix) and hasattr(target, cancel_func): getattr(target, cancel_func)()

        target.canvas.itemconfig(target.canvas_image_id, state='normal')
        try: target.window.attributes('-alpha', 1.0)
        except: pass

        target.current_state = 'reshiram_burn'
        target.reshiram_burn_timer = 166 # 5 segundos a 30ms el tick
        target.is_facing_right = random.choice([True, False])

    def _fsm_reshiram_burn(self):
        self.reshiram_burn_timer -= 1
        if self.reshiram_burn_timer <= 0:
            self.current_state = 'idle'
            self.schedule_loop(30, self.physics_loop)
            return
            
        speed = self.speed * 1.5
        
        if getattr(self, 'anchored_rect', None):
            rect = self.anchored_rect
            if self.x > rect[2] - self.size_w:
                self.x = rect[2] - self.size_w
                self.is_facing_right = False
            elif self.x < rect[0]:
                self.x = rect[0]
                self.is_facing_right = True
            else:
                if self.is_facing_right and self.x + speed > rect[2] - self.size_w:
                    self.is_facing_right = False
                elif not self.is_facing_right and self.x - speed < rect[0]:
                    self.is_facing_right = True

        self.x += speed if self.is_facing_right else -speed
        
        if getattr(self, 'can_screen_wrap', False):
            if self.x <= self.v_x - self.size_w: self.x = self.v_x + self.v_width
            elif self.x >= self.v_x + self.v_width: self.x = self.v_x - self.size_w
        else:
            if self.x <= self.v_x:
                self.x = self.v_x
                self.is_facing_right = True
            elif self.x >= (self.v_x + self.v_width) - self.size_w:
                self.x = (self.v_x + self.v_width) - self.size_w
                self.is_facing_right = False

        if not self.is_flying:
            current_env, _ = self.get_window_environment()
            physical_floor = current_env['y'] if self.y <= current_env['y'] + 15 else self.default_floor_y
            
            if self.y < physical_floor - 15 or getattr(self, 'v_y_velocity', 0) > 0:
                self.v_y_velocity = getattr(self, 'v_y_velocity', 0.0) + 1.5
                self.y += self.v_y_velocity
                if self.y >= physical_floor:
                    self.y = physical_floor
                    self.floor_y = physical_floor
                    self.v_y_velocity = 0.0
                    if current_env['hwnd']:
                        self.anchored_hwnd = current_env['hwnd']
                        self.anchored_rect = current_env['rect']
            else:
                self.y = physical_floor
                self.floor_y = physical_floor
                self.v_y_velocity = 0.0
                
                if random.randint(1, 100) <= 6:
                    self.v_y_velocity = -9.0 
                    self.y += self.v_y_velocity
                    self.anchored_hwnd = None
        else:
            self.fly_amplitude += 0.3
            self.y = self.floor_y + math.sin(self.fly_amplitude) * 10
            
        # Reutiliza el VFX de fuego de Ho-Oh heredado para la víctima
        if self.reshiram_burn_timer % 3 == 0 and hasattr(self, 'show_fire_vfx'):
            self.show_fire_vfx(is_master=False)

        self.update_position()
        self.schedule_loop(30, self.physics_loop)