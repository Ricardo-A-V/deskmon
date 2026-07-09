import random
import math
import tkinter as tk

class KyuremMechanics:
    def cancel_kyurem_arts(self):
        if hasattr(self, 'kyurem_win') and self.kyurem_win and self.kyurem_win.winfo_exists():
            self.kyurem_win.destroy()
            self.kyurem_win = None

        for attr in ['kyurem_phase', 'kyurem_timer']:
            if hasattr(self, attr): delattr(self, attr)

        self.canvas.itemconfig(self.canvas_image_id, state='normal')
        self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)

        if self.current_state not in ['dragged', 'exiting']:
            if getattr(self, 'is_flying', False):
                self.floor_y = getattr(self, 'target_floor_y', self.y)
                self.current_state = 'ascending'
            else:
                self.current_state = 'falling'

    def _fsm_kyurem_channeling(self):
        if not hasattr(self, 'kyurem_phase'):
            self.kyurem_phase = 0
            self.kyurem_timer = 40 

        if self.kyurem_phase == 0:
            ox = random.choice([-4, 0, 4])
            oy = random.choice([-3, 0, 3])
            self.canvas.coords(self.canvas_image_id, (self.size_w//2) + ox, (self.size_h//2) + oy)
            
            self.kyurem_timer -= 1
            if self.kyurem_timer <= 0:
                self.kyurem_phase = 1
                self.kyurem_timer = 100 
                self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
                self.spawn_kyurem_global_vfx() 
                
        elif self.kyurem_phase == 1:
            self.kyurem_timer -= 1
            
            if self.kyurem_timer % 5 == 0:
                self.kyurem_apply_glaciate_hitbox()
                
            if self.kyurem_timer <= 0:
                if hasattr(self, 'kyurem_win') and self.kyurem_win:
                    self.kyurem_win.destroy()
                    self.kyurem_win = None
                    
                self.current_state = 'idle'
                self.kyurem_cooldown = 108000 
                delattr(self, 'kyurem_phase')

        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def spawn_kyurem_global_vfx(self):
        self.kyurem_win = tk.Toplevel(self.window.master)
        self.kyurem_win.title("VFX_Kyurem_Ignore") # FIX TÉCNICO: Evitar colisión física
        self.kyurem_win.overrideredirect(True)
        self.kyurem_win.attributes('-topmost', True)
        
        TRANS_COLOR = '#010101'
        self.kyurem_win.config(bg=TRANS_COLOR)
        try: self.kyurem_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass

        # OPTIMIZACIÓN: Reducción del tamaño de la ventana al nuevo radio (400px * 2)
        self.kyurem_win_size = 800
        cx = int(self.x + self.size_w/2 - self.kyurem_win_size/2)
        cy = int(self.y + self.size_h/2 - self.kyurem_win_size/2)
        self.kyurem_win.geometry(f"{self.kyurem_win_size}x{self.kyurem_win_size}+{cx}+{cy}")

        self.kyurem_canvas = tk.Canvas(self.kyurem_win, width=self.kyurem_win_size, height=self.kyurem_win_size, bg=TRANS_COLOR, highlightthickness=0)
        self.kyurem_canvas.pack()
        self.kyurem_particles = []
        self.kyurem_global_loop()

    def kyurem_global_loop(self):
        if getattr(self, 'current_state', '') != 'kyurem_channeling': return
        if not hasattr(self, 'kyurem_win') or not self.kyurem_win or not self.kyurem_win.winfo_exists(): return

        cx = self.kyurem_win_size / 2
        cy = self.kyurem_win_size / 2

        for direction in [-1, 1]:
            for _ in range(2): 
                base_angle = 0 if direction == 1 else math.pi
                
                # FIX: Dispersión visual ampliada a 0.8 radianes (~45 grados) para coincidir con la nueva hitbox
                angle = random.uniform(base_angle - 0.8, base_angle + 0.8)
                speed = random.uniform(15.0, 35.0) 
                
                size = random.choice([6, 8, 12])
                color = random.choice(["#E0FFFF", "#ADD8E6", "#FFFFFF"])
                
                pid = self.kyurem_canvas.create_polygon(
                    cx, cy-size, cx+size, cy, cx, cy+size, cx-size, cy,
                    fill=color, outline="#87CEEB", tags="vfx_k"
                )
                self.kyurem_particles.append({
                    'id': pid, 'vx': math.cos(angle)*speed, 'vy': math.sin(angle)*speed, 'life': 20
                })

        alive = []
        for p in self.kyurem_particles:
            if p['life'] > 0:
                self.kyurem_canvas.move(p['id'], p['vx'], p['vy'])
                p['life'] -= 1
                alive.append(p)
            else:
                self.kyurem_canvas.delete(p['id'])
        self.kyurem_particles = alive

        self.window.after(80, self.kyurem_global_loop)

    def kyurem_apply_glaciate_hitbox(self):
        if not getattr(self, 'get_all_pets', None): return
        
        for target in self.get_all_pets():
            # FIX ESTRUCTURAL: Ignorar siempre a los huevos
            if target != self and target.current_state != 'exiting' and getattr(target, 'kyurem_frozen_timer', 0) <= 0 and not getattr(target, 'is_egg', False):
                
                my_cx = self.x + self.size_w / 2
                my_cy = self.y + self.size_h / 2
                target_cx = target.x + target.size_w / 2
                target_cy = target.y + target.size_h / 2
                
                dx = target_cx - my_cx
                dy = target_cy - my_cy
                dist = math.hypot(dx, dy)
                
                if dist < 400:
                    angle = math.degrees(math.atan2(dy, dx))
                    
                    if (-35 <= angle <= 35) or (angle >= 125) or (angle <= -125):
                        self.apply_freeze(target)

    def apply_freeze(self, target):
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
        target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
        try: target.window.attributes('-alpha', 1.0)
        except: pass

        target.current_state = 'kyurem_frozen'
        target.kyurem_frozen_timer = 300 
        
        # FIX: Eliminamos la aniquilación de velocidad. 
        # Si iban corriendo al ser impactados, conservarán su inercia y resbalarán.
        if not hasattr(target, 'v_x_velocity'): target.v_x_velocity = 0.0
        if not hasattr(target, 'v_y_velocity'): target.v_y_velocity = 0.0

        target.kyurem_frozen_cube_loop()

    def _fsm_kyurem_frozen(self):
        # 1. FÍSICA HORIZONTAL (Hielo resbaladizo)
        # Factor de fricción muy bajo (0.98) comparado con el estándar de Tkinter
        self.v_x_velocity *= 0.98 
        self.x += self.v_x_velocity

        # Límites del monitor para evitar que se resbalen fuera de la pantalla
        if getattr(self, 'can_screen_wrap', False):
            if self.x <= self.v_x - self.size_w: self.x = self.v_x + self.v_width
            elif self.x >= self.v_x + self.v_width: self.x = self.v_x - self.size_w
        else:
            if self.x <= self.v_x:
                self.x = self.v_x
                self.v_x_velocity *= -0.7 # Rebote contra el borde izquierdo
            elif self.x >= (self.v_x + self.v_width) - self.size_w:
                self.x = (self.v_x + self.v_width) - self.size_w
                self.v_x_velocity *= -0.7 # Rebote contra el borde derecho

        # 2. FÍSICA VERTICAL (Gravedad)
        gravity = 4.0 if getattr(self, 'heavy_fall', False) else 1.5
        self.v_y_velocity += gravity
        next_y = self.y + self.v_y_velocity
        
        # Tolerancia dinámica para no atravesar ventanas cayendo a alta velocidad
        fall_tolerance = max(15, int(self.v_y_velocity) + 15) if self.v_y_velocity > 0 else 15
        current_env, _ = self.get_window_environment()
        
        highest_surface = current_env['y'] if self.y <= current_env['y'] + fall_tolerance else self.default_floor_y
        target_hwnd = current_env['hwnd'] if highest_surface == current_env['y'] else None
        target_rect = current_env['rect'] if highest_surface == current_env['y'] else None
        
        # 3. MOTOR DE COLISIÓN AABB 2D (Cubos entre sí)
        if getattr(self, 'get_all_pets', None):
            for other in self.get_all_pets():
                if other != self and other.current_state == 'kyurem_frozen':
                    
                    # Verificación rápida de Hitbox masivo
                    if abs(self.x - other.x) < self.size_w * 0.95 and abs(self.y - other.y) < self.size_h * 1.5:
                        
                        other_roof_y = other.y - self.size_h
                        
                        # A. Colisión Vertical (Apilamiento Perfecto)
                        if self.y <= other_roof_y + 15 and next_y >= other_roof_y:
                            if other_roof_y < highest_surface:
                                highest_surface = other_roof_y
                                target_hwnd = getattr(other, 'anchored_hwnd', None)
                                target_rect = getattr(other, 'anchored_rect', None)
                                
                        # B. Colisión Lateral (Choque Transversal y Transferencia de Momento)
                        elif abs(next_y - other.y) < self.size_h * 0.8:
                            # Choca por la izquierda del otro bloque
                            if self.x < other.x and self.v_x_velocity > 0:
                                self.x = other.x - self.size_w * 0.95
                                other.v_x_velocity += self.v_x_velocity * 0.7 # Transfiere el 70% de su energía
                                self.v_x_velocity *= -0.3 # Rebota levemente
                            # Choca por la derecha del otro bloque
                            elif self.x > other.x and self.v_x_velocity < 0:
                                self.x = other.x + self.size_w * 0.95
                                other.v_x_velocity += self.v_x_velocity * 0.7
                                self.v_x_velocity *= -0.3

        # 4. RESOLUCIÓN DE SUELO Y ANCLAJE
        if next_y >= highest_surface:
            self.y = highest_surface
            self.floor_y = highest_surface
            self.v_y_velocity = 0.0
            
            # FIX: Anclar lógicamente el bloque a la ventana detectada
            if target_hwnd:
                self.anchored_hwnd = target_hwnd
                self.anchored_rect = target_rect
            else:
                self.anchored_hwnd = None
        else:
            self.y = next_y
            
        self.update_position()
        
        # FIX: Hilo acelerado a 20ms en lugar de 50ms para que el deslizamiento
        # y las colisiones AABB se procesen de forma fluida y sin empotramientos.
        self.schedule_loop(20, self.physics_loop)

    def kyurem_frozen_cube_loop(self):
        if getattr(self, 'current_state', 'exiting') == 'exiting': return
        
        if getattr(self, 'kyurem_frozen_timer', 0) <= 0:
            self.canvas.delete("vfx_ice_cube")
            
            if self.current_state == 'kyurem_frozen':
                if getattr(self, 'is_flying', False):
                    self.floor_y = self.y
                    self.current_state = 'ascending'
                else:
                    self.current_state = 'idle'
            return

        self.kyurem_frozen_timer -= 1
        self.canvas.delete("vfx_ice_cube")
        
        cx = self.size_w / 2
        cy = self.size_h / 2
        s = (min(self.size_w, self.size_h) / 2)
        
        self.canvas.create_rectangle(
            cx-s, cy-s, cx+s, cy+s, 
            fill="#ADD8E6", outline="#FFFFFF", width=4, 
            stipple="gray50", tags="vfx_ice_cube"
        )
        
        self.canvas.create_line(cx-s, cy-s, cx-s+10, cy-s+10, fill="#FFFFFF", width=2, tags="vfx_ice_cube")
        self.canvas.create_line(cx+s, cy-s, cx+s-10, cy-s+10, fill="#FFFFFF", width=2, tags="vfx_ice_cube")

        self.window.after(50, self.kyurem_frozen_cube_loop)