import random
import math
import os

class LugiaMechanics:
    def cancel_lugia_arts(self):
        self.surface_angle = 0 
        if hasattr(self, 'lugia_target_x'): delattr(self, 'lugia_target_x')
        if hasattr(self, 'lugia_dash_direction'): delattr(self, 'lugia_dash_direction')
        
        if self.current_state not in ['dragged', 'exiting']:
            if getattr(self, 'is_flying', False):
                self.floor_y = self.y
                self.current_state = 'ascending'
            else:
                self.current_state = 'falling'

    def _fsm_lugia_channeling(self):
        # FIX: Calcular el objetivo una sola vez y guardarlo en memoria estática
        if not hasattr(self, 'lugia_target_x'):
            # Guardamos la dirección real del ataque futuro
            self.lugia_dash_direction = self.is_facing_right 
            
            # Calculamos el punto de retiro (A la inversa del ataque)
            if self.lugia_dash_direction:
                self.lugia_target_x = self.v_x - 300
            else:
                self.lugia_target_x = self.v_x + self.v_width + 300
                
            self.lugia_target_y = self.v_y + (self.v_height * 0.3)

        dx = self.lugia_target_x - self.x
        dy = self.lugia_target_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        fly_speed = self.speed * 2.5
        
        if dist > fly_speed:
            self.x += (dx/dist) * fly_speed
            self.y += (dy/dist) * fly_speed
            # El sprite mira hacia la dirección de su vuelo actual (De frente)
            self.is_facing_right = (dx > 0)
        else:
            self.x = self.lugia_target_x
            self.y = self.lugia_target_y
            self.current_state = 'lugia_dash'
            # Se da la vuelta para encarar la pantalla usando la dirección guardada
            self.is_facing_right = self.lugia_dash_direction
            self.lugia_pushed = False
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_lugia_dash(self):
        # 2. Cruzar la pantalla a velocidad extrema (Túnel de Viento)
        dash_speed = 100.0 
        
        self.x += dash_speed if self.is_facing_right else -dash_speed
        self.y += math.sin(self.x * 0.02) * 4.0 
        
        # FIX: Rotación de 45 grados hacia adelante (Picado aerodinámico)
        self.surface_angle = -30 if self.is_facing_right else 30
        
        # 3. Gatillo de la Onda de Viento (Justo al entrar en la zona visible)
        if not getattr(self, 'lugia_pushed', False):
            if (self.is_facing_right and self.x > self.v_x) or (not self.is_facing_right and self.x < self.v_x + self.v_width - self.size_w):
                self.lugia_pushed = True
                
                # TEMBLOR HORIZONTAL (Símil de onda sónica)
                if self.game_controller and hasattr(self.game_controller, 'root'):
                    pc = self.game_controller.root
                    try:
                        if not getattr(self.game_controller, 'is_shaking', False):
                            self.game_controller.is_shaking = True
                            ox = pc.winfo_x()
                            oy = pc.winfo_y()
                            shake_x = random.choice([-20, 20])
                            pc.geometry(f"+{ox + shake_x}+{oy}")
                            def restore_pc():
                                if pc.winfo_exists():
                                    pc.geometry(f"+{ox}+{oy}")
                                    self.game_controller.is_shaking = False
                            self.schedule_loop(80, restore_pc)
                    except: pass
                
                # PROPULSAR A TODAS LAS VÍCTIMAS
                if getattr(self, 'get_all_pets', None):
                    for target in self.get_all_pets():
                        if target != self and target.window.winfo_exists() and target.current_state not in ['exiting', 'dragged', 'spawning_wild', 'despawning_wild', 'falling_pokeball', 'falling_egg']:
                            
                            # LIMPIEZA DE EVENTOS ESTRICTA
                            if target.current_state.startswith('dark_'): target.cancel_dark_arts()
                            elif target.current_state.startswith('mewtwo_'): target.cancel_mewtwo_arts()
                            elif target.current_state in ['hooh_channeling', 'panic_run']: target.cancel_hooh_arts()
                            elif target.current_state in ['kyogre_channeling', 'deluge_float']: target.cancel_kyogre_arts()
                            elif target.current_state == 'groudon_channeling': target.cancel_groudon_arts()
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
                            
                            # INERCIA HORIZONTAL EXTREMA
                            target.current_state = 'thrown'
                            force_x = random.uniform(55.0, 95.0) 
                            target.v_x_velocity = force_x if self.is_facing_right else -force_x
                            target.v_y_velocity = random.uniform(-10.0, -25.0) 
                            target.anchored_hwnd = None
                            
                            target.wind_tunnel_timer = 50
                            target.show_wind_tunnel_vfx(self.is_facing_right)

        # 4. Finalizar el ataque al salir de la pantalla por el otro lado
        if (self.is_facing_right and self.x > self.v_x + self.v_width + 100) or (not self.is_facing_right and self.x < self.v_x - self.size_w - 100):
            self.surface_angle = 0 
            if hasattr(self, 'lugia_target_x'): delattr(self, 'lugia_target_x')
            if hasattr(self, 'lugia_dash_direction'): delattr(self, 'lugia_dash_direction')
            
            if getattr(self, 'is_flying', False):
                self.floor_y = self.y 
                self.current_state = 'ascending'
            else:
                self.current_state = 'falling'
            
        self.update_position()
        self.schedule_loop(16, self.physics_loop)

    def show_wind_tunnel_vfx(self, wind_to_right):
        # Delegación: Esta función la ejecutan LAS VÍCTIMAS, dibujando viento sobre sus propios cuerpos
        if getattr(self, 'current_state', 'exiting') == 'exiting' or getattr(self, 'wind_tunnel_timer', 0) <= 0: 
            self.canvas.delete("vfx_wind")
            return
            
        self.wind_tunnel_timer -= 1
        self.canvas.delete("vfx_wind")
        
        # Dibuja de 2 a 4 estelas de viento dinámicas
        for _ in range(random.randint(2, 4)):
            y = random.randint(10, self.size_h - 10)
            length = random.randint(20, 50)
            
            # Las líneas "atraviesan" la caja del Pokémon a la velocidad del viento
            x = random.randint(0, self.size_w // 2) if wind_to_right else random.randint(self.size_w // 2, self.size_w)
            end_x = x + length if wind_to_right else x - length
            
            self.canvas.create_line(x, y, end_x, y, fill="#FFFFFF", width=2, tags="vfx_wind")
            
        self.schedule_loop(30, lambda: self.show_wind_tunnel_vfx(wind_to_right))

