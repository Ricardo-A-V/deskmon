import random
import math
import tkinter as tk

class TerapagosMechanics:
    def start_terapagos_mechanic(self):
        if getattr(self, 'current_state', '') in ['dragged', 'exiting']: return
        if getattr(self, 'terapagos_cooldown', 0) > 0: return
        if hasattr(self, 'is_global_mechanic_active') and self.is_global_mechanic_active(): return

        name = self.pet_name.lower().replace("_", "").replace("-", "")
        if name not in ["terapagos", "terapagos1"]: return

        self.current_state = 'terapagos_channeling'
        self.terapagos_timer = 150 # 5 seconds
        self.terapagos_cooldown = 120000 # 1 hour
        
        self._init_terapagos_vfx()
        self.schedule_loop(30, self.physics_loop)

    def _init_terapagos_vfx(self):
        if hasattr(self, 'terapagos_vfx_win') and self.terapagos_vfx_win and self.terapagos_vfx_win.winfo_exists():
            return
            
        self.terapagos_vfx_win = tk.Toplevel(self.window.master)
        self.terapagos_vfx_win.overrideredirect(True)
        self.terapagos_vfx_win.attributes('-topmost', True)
        TRANS_COLOR = '#010101'
        self.terapagos_vfx_win.config(bg=TRANS_COLOR)
        try: self.terapagos_vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass
        self.terapagos_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        self.terapagos_canvas = tk.Canvas(self.terapagos_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
        self.terapagos_canvas.pack()
        
        self.terapagos_particles = []

    def cancel_terapagos_arts(self):
        if hasattr(self, 'terapagos_vfx_win') and self.terapagos_vfx_win and self.terapagos_vfx_win.winfo_exists():
            self.terapagos_vfx_win.destroy()
            self.terapagos_vfx_win = None
            
        for attr in ['terapagos_timer', 'terapagos_canvas', 'terapagos_particles', 'terapagos_area_x', 'terapagos_area_y', 'terapagos_area_r', 'tera_proj_x', 'tera_proj_y', 'tera_proj_vx', 'tera_proj_vy', 'tera_proj_g']:
            if hasattr(self, attr): delattr(self, attr)

        if self.current_state not in ['dragged', 'exiting']:
            self.current_state = 'falling'
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0

    def _fsm_terapagos_channeling(self):
        self.terapagos_timer -= 1
        
        my_cx = self.x - self.v_x + self.size_w/2
        my_cy = self.y - self.v_y + self.size_h/2
        
        if self.terapagos_timer % 3 == 0:
            color = random.choice(["#0000FF", "#00FFFF", "#FFFFFF"])
            angle = random.uniform(0, 2*math.pi)
            dist = random.uniform(40, 80)
            px = my_cx + math.cos(angle)*dist
            py = my_cy + math.sin(angle)*dist
            vx = -math.cos(angle)*2
            vy = -math.sin(angle)*2
            pts = [px, py-5, px+4, py, px, py+5, px-4, py]
            pid = self._draw_pixel_polygon(self.terapagos_canvas, pts, color, "", p_size=4, tags="tera_vfx")
            self.terapagos_particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': 20})
            
            speed = random.uniform(2, 5)
            self.spawn_terapagos_particle(my_cx, my_cy, math.cos(angle)*speed, math.sin(angle)*speed, 15, color)
            
        self._update_terapagos_vfx()
        
        if self.terapagos_timer <= 0:
            for _ in range(40):
                color = random.choice(["#0000FF", "#00FFFF", "#FFFFFF"])
                angle = random.uniform(0, 2*math.pi)
                speed = random.uniform(5, 12)
                self.spawn_terapagos_particle(my_cx, my_cy, math.cos(angle)*speed, math.sin(angle)*speed, 20, color)
            
            name = self.pet_name.lower().replace("_", "").replace("-", "")
            if name == "terapagos":
                self.manual_alter_form()
            
            self.current_state = 'terapagos_shooting'
            self.terapagos_area_r = self.v_width / 6.0 / 2.0
            self.terapagos_area_x = random.uniform(self.v_x + self.terapagos_area_r, self.v_x + self.v_width - self.terapagos_area_r)
            self.terapagos_area_y = self.default_floor_y
            
            self.tera_proj_x = my_cx
            self.tera_proj_y = my_cy
            dx = self.terapagos_area_x - self.tera_proj_x
            dy = self.terapagos_area_y - self.tera_proj_y
            ticks = 30.0
            self.tera_proj_vx = dx / ticks
            self.tera_proj_g = 1.0
            self.tera_proj_vy = (dy - 0.5 * self.tera_proj_g * ticks**2) / ticks
            
        self.schedule_loop(30, self.physics_loop)

    def _fsm_terapagos_shooting(self):
        self.tera_proj_x += self.tera_proj_vx
        self.tera_proj_y += self.tera_proj_vy
        self.tera_proj_vy += self.tera_proj_g
        
        color = random.choice(["#0000FF", "#00FFFF", "#FFFFFF", "#FF00FF"])
        self.spawn_terapagos_particle(self.tera_proj_x, self.tera_proj_y, -self.tera_proj_vx*0.2, -self.tera_proj_vy*0.2, 15, color)
        
        self._update_terapagos_vfx()
        
        if self.tera_proj_y >= self.terapagos_area_y:
            self.current_state = 'terapagos_area'
            self.terapagos_timer = 300 # 10 seconds
            
            r = self.terapagos_area_r
            corners = []
            for i in range(6):
                ang = i * (math.pi / 3)
                cx = self.terapagos_area_x - self.v_x + math.cos(ang) * r
                cy = self.terapagos_area_y - self.v_y + math.sin(ang) * r
                corners.append((cx, cy))
            
            # Smooth regular hexagon
            self.terapagos_canvas.create_polygon(corners, outline="#00FFFF", fill="", width=3, tags="tera_area_line")
            
        self.schedule_loop(30, self.physics_loop)

    def _fsm_terapagos_area(self):
        self.terapagos_timer -= 1
        
        if self.terapagos_timer % 4 == 0:
            angle = random.uniform(0, 2*math.pi)
            px = self.terapagos_area_x - self.v_x + math.cos(angle)*self.terapagos_area_r
            py = self.terapagos_area_y - self.v_y + math.sin(angle)*self.terapagos_area_r
            
            color = random.choice(["#0000FF", "#00FFFF", "#FFFFFF", "#FF00FF", "#FF0000", "#00FF00"])
            self.spawn_terapagos_particle(px, py, 0, -random.uniform(1, 3), 20, color)
            
            angle_in = random.uniform(0, 2*math.pi)
            dist_in = random.uniform(0, self.terapagos_area_r)
            px_in = self.terapagos_area_x - self.v_x + math.cos(angle_in)*dist_in
            py_in = self.terapagos_area_y - self.v_y + math.sin(angle_in)*dist_in
            self.spawn_terapagos_particle(px_in, py_in, 0, -random.uniform(2, 5), 15, color)
            
        if hasattr(self, 'get_all_pets'):
            for p in self.get_all_pets():
                if p != self and not getattr(p, 'is_egg', False) and p.current_state not in ['exiting', 'dragged', 'thrown', 'tera_absorbing']:
                    if not getattr(p, 'is_terastallized', False):
                        cx = p.x + p.size_w/2
                        cy = p.y + p.size_h/2
                        dx = cx - self.terapagos_area_x
                        dy = cy - self.terapagos_area_y
                        if math.hypot(dx, dy) <= self.terapagos_area_r:
                            self.terastallize_pet(p)
                            
        self._update_terapagos_vfx()
        
        if self.terapagos_timer <= 0:
            self.cancel_terapagos_arts()
            self.schedule_loop(30, self.physics_loop)
            return
            
        self.schedule_loop(30, self.physics_loop)

    def terastallize_pet(self, p):
        if hasattr(p, 'interrupt_current_state'): p.interrupt_current_state()
        p.current_state = 'tera_absorbing'
        p.tera_timer = 150 # 5 seconds
        p.is_terastallized = True
        p.v_x_velocity = 0.0
        p.v_y_velocity = 0.0
        
        types_colors = [
            (168, 168, 120), (192, 48, 40), (168, 144, 240), (160, 64, 160),
            (224, 192, 104), (184, 160, 56), (168, 184, 32), (112, 88, 152),
            (184, 184, 208), (240, 128, 48), (104, 144, 240), (120, 200, 80),
            (248, 208, 48), (248, 88, 136), (152, 216, 216), (112, 56, 248),
            (112, 88, 72), (238, 153, 172)
        ]
        p.tera_color = random.choice(types_colors)
        
        p._init_tera_victim_vfx()

    def _init_tera_victim_vfx(self):
        if hasattr(self, 'tera_vfx_win') and self.tera_vfx_win and self.tera_vfx_win.winfo_exists():
            return
            
        self.tera_vfx_win = tk.Toplevel(self.window.master)
        self.tera_vfx_win.overrideredirect(True)
        self.tera_vfx_win.attributes('-topmost', True)
        TRANS_COLOR = '#010101'
        self.tera_vfx_win.config(bg=TRANS_COLOR)
        try: self.tera_vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass
        self.tera_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        self.tera_canvas = tk.Canvas(self.tera_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
        self.tera_canvas.pack()
        self.tera_particles = []
        self.tera_crystal_id = None

    def cancel_tera_victim_arts(self):
        if hasattr(self, 'tera_vfx_win') and self.tera_vfx_win and self.tera_vfx_win.winfo_exists():
            self.tera_vfx_win.destroy()
            self.tera_vfx_win = None
            
        for attr in ['tera_timer', 'tera_canvas', 'tera_particles', 'tera_crystal_id', 'is_terastallized', 'tera_color', 'tera_active_timer']:
            if hasattr(self, attr): delattr(self, attr)

    def _fsm_tera_absorbing(self):
        self.tera_timer -= 1
        
        my_cx = self.x - self.v_x + self.size_w/2
        my_cy = self.y - self.v_y + self.size_h/2
        
        if self.tera_timer % 2 == 0:
            if hasattr(self, 'tera_canvas'):
                if self.tera_crystal_id:
                    self.tera_canvas.delete(self.tera_crystal_id)
                prog = 1.0 - (self.tera_timer / 150.0)
                my_cy = self.y - self.v_y + 10
                w = self.size_w * 0.6 * prog
                h = self.size_h * 0.7 * prog
                pts = [
                    my_cx, my_cy - h/2,
                    my_cx + w/2, my_cy - h/6,
                    my_cx + w/4, my_cy + h/2,
                    my_cx - w/4, my_cy + h/2,
                    my_cx - w/2, my_cy - h/6
                ]
                hex_color = '#%02x%02x%02x' % self.tera_color
                self.tera_crystal_id = self.tera_canvas.create_polygon(pts, outline=hex_color, fill="", width=4, tags="tera_c", joinstyle=tk.MITER)
                
                angle = random.uniform(0, 2*math.pi)
                dist = 80
                px = my_cx + math.cos(angle)*dist
                py = my_cy + math.sin(angle)*dist
                vx = -math.cos(angle)*4
                vy = -math.sin(angle)*4
                pid = self.tera_canvas.create_rectangle(px-2, py-2, px+2, py+2, fill=hex_color, outline=hex_color)
                self.tera_particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': 20})
                
        self._update_tera_victim_vfx()
        
        if self.tera_timer <= 0:
            self.current_state = 'idle'
            self.tera_active_timer = 900 # 30 seconds
            self.tera_active_loop()
            self.schedule_loop(30, self.physics_loop)
            return
            
        self.schedule_loop(30, self.physics_loop)
        
    def tera_active_loop(self):
        if not hasattr(self, 'tera_active_timer'): return
        
        self.tera_active_timer -= 1
        
        if getattr(self, 'is_terastallized', False):
            if hasattr(self, 'tera_canvas') and getattr(self, 'tera_crystal_id', None):
                my_cx = self.x - self.v_x + self.size_w/2
                my_cy = self.y - self.v_y + 10 # Above the head
                w = self.size_w * 0.6
                h = self.size_h * 0.7
                pts = [
                    my_cx, my_cy - h/2,
                    my_cx + w/2, my_cy - h/6,
                    my_cx + w/4, my_cy + h/2,
                    my_cx - w/4, my_cy + h/2,
                    my_cx - w/2, my_cy - h/6
                ]
                self.tera_canvas.coords(self.tera_crystal_id, *pts)
                
            if self.tera_active_timer <= 0:
                if hasattr(self, 'tera_canvas'):
                    my_cx = self.x - self.v_x + self.size_w/2
                    my_cy = self.y - self.v_y + self.size_h/2
                    hex_color = '#%02x%02x%02x' % self.tera_color
                    for _ in range(40):
                        angle = random.uniform(0, 2*math.pi)
                        speed = random.uniform(4, 12)
                        pid = self.tera_canvas.create_rectangle(my_cx-3, my_cy-3, my_cx+3, my_cy+3, fill=hex_color, outline=hex_color)
                        self.tera_particles.append({'id': pid, 'vx': math.cos(angle)*speed, 'vy': math.sin(angle)*speed, 'life': 20})
                        
                    if getattr(self, 'tera_crystal_id', None):
                        self.tera_canvas.delete(self.tera_crystal_id)
                        self.tera_crystal_id = None
                        
                self.is_terastallized = False
                if hasattr(self, 'tera_color'): delattr(self, 'tera_color')
                # Add extra time for particles to finish
                self.tera_active_timer = 25 
                
        self._update_tera_victim_vfx()
        
        if not getattr(self, 'is_terastallized', False) and self.tera_active_timer <= 0:
            self.cancel_tera_victim_arts()
            return
            
        self.window.after(33, self.tera_active_loop)

    def _update_tera_victim_vfx(self):
        if not hasattr(self, 'tera_canvas') or not self.tera_canvas.winfo_exists(): return
        new_parts = []
        for p in self.tera_particles:
            p['life'] -= 1
            if p['life'] > 0:
                self.tera_canvas.move(p['id'], p['vx'], p['vy'])
                new_parts.append(p)
            else:
                self.tera_canvas.delete(p['id'])
        self.tera_particles = new_parts

    def spawn_terapagos_particle(self, cx, cy, vx, vy, life, color):
        if not hasattr(self, 'terapagos_canvas'): return
        pid = self.terapagos_canvas.create_rectangle(cx-2, cy-2, cx+2, cy+2, fill=color, outline=color, tags="tera_vfx")
        self.terapagos_particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': life})
        
    def _update_terapagos_vfx(self):
        if not hasattr(self, 'terapagos_canvas') or not self.terapagos_canvas.winfo_exists(): return
        new_parts = []
        for p in self.terapagos_particles:
            p['life'] -= 1
            if p['life'] > 0:
                self.terapagos_canvas.move(p['id'], p['vx'], p['vy'])
                new_parts.append(p)
            else:
                self.terapagos_canvas.delete(p['id'])
        self.terapagos_particles = new_parts
