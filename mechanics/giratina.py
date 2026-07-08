import random
import math
import time
import os

class GiratinaMechanics:
    def cancel_giratina_arts(self):
        for attr in ['giratina_phase', 'giratina_timer', 'giratina_vortex_active']:
            if hasattr(self, attr): delattr(self, attr)

        self.canvas.delete("vfx_g_vortex")
        self.canvas.delete("vfx_g_eyes")

        # CRÍTICO: Restaurar la opacidad y la visibilidad del Canvas inmediatamente
        try: self.window.attributes('-alpha', 1.0)
        except: pass
        self.canvas.itemconfig(self.canvas_image_id, state='normal')

        if self.current_state not in ['dragged', 'exiting']:
            if getattr(self, 'is_flying', False):
                self.floor_y = self.y
                self.current_state = 'ascending'
            else:
                self.current_state = 'falling'

        targets = getattr(self, 'giratina_targets', [])
        self.giratina_targets = []
        for target in targets:
            if target and target.window.winfo_exists():
                target.giratina_master = None
                try: target.window.attributes('-alpha', 1.0)
                except: pass
                if target.current_state in ['giratina_victim_pulled', 'giratina_victim_fade', 'giratina_victim_absorbed']:
                    target.current_state = 'falling'
                    target.canvas.itemconfig(target.canvas_image_id, state='normal')

    def _fsm_giratina_channeling(self):
        # 1. PREPARACIÓN (Cero rastro del vórtice aquí)
        if not hasattr(self, 'giratina_phase'):
            self.giratina_phase = 0
            self.giratina_timer = 0
            self.giratina_center_x = self.x + self.size_w / 2
            self.giratina_center_y = self.y + self.size_h / 2

        # 2. FASE 0: Desvanecimiento de Giratina
        if self.giratina_phase == 0:
            current_alpha = self.window.attributes('-alpha')
            if current_alpha > 0.0:
                self.window.attributes('-alpha', max(0.0, current_alpha - 0.05))
            else:
                self.canvas.itemconfig(self.canvas_image_id, state='hidden')
                self.swap_giratina_form("giratina_1")
                self.window.attributes('-alpha', 1.0) 
                
                # --- FIX: EL VÓRTICE NACE ESTRICTAMENTE AQUÍ ---
                self.giratina_vortex_active = True
                self.giratina_vortex_radius = 1.0
                self.giratina_vortex_loop()
                # -----------------------------------------------
                
                self.giratina_phase = 1
                self.giratina_timer = 200 

        # 3. FASE 1: Absorción de Víctimas (Máximo 10s)
        elif self.giratina_phase == 1:
            self.giratina_timer -= 1 
            all_absorbed = True
            
            for target in getattr(self, 'giratina_targets', []):
                if target and target.window.winfo_exists() and target.current_state != 'giratina_victim_absorbed':
                    all_absorbed = False
                    break

            if all_absorbed or self.giratina_timer <= 0:
                # Liberación de seguridad si alguien se atasca
                for target in getattr(self, 'giratina_targets', []):
                    if target and target.window.winfo_exists() and target.current_state != 'giratina_victim_absorbed':
                        if target.current_state in ['giratina_victim_pulled', 'giratina_victim_fade']:
                            target.current_state = 'falling'
                            target.giratina_master = None
                            try: target.window.attributes('-alpha', 1.0)
                            except: pass

                self.giratina_phase = 2
                self.giratina_timer = 80 # 4 Segundos exactos de vórtice estable 

        # 4. FASE 2: Vórtice Estable
        elif self.giratina_phase == 2:
            self.giratina_timer -= 1
            if self.giratina_timer <= 0:
                self.giratina_phase = 3
                self.giratina_timer = 100 # 5 Segundos de encogimiento progresivo

        # 5. FASE 3: Disipación del Vórtice
        elif self.giratina_phase == 3:
            self.giratina_timer -= 1
            self.giratina_vortex_radius = max(0.0, self.giratina_timer / 100.0)
            
            if self.giratina_timer <= 0:
                self.giratina_vortex_active = False 
                self.canvas.delete("vfx_g_eyes")
                self.canvas.delete("vfx_g_vortex")
                self.giratina_phase = 4
                self.giratina_timer = 200 # 10 Segundos de vacío absoluto antes del dash

        # 6. FASE 4: Silencio y Arranque del Vuelo
        elif self.giratina_phase == 4:
            self.giratina_timer -= 1
            if self.giratina_timer <= 0:
                self.current_state = 'giratina_dash_prep'

        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def _fsm_giratina_dash_prep(self):
        self.is_facing_right = random.choice([True, False])
        self.y = self.v_y + (self.v_height * 0.4)
        if self.is_facing_right:
            self.x = self.v_x - self.size_w - 50
        else:
            self.x = self.v_x + self.v_width + 50
            
        self.update_position()
        self.canvas.itemconfig(self.canvas_image_id, state='normal')
        self.window.attributes('-alpha', 1.0)
        
        self.current_state = 'giratina_dash'
        self.window.after(1500, self.start_ejection_sequence)
        self.schedule_loop(30, self.physics_loop)

    def _fsm_giratina_dash(self):
        dash_speed = 6.0 
        self.x += dash_speed if self.is_facing_right else -dash_speed
        
        self.fly_amplitude = getattr(self, 'fly_amplitude', 0) + 0.1
        self.y += math.sin(self.fly_amplitude) * 3

        if (self.is_facing_right and self.x > self.v_x + self.v_width + 100) or \
           (not self.is_facing_right and self.x < self.v_x - self.size_w - 100):
            self.current_state = 'giratina_wait_reappear'
            self.giratina_timer = 40 
            self.window.attributes('-alpha', 0.0)

        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_giratina_wait_reappear(self):
        self.giratina_timer -= 1
        if self.giratina_timer <= 0:
            self.x = random.randint(self.v_x + 100, self.v_x + self.v_width - self.size_w - 100)
            self.y = random.randint(self.v_y + 50, self.v_y + int(self.v_height * 0.4))
            
            # FIX DE GRAVEDAD: Sincronizar el vector del suelo con la aparición aérea
            self.floor_y = self.y 
            
            self.current_state = 'giratina_reappear'
            self.update_position()
            self.canvas.itemconfig(self.canvas_image_id, state='normal')
            
        self.schedule_loop(50, self.physics_loop)

    def _fsm_giratina_reappear(self):
        current_alpha = self.window.attributes('-alpha')
        if current_alpha < 1.0:
            self.window.attributes('-alpha', min(1.0, current_alpha + 0.05))
        else:
            self.giratina_cooldown = 108000 
            # FIX DE GRAVEDAD: Devolverle el FSM de levitación para que no se estrelle
            if getattr(self, 'is_flying', False):
                self.current_state = 'ascending'
            else:
                self.current_state = 'idle'

        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def giratina_vortex_loop(self):
        if getattr(self, 'current_state', 'exiting') == 'exiting': return
        if not getattr(self, 'giratina_vortex_active', False): return

        particles = []
        cx = self.size_w / 2
        cy = self.size_h / 2
        radius_mult = getattr(self, 'giratina_vortex_radius', 1.0)

        for _ in range(8):
            if radius_mult <= 0.05: break 
            
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(5.0, 15.0)

            ang_speed = random.uniform(0.1, 0.4) * random.choice([1, -1])
            rad_speed = random.uniform(2.0, 6.0) * radius_mult 

            size = random.choice([3, 4, 5])
            color = random.choice(["#000000", "#1A1A1A", "#4B0082", "#2C003E", "#8A2BE2"])

            px = cx + math.cos(angle) * radius
            py = cy + math.sin(angle) * radius

            pid = self.canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color, tags="vfx_g_vortex")
            particles.append({'id': pid, 'angle': angle, 'radius': radius, 'ang_speed': ang_speed, 'rad_speed': rad_speed, 'cx': cx, 'cy': cy, 'life': random.randint(25, 45)})

        self.canvas.delete("vfx_g_eyes")
        if radius_mult > 0.05:
            self.canvas.create_polygon(cx-15, cy-5, cx-5, cy-2, cx-15, cy+5, cx-20, cy+2, fill="#FF0000", outline="#FF0000", tags="vfx_g_eyes")
            self.canvas.create_polygon(cx+15, cy-5, cx+5, cy-2, cx+15, cy+5, cx+20, cy+2, fill="#FF0000", outline="#FF0000", tags="vfx_g_eyes")

        def animate():
            if getattr(self, 'current_state', 'exiting') == 'exiting': return
            alive = 0
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
                    alive += 1
                elif p['life'] == 0:
                    self.canvas.delete(p['id'])
                    p['life'] = -1

            if alive > 0:
                self.window.after(30, animate)

        animate()
        self.window.after(80, self.giratina_vortex_loop)

    def _fsm_giratina_victim_pulled(self):
        master = getattr(self, 'giratina_master', None)
        if not master or not master.window.winfo_exists() or master.current_state not in ['giratina_channeling']:
            self.current_state = 'falling'
            self.window.attributes('-alpha', 1.0)
            self.schedule_loop(30, self.physics_loop)
            return

        cx = self.x + self.size_w / 2
        cy = self.y + self.size_h / 2

        master_cx = getattr(master, 'giratina_center_x', master.x + master.size_w / 2)
        master_cy = getattr(master, 'giratina_center_y', master.y + master.size_h / 2)

        dx = master_cx - cx
        dy = master_cy - cy
        dist = math.sqrt(dx**2 + dy**2)

        pull_speed = 10.0 
        if dist > pull_speed:
            self.x += (dx / dist) * pull_speed
            self.y += (dy / dist) * pull_speed
            self.is_facing_right = (dx > 0)
        else:
            self.current_state = 'giratina_victim_fade'

        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_giratina_victim_fade(self):
        current_alpha = self.window.attributes('-alpha')
        if current_alpha > 0.0:
            self.window.attributes('-alpha', max(0.0, current_alpha - 0.05))
        else:
            self.current_state = 'giratina_victim_absorbed'
            self.canvas.itemconfig(self.canvas_image_id, state='hidden')

        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def _fsm_giratina_victim_absorbed(self):
        self.schedule_loop(100, self.physics_loop)

    def start_ejection_sequence(self):
        if getattr(self, 'current_state', 'exiting') == 'exiting': return
        self.eject_next_victim()

    def eject_next_victim(self):
        if getattr(self, 'current_state', 'exiting') == 'exiting': return
        targets = getattr(self, 'giratina_targets', [])

        targets = [t for t in targets if t and t.window.winfo_exists() and t.current_state == 'giratina_victim_absorbed']
        self.giratina_targets = targets

        if not targets: return
        target = targets.pop(0)

        target.x = random.randint(self.v_x + 50, self.v_x + self.v_width - target.size_w - 50)
        target.y = random.randint(self.v_y + 50, self.v_y + int(self.v_height * 0.25))
        target.update_position()

        target.window.attributes('-alpha', 1.0)
        
        if hasattr(self, 'show_mini_vortex'):
            self.show_mini_vortex(target)

        if targets:
            self.window.after(2000, self.eject_next_victim)

    def show_mini_vortex(self, target): 
        state = {'ticks': 0, 'ejected': False}
        cx = target.size_w / 2
        cy = target.size_h / 2
        particles = []

        def animate():
            if getattr(self, 'current_state', 'exiting') == 'exiting' or getattr(target, 'current_state', 'exiting') == 'exiting' or not target.window.winfo_exists():
                try: target.canvas.delete("vfx_g_mini")
                except: pass
                return

            state['ticks'] += 1
            progress = state['ticks'] / 83.0 

            if state['ticks'] <= 50:
                scale = progress
            else:
                scale = max(0.0, 2.0 - progress)

            if state['ticks'] == 50 and not state['ejected']:
                state['ejected'] = True
                target.canvas.itemconfig(target.canvas_image_id, state='normal')
                target.giratina_master = None
                target.current_state = 'thrown'

                angle = random.uniform(math.pi + 0.2, 2 * math.pi - 0.2)
                force = random.uniform(15.0, 25.0)
                target.v_x_velocity = math.cos(angle) * force
                
                if getattr(target, 'gravity_inverted', False):
                    target.v_y_velocity = math.sin(angle) * force
                else:
                    target.v_y_velocity = -(math.sin(angle) * force)

            if state['ticks'] < 90 and scale > 0.1:
                for _ in range(2):
                    angle = random.uniform(0, 2 * math.pi)
                    radius = random.uniform(10.0, min(target.size_w, target.size_h) / 2) * scale
                    ang_speed = random.uniform(0.2, 0.4)
                    rad_speed = -random.uniform(1.0, 3.0)
                    size = random.choice([2, 3, 4])
                    color = random.choice(["#000000", "#4B0082", "#2C003E"])

                    px = cx + math.cos(angle) * radius
                    py = cy + math.sin(angle) * radius

                    pid = target.canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color, tags="vfx_g_mini")
                    particles.append({'id': pid, 'angle': angle, 'radius': radius, 'ang_speed': ang_speed, 'rad_speed': rad_speed, 'cx': cx, 'cy': cy, 'life': 10})

            alive = 0
            for p in particles:
                if p['life'] > 0:
                    p['angle'] += p['ang_speed']
                    p['radius'] = max(0, p['radius'] + p['rad_speed'])
                    new_x = p['cx'] + math.cos(p['angle']) * p['radius']
                    new_y = p['cy'] + math.sin(p['angle']) * p['radius']

                    coords = target.canvas.coords(p['id'])
                    if coords:
                        curr_x = (coords[0] + coords[2]) / 2
                        curr_y = (coords[1] + coords[3]) / 2
                        target.canvas.move(p['id'], new_x - curr_x, new_y - curr_y)
                    p['life'] -= 1
                    alive += 1
                elif p['life'] == 0:
                    target.canvas.delete(p['id'])
                    p['life'] = -1

            if state['ticks'] < 100 or alive > 0:
                target.window.after(30, animate)
            else:
                target.canvas.delete("vfx_g_mini")

        animate()

    def swap_giratina_form(self, form_name):
        # Mantenemos intacto el núcleo central absoluto en la pantalla
        old_cx = self.x + self.size_w / 2
        old_cy = self.y + self.size_h / 2

        self.pet_name = form_name
        self.pet_data["species"] = form_name
        self.pet_dir = os.path.join(self.base_dir, "game_env", "pets", self.pet_name)

        self.config = self.load_config()

        multiplicador_tamaño = 1.55
        if getattr(self, 'is_legendary', False):
            multiplicador_tamaño *= 1.2

        physics = self.config.get("physics", {})
        self.size_w = int(physics.get("size", 64) * multiplicador_tamaño)
        self.size_h = int(physics.get("size", 64) * multiplicador_tamaño)
        
        # --- FIX ESPACIAL: REAJUSTE DE ANCLAJE ---
        # Si la ventana se hace más grande, restamos el crecimiento a las coordenadas X e Y
        # para que el centro exacto siga estando milimétricamente en el mismo sitio.
        self.x = old_cx - (self.size_w / 2)
        self.y = old_cy - (self.size_h / 2)

        self.is_flying = physics.get("is_flying", False)
        if self.is_flying:
            fly_height_pct = self.pet_data.get("flying_height_pct", 3.0)
            max_offset = self.v_height - self.size_h
            self.target_offset_y = int(max_offset * (fly_height_pct / 100.0))
            self.target_floor_y = (self.v_y + self.v_height) - self.size_h - self.target_offset_y
            self.offset_y = -6
        else:
            self.offset_y = -6
            self.target_floor_y = (self.v_y + self.v_height) - self.size_h - self.offset_y
            
        self.default_floor_y = (self.v_y + self.v_height) - self.size_h - self.offset_y

        self.canvas.config(width=self.size_w, height=self.size_h)

        animator_dir = os.path.join(self.pet_dir, "shiny") if self.is_shiny else self.pet_dir
        if self.is_shiny and not os.path.exists(animator_dir):
            animator_dir = self.pet_dir

        from entities.animator import DesktopPetAnimator
        self.animator = DesktopPetAnimator(self.canvas, self.config.get("images", {}), (self.size_w, self.size_h), (self.size_w, self.size_h), animator_dir)