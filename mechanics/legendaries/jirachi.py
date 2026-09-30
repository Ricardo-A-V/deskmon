import math
import random
import tkinter as tk

class JirachiMechanics:
    def trigger_jirachi_arts(self):
        if not getattr(self, 'get_all_pets', None): return
        
        self.current_state = 'jirachi_channeling'
        self.jirachi_timer = 100 
        self.jirachi_rot_speed = 0.01
        self.jirachi_angle_offset = 0.0
        
        self.schedule_loop(50, self.physics_loop)

    def cancel_jirachi_arts(self):
        for attr in ['jirachi_timer', 'jirachi_rot_speed', 'jirachi_angle_offset', 'flyby_tick', 'jirachi_sprite_x']:
            if hasattr(self, attr): delattr(self, attr)

        self.canvas.delete("jirachi_star_vfx")
        self.canvas.delete("jirachi_trail_vfx")
        
        self.canvas.config(width=self.size_w, height=self.size_h)
        self.canvas.itemconfig(self.canvas_image_id, state='normal')
        self.canvas.coords(self.canvas_image_id, self.size_w // 2, self.size_h // 2)

        if self.current_state not in ['dragged', 'exiting']:
            self.climbing_surface = 'floor'
            self.anchored_hwnd = None
            self.anchored_rect = None
            
            if self.x < self.v_x - 100 or self.x > self.v_x + self.v_width + 100:
                self.x = self.v_x + (self.v_width // 2)
                self.y = getattr(self, 'target_floor_y', self.default_floor_y) if getattr(self, 'is_flying', False) else self.default_floor_y
            
            if getattr(self, 'is_flying', False):
                self.floor_y = getattr(self, 'target_floor_y', self.y)
                self.current_state = 'ascending'
            else:
                self.current_state = 'falling'
                self.v_x_velocity = 0.0

    def _fsm_jirachi_channeling(self):
        if self.current_state != 'jirachi_channeling':
            self.cancel_jirachi_arts()
            return
        
        self.jirachi_timer -= 1
        self.canvas.delete("jirachi_star_vfx")
        
        if self.jirachi_timer > 0:
            self.jirachi_rot_speed += 0.003
            self.jirachi_angle_offset += self.jirachi_rot_speed
            
            cx = self.size_w / 2
            cy = (self.size_h / 2) + 15 
            
            R = 30.0 
            r = 12.0 
            
            points = []
            for i in range(10):
                radius = R if i % 2 == 0 else r
                angle = self.jirachi_angle_offset + (i * (math.pi / 5)) - (math.pi / 2)
                px = cx + math.cos(angle) * radius
                py = cy + math.sin(angle) * radius
                points.extend([px, py])
                
                if i % 2 == 0:
                    self.canvas.create_rectangle(px-2, py-2, px+2, py+2, fill="#FFFFFF", outline="", tags="jirachi_star_vfx")
            
            # FIX: Desempaquetado estricto (*points) para prevenir excepciones de sintaxis de Tkinter
            self.canvas.create_polygon(*points, outline="#FFD700", fill="", width=2, tags="jirachi_star_vfx")
            self.canvas.tag_lower("jirachi_star_vfx", self.canvas_image_id)
        else:
            self.current_state = 'jirachi_vanished'
            # FIX: Inyección de los argumentos obligatorios para prevenir el TypeError que mataba el hilo
            self._spawn_teleport_explosion(self.x, self.y)
            
            try: self.window.attributes('-alpha', 0.0)
            except: pass
            
            self.window.after(1000, self._start_flyby)
            return
            
        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def _fsm_jirachi_vanished(self):
        # FIX: Se requiere el estado intermedio para que el despachador dinámico no fuerce a Jirachi 
        # a retomar la rutina `_fsm_active` y rompa el canal Alpha durante el segundo de espera.
        self.schedule_loop(50, self.physics_loop)

    def _spawn_teleport_explosion(self, abs_x, abs_y):
        exp_win = tk.Toplevel(self.window.master)
        exp_win.overrideredirect(True)
        exp_win.attributes('-topmost', True)
        
        TRANS = '#010101'
        exp_win.config(bg=TRANS)
        try: exp_win.wm_attributes('-transparentcolor', TRANS)
        except: pass
        
        exp_win.geometry(f"{self.size_w}x{self.size_h}+{int(abs_x)}+{int(abs_y)}")
        c = tk.Canvas(exp_win, width=self.size_w, height=self.size_h, bg=TRANS, highlightthickness=0)
        c.pack()
        
        cx = self.size_w / 2
        cy = self.size_h / 2
        
        particles = []
        for _ in range(25):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(4.0, 10.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.choice([2, 3, 4])
            color = random.choice(["#FFD700", "#FFFFFF"])
            pid = c.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline="")
            particles.append({'id': pid, 'x': cx, 'y': cy, 'vx': vx, 'vy': vy})
            
        def animate_exp(step):
            if not exp_win.winfo_exists(): return
            if step > 15:
                exp_win.destroy()
                return
            for p in particles:
                p['x'] += p['vx']
                p['y'] += p['vy']
                p['vx'] *= 0.85 
                p['vy'] *= 0.85
                c.coords(p['id'], p['x']-2, p['y']-2, p['x']+2, p['y']+2)
            exp_win.after(30, lambda: animate_exp(step + 1))
            
        animate_exp(0)

    def _start_flyby(self):
        if not self.window.winfo_exists(): return
        self.current_state = 'jirachi_flyby'
        self.is_facing_right = True
        
        self.flyby_h = self.size_h * 4
        self.window.geometry(f"{self.v_width}x{self.flyby_h}+{self.v_x}+{int(self.v_y + self.v_height // 4)}")
        self.canvas.config(width=self.v_width, height=self.flyby_h)
        
        self.jirachi_sprite_x = -self.size_w
        self.flyby_tick = 0.0
        
        cy = (self.flyby_h / 2) + (40.0 * math.sin(self.flyby_tick))
        self.canvas.coords(self.canvas_image_id, self.jirachi_sprite_x, cy)
        
        # FIX: Restauración obligatoria del canal Alpha para evitar la invisibilidad durante el vuelo panorámico
        try: self.window.attributes('-alpha', 1.0)
        except: pass
        
        self.schedule_loop(20, self.physics_loop)

    def _fsm_jirachi_flyby(self):
        if self.current_state != 'jirachi_flyby':
            self.cancel_jirachi_arts()
            return
        
        self.flyby_tick += 0.2
        self.jirachi_sprite_x += 25.0
        
        cy = (self.flyby_h / 2) + (40.0 * math.sin(self.flyby_tick))
        self.canvas.coords(self.canvas_image_id, self.jirachi_sprite_x, cy)
        
        self._spawn_panoramic_trail(self.jirachi_sprite_x, cy)
        
        if self.jirachi_sprite_x > self.v_width + self.size_w:
            self._execute_star_shower()
            
            self.canvas.config(width=self.size_w, height=self.size_h)
            self.canvas.delete("jirachi_trail_vfx")
            
            self.canvas.coords(self.canvas_image_id, self.size_w // 2, self.size_h // 2)
            
            self.x = random.randint(self.v_x + 100, self.v_x + self.v_width - 100)
            self.y = getattr(self, 'target_floor_y', self.default_floor_y)
            self.floor_y = self.y
            
            # FIX: Encogimiento estructural de la ventana principal para alinear el Canvas con las coordenadas reales
            self.window.geometry(f"{self.size_w}x{self.size_h}+{int(self.x)}+{int(self.y)}")
            
            self.current_state = 'teleporting_in'
            self.teleport_step = 0.0
            try: self.window.attributes('-alpha', 0.0)
            except: pass
            
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            
            self._spawn_teleport_explosion(self.x, self.y)
            
            self.update_position()
            self.schedule_loop(20, self.physics_loop)
            return
            
        self.schedule_loop(20, self.physics_loop)

    def _spawn_panoramic_trail(self, cx, cy):
        for _ in range(2):
            ox = random.uniform(-15, 0)
            oy = random.uniform(-10, 10)
            size = random.choice([2, 3])
            
            pid = self.canvas.create_rectangle(cx+ox-size, cy+oy-size, cx+ox+size, cy+oy+size, fill="#FFD700", outline="", tags="jirachi_trail_vfx")
            self.canvas.tag_lower(pid, self.canvas_image_id)
            
            vx = random.uniform(-2.0, 0.0)
            vy = random.uniform(1.0, 4.0)
            
            def animate_trail(step, p_id, current_vx, current_vy):
                if self.current_state != 'jirachi_flyby' or not self.canvas.winfo_exists(): return
                
                if step > 50:
                    self.canvas.delete(p_id)
                else:
                    self.canvas.move(p_id, current_vx, current_vy)
                    self.schedule_loop(20, lambda: animate_trail(step + 1, p_id, current_vx, current_vy))
                    
            animate_trail(0, pid, vx, vy)

    def _execute_star_shower(self):
        star_count = random.randint(6, 12)
        limit_y = self.v_y + self.v_height
        
        for _ in range(star_count):
            start_x = random.randint(self.v_x + 50, self.v_x + self.v_width - 50)
            start_y = random.randint(self.v_y - 200, self.v_y - 50)
            self._spawn_physical_star(start_x, start_y, limit_y)

    def _spawn_physical_star(self, start_x, start_y, limit_y):
        s_win = tk.Toplevel(self.window.master)
        s_win.overrideredirect(True)
        s_win.attributes('-topmost', True)
        
        TRANS = '#010101'
        s_win.config(bg=TRANS)
        try: s_win.wm_attributes('-transparentcolor', TRANS)
        except: pass
        
        s_win.geometry(f"40x200+{int(start_x)}+{int(start_y)}")
        s_canvas = tk.Canvas(s_win, width=40, height=200, bg=TRANS, highlightthickness=0)
        s_canvas.pack()
        
        s_canvas.create_polygon(20,170, 24,180, 35,181, 26,188, 29,198, 20,192, 11,198, 14,188, 5,181, 16,180, fill="#FFD700", outline="")
        
        physics_data = {
            'x': float(start_x),
            'y': float(start_y),
            'vx': random.uniform(-3.0, 3.0),
            'vy': random.uniform(8.0, 15.0),
            'active': True,
            'trails': []
        }
        
        self._star_physics_loop(s_win, s_canvas, physics_data, limit_y)

    def _star_physics_loop(self, s_win, s_canvas, pd, limit_y):
        if not s_win.winfo_exists() or not pd['active']: return
        
        pd['x'] += pd['vx']
        pd['y'] += pd['vy']
        s_win.geometry(f"40x200+{int(pd['x'])}+{int(pd['y'])}")
        
        real_star_x = pd['x'] + 20
        real_star_y = pd['y'] + 180
        
        if random.randint(1, 100) <= 60:
            pid = s_canvas.create_rectangle(18, 178, 22, 182, fill="#FFD700", outline="")
            pd['trails'].append({'id': pid, 'life': 15})
            
        alive_trails = []
        for t in pd['trails']:
            s_canvas.move(t['id'], -pd['vx'] + random.uniform(-1, 1), -pd['vy'] - random.uniform(0.5, 2.0))
            t['life'] -= 1
            if t['life'] > 0:
                alive_trails.append(t)
            else:
                s_canvas.delete(t['id'])
        pd['trails'] = alive_trails
        
        hit_target = None
        if getattr(self, 'get_all_pets', None):
            for p in self.get_all_pets():
                if p.current_state not in ['exiting', 'dragged', 'falling_pokeball']:
                    if (p.x < real_star_x < p.x + p.size_w) and (p.y < real_star_y < p.y + p.size_h):
                        hit_target = p
                        break
        
        if hit_target:
            self._grant_wish_buff(hit_target)
            self._shatter_star(real_star_x, real_star_y)
            s_win.destroy()
            return
            
        if real_star_y >= limit_y or real_star_x < self.v_x or real_star_x > self.v_x + self.v_width:
            self._shatter_star(real_star_x, min(real_star_y, limit_y - 20))
            s_win.destroy()
            return
            
        s_win.after(20, lambda: self._star_physics_loop(s_win, s_canvas, pd, limit_y))

    def _grant_wish_buff(self, target):
        target.jirachi_buff_timer = 600 
        
        if not hasattr(target, 'base_buffered_speed'):
            target.base_buffered_speed = target.speed
            
        target.speed = int(target.base_buffered_speed * 2.0)
        target.necrozma_bright_mod = 1.5 
        
        self._buff_vfx_loop(target)

    def _buff_vfx_loop(self, target):
        if not target.window.winfo_exists() or getattr(target, 'jirachi_buff_timer', 0) <= 0: 
            if hasattr(target, 'necrozma_bright_mod'):
                target.necrozma_bright_mod = 1.0
            return
            
        target.necrozma_bright_mod = 1.5
        
        cx, cy = target.size_w / 2, target.size_h / 2
        rx = cx + random.randint(-20, 20)
        ry = cy + random.randint(-20, 20)
        size = random.choice([2, 3])
        pid = target.canvas.create_rectangle(rx-size, ry-size, rx+size, ry+size, fill="#FFD700", outline="")
        
        def fade(p_id):
            if not target.canvas.winfo_exists(): return
            target.canvas.delete(p_id)
            
        target.schedule_loop(150, lambda: fade(pid))
        target.window.after(100, lambda: self._buff_vfx_loop(target))

    def _shatter_star(self, x, y):
        exp_win = tk.Toplevel(self.window.master)
        exp_win.overrideredirect(True)
        exp_win.attributes('-topmost', True)
        
        TRANS = '#010101'
        exp_win.config(bg=TRANS)
        try: exp_win.wm_attributes('-transparentcolor', TRANS)
        except: pass
        
        exp_win.geometry(f"100x100+{int(x-50)}+{int(y-50)}")
        c = tk.Canvas(exp_win, width=100, height=100, bg=TRANS, highlightthickness=0)
        c.pack()
        
        particles = []
        for _ in range(8):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3.0, 7.0)
            particles.append({'x': 50, 'y': 50, 'vx': math.cos(angle)*speed, 'vy': math.sin(angle)*speed, 'id': None})
            
        for p in particles:
            p['id'] = c.create_rectangle(p['x']-2, p['y']-2, p['x']+2, p['y']+2, fill="#FFD700", outline="")
            
        def animate_shatter(step):
            if not exp_win.winfo_exists(): return
            if step > 10:
                exp_win.destroy()
                return
            for p in particles:
                p['x'] += p['vx']
                p['y'] += p['vy'] + (step * 0.5) 
                c.coords(p['id'], p['x']-2, p['y']-2, p['x']+2, p['y']+2)
            exp_win.after(30, lambda: animate_shatter(step + 1))
            
        animate_shatter(0)