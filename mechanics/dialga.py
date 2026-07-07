import random
import math
import time

class DialgaMechanics:
    def cancel_dialga_arts(self):
        for attr in ['dialga_phase', 'dialga_timer']:
            if hasattr(self, attr): delattr(self, attr)
            
        if self.current_state not in ['dragged', 'exiting']:
            if getattr(self, 'is_flying', False):
                self.floor_y = self.y
                self.current_state = 'ascending'
            else:
                self.current_state = 'falling'

    def _fsm_dialga_channeling(self):
        if not hasattr(self, 'dialga_phase'):
            self.dialga_phase = 0
            
        if self.dialga_phase == 0:
            # Salto parabólico regido por inercia
            self.v_y_velocity = -28.0
            self.dialga_phase = 1
            
        elif self.dialga_phase == 1:
            # Gravedad pesada
            gravity = 4.0
            self.v_y_velocity = getattr(self, 'v_y_velocity', 0.0) + gravity
            self.y += self.v_y_velocity

            # Escaneo topográfico para aterrizar en la barra de tareas o ventanas
            current_env, _ = self.get_window_environment()
            fall_tolerance = max(15, int(self.v_y_velocity) + 15) if self.v_y_velocity > 0 else 15
            floor = current_env['y'] if self.y <= current_env['y'] + fall_tolerance else getattr(self, 'default_floor_y', self.y)

            # Impacto contra el suelo (Fin del salto)
            if self.y >= floor and self.v_y_velocity > 0:
                self.y = floor
                self.v_y_velocity = 0.0
                self.dialga_phase = 2
                self.dialga_timer = 0
                self.trigger_landing_shake()
                
                # PROPAGACIÓN INSTANTÁNEA DE LA DISTORSIÓN (20 Segundos exactos)
                if getattr(self, 'get_all_pets', None):
                    for target in self.get_all_pets():
                        if target != self and target.window.winfo_exists() and target.current_state not in ['exiting', 'dragged', 'spawning_wild', 'despawning_wild', 'falling_pokeball', 'falling_egg']:
                            target.apply_time_distortion(20) 
                
                # ACTIVACIÓN INSTANTÁNEA DEL VFX PARA EL MAESTRO (Dialga)
                self.time_distorted_master = True
                self.time_distortion_end = time.time() + 20
                self.time_distortion_vfx_loop(is_master=True)
                
        elif self.dialga_phase == 2:
            self.dialga_timer += 1
            if self.dialga_timer > 60: # Recuperación post-impacto
                self.current_state = 'idle'
                self.dialga_cooldown = 108000 # 1.5 horas
                delattr(self, 'dialga_phase')
                delattr(self, 'dialga_timer')

        self.update_position()
        self.window.after(30, self.physics_loop)

    def apply_time_distortion(self, duration_secs):
        self.time_distorted = True
        self.time_distortion_end = time.time() + duration_secs
        self.time_distortion_vfx_loop(is_master=False)

    def check_time_distortion(self):
        if getattr(self, 'time_distorted', False) or getattr(self, 'time_distorted_master', False):
            if time.time() > getattr(self, 'time_distortion_end', 0):
                self.time_distorted = False
                self.time_distorted_master = False

    def time_distortion_vfx_loop(self, is_master=False):
        # Si el Pokémon es guardado o el tiempo se acaba, detener emisión
        is_active = getattr(self, 'time_distorted', False) if not is_master else getattr(self, 'time_distorted_master', False)
        if not is_active or getattr(self, 'current_state', 'exiting') == 'exiting': 
            return

        # FIX: Cadencia estricta en lugar de probabilidad (RNG).
        self.show_time_distortion_vfx(is_master)
            
        # Dialga emite un pulso cada 90ms, las víctimas cada 150ms. Flujo constante y sin cortes.
        delay = 90 if is_master else 150
        self.window.after(delay, lambda: self.time_distortion_vfx_loop(is_master))

    def show_time_distortion_vfx(self, is_master=False):
        if getattr(self, 'current_state', 'exiting') == 'exiting': return
        
        particles = []
        cx = self.size_w // 2
        
        # Desplazamiento anatómico del núcleo de emisión
        offset = int(self.size_h * 0.25) if is_master else int(self.size_h * 0.15)
        cy = (self.size_h // 2) + offset
        
        count = random.randint(3, 4) if is_master else random.randint(1, 2)
        
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(5.0, 15.0)
            
            angular_speed = random.uniform(0.05, 0.15) * random.choice([1, -1])
            radial_speed = random.uniform(2.0, 4.0) if is_master else random.uniform(1.0, 2.5)
            
            size = random.choice([2, 3])
            color = random.choice(["#4B0082", "#8A2BE2", "#9B59B6", "#8E44AD", "#3498DB", "#2E86C1", "#5DADE2"])
            
            px = cx + math.cos(angle) * radius
            py = cy + math.sin(angle) * radius
            
            pid = self.canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color, tags="vfx_dialga")
            
            particles.append({
                'id': pid, 
                'angle': angle, 
                'radius': radius, 
                'ang_speed': angular_speed, 
                'rad_speed': radial_speed, 
                'cx': cx, 
                'cy': cy,
                'life': random.randint(25, 45) 
            })
            
        def animate_distortion():
            if getattr(self, 'current_state', 'exiting') == 'exiting': return
            alive_count = 0
            
            for p in particles:
                if p['life'] > 0:
                    p['angle'] += p['ang_speed']
                    p['radius'] += p['rad_speed']
                    
                    p['rad_speed'] *= 0.92 
                    
                    new_x = p['cx'] + math.cos(p['angle']) * p['radius']
                    new_y = p['cy'] + math.sin(p['angle']) * p['radius']
                    
                    coords = self.canvas.coords(p['id'])
                    if coords:
                        curr_x = (coords[0] + coords[2]) / 2
                        curr_y = (coords[1] + coords[3]) / 2
                        self.canvas.move(p['id'], new_x - curr_x, new_y - curr_y)
                        
                    p['life'] -= 1
                    alive_count += 1
                elif p['life'] == 0:
                    self.canvas.delete(p['id'])
                    p['life'] = -1
                    
            if alive_count > 0:
                self.window.after(30, animate_distortion)
                
        animate_distortion()