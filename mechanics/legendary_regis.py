import math
import random
import tkinter as tk

class LegendaryRegisMechanics:
    def _get_regi_color(self):
        regi_id = self.pet_name.lower().replace("_", "").replace("-", "")
        colors = {
            "regice": "#00FFFF",
            "regirock": "#8B4513",
            "registeel": "#808080",
            "regieleki": "#FFFF00",
            "regidrago": "#FF1493",
            "regigigas": "#FFD700" 
        }
        return colors.get(regi_id, "#FFFFFF")

    def cancel_regi_arts(self):
        for attr in ['regi_target', 'regi_phase', 'regi_timer', 'regi_approach_timer', 'rg_speed_mult', 'rg_speed_timer', 'rg_step_counter', 'rg_walk_ticks']:
            if hasattr(self, attr): delattr(self, attr)

        self.canvas.itemconfig(self.canvas_image_id, state='normal')

        if self.current_state not in ['dragged', 'exiting']:
            self.climbing_surface = 'floor'
            self.anchored_hwnd = None
            self.anchored_rect = None
            
            regi_id = self.pet_name.lower().replace("_", "").replace("-", "")
            
            if regi_id == "regieleki":
                self.current_state = 'thrown'
                self.v_x_velocity = 0.0
                self.v_y_velocity = 0.0
            elif getattr(self, 'is_flying', False):
                self.floor_y = getattr(self, 'target_floor_y', self.y)
                self.current_state = 'ascending'
            else:
                self.current_state = 'falling'
                self.v_x_velocity = 0.0

    def trigger_regi_arts(self):
        if not getattr(self, 'get_all_pets', None): return
        
        excluded_states = ['exiting', 'dragged', 'spawning_wild', 'despawning_wild', 'falling_pokeball', 'falling_egg', 'celebi_frozen']
        valid_targets = []
        
        my_anchor = getattr(self, 'anchored_hwnd', None)
        regi_id = self.pet_name.lower().replace("_", "").replace("-", "")
        
        my_physical_floor = self.floor_y + self.size_h + getattr(self, 'offset_y', 0)
        
        for p in self.get_all_pets():
            if p != self and p.current_state not in excluded_states and not getattr(p, 'is_egg', False):
                p_physical_floor = p.floor_y + p.size_h + getattr(p, 'offset_y', 0)
                
                if regi_id == "regieleki":
                    valid_targets.append(p)
                elif regi_id == "regigigas":
                    if getattr(p, 'anchored_hwnd', None) == my_anchor and abs(p_physical_floor - my_physical_floor) < 150:
                        valid_targets.append(p)
                else:
                    if getattr(p, 'anchored_hwnd', None) == my_anchor and getattr(p, 'climbing_surface', 'floor') == 'floor':
                        if abs(p_physical_floor - my_physical_floor) < 20:
                            valid_targets.append(p)
                    
        if valid_targets:
            self.regi_target = random.choice(valid_targets)
            self.current_state = 'regi_channeling'
            self.regi_timer = 60 
            self.schedule_loop(50, self.physics_loop)

    def _fsm_regi_channeling(self):
        if self.current_state != 'regi_channeling': return
        
        self.regi_timer -= 1
        regi_id = self.pet_name.lower().replace("_", "").replace("-", "")
        
        if self.regi_timer > 0:
            if regi_id == "regigigas":
                ox = random.choice([-2, 0, 2])
                oy = random.choice([-1, 0, 1])
                self.canvas.coords(self.canvas_image_id, (self.size_w//2) + ox, (self.size_h//2) + oy)
                
                if self.regi_timer % 3 == 0:
                    self._spawn_regigigas_channel_vfx()
            elif self.regi_timer % 2 == 0:
                self._spawn_channeling_particles()
        else:
            self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
            
            if regi_id == "regigigas":
                self.current_state = 'regigigas_approach'
                self.rg_speed_mult = 0.33
                self.rg_speed_timer = 166 
                self.rg_step_counter = 0.0
            else:
                self.current_state = 'regi_approach'
                self.regi_approach_timer = 200 
            
        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def _spawn_regigigas_channel_vfx(self):
        px = random.uniform(20, self.size_w - 20)
        py = self.size_h - 10
        vx_out = random.uniform(-4.0, 4.0)
        vy_out = random.uniform(-6.0, -2.0)
        
        d_size = random.choice([3, 4, 5])
        pid_dirt = self.canvas.create_rectangle(px-d_size, py-d_size, px+d_size, py+d_size, fill="#654321", outline="")
        
        angle = random.uniform(0, math.pi)
        radius = random.uniform(60.0, 100.0)
        ex = (self.size_w / 2) + math.cos(angle) * radius
        ey = (self.size_h / 2) - math.sin(angle) * radius
        
        dx = (self.size_w / 2) - ex
        dy = (self.size_h / 2) - ey
        dist = math.hypot(dx, dy)
        vx_in = (dx / dist) * 8.0 if dist > 0 else 0
        vy_in = (dy / dist) * 8.0 if dist > 0 else 0
        
        e_size = 3
        pid_energy = self.canvas.create_rectangle(ex-e_size, ey-e_size, ex+e_size, ey+e_size, fill="#FFD700", outline="")

        def animate_fx(step, c_px, c_py, c_ex, c_ey):
            if self.current_state == 'exiting' or not self.canvas.winfo_exists(): return
            if step > 15:
                self.canvas.delete(pid_dirt)
                self.canvas.delete(pid_energy)
            else:
                c_px += vx_out
                c_py += vy_out + (step * 0.5) 
                c_ex += vx_in
                c_ey += vy_in
                
                self.canvas.coords(pid_dirt, c_px-d_size, c_py-d_size, c_px+d_size, c_py+d_size)
                self.canvas.coords(pid_energy, c_ex-e_size, c_ey-e_size, c_ex+e_size, c_ey+e_size)
                self.schedule_loop(30, lambda: animate_fx(step + 1, c_px, c_py, c_ex, c_ey))
                
        animate_fx(0, px, py, ex, ey)

    def _spawn_channeling_particles(self):
        regi_id = self.pet_name.lower().replace("_", "").replace("-", "")
        color = self._get_regi_color()
        
        if regi_id == "regieleki":
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(20.0, 50.0)
            px = (self.size_w / 2) + math.cos(angle) * radius
            py = (self.size_h / 2) + math.sin(angle) * radius
            vy = random.uniform(-2.0, 2.0)
            vx = random.uniform(-2.0, 2.0)
        else:
            px = random.uniform(10, self.size_w - 10)
            py = self.size_h - random.uniform(0, 10)
            vy = random.uniform(-3.0, -1.0)
            vx = random.uniform(-0.5, 0.5)
            
        size = random.choice([2, 3, 4])
        pid = self.canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline="")
        
        def animate_particle(step, current_px, current_py):
            if self.current_state == 'exiting' or not self.canvas.winfo_exists(): return
            if step > 10:
                self.canvas.delete(pid)
            else:
                current_px += vx
                current_py += vy
                self.canvas.coords(pid, current_px-size, current_py-size, current_px+size, current_py+size)
                self.schedule_loop(50, lambda: animate_particle(step + 1, current_px, current_py))
                
        animate_particle(0, px, py)

    # ---------------------------------------------------------
    # REGIGIGAS EXCLUSIVE LOGIC
    # ---------------------------------------------------------
    
    def _trigger_regigigas_shake(self):
        def _shake(step):
            if self.current_state == 'exiting' or not self.canvas.winfo_exists(): return
            if step > 6:
                self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
                return
            ox = random.choice([-5, 0, 5])
            oy = random.choice([-3, 0, 3])
            self.canvas.coords(self.canvas_image_id, (self.size_w//2) + ox, (self.size_h//2) + oy)
            self.schedule_loop(20, lambda: _shake(step + 1))
        _shake(0)

    def _fsm_regigigas_approach(self):
        if self.current_state != 'regigigas_approach': return
        
        if not getattr(self, 'regi_target', None) or not self.regi_target.window.winfo_exists() or self.regi_target.current_state == 'exiting':
            self.cancel_regi_arts()
            self.schedule_loop(50, self.physics_loop)
            return
            
        target = self.regi_target
        
        my_physical_floor = self.floor_y + self.size_h + getattr(self, 'offset_y', 0)
        p_physical_floor = target.floor_y + target.size_h + getattr(target, 'offset_y', 0)
        
        if getattr(target, 'anchored_hwnd', None) != getattr(self, 'anchored_hwnd', None) or abs(p_physical_floor - my_physical_floor) > 150 or target.current_state == 'dragged':
            self.cancel_regi_arts()
            self.schedule_loop(50, self.physics_loop)
            return

        self.rg_speed_timer -= 1
        if self.rg_speed_timer <= 0:
            self.rg_speed_mult = min(1.0, self.rg_speed_mult + 0.1)
            self.rg_speed_timer = 166 

        my_cx = self.x + self.size_w / 2
        target_cx = target.x + target.size_w / 2
        
        self.is_facing_right = (target_cx > my_cx)
        push_dir = 1 if self.is_facing_right else -1
        
        base_speed = 5.0
        current_speed = base_speed * self.rg_speed_mult
        
        hitbox_range = max(self.size_w * 0.5, current_speed + 15)
        dist_x = abs(my_cx - target_cx)
        
        if dist_x > hitbox_range:
            old_x = self.x
            self.x += current_speed * push_dir
            
            if not getattr(self, 'can_screen_wrap', False):
                self.x = max(self.v_x, min(self.x, (self.v_x + self.v_width) - self.size_w))

            if abs(self.x - old_x) < 0.1:
                self.current_state = 'regigigas_grab'
                self.rg_walk_ticks = 40 
                if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
                target.current_state = 'regigigas_lifted'
                target.v_x_velocity = 0.0
                target.v_y_velocity = 0.0
            else:
                self.rg_step_counter += current_speed
                if self.rg_step_counter >= 35.0: 
                    self.rg_step_counter = 0.0
                    self._trigger_regigigas_shake() 
                    self._spawn_regigigas_dirt_step()
                
        else:
            self.current_state = 'regigigas_grab'
            self.rg_walk_ticks = 40 
            if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
            target.current_state = 'regigigas_lifted'
            target.v_x_velocity = 0.0
            target.v_y_velocity = 0.0
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _spawn_regigigas_dirt_step(self):
        # Corrección isométrica: Los pies reales están al 55% y 45% del AABB duplicado
        px = (self.size_w * 0.55) if self.is_facing_right else (self.size_w * 0.45)
        py = self.size_h - 5
        
        # Corrección balística: Multiplicada masa y vectores de salpicadura
        for _ in range(random.randint(12, 18)):
            vx = random.uniform(2.0, 9.0) * (-1 if self.is_facing_right else 1)
            vy = random.uniform(-10.0, -3.0)
            d_size = random.choice([4, 6, 8])
            pid = self.canvas.create_rectangle(px-d_size, py-d_size, px+d_size, py+d_size, fill="#654321", outline="")
            
            def fade(step, i_pid, c_px, c_py, c_vx, c_vy):
                if self.current_state == 'exiting' or not self.canvas.winfo_exists(): return
                if step > 12:
                    self.canvas.delete(i_pid)
                else:
                    c_px += c_vx
                    c_py += c_vy + (step * 0.8)
                    self.canvas.coords(i_pid, c_px-d_size, c_py-d_size, c_px+d_size, c_py+d_size)
                    self.schedule_loop(30, lambda: fade(step+1, i_pid, c_px, c_py, c_vx, c_vy))
            fade(0, pid, px, py, vx, vy)

    def _fsm_regigigas_grab(self):
        if self.current_state != 'regigigas_grab': return
        
        target = getattr(self, 'regi_target', None)
        
        if not target or not target.window.winfo_exists() or target.current_state != 'regigigas_lifted':
            self.cancel_regi_arts()
            self.schedule_loop(50, self.physics_loop)
            return
            
        self.rg_walk_ticks -= 1
        
        offset_x = (self.size_w * 0.35) if self.is_facing_right else -(target.size_w * 0.35)
        target.x = self.x + offset_x
        target.y = self.y + (self.size_h // 2) - (target.size_h // 2)
        target.update_position()
        
        if self.rg_walk_ticks > 0:
            push_dir = 1 if self.is_facing_right else -1
            self.x += (5.0 * self.rg_speed_mult) * push_dir
            if not getattr(self, 'can_screen_wrap', False):
                self.x = max(self.v_x, min(self.x, (self.v_x + self.v_width) - self.size_w))
                
            self.rg_step_counter += (5.0 * self.rg_speed_mult)
            if self.rg_step_counter >= 35.0: 
                self.rg_step_counter = 0.0
                self._trigger_regigigas_shake() 
                self._spawn_regigigas_dirt_step()
        else:
            self._execute_regigigas_throw(target)
            self.cancel_regi_arts()
            self.schedule_loop(50, self.physics_loop)
            return
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_regigigas_lifted(self):
        # Silenciador físico para la víctima. 
        # Evita que el motor nativo del objetivo intente levitar o caer mientras está agarrado.
        if self.current_state != 'regigigas_lifted': return
        self.v_x_velocity = 0.0
        self.v_y_velocity = 0.0
        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def _execute_regigigas_throw(self, target):
        my_cx = self.x + self.size_w / 2
        target_cx = target.x + target.size_w / 2
        self.is_facing_right = (target_cx > my_cx)
        
        if target.current_state.startswith('dark_') and hasattr(target, 'cancel_dark_arts'): target.cancel_dark_arts()
        if target.current_state.startswith('mewtwo_') and hasattr(target, 'cancel_mewtwo_arts'): target.cancel_mewtwo_arts()
            
        target.climbing_surface = 'floor'
        target.anchored_hwnd = None
        target.anchored_rect = None
        target.surface_angle = 0
        target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
        
        if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
        target.current_state = 'regi_victim_flying'
        target.regi_attacker_id = "regigigas"
        target.regi_bounces = 0
        target.regi_max_bounces = random.randint(5, 10)
        target.regi_trail_color = "#FFD700" 
        
        push_dir = 1 if self.is_facing_right else -1
        target.v_x_velocity = 55.0 * push_dir
        target.v_y_velocity = random.choice([-35.0, 35.0])
        
        self._trigger_regigigas_shake()
        self._spawn_regi_explosion("#FFD700")

    # ---------------------------------------------------------
    # STANDARD REGIS LOGIC
    # ---------------------------------------------------------
    def _fsm_regi_approach(self):
        if self.current_state != 'regi_approach': return
        
        self.regi_approach_timer -= 1
        
        if self.regi_approach_timer <= 0 or not getattr(self, 'regi_target', None) or not self.regi_target.window.winfo_exists() or self.regi_target.current_state == 'exiting':
            self.cancel_regi_arts()
            self.schedule_loop(50, self.physics_loop)
            return
            
        target = self.regi_target
        regi_id = self.pet_name.lower().replace("_", "").replace("-", "")
        
        my_physical_floor = self.floor_y + self.size_h + getattr(self, 'offset_y', 0)
        p_physical_floor = target.floor_y + target.size_h + getattr(target, 'offset_y', 0)
        
        if regi_id != "regieleki":
            if getattr(target, 'anchored_hwnd', None) != getattr(self, 'anchored_hwnd', None) or getattr(target, 'climbing_surface', 'floor') != 'floor' or abs(p_physical_floor - my_physical_floor) > 20 or target.current_state == 'dragged':
                self.cancel_regi_arts()
                self.schedule_loop(50, self.physics_loop)
                return

        my_cx = self.x + self.size_w / 2
        target_cx = target.x + target.size_w / 2
        self.is_facing_right = (target_cx > my_cx)
        push_dir = 1 if self.is_facing_right else -1
        
        if regi_id == "regieleki": speed = 35.0
        elif regi_id == "regice": speed = 12.0
        else: speed = 6.0
        
        hitbox_range = max(self.size_w * 0.6, speed + 5)
        
        if regi_id == "regieleki":
            dx = target.x - self.x
            dy = target.y - self.y
            dist = math.hypot(dx, dy)
            
            if dist > hitbox_range:
                old_x, old_y = self.x, self.y
                self.x += (dx / dist) * speed
                self.y += (dy / dist) * speed
                
                if not getattr(self, 'can_screen_wrap', False):
                    self.x = max(self.v_x, min(self.x, (self.v_x + self.v_width) - self.size_w))
                
                if abs(self.x - old_x) < 0.1 and abs(self.y - old_y) < 0.1:
                    self.current_state = 'regi_strike'
                    self.regi_timer = 1 
                elif random.randint(1, 100) <= 30: 
                    self._spawn_regi_trail(self._get_regi_color())
            else:
                self.current_state = 'regi_strike'
                self.regi_timer = 1 
        else:
            dist_x = abs(my_cx - target_cx)
            if dist_x > hitbox_range:
                old_x = self.x
                
                if dist_x < speed:
                    self.x += dist_x * push_dir
                else:
                    self.x += speed * push_dir
                
                if not getattr(self, 'can_screen_wrap', False):
                    self.x = max(self.v_x, min(self.x, (self.v_x + self.v_width) - self.size_w))
                    
                if abs(self.x - old_x) < 0.1:
                    self.current_state = 'regi_strike'
                    self.regi_timer = 1 
                elif regi_id == "regice" and random.randint(1, 100) <= 30: 
                    self._spawn_regi_trail(self._get_regi_color())
            else:
                self.current_state = 'regi_strike'
                self.regi_timer = 1  
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_regi_strike(self):
        if self.current_state != 'regi_strike': return
        
        self.regi_timer -= 1
        
        if getattr(self, 'regi_target', None) and self.regi_target.window.winfo_exists():
            my_cx = self.x + self.size_w / 2
            target_cx = self.regi_target.x + self.regi_target.size_w / 2
            self.is_facing_right = (target_cx > my_cx)
        
        if self.regi_timer <= 0:
            target = getattr(self, 'regi_target', None)
            if target and target.window.winfo_exists() and target.current_state != 'exiting':
                self._execute_regi_impact(target)
            self.cancel_regi_arts()
            self.schedule_loop(50, self.physics_loop)
            return
            
        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def _execute_regi_impact(self, target):
        regi_id = self.pet_name.lower().replace("_", "").replace("-", "")
        
        my_cx = self.x + self.size_w / 2
        target_cx = target.x + target.size_w / 2
        self.is_facing_right = (target_cx > my_cx)
        
        if target.current_state.startswith('dark_') and hasattr(target, 'cancel_dark_arts'): target.cancel_dark_arts()
        if target.current_state.startswith('mewtwo_') and hasattr(target, 'cancel_mewtwo_arts'): target.cancel_mewtwo_arts()
        if target.current_state == 'bubbled': 
            if hasattr(target, 'manage_bubble_vfx'): target.manage_bubble_vfx(False)
            if hasattr(target, 'show_bubble_burst_vfx'): target.show_bubble_burst_vfx()
            
        target.climbing_surface = 'floor'
        target.anchored_hwnd = None
        target.anchored_rect = None
        target.surface_angle = 0
        target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
        
        if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
        target.current_state = 'regi_victim_flying'
        target.regi_attacker_id = regi_id
        target.regi_bounces = 0
        
        push_dir = 1 if self.is_facing_right else -1
        trail_color = self._get_regi_color()
        target.regi_trail_color = trail_color
        
        self._spawn_regi_explosion(trail_color)
        
        if regi_id == "registeel":
            target.v_x_velocity = 45.0 * push_dir
            target.v_y_velocity = random.choice([-30.0, 30.0])
        elif regi_id == "regieleki":
            target.v_x_velocity = 65.0 * push_dir
            target.v_y_velocity = -12.0
        elif regi_id == "regidrago":
            target.v_x_velocity = 65.0 * push_dir
            target.v_y_velocity = -8.0
        elif regi_id == "regirock":
            target.v_x_velocity = 30.0 * push_dir
            target.v_y_velocity = -45.0
        elif regi_id == "regice":
            target.v_x_velocity = 45.0 * push_dir
            target.v_y_velocity = -25.0
        else:
            target.v_x_velocity = 40.0 * push_dir
            target.v_y_velocity = -30.0

    def _spawn_regi_explosion(self, color):
        cx = self.x - self.v_x + self.size_w / 2
        cy = self.y - self.v_y + self.size_h / 2
        
        wave_win = tk.Toplevel(self.window.master)
        wave_win.overrideredirect(True)
        wave_win.attributes('-topmost', True)
        
        TRANS = '#010101'
        wave_win.config(bg=TRANS)
        try: wave_win.wm_attributes('-transparentcolor', TRANS)
        except: pass
        
        wave_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        w_canvas = tk.Canvas(wave_win, width=self.v_width, height=self.v_height, bg=TRANS, highlightthickness=0)
        w_canvas.pack()
        
        state = {'r': 5.0, 'width': 15.0}
        
        def animate():
            if not wave_win.winfo_exists(): return
            w_canvas.delete("wave")
            state['r'] += 15.0
            state['width'] *= 0.8
            
            if state['r'] >= 150 or state['width'] < 1.0:
                wave_win.destroy()
                return
                
            self._draw_pixel_circle_bbox(w_canvas, cx-state['r'], cy-state['r'], cx+state['r'], cy+state['r'], outline=color, width=max(1, int(state['width'])), tags="wave")
            wave_win.after(20, animate)
        animate()

    def _spawn_regi_trail(self, color):
        cx = self.size_w / 2
        cy = self.size_h / 2
        pid = self.canvas.create_rectangle(cx-3, cy-3, cx+3, cy+3, fill=color, outline="")
        
        def fade(step):
            if self.current_state == 'exiting' or not self.canvas.winfo_exists(): return
            if step > 5:
                self.canvas.delete(pid)
            else:
                self.schedule_loop(30, lambda: fade(step + 1))
        fade(0)
    
    # ---------------------------------------------------------
    # VICTIM PHYSICS (INCLUDES REGIGIGAS LOCAL/GLOBAL SHOCKS)
    # ---------------------------------------------------------
    def _fsm_regi_victim_flying(self):
        if getattr(self, 'current_state', '') != 'regi_victim_flying': return
        
        attacker = getattr(self, 'regi_attacker_id', '')
        self._spawn_regi_trail(getattr(self, 'regi_trail_color', '#FFFFFF'))
        
        bounce_limit = getattr(self, 'regi_max_bounces', 5) if attacker == "regigigas" else (3 if attacker == "registeel" else 0)
        
        if bounce_limit > 0 and getattr(self, 'regi_bounces', 0) < bounce_limit:
            self.x += self.v_x_velocity
            self.y += self.v_y_velocity
            self.surface_angle = (getattr(self, 'surface_angle', 0) + 45) % 360
            
            bounced = False
            if self.x <= self.v_x:
                self.x = self.v_x; self.v_x_velocity *= -1; bounced = True
            elif self.x >= self.v_x + self.v_width - self.size_w:
                self.x = self.v_x + self.v_width - self.size_w; self.v_x_velocity *= -1; bounced = True
                
            if self.y <= self.v_y:
                self.y = self.v_y; self.v_y_velocity *= -1; bounced = True
            elif self.y >= self.default_floor_y:
                self.y = self.default_floor_y; self.v_y_velocity *= -1; bounced = True
                
            if bounced:
                self.regi_bounces += 1
                if attacker == "regigigas":
                    if self.regi_bounces < bounce_limit:
                        self._trigger_local_shockwave()
                    else:
                        self._trigger_global_earthquake()
                        self._embed_victim()
                        return
                
            self.update_position()
            self.schedule_loop(20, self.physics_loop)
            return
            
        if attacker == "registeel": self.surface_angle = 0 
        
        self.v_y_velocity += 1.5
        self.x += self.v_x_velocity
        self.y += self.v_y_velocity
        
        hit_surface = None
        
        if self.x <= self.v_x:
            self.x = self.v_x; self.v_x_velocity *= -0.7; hit_surface = 'wall_l'
        elif self.x >= self.v_x + self.v_width - self.size_w:
            self.x = self.v_x + self.v_width - self.size_w; self.v_x_velocity *= -0.7; hit_surface = 'wall_r'
            
        if self.y >= self.default_floor_y:
            self.y = self.default_floor_y; self.v_y_velocity = 0; hit_surface = 'floor'
        elif self.y <= self.v_y:
            self.y = self.v_y; hit_surface = 'ceiling'

        if hit_surface:
            if attacker == "regirock":
                self._embed_victim(surface=hit_surface)
                return
            elif hit_surface == 'floor':
                if attacker == "regice":
                    self.current_state = 'regice_frozen'
                    self.regice_frozen_timer = 150 
                    self.v_x_velocity = 0.0
                    self.regice_frozen_vfx_loop()
                elif attacker == "regieleki":
                    self.current_state = 'zekrom_paralyzed'
                    self.zekrom_para_timer = 200
                    if hasattr(self, 'zekrom_para_vfx_loop'): self.zekrom_para_vfx_loop()
                elif attacker == "regidrago":
                    self.current_state = 'regidrago_slowed'
                    self.drago_slow_timer = 300 
                    self.drago_slow_vfx_loop()
                elif attacker == "registeel":
                    self.current_state = 'falling'
                    
        self.update_position()
        self.schedule_loop(20, self.physics_loop)

    def _embed_victim(self, surface=None):
        self.current_state = 'regirock_embedded'
        
        if not surface:
            if self.x <= self.v_x + 10: surface = 'wall_l'
            elif self.x >= self.v_x + self.v_width - self.size_w - 10: surface = 'wall_r'
            elif self.y <= self.v_y + 10: surface = 'ceiling'
            else: surface = 'floor'
            
        if surface == 'floor':
            self.surface_angle = 180
            self.y = self.default_floor_y + (self.size_h // 2)
        elif surface == 'ceiling':
            self.surface_angle = 0
            self.y = self.v_y - (self.size_h // 2)
        elif surface == 'wall_l':
            self.surface_angle = 90
            self.x = self.v_x - (self.size_w // 2)
        elif surface == 'wall_r':
            self.surface_angle = 270
            self.x = (self.v_x + self.v_width) - (self.size_w // 2)
            
        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def _trigger_local_shockwave(self):
        if not getattr(self, 'get_all_pets', None): return
        
        for p in self.get_all_pets():
            if p != self and p.current_state not in ['exiting', 'regirock_embedded', 'regigigas_lifted']:
                dist = math.hypot(p.x - self.x, p.y - self.y)
                if dist < 250:
                    if hasattr(p, 'interrupt_current_state'): p.interrupt_current_state()
                    p.current_state = 'thrown'
                    push_dir = 1 if p.x > self.x else -1
                    p.v_x_velocity = 20.0 * push_dir
                    p.v_y_velocity = -10.0
                    p.anchored_hwnd = None
                    p.climbing_surface = 'floor'

    def _trigger_global_earthquake(self):
        if not getattr(self, 'get_all_pets', None): return
        
        for p in self.get_all_pets():
            if p != self and p.current_state not in ['exiting', 'regirock_embedded']:
                if hasattr(p, 'interrupt_current_state'): p.interrupt_current_state()
                p.current_state = 'thrown'
                p.v_x_velocity = random.choice([-25.0, 25.0])
                p.v_y_velocity = -35.0
                p.anchored_hwnd = None
                p.climbing_surface = 'floor'
                
                if hasattr(p, 'trigger_landing_shake'): p.trigger_landing_shake()

    def _fsm_regirock_embedded(self):
        if getattr(self, 'current_state', '') != 'regirock_embedded': return
        self.v_x_velocity = 0.0
        self.v_y_velocity = 0.0
        self.update_position()
        self.schedule_loop(100, self.physics_loop)
        
    def _fsm_regidrago_slowed(self):
        if getattr(self, 'current_state', '') != 'regidrago_slowed': return
        self.drago_slow_timer -= 1
        if random.randint(1, 100) <= 5: self.is_facing_right = not self.is_facing_right
        speed = max(1.0, self.speed * 0.3)
        self.x += speed if self.is_facing_right else -speed
        self.x = max(self.v_x, min(self.x, (self.v_x + self.v_width) - self.size_w))
        if self.drago_slow_timer <= 0: self.current_state = 'idle'
        self.update_position()
        self.schedule_loop(50, self.physics_loop)
        
    def drago_slow_vfx_loop(self):
        if getattr(self, 'drago_slow_timer', 0) <= 0 or getattr(self, 'current_state', '') not in ['regidrago_slowed', 'dragged']: return
        if random.randint(1, 100) <= 40:
            cx, cy = self.size_w / 2, self.size_h / 2
            rx = cx + random.randint(-15, 15)
            ry = cy + random.randint(-15, 15)
            color = random.choice(["#000000", "#DC143C"])
            size = random.choice([2, 3])
            pid = self.canvas.create_rectangle(rx-size, ry-size, rx+size, ry+size, fill=color, outline="")
            def fade(p_id):
                if self.current_state == 'exiting' or not self.canvas.winfo_exists(): return
                self.canvas.delete(p_id)
            self.schedule_loop(200, lambda: fade(pid))
        self.window.after(100, self.drago_slow_vfx_loop)
        
    def _fsm_regice_frozen(self):
        if getattr(self, 'current_state', '') != 'regice_frozen': return
        self.regice_frozen_timer -= 1
        if self.regice_frozen_timer <= 0:
            if getattr(self, 'is_flying', False):
                self.floor_y = getattr(self, 'target_floor_y', self.y)
                self.current_state = 'ascending'
            else:
                self.current_state = 'idle'
        self.update_position()
        self.schedule_loop(20, self.physics_loop)
        
    def regice_frozen_vfx_loop(self):
        if getattr(self, 'current_state', 'exiting') not in ['regice_frozen', 'dragged'] or getattr(self, 'regice_frozen_timer', 0) <= 0:
            self.canvas.delete("vfx_ice_cube")
            return
        self.canvas.delete("vfx_ice_cube")
        cx, cy = self.size_w / 2, self.size_h / 2
        s = (min(self.size_w, self.size_h) / 2)
        self.canvas.create_rectangle(cx-s, cy-s, cx+s, cy+s, fill="#ADD8E6", outline="#FFFFFF", width=4, stipple="gray50", tags="vfx_ice_cube")
        self.canvas.create_line(cx-s, cy-s, cx-s+10, cy-s+10, fill="#FFFFFF", width=2, tags="vfx_ice_cube")
        self.canvas.create_line(cx+s, cy-s, cx+s-10, cy-s+10, fill="#FFFFFF", width=2, tags="vfx_ice_cube")
        self.window.after(50, self.regice_frozen_vfx_loop)