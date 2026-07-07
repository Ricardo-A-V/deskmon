import random
import math
import os

class MewtwoMechanics:
    def cancel_mewtwo_arts(self):
        self.manage_tk_aura(self.canvas, self.size_w, self.size_h, False)
        if hasattr(self, 'mewtwo_base_y'): delattr(self, 'mewtwo_base_y')
        
        if self.current_state not in ['dragged', 'exiting']:
            self.current_state = 'falling'
            
        targets = getattr(self, 'mewtwo_targets', [])
        self.mewtwo_targets = [] 
        for target in targets:
            if target and target.window.winfo_exists():
                target.mewtwo_master = None
                target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
                # FIX: Limpieza visual de emergencia si se cancela la habilidad
                target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
                if target.current_state not in ['dragged', 'exiting']:
                    target.current_state = 'falling'
                    
        master = getattr(self, 'mewtwo_master', None)
        self.mewtwo_master = None
        if master and master.window.winfo_exists():
            master.cancel_mewtwo_arts()

    def _fsm_mewtwo_channeling(self):
        if not getattr(self, 'mewtwo_targets', None):
            self.cancel_mewtwo_arts()
            self.schedule_loop(30, self.physics_loop)
            return

        self.mewtwo_timer += 1
        
        # FIX: Levitación con onda senoidal de amplitud baja (4 píxeles)
        target_y = self.default_floor_y - 140
        if not hasattr(self, 'mewtwo_base_y'):
            self.mewtwo_base_y = self.y
            
        if self.mewtwo_base_y > target_y:
            self.mewtwo_base_y -= 1.5
            
        self.y = self.mewtwo_base_y + math.sin(self.mewtwo_timer * 0.1) * 4.0
            
        self.manage_tk_aura(self.canvas, self.size_w, self.size_h, True)

        if self.mewtwo_timer >= 500:
            self.show_mewtwo_blast_vfx()
            self.manage_tk_aura(self.canvas, self.size_w, self.size_h, False)
            
            my_cx = self.x + self.size_w / 2
            
            for target in self.mewtwo_targets:
                if target and target.window.winfo_exists():
                    target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
                    # FIX: Limpieza visual al salir expulsados
                    target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
                    target.mewtwo_master = None
                    target.current_state = 'thrown'
                    
                    t_cx = target.x + target.size_w / 2
                    push_dir = 1 if t_cx > my_cx else -1
                    
                    target.v_x_velocity = push_dir * random.uniform(30.0, 60.0)
                    target.v_y_velocity = random.uniform(-35.0, -60.0)
            
            self.mewtwo_targets = []
            self.current_state = 'falling'
            if hasattr(self, 'mewtwo_base_y'): delattr(self, 'mewtwo_base_y')
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_mewtwo_victim(self):
        master = getattr(self, 'mewtwo_master', None)
        if not master or master.current_state != 'mewtwo_channeling' or not master.window.winfo_exists():
            self.cancel_mewtwo_arts()
            self.schedule_loop(30, self.physics_loop)
            return

        timer = master.mewtwo_timer
        activation_tick = getattr(self, 'mewtwo_activation_tick', 0)
        
        if timer < activation_tick:
            self.manage_tk_aura(self.canvas, self.size_w, self.size_h, True)
            self.schedule_loop(30, self.physics_loop)
            return

        self.manage_tk_aura(self.canvas, self.size_w, self.size_h, True)

        my_cx = self.x + self.size_w / 2
        my_cy = self.y + self.size_h / 2
        m_cx = master.x + master.size_w / 2
        m_cy = master.y + master.size_h / 2

        active_timer = timer - activation_tick

        # MATEMÁTICA ORBITAL FIX 2.0:
        # Distancia masiva: Empieza a 1600px y se cierra hasta mantener un anillo de 800px de radio (Casi ocupa toda la pantalla)
        orbit_radius = max(800, 1600 - (active_timer * 1.5))
        
        # Velocidad exponencial: Inicia a (0.002) y usa el cuadrado del tiempo para que la aceleración real ocurra al final
        angular_speed = 0.002 + ((timer ** 2) * 0.0000008)
        offset = getattr(self, 'mewtwo_orbit_offset', 0)
        current_angle = (timer * angular_speed) + offset
        
        target_x = m_cx + math.cos(current_angle) * orbit_radius - self.size_w / 2
        target_y = m_cy + math.sin(current_angle) * orbit_radius - self.size_h / 2
        
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        pull_speed = 4.0 + (active_timer * 0.1)
        
        if dist > pull_speed:
            self.x += (dx / dist) * pull_speed
            self.y += (dy / dist) * pull_speed
        else:
            self.x = target_x
            self.y = target_y

        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def show_mewtwo_blast_vfx(self):
        particles = []
        cx = self.size_w // 2
        cy = self.size_h // 2
        
        # Generamos 30 partículas de alta velocidad de energía psíquica
        for _ in range(30):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(10.0, 25.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            size = random.choice([2, 3, 4])
            color = random.choice(["#8E44AD", "#9B59B6", "#D2B4DE", "#D441F5", "#FFFFFF"]) 
            
            pid = self.canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline=color, tags="vfx_mewtwo")
            particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': random.randint(15, 25)})
            
        def animate_blast():
            if getattr(self, 'current_state', 'exiting') == 'exiting': return
            alive_count = 0
            for p in particles:
                if p['life'] > 0:
                    self.canvas.move(p['id'], p['vx'], p['vy'])
                    # Fricción para crear el efecto de "estallido y parada súbita" en el aire
                    p['vx'] *= 0.88  
                    p['vy'] *= 0.88
                    p['life'] -= 1
                    alive_count += 1
                elif p['life'] == 0:
                    self.canvas.delete(p['id'])
                    p['life'] = -1
                    
            if alive_count > 0:
                self.schedule_loop(30, animate_blast)
                
        animate_blast()

