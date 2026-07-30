import random
import math
import tkinter as tk

class NecrozmaMechanics:
    def cancel_necrozma_arts(self):
        # Destroys the independent VFX canvas to prevent memory leaks during forced interruptions
        if hasattr(self, 'necrozma_win') and self.necrozma_win and self.necrozma_win.winfo_exists():
            self.necrozma_win.destroy()
            self.necrozma_win = None

        # Cleans up FSM phase trackers and active projectile matrices
        for attr in ['necrozma_phase', 'necrozma_timer', 'necrozma_shots_fired', 'n_projectiles', 'n_charge_particles']:
            if hasattr(self, attr): delattr(self, attr)

        self.canvas.delete("vfx_n_charge")
        
        if self.current_state not in ['dragged', 'exiting']:
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            if getattr(self, 'is_flying', False):
                self.floor_y = getattr(self, 'target_floor_y', self.y)
                self.current_state = 'ascending'
            else:
                self.current_state = 'falling'

    def _fsm_necrozma_channeling(self):
        if not hasattr(self, 'necrozma_phase'):
            self.necrozma_phase = 0
            self.necrozma_timer = 60 
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            
            # CONFIGURACIÓN: Modifica este valor para cambiar la cantidad total de proyectiles disparados
            self.necrozma_total_shots = 20
            
            if not getattr(self, 'is_flying', False):
                current_env, _ = self.get_window_environment()
                physical_floor = current_env['y'] if self.y <= current_env['y'] + 15 else self.default_floor_y
                if self.y < physical_floor:
                    self.y = physical_floor

            self.create_necrozma_global_canvas()

        if self.necrozma_phase == 0:
            self.necrozma_timer -= 1
            self.spawn_necrozma_charge_vfx()
            
            if self.necrozma_timer <= 0:
                # FIX: Borrado estricto e inmediato de las partículas de carga justo antes de empezar a disparar
                self.canvas.delete("vfx_n_charge")
                
                self.necrozma_phase = 1
                self.necrozma_timer = 20 
                self.necrozma_shots_fired = 0

        elif self.necrozma_phase == 1:
            self.necrozma_timer -= 1
            
            ox = random.choice([-4, 0, 4])
            oy = random.choice([-4, 0, 4])
            self.canvas.coords(self.canvas_image_id, (self.size_w//2) + ox, (self.size_h//2) + oy)
            
            # Utiliza la variable dinámica en lugar de un número fijo
            total_shots = getattr(self, 'necrozma_total_shots', 10)
            if self.necrozma_timer % 1 == 0 and getattr(self, 'necrozma_shots_fired', 0) < total_shots:
                self.fire_necrozma_projectile()
                self.necrozma_shots_fired += 1
                
            if self.necrozma_timer <= 0:
                self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2) 
                self.necrozma_phase = 2
                self.necrozma_timer = 100 

        elif self.necrozma_phase == 2:
            self.necrozma_timer -= 1
            if not getattr(self, 'n_projectiles', []) or self.necrozma_timer <= 0:
                self.necrozma_cooldown = 72000 
                self.current_state = 'idle'
                self.cancel_necrozma_arts()
                
        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def spawn_necrozma_charge_vfx(self):
        # Spawns particles radially that travel inward to simulate light being devoured
        cx = self.size_w / 2
        cy = self.size_h / 2
        
        for _ in range(2):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(60, 120)
            
            px = cx + math.cos(angle) * dist
            py = cy + math.sin(angle) * dist
            
            size = random.choice([2, 3, 4])
            color = random.choice(["#FFFFFF", "#FFFFE0", "#FFFACD"]) # White and slight yellow tones
            
            pid = self.canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color, tags="vfx_n_charge")
            
            if not hasattr(self, 'n_charge_particles'): self.n_charge_particles = []
            
            # Vectors are strictly directed to the core with high friction to simulate gravitational pull
            self.n_charge_particles.append({
                'id': pid,
                'x': px, 'y': py,
                'vx': (cx - px) * 0.15,
                'vy': (cy - py) * 0.15,
                'life': 8
            })
            
        self.necrozma_charge_vfx_loop()

    def necrozma_charge_vfx_loop(self):
        if not hasattr(self, 'n_charge_particles'): return
        alive = []
        for p in self.n_charge_particles:
            if p['life'] > 0:
                self.canvas.move(p['id'], p['vx'], p['vy'])
                p['life'] -= 1
                alive.append(p)
            else:
                self.canvas.delete(p['id'])
        self.n_charge_particles = alive

    def create_necrozma_global_canvas(self):
        self.necrozma_win = tk.Toplevel(self.window.master)
        self.necrozma_win.title("VFX_Necrozma_Ignore")
        self.necrozma_win.overrideredirect(True)
        self.necrozma_win.attributes('-topmost', True)
        
        TRANS_COLOR = '#010101'
        self.necrozma_win.config(bg=TRANS_COLOR)
        try: self.necrozma_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass

        self.necrozma_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        self.necrozma_canvas = tk.Canvas(self.necrozma_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
        self.necrozma_canvas.pack()
        
        if not hasattr(self, 'n_projectiles'):
            self.n_projectiles = []
            self.necrozma_projectile_engine()

    def fire_necrozma_projectile(self):
        start_x = (self.x + self.size_w / 2) - self.v_x
        start_y = (self.y + self.size_h / 2) - self.v_y
        
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(35.0, 50.0) 
        
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        
        # FIX VISUAL: Dibujado como segmento lineal con reborde simulado (dos líneas superpuestas)
        tracer_length = 2.0 
        tail_x = start_x - vx * tracer_length
        tail_y = start_y - vy * tracer_length
        
        self.necrozma_canvas.create_line(start_x, start_y, tail_x, tail_y, fill="#FFFACD", width=6, capstyle=tk.ROUND, tags="vfx_n_proj_bg")
        pid = self.necrozma_canvas.create_line(start_x, start_y, tail_x, tail_y, fill="#FFFFFF", width=3, capstyle=tk.ROUND, tags="vfx_n_proj")
        
        self.n_projectiles.append({
            'id': pid,
            'x': start_x,
            'y': start_y,
            'vx': vx,
            'vy': vy,
            'bounces_left': random.randint(3, 7) 
        })

    def necrozma_projectile_engine(self):
        if not hasattr(self, 'necrozma_canvas'): return
        if not getattr(self, 'n_projectiles', []) and getattr(self, 'current_state', '') != 'necrozma_channeling': 
            return
            
        alive_projectiles = []
        hit_targets = set()
        
        if hasattr(self, 'n_projectiles'):
            self.necrozma_canvas.delete("vfx_n_proj_bg") 
            
            for p in self.n_projectiles:
                p['x'] += p['vx']
                p['y'] += p['vy']
                
                bounced = False
                if p['x'] < 0:
                    p['x'] = 0
                    p['vx'] *= -1
                    bounced = True
                elif p['x'] > self.v_width:
                    p['x'] = self.v_width
                    p['vx'] *= -1
                    bounced = True
                    
                if p['y'] < 0:
                    p['y'] = 0
                    p['vy'] *= -1
                    bounced = True
                elif p['y'] > self.v_height:
                    p['y'] = self.v_height
                    p['vy'] *= -1
                    bounced = True
                    
                if bounced:
                    p['bounces_left'] -= 1
                    
                tracer_length = 2.0
                tail_x = p['x'] - p['vx'] * tracer_length
                tail_y = p['y'] - p['vy'] * tracer_length
                
                self.necrozma_canvas.create_line(p['x'], p['y'], tail_x, tail_y, fill="#FFFACD", width=6, capstyle=tk.ROUND, tags="vfx_n_proj_bg")
                self.necrozma_canvas.coords(p['id'], p['x'], p['y'], tail_x, tail_y)
                    
                destroyed = False
                if getattr(self, 'get_all_pets', None):
                    for target in self.get_all_pets():
                        if target == self or target.current_state in ['exiting', 'dragged'] or getattr(target, 'is_egg', False): continue
                        
                        target_cx = target.x + target.size_w / 2 - self.v_x
                        target_cy = target.y + target.size_h / 2 - self.v_y
                        
                        if math.hypot(p['x'] - target_cx, p['y'] - target_cy) < max(target.size_w, target.size_h) / 2:
                            hit_targets.add(target)
                            destroyed = True
                            break 
                
                if p['bounces_left'] < 0 or destroyed:
                    self.necrozma_canvas.delete(p['id'])
                else:
                    alive_projectiles.append(p)
                    
            self.n_projectiles = alive_projectiles
            
        for target in hit_targets:
            self.apply_necrozma_darkness(target)
            self.apply_necrozma_growth_buff()
            
        if getattr(self, 'current_state', '') == 'necrozma_channeling' or getattr(self, 'n_projectiles', []):
            # FIX LÓGICO: Solo intenta reordenar las capas (Z-Order) si hay proyectiles vivos en este fotograma
            if getattr(self, 'n_projectiles', []):
                try:
                    self.necrozma_canvas.tag_raise("vfx_n_proj", "vfx_n_proj_bg")
                except tk.TclError:
                    pass
            self.window.after(30, self.necrozma_projectile_engine)

    # ==========================================
    # MODIFIER PIPELINE & DECAY TIMERS
    # ==========================================
    def apply_necrozma_darkness(self, target):
        # Accumulates exactly 33.33% darkness per hit, capped at 1.0 (100% black).
        # Your rendering pipeline MUST map 'target.darkness_mod' to PIL.ImageEnhance.Brightness()
        current_darkness = getattr(target, 'darkness_mod', 0.0)
        target.darkness_mod = min(1.0, current_darkness + 0.3333)
        
        # Resets the 30 seconds wait timer (Decay starts AFTER 30 seconds of not being hit)
        target.darkness_wait_timer = 30 
        
        # Bootstraps the autonomous decay loop if it's not already running
        if not getattr(target, 'darkness_decay_active', False):
            target.darkness_decay_active = True
            self.target_darkness_decay_loop(target)

    def target_darkness_decay_loop(self, target):
        if not hasattr(target, 'darkness_mod') or target.darkness_mod <= 0:
            target.darkness_mod = 0.0
            target.darkness_decay_active = False
            return
            
        if getattr(target, 'darkness_wait_timer', 0) > 0:
            # Still in the 30 seconds waiting period
            target.darkness_wait_timer -= 1
        else:
            # Decreases by 1% (0.01) per second
            target.darkness_mod = max(0.0, target.darkness_mod - 0.01)
            
        # Loops exactly every 1000ms (1 second) to maintain strict chronological timing
        target.window.after(1000, lambda t=target: self.target_darkness_decay_loop(t))

    def apply_necrozma_growth_buff(self):
        # Accumulates 5% growth and 5% brightness per hit.
        # Your rendering pipeline MUST map these to PIL.Image.resize and PIL.ImageEnhance.Brightness
        self.necrozma_scale_mod = getattr(self, 'necrozma_scale_mod', 1.0) + 0.05
        self.necrozma_bright_mod = getattr(self, 'necrozma_bright_mod', 1.0) + 0.05
        
        # Resets the 2 minutes (120 seconds) wait timer
        self.necrozma_buff_wait_timer = 120 
        
        if not getattr(self, 'necrozma_buff_decay_active', False):
            self.necrozma_buff_decay_active = True
            self.necrozma_self_buff_decay_loop()

    def necrozma_self_buff_decay_loop(self):
        is_scale_base = getattr(self, 'necrozma_scale_mod', 1.0) <= 1.0
        is_bright_base = getattr(self, 'necrozma_bright_mod', 1.0) <= 1.0
        
        if is_scale_base and is_bright_base:
            self.necrozma_scale_mod = 1.0
            self.necrozma_bright_mod = 1.0
            self.necrozma_buff_decay_active = False
            return
            
        if getattr(self, 'necrozma_buff_wait_timer', 0) > 0:
            # The wait timer ticks down 5 seconds at a time in this specific loop context
            self.necrozma_buff_wait_timer -= 5
        else:
            # Decreases by 1% (0.01) every 5 seconds
            self.necrozma_scale_mod = max(1.0, self.necrozma_scale_mod - 0.01)
            self.necrozma_bright_mod = max(1.0, self.necrozma_bright_mod - 0.01)
            
        # Loops exactly every 5000ms (5 seconds) per your specification
        self.window.after(5000, self.necrozma_self_buff_decay_loop)