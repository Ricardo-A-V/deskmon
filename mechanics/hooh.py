import win32api
import win32con

import random
import math
import os

class HoOhMechanics:
    def cancel_hooh_arts(self):
        if self.current_state not in ['dragged', 'exiting']:
            self.current_state = 'falling'
            
        targets = getattr(self, 'hooh_targets', [])
        self.hooh_targets = []
        for target in targets:
            if target and target.window.winfo_exists():
                target.hooh_master = None
                # FIX: Solo cancelar la acción de la víctima si realmente ya había empezado a correr
                if target.current_state == 'panic_run' and target.current_state not in ['dragged', 'exiting']:
                    target.current_state = 'falling'
                    
        master = getattr(self, 'hooh_master', None)
        self.hooh_master = None
        if master and master.window.winfo_exists():
            master.cancel_hooh_arts()

    def _fsm_hooh_channeling(self):
        if not hasattr(self, 'hooh_target_x'):
            try:
                monitor = win32api.MonitorFromPoint((int(self.x), int(self.y)), win32con.MONITOR_DEFAULTTONEAREST)
                mon_info = win32api.GetMonitorInfo(monitor)
                mon_rect = mon_info['Monitor']
                mon_x = mon_rect[0]
                mon_w = mon_rect[2] - mon_rect[0]
            except:
                mon_x = self.v_x
                mon_w = self.v_width
            self.hooh_target_x = mon_x + (mon_w // 2) - self.size_w // 2

        target_y = self.v_y + 40 
        
        dx = self.hooh_target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if getattr(self, 'hooh_phase', 0) == 0:
            self.is_facing_right = (dx > 0)
            fly_speed = self.speed * 1.5
            
            if dist > fly_speed:
                self.x += (dx/dist) * fly_speed
                self.y += (dy/dist) * fly_speed
            else:
                self.x = self.hooh_target_x
                self.y = target_y
                self.hooh_phase = 1
                
                # FIX ESTRUCTURAL: Secuestro en el Momento Cero.
                # Ahora que Ho-Oh está en posición, interrumpimos violentamente a todos los objetivos.
                active_targets = []
                for target in getattr(self, 'hooh_targets', []):
                    # Volvemos a validar por si los atraparon/borraron durante el vuelo de Ho-Oh
                    if target and target.window.winfo_exists() and target.current_state not in ['exiting', 'dragged', 'spawning_wild', 'despawning_wild', 'falling_pokeball', 'falling_egg']:
                        
                        if target.current_state.startswith('dark_'):
                            target.cancel_dark_arts()
                        elif target.current_state.startswith('mewtwo_'):
                            target.cancel_mewtwo_arts()
                        elif target.current_state == 'tk_channeling':
                            target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
                            if getattr(target, 'tk_target', None):
                                if getattr(target.tk_target, 'current_state', '') in ['tk_controlled', 'tk_lifted']:
                                    
                                    # FIX: Forzar la limpieza de partículas del objeto/víctima flotante
                                    t_targ = target.tk_target
                                    t_w = t_targ.size_w if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size
                                    t_h = t_targ.size_h if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size
                                    target.manage_tk_aura(t_targ.canvas, t_w, t_h, False)
                                    
                                    t_targ.current_state = 'falling'
                                    if hasattr(t_targ, 'tk_master'):
                                        t_targ.tk_master = None
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
                        
                        target.current_state = 'panic_run'
                        target.panic_timer = self.hooh_timer 
                        target.hooh_master = self
                        target.is_facing_right = random.choice([True, False])
                        active_targets.append(target)
                
                self.hooh_targets = active_targets
        else:
            self.hooh_timer -= 1
            self.y = target_y + math.sin(self.hooh_timer * 0.2) * 5.0
            
            if self.hooh_timer % 3 == 0:
                self.show_fire_vfx(is_master=True)
                
            if self.hooh_timer <= 0:
                if getattr(self, 'is_flying', False):
                    # FIX: Eliminamos el recálculo defectuoso. 
                    # El Pokémon ya recuerda su 'target_floor_y' original perfectamente.
                    self.floor_y = self.y 
                    self.current_state = 'ascending'
                else:
                    self.current_state = 'falling'
                    
                self.hooh_targets = []
                if hasattr(self, 'hooh_target_x'): delattr(self, 'hooh_target_x')
                
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_panic_run(self):
        master = getattr(self, 'hooh_master', None)
        if not master or master.current_state != 'hooh_channeling' or not master.window.winfo_exists():
            self.cancel_hooh_arts()
            self.schedule_loop(30, self.physics_loop)
            return

        self.panic_timer -= 1
        if self.panic_timer <= 0:
            self.current_state = 'idle'
            self.hooh_master = None
            self.schedule_loop(30, self.physics_loop)
            return
            
        speed = self.speed * 1.5
        
        # Predictor de rebote horizontal para ventanas
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

        # FIX: Evaluación de físicas en Y (Caída Lemming interna y saltitos esporádicos)
        if not self.is_flying:
            current_env, _ = self.get_window_environment()
            physical_floor = current_env['y'] if self.y <= current_env['y'] + 15 else self.default_floor_y
            
            # Si le quitan el suelo (ej: ventana minimizada) o ya estaba saltando
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
                
                # Gatillo de saltos erráticos de pánico (aprox 6% de probabilidad por tick)
                if random.randint(1, 100) <= 6:
                    self.v_y_velocity = -9.0 # FIX: Altura del salto drásticamente aumentada
                    self.y += self.v_y_velocity
                    self.anchored_hwnd = None
        else:
            self.fly_amplitude += 0.3
            self.y = self.floor_y + math.sin(self.fly_amplitude) * 10
            
        if self.panic_timer % 3 == 0:
            self.show_fire_vfx(is_master=False)

        self.update_position()
        self.schedule_loop(30, self.physics_loop) # FIX: Hilo ajustado a 30ms para no desfasarse de Ho-Oh

    def show_fire_vfx(self, is_master=False):
        particles = []
        cx = self.size_w // 2
        
        # El maestro genera fuego desde su centro, las víctimas desde los pies
        cy = self.size_h // 2 if is_master else self.size_h
        
        count = random.randint(4, 8) if is_master else random.randint(2, 4)
        speed_mult = 2.0 if is_master else 1.0
        base_life = 15 if is_master else 10
            
        for _ in range(count):
            # FIX MATEMÁTICO: Ho-Oh emite en 360 grados reales. Las víctimas mantienen el arco superior.
            if is_master:
                angle = random.uniform(0, 2 * math.pi)
            else:
                angle = random.uniform(math.pi + 0.2, 2 * math.pi - 0.2) 
                
            speed = random.uniform(2.0, 5.0) * speed_mult
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            size = random.choice([2, 3])
            color = random.choice(["#E74C3C", "#E67E22", "#F1C40F", "#D35400"]) 
            
            pid = self.canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline=color, tags="vfx_fire")
            
            # Almacenamos su identidad para aplicarle físicas distintas
            particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': random.randint(base_life, base_life + 10), 'is_master': is_master})
            
        def animate_fire():
            if getattr(self, 'current_state', 'exiting') == 'exiting': return
            
            alive_count = 0
            for p in particles:
                if p['life'] > 0:
                    self.canvas.move(p['id'], p['vx'], p['vy'])
                    
                    # FIX FÍSICO: Gravedad y fricción independientes
                    if p['is_master']:
                        # Expansión radial (Nova) con fricción intensa y una levísima tendencia térmica al final
                        p['vx'] *= 0.85
                        p['vy'] *= 0.85
                        p['vy'] -= 0.05 
                    else:
                        # Fuego de suelo (Ascenso forzado por convección)
                        p['vx'] *= 0.9 
                        p['vy'] -= 0.5 
                    
                    if p['life'] < 5:
                        self.canvas.itemconfig(p['id'], fill="#555555", outline="#555555") 
                        
                    p['life'] -= 1
                    alive_count += 1
                elif p['life'] == 0:
                    self.canvas.delete(p['id'])
                    p['life'] = -1
                    
            if alive_count > 0:
                self.schedule_loop(30, animate_fire)
                
        animate_fire()

