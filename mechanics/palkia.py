import time
import random
import math

class PalkiaMechanics:
    def cancel_palkia_arts(self):
        for attr in ['palkia_phase', 'palkia_timer']:
            if hasattr(self, attr): delattr(self, attr)
            
        if self.current_state not in ['dragged', 'exiting']:
            if getattr(self, 'is_flying', False):
                self.floor_y = self.y
                self.current_state = 'ascending'
            else:
                self.current_state = 'falling'

    def _fsm_palkia_channeling(self):
        if not hasattr(self, 'palkia_phase'):
            self.palkia_phase = 0
            
        if self.palkia_phase == 0:
            self.v_y_velocity = -28.0
            self.palkia_phase = 1
            
        elif self.palkia_phase == 1:
            gravity = 4.0
            self.v_y_velocity = getattr(self, 'v_y_velocity', 0.0) + gravity
            self.y += self.v_y_velocity

            current_env, _ = self.get_window_environment()
            fall_tolerance = max(15, int(self.v_y_velocity) + 15) if self.v_y_velocity > 0 else 15
            floor = current_env['y'] if self.y <= current_env['y'] + fall_tolerance else getattr(self, 'default_floor_y', self.y)

            # Impacto sísmico
            if self.y >= floor and self.v_y_velocity > 0:
                self.y = floor
                self.v_y_velocity = 0.0
                self.palkia_phase = 2
                self.palkia_timer = 0
                self.trigger_landing_shake()
                
                # ONDA EXPANSIVA: INVERSIÓN GRAVITATORIA
                if getattr(self, 'get_all_pets', None):
                    for target in self.get_all_pets():
                        is_climber = getattr(target, 'is_climbing', False) or target.config.get("physics", {}).get("is_climbing", False)
                        
                        if target != self and target.window.winfo_exists() and target.current_state not in ['exiting', 'dragged', 'spawning_wild', 'despawning_wild', 'falling_pokeball', 'falling_egg'] and not is_climber:
                            target.apply_gravity_inversion(60) # 60 segundos
                            
                # ACTIVACIÓN DEL VFX PARA EL MAESTRO (Palkia)
                self.palkia_aura_end = time.time() + 60
                self.palkia_vfx_loop()
                
        elif self.palkia_phase == 2:
            self.palkia_timer += 1
            if self.palkia_timer > 60:
                self.current_state = 'idle'
                self.palkia_cooldown = 108000 # 1.5 horas
                delattr(self, 'palkia_phase')
                delattr(self, 'palkia_timer')

        self.update_position()
        self.schedule_loop(30, self.physics_loop)
        
    def palkia_vfx_loop(self):
        # Bucle asíncrono para emitir partículas de espacio
        if getattr(self, 'current_state', 'exiting') == 'exiting': return
        if time.time() > getattr(self, 'palkia_aura_end', 0): return
        
        # Emite ráfagas cortas constantemente
        if random.randint(1, 4) <= 2:
            self.show_spatial_rend_vfx()
            
        self.window.after(60, self.palkia_vfx_loop)
        
    def show_spatial_rend_vfx(self):
        if getattr(self, 'current_state', 'exiting') == 'exiting': return
        
        particles = []
        cx = self.size_w // 2
        cy = self.size_h // 2
        
        # Generar 3-5 partículas por ráfaga
        for _ in range(random.randint(3, 5)):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1.5, 4.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            size = random.choice([2, 3])
            # Paleta de distorsión espacial: Rosas y Blancos brillantes
            color = random.choice(["#FFB6C1", "#FF69B4", "#FFFFFF", "#F8BBD0", "#F48FB1"])
            
            pid = self.canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline=color, tags="vfx_palkia")
            particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': random.randint(20, 40)})
            
        def animate_palkia_aura():
            if getattr(self, 'current_state', 'exiting') == 'exiting': return
            alive_count = 0
            for p in particles:
                if p['life'] > 0:
                    self.canvas.move(p['id'], p['vx'], p['vy'])
                    # Distorsión fluida (Fricción espacial y levitación errática)
                    p['vx'] *= 0.94
                    p['vy'] *= 0.94
                    p['vy'] -= 0.15 
                    
                    p['life'] -= 1
                    alive_count += 1
                elif p['life'] == 0:
                    self.canvas.delete(p['id'])
                    p['life'] = -1
                    
            if alive_count > 0:
                self.window.after(30, animate_palkia_aura)
                
        animate_palkia_aura()

    def apply_gravity_inversion(self, duration_secs):
        # 1. Limpieza de estados genéricos
        if self.current_state in ['digging_in', 'digging', 'digging_out']:
            self.canvas.itemconfig(self.canvas_image_id, state='normal')
            self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
        elif self.current_state == 'bubbled':
            if hasattr(self, 'manage_bubble_vfx'): self.manage_bubble_vfx(False)
            if hasattr(self, 'show_bubble_burst_vfx'): self.show_bubble_burst_vfx()
        elif self.current_state == 'tk_channeling':
            if hasattr(self, 'manage_tk_aura'): self.manage_tk_aura(self.canvas, self.size_w, self.size_h, False)
            target = getattr(self, 'tk_target', None)
            if target:
                t_w = target.size_w if target.__class__.__name__ == 'DesktopPet' else target.size
                t_h = target.size_h if target.__class__.__name__ == 'DesktopPet' else target.size
                if hasattr(self, 'manage_tk_aura'): self.manage_tk_aura(target.canvas, t_w, t_h, False)
                target.current_state = 'falling'
                if hasattr(target, 'tk_master'): target.tk_master = None
            self.tk_target = None
        elif self.current_state == 'tk_lifted':
            if hasattr(self, 'manage_tk_aura'): self.manage_tk_aura(self.canvas, self.size_w, self.size_h, False)
            master = getattr(self, 'tk_master', None)
            if master:
                master.tk_target = None
                if hasattr(master, 'manage_tk_aura'): master.manage_tk_aura(master.canvas, master.size_w, master.size_h, False)
                master.current_state = 'falling'
            self.tk_master = None

        if getattr(self, 'is_glitching', False):
            self.is_glitching = False
            self.glitch_teleports_left = 0
            self.glitch_cooldown = 12000
            try: self.window.attributes('-alpha', 1.0)
            except: pass

        # 2. Limpieza de mecánicas legendarias
        if self.current_state.startswith('dark_'): self.cancel_dark_arts()
        elif self.current_state.startswith('mewtwo_'): self.cancel_mewtwo_arts()
        elif self.current_state in ['hooh_channeling', 'panic_run']: self.cancel_hooh_arts()
        elif self.current_state in ['kyogre_channeling', 'deluge_float']: self.cancel_kyogre_arts()
        elif self.current_state == 'groudon_channeling': self.cancel_groudon_arts()
        elif self.current_state in ['lugia_channeling', 'lugia_dash']: self.cancel_lugia_arts()
        elif self.current_state == 'rayquaza_channeling': self.cancel_rayquaza_arts()
        elif self.current_state == 'dialga_channeling': self.cancel_dialga_arts()
        
        self.gravity_inversion_end = time.time() + duration_secs
        self.gravity_inverted = True
        self.current_state = 'palkia_invert_transition'
        self.palkia_rot_step = 0
        
        if getattr(self, 'is_flying', False):
            self.target_floor_y = self.v_y + getattr(self, 'target_offset_y', 0)
        
    def check_gravity_inversion(self):
        if getattr(self, 'gravity_inverted', False) and self.current_state not in ['palkia_invert_transition', 'palkia_revert_transition', 'dragged', 'exiting']:
            if time.time() > getattr(self, 'gravity_inversion_end', 0):
                self.current_state = 'palkia_revert_transition'
                self.palkia_rot_step = 0

    def _fsm_palkia_invert_transition(self):
        self.palkia_rot_step += 1
        progress = self.palkia_rot_step / 30.0 
        
        self.surface_angle = int(180 * progress)
        self.y -= 2.0 
        
        if self.palkia_rot_step >= 30:
            self.surface_angle = 180
            self.current_state = 'falling'
            delattr(self, 'palkia_rot_step')
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)
        
    def _fsm_palkia_revert_transition(self):
        self.palkia_rot_step += 1
        progress = self.palkia_rot_step / 30.0
        
        self.surface_angle = 180 - int(180 * progress)
        self.y += 2.0 
        
        if self.palkia_rot_step >= 30:
            self.surface_angle = 0
            self.gravity_inverted = False
            self.current_state = 'falling'
            
            if getattr(self, 'is_flying', False):
                self.target_floor_y = (self.v_y + self.v_height) - self.size_h - getattr(self, 'target_offset_y', 0)
                
            delattr(self, 'palkia_rot_step')
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)