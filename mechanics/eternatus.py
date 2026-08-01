import os
import math
import random
import ctypes
import tkinter as tk

class EternatusMechanics:
    def cancel_eternatus_arts(self):
        # Clears UI overlays immediately to free memory resources
        if hasattr(self, 'etr_beam_win') and self.etr_beam_win and self.etr_beam_win.winfo_exists():
            self.etr_beam_win.destroy()
            self.etr_beam_win = None

        if hasattr(self, 'etr_vfx_win') and self.etr_vfx_win and self.etr_vfx_win.winfo_exists():
            self.etr_vfx_win.destroy()
            self.etr_vfx_win = None

        for attr in ['etr_phase', 'etr_timer', 'etr_beam_x', 'etr_particles', 'etr_scale', 'etr_vfx_dim']:
            if hasattr(self, attr): delattr(self, attr)

        if hasattr(self, 'necrozma_scale_mod'):
            self.necrozma_scale_mod = 1.0

        if self.current_state not in ['dragged', 'exiting']:
            self.v_x_velocity = 0.0
            self.anchored_hwnd = None
            
            # Repositions entity to physical drop point if interrupted while off-screen
            if self.y < self.v_y:
                self.y = self.v_y - self.size_h
                self.x = random.randint(self.v_x, self.v_x + self.v_width - self.size_w)
                self.current_state = 'falling'
            else:
                self.current_state = 'ascending' if getattr(self, 'is_flying', False) else 'idle'
                
            self.v_y_velocity = 0.0

    def _fsm_eternatus_channeling(self):
        if not hasattr(self, 'etr_phase'):
            self.etr_phase = 0
            self.etr_timer = 100 
            self.etr_scale = 1.0
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            
            # Caches initial dimensions to calculate relative scaling correctly
            if not hasattr(self, 'base_size_w'):
                self.base_size_w = self.size_w
                self.base_size_h = self.size_h
            
            self.setup_etr_vfx_layer()

        if self.etr_phase == 0:
            self.etr_timer -= 1
            
            self.spawn_etr_absorption_particle()
            self.process_etr_particles()
            
            # Modifies scaling parameter at reduced intervals to avoid DWM update saturation
            if self.etr_timer % 2 == 0:
                self.etr_scale += 0.02
                self.necrozma_scale_mod = self.etr_scale
            
            if self.etr_timer <= 0:
                self.etr_phase = 1
                self.v_y_velocity = -15.0 
                
                if hasattr(self, 'etr_vfx_win') and self.etr_vfx_win:
                    self.etr_vfx_win.destroy()
                    self.etr_vfx_win = None

        elif self.etr_phase == 1:
            self.y += self.v_y_velocity
            if self.y + self.size_h < self.v_y:
                self.etr_phase = 2
                self.etr_timer = 100 
                self.v_y_velocity = 0.0
                self.necrozma_scale_mod = 1.0

        elif self.etr_phase == 2:
            self.etr_timer -= 1
            if self.etr_timer <= 0:
                self.etr_phase = 3
                self.etr_timer = 7 
                
                single_monitor_w = self.window.winfo_screenwidth()
                self.etr_beam_width = single_monitor_w // 6
                self.etr_beam_x = random.randint(self.v_x, self.v_x + self.v_width - self.etr_beam_width)
                self.spawn_eternabeam_window()

        elif self.etr_phase == 3:
            self.etr_timer -= 1
            progress = 1.0 - (self.etr_timer / 7.0)
            current_h = max(1, int(self.v_height * progress))
            
            if hasattr(self, 'etr_beam_win') and self.etr_beam_win.winfo_exists():
                self.etr_beam_win.geometry(f"{self.etr_beam_width}x{current_h}+{self.etr_beam_x}+{self.v_y}")
                self.etr_beam_canvas.move("etr_lines", 0, 80)

            if self.etr_timer <= 0:
                self.etr_phase = 4
                self.etr_timer = 200 

        elif self.etr_phase == 4:
            self.etr_timer -= 1
            
            if hasattr(self, 'etr_beam_win') and self.etr_beam_win.winfo_exists():
                self.etr_beam_canvas.move("etr_lines", 0, 25)
                # Loops rendering lines back to the top to simulate continuous descent
                for item in self.etr_beam_canvas.find_withtag("etr_lines"):
                    coords = self.etr_beam_canvas.coords(item)
                    if coords and coords[1] > self.v_height:
                        self.etr_beam_canvas.move(item, 0, -self.v_height - 100)
                
                # Countermeasures OS Z-Index override: If the user clicks the taskbar, Windows 
                # naturally pulls the taskbar above transparent layers. This forces the beam back on top every 2 seconds.
                if self.etr_timer % 40 == 0:
                    try: self.etr_beam_win.attributes('-topmost', True)
                    except: pass
            
            if getattr(self, 'get_all_pets', None):
                invalid_states = ['exiting', 'dragged', 'falling', 'thrown', 'jumping_arc', 'landing_shake']
                for target in self.get_all_pets():
                    if target == self or getattr(target, 'is_egg', False) or target.current_state in invalid_states: 
                        continue
                    if not getattr(target, 'is_dynamaxed', False) and getattr(target, 'climbing_surface', 'floor') == 'floor':
                        tx_center = target.x + target.size_w / 2
                        if self.etr_beam_x <= tx_center <= self.etr_beam_x + self.etr_beam_width:
                            self.inject_dynamax_lifecycle(target)

            if self.etr_timer <= 0:
                self.etr_phase = 5
                self.v_y_velocity = 8.0 
                self.y = self.v_y - self.size_h
                self.x = random.randint(self.v_x, self.v_x + self.v_width - self.size_w)
                
                if hasattr(self, 'etr_beam_win') and self.etr_beam_win.winfo_exists():
                    self.etr_beam_win.destroy()
                    self.etr_beam_win = None

        elif self.etr_phase == 5:
            self.y += self.v_y_velocity
            target_y = getattr(self, 'target_floor_y', self.default_floor_y) if getattr(self, 'is_flying', False) else self.default_floor_y
            
            if self.y >= target_y:
                self.y = target_y
                self.v_y_velocity = 0.0
                self.etr_phase = 6
                
        elif self.etr_phase == 6:
            self.eternatus_cooldown = 72000
            self.cancel_eternatus_arts()
            self.schedule_loop(50, self.physics_loop)
            return

        self.update_position()
            
        if hasattr(self, 'etr_vfx_win') and self.etr_vfx_win and self.etr_vfx_win.winfo_exists() and hasattr(self, 'etr_vfx_dim'):
            dim = self.etr_vfx_dim
            self.etr_vfx_win.geometry(f"{dim}x{dim}+{int(self.x + self.size_w/2 - dim/2)}+{int(self.y + self.size_h/2 - dim/2)}")
            
        self.schedule_loop(50, self.physics_loop)
        
    def setup_etr_vfx_layer(self):
        self.etr_particles = []
        # Pre-allocates a static dimension multiplier to prevent geometry adjustments from squishing the particle canvas
        self.etr_vfx_dim = int(max(self.size_w, self.size_h) * 2.5) + 200
        
        self.etr_vfx_win = tk.Toplevel(self.window.master)
        self.etr_vfx_win.title("VFX_Eternatus_Energy")
        self.etr_vfx_win.overrideredirect(True)
        self.etr_vfx_win.attributes('-topmost', True)
        
        TRANS = '#010101'
        self.etr_vfx_win.config(bg=TRANS)
        try: self.etr_vfx_win.wm_attributes('-transparentcolor', TRANS)
        except: pass
        
        dim = self.etr_vfx_dim
        self.etr_vfx_win.geometry(f"{dim}x{dim}+{int(self.x + self.size_w/2 - dim/2)}+{int(self.y + self.size_h/2 - dim/2)}")
        self.etr_vfx_canvas = tk.Canvas(self.etr_vfx_win, width=dim, height=dim, bg=TRANS, highlightthickness=0)
        self.etr_vfx_canvas.pack()

    def spawn_etr_absorption_particle(self):
        if not hasattr(self, 'etr_vfx_canvas') or not self.etr_vfx_canvas: return
        dim = self.etr_vfx_dim
        cx, cy = dim // 2, dim // 2
        
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(100, 160)
        px = cx + math.cos(angle) * dist
        py = cy + math.sin(angle) * dist
        
        color = random.choice(["#E74C3C", "#9B59B6", "#FF00FF", "#8E44AD"])
        size = random.choice([2, 3, 4])
        
        pid = self.etr_vfx_canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color)
        
        speed = random.uniform(5.0, 8.0)
        vx = -math.cos(angle) * speed
        vy = -math.sin(angle) * speed
        
        self.etr_particles.append({'id': pid, 'x': px, 'y': py, 'vx': vx, 'vy': vy, 'life': 20})

    def process_etr_particles(self):
        if not hasattr(self, 'etr_vfx_canvas') or not self.etr_vfx_canvas: return
        
        alive = []
        for p in self.etr_particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1
            
            if p['life'] > 0:
                self.etr_vfx_canvas.coords(p['id'], p['x']-2, p['y']-2, p['x']+2, p['y']+2)
                alive.append(p)
            else:
                self.etr_vfx_canvas.delete(p['id'])
                
        self.etr_particles = alive

    def spawn_eternabeam_window(self):
        self.etr_beam_win = tk.Toplevel(self.window.master)
        self.etr_beam_win.title("VFX_Eternatus_Beam")
        self.etr_beam_win.overrideredirect(True)
        self.etr_beam_win.attributes('-topmost', True)
        self.etr_beam_win.attributes('-alpha', 0.20)
        
        TRANS_COLOR = '#010101'
        self.etr_beam_win.config(bg=TRANS_COLOR)
        try: self.etr_beam_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass

        self.etr_beam_win.geometry(f"{self.etr_beam_width}x1+{self.etr_beam_x}+{self.v_y}")
        
        # Forces Tkinter to map the geometry to the OS environment synchronously before modifying flags.
        # Otherwise, ctypes alters a phantom handler that gets overridden during the next render tick.
        self.etr_beam_win.update()
        
        try:
            hwnd = ctypes.windll.user32.GetParent(self.etr_beam_win.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            
            # Merges WS_EX_LAYERED (0x00080000) and WS_EX_TRANSPARENT (0x00000020) explicitly 
            # to guarantee OS-level hit-test bypass for mouse events.
            # Adds WS_EX_TOPMOST (0x00000008) directly into the API to fortify the Z-Index natively.
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x00080000 | 0x00000020 | 0x00000008)
        except: pass

        self.etr_beam_canvas = tk.Canvas(self.etr_beam_win, width=self.etr_beam_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
        self.etr_beam_canvas.pack()
        
        self.etr_beam_canvas.create_rectangle(0, 0, self.etr_beam_width, self.v_height, fill="#FF1493", outline="")
        
        for _ in range(15):
            lx = random.randint(0, self.etr_beam_width)
            ly = random.randint(-self.v_height, self.v_height)
            length = random.randint(40, 150)
            self.etr_beam_canvas.create_line(lx, ly, lx, ly+length, fill="#FFFFFF", width=5, tags="etr_lines")

    # -------------------------------------------------------------------------
    # DYNAMAX INJECTION ENGINE 
    # -------------------------------------------------------------------------
    def inject_dynamax_lifecycle(self, target):
        target.is_dynamaxed = True
        target.base_size_w = target.size_w
        target.base_size_h = target.size_h
        target.dyna_clouds_front = []
        target.dyna_clouds_back = []
        target.dyna_particles = []
        
        target.dyna_dim = int(max(target.size_w, target.size_h) * 4)
        TRANS = '#010101'
        
        # Dual-layer architecture: Orchestrates Z-indexing by segregating front and back rendering calls into isolated TopLevel windows
        target.dyna_vfx_back = tk.Toplevel(target.window.master)
        target.dyna_vfx_back.title("VFX_Dynamax_Back")
        target.dyna_vfx_back.overrideredirect(True)
        target.dyna_vfx_back.attributes('-topmost', True)
        target.dyna_vfx_back.config(bg=TRANS)
        try: target.dyna_vfx_back.wm_attributes('-transparentcolor', TRANS)
        except: pass
        
        target.dyna_canvas_back = tk.Canvas(target.dyna_vfx_back, width=target.dyna_dim, height=target.dyna_dim, bg=TRANS, highlightthickness=0)
        target.dyna_canvas_back.pack()

        target.dyna_vfx_front = tk.Toplevel(target.window.master)
        target.dyna_vfx_front.title("VFX_Dynamax_Front")
        target.dyna_vfx_front.overrideredirect(True)
        target.dyna_vfx_front.attributes('-topmost', True)
        target.dyna_vfx_front.config(bg=TRANS)
        try: target.dyna_vfx_front.wm_attributes('-transparentcolor', TRANS)
        except: pass
        
        target.dyna_canvas_front = tk.Canvas(target.dyna_vfx_front, width=target.dyna_dim, height=target.dyna_dim, bg=TRANS, highlightthickness=0)
        target.dyna_canvas_front.pack()

        target.dyna_vfx_back.lower(target.window)
        target.dyna_vfx_front.lift(target.window)
        
        target.last_dyna_geo = ""
        
        self._hijack_fsm(target)
        self.dyna_fase_absorb(target, 60)

    def _sync_dyna_windows(self, target):
        geo = f"{target.dyna_dim}x{target.dyna_dim}+{int(target.x + target.size_w/2 - target.dyna_dim/2)}+{int(target.y + target.size_h/2 - target.dyna_dim/2)}"
        if getattr(target, 'last_dyna_geo', '') != geo:
            if hasattr(target, 'dyna_vfx_front') and target.dyna_vfx_front.winfo_exists():
                target.dyna_vfx_front.geometry(geo)
            if hasattr(target, 'dyna_vfx_back') and target.dyna_vfx_back.winfo_exists():
                target.dyna_vfx_back.geometry(geo)
            target.last_dyna_geo = geo

    def _cleanup_dyna_windows(self, target):
        if hasattr(target, 'dyna_vfx_front') and target.dyna_vfx_front:
            try: target.dyna_vfx_front.destroy()
            except: pass
            target.dyna_vfx_front = None
        if hasattr(target, 'dyna_vfx_back') and target.dyna_vfx_back:
            try: target.dyna_vfx_back.destroy()
            except: pass
            target.dyna_vfx_back = None

    def _hijack_fsm(self, target):
        # State Machine Hijack: Disables movement autonomy to enforce a clean 'idle' animation.
        # Physics handlers ('falling', 'thrown') and mouse events ('dragged') remain structurally operational.
        if hasattr(target, 'fsm') and hasattr(target, '_fsm_wait'):
            target.fsm['idle'] = target._fsm_wait
            target.fsm['walking'] = target._fsm_wait
        if target.current_state in ['idle', 'walking']:
            target.current_state = 'idle'
            target.v_x_velocity = 0.0

    def _restore_fsm(self, target):
        # State Machine Release: Restores standard routing logic and native pet.py AI RNG
        if hasattr(target, 'fsm') and hasattr(target, '_fsm_active'):
            target.fsm['idle'] = target._fsm_active
            target.fsm['walking'] = target._fsm_active

    def dyna_fase_absorb(self, target, time_left):
        if not target.window.winfo_exists() or getattr(target, 'current_state', '') == 'exiting':
            self._cleanup_dyna_windows(target)
            self._restore_fsm(target)
            return
        
        if time_left <= 0:
            target.dyna_canvas_front.delete("absorb")
            self.dyna_fase_grow(target, 100, 1.0)
            return

        self._sync_dyna_windows(target)
        cx, cy = target.dyna_dim / 2, target.dyna_dim / 2
        
        if time_left > 10: 
            for _ in range(3):
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(80, 160)
                px = cx + math.cos(angle) * dist
                py = cy + math.sin(angle) * dist
                color = random.choice(["#E74C3C", "#FF00FF", "#C0392B"])
                
                pid = target.dyna_canvas_front.create_rectangle(px-3, py-3, px+3, py+3, fill=color, outline=color, tags="absorb")
                
                speed = random.uniform(10.0, 18.0)
                vx = -math.cos(angle) * speed
                vy = -math.sin(angle) * speed
                target.dyna_particles.append({'id': pid, 'x': px, 'y': py, 'vx': vx, 'vy': vy})

        alive = []
        for p in target.dyna_particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            dist = math.hypot(p['x'] - cx, p['y'] - cy)
            if dist > 15:
                target.dyna_canvas_front.coords(p['id'], p['x']-3, p['y']-3, p['x']+3, p['y']+3)
                alive.append(p)
            else:
                target.dyna_canvas_front.delete(p['id'])
        target.dyna_particles = alive

        target.window.after(50, lambda: self.dyna_fase_absorb(target, time_left - 1))

    def dyna_fase_grow(self, target, steps_left, current_scale):
        if not target.window.winfo_exists() or getattr(target, 'current_state', '') == 'exiting':
            self._cleanup_dyna_windows(target)
            self._restore_fsm(target)
            return
            
        if steps_left <= 0:
            for _ in range(3):
                cid_front = target.dyna_canvas_front.create_rectangle(0, 0, 45, 18, fill="#E74C3C", outline="#C0392B", width=2)
                cid_back = target.dyna_canvas_back.create_rectangle(0, 0, 45, 18, fill="#E74C3C", outline="#C0392B", width=2)
                target.dyna_clouds_front.append(cid_front)
                target.dyna_clouds_back.append(cid_back)
                
            target.heavy_fall = True
            target.push_force_mult = 3.0
            
            # Autonomy unlock: Restores walking behavior matrix once the entity hits Dynamax limit
            self._restore_fsm(target)
            self.dyna_fase_active(target, 600, 0.0) 
            return

        if steps_left % 2 == 0:
            current_scale += 0.04
            target.necrozma_scale_mod = current_scale

        target.default_floor_y = (target.v_y + target.v_height) - target.size_h - getattr(target, 'offset_y', 0)
        if getattr(target, 'is_flying', False):
            target.target_floor_y = (target.v_y + target.v_height) - target.size_h - getattr(target, 'target_offset_y', 0)
            target.floor_y = target.target_floor_y
        else:
            target.floor_y = target.default_floor_y
            
        if target.y > target.floor_y:
            target.y = target.floor_y

        self._sync_dyna_windows(target)
        target.window.after(50, lambda: self.dyna_fase_grow(target, steps_left - 1, current_scale))

    def dyna_fase_active(self, target, time_left, theta):
        if not target.window.winfo_exists() or getattr(target, 'current_state', '') == 'exiting':
            self._cleanup_dyna_windows(target)
            self._restore_fsm(target)
            return
            
        if time_left <= 0:
            target.dyna_canvas_front.delete("all")
            target.dyna_canvas_back.delete("all")
            target.dyna_clouds_front.clear()
            target.dyna_clouds_back.clear()
            
            # Autonomy lock: Hijacks the FSM to ensure safe idle processing during structural scale decay
            self._hijack_fsm(target)
            self.dyna_fase_shrink(target, 100, target.necrozma_scale_mod)
            return

        self._sync_dyna_windows(target)
        theta += 0.15
        cx = target.dyna_dim / 2
        cy = target.dyna_dim / 2 - target.size_h * 0.45
        rx = target.size_w * 0.55
        ry = target.size_h * 0.12
        
        for i in range(3):
            angle = theta + i * (2 * math.pi / 3)
            px = cx + rx * math.cos(angle)
            py = cy - ry * math.sin(angle)
            
            cf = target.dyna_clouds_front[i]
            cb = target.dyna_clouds_back[i]
            
            target.dyna_canvas_front.coords(cf, px-22, py-9, px+22, py+9)
            target.dyna_canvas_back.coords(cb, px-22, py-9, px+22, py+9)
            
            if math.sin(angle) > 0:
                target.dyna_canvas_front.itemconfig(cf, state='hidden')
                target.dyna_canvas_back.itemconfig(cb, state='normal')
            else:
                target.dyna_canvas_front.itemconfig(cf, state='normal')
                target.dyna_canvas_back.itemconfig(cb, state='hidden')

        target.window.after(50, lambda: self.dyna_fase_active(target, time_left - 1, theta))

    def dyna_fase_shrink(self, target, steps_left, current_scale):
        if not target.window.winfo_exists() or getattr(target, 'current_state', '') == 'exiting':
            self._cleanup_dyna_windows(target)
            self._restore_fsm(target)
            return
        
        if steps_left <= 0:
            self._cleanup_dyna_windows(target)
            self._restore_fsm(target)
            
            target.is_dynamaxed = False
            target.heavy_fall = target.config.get("physics", {}).get("heavy_fall", False)
            target.push_force_mult = 1.0
            target.necrozma_scale_mod = 1.0
            
            self.spawn_dynamax_explosion(target)
            return

        if steps_left % 2 == 0:
            current_scale -= 0.04
            target.necrozma_scale_mod = max(1.0, current_scale)
        
        target.default_floor_y = (target.v_y + target.v_height) - target.size_h - getattr(target, 'offset_y', 0)
        if getattr(target, 'is_flying', False):
            target.target_floor_y = (target.v_y + target.v_height) - target.size_h - getattr(target, 'target_offset_y', 0)
            target.floor_y = target.target_floor_y
        else:
            target.floor_y = target.default_floor_y
            
        if target.y > target.floor_y:
            target.y = target.floor_y
        
        self._sync_dyna_windows(target)
        target.window.after(50, lambda: self.dyna_fase_shrink(target, steps_left - 1, current_scale))

    def spawn_dynamax_explosion(self, target):
        exp_win = tk.Toplevel(target.window.master)
        exp_win.title("VFX_Dynamax_Explosion")
        exp_win.overrideredirect(True)
        exp_win.attributes('-topmost', True)
        
        TRANS = '#010101'
        exp_win.config(bg=TRANS)
        try: exp_win.wm_attributes('-transparentcolor', TRANS)
        except: pass
        
        dim = int(max(target.size_w, target.size_h) * 2.5)
        exp_win.geometry(f"{dim}x{dim}+{int(target.x + target.size_w/2 - dim/2)}+{int(target.y + target.size_h/2 - dim/2)}")
        exp_cv = tk.Canvas(exp_win, width=dim, height=dim, bg=TRANS, highlightthickness=0)
        exp_cv.pack()
        
        particles = []
        cx, cy = dim // 2, dim // 2
        for _ in range(50):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(15.0, 35.0) 
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = random.choice(["#E74C3C", "#FF00FF", "#C0392B", "#9B59B6"])
            size = random.choice([3, 4, 5])
            
            pid = exp_cv.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline=color)
            particles.append({'id': pid, 'x': cx, 'y': cy, 'vx': vx, 'vy': vy, 'life': 25})
            
        self.animate_dynamax_explosion(exp_win, exp_cv, particles)

    def animate_dynamax_explosion(self, win, cv, particles):
        if not win.winfo_exists(): return
        
        alive = []
        for p in particles:
            if p['life'] > 0:
                p['x'] += p['vx']
                p['y'] += p['vy']
                
                p['vx'] *= 0.85
                p['vy'] *= 0.85
                p['life'] -= 1
                
                cv.coords(p['id'], p['x']-3, p['y']-3, p['x']+3, p['y']+3)
                alive.append(p)
            else:
                cv.delete(p['id'])
                
        if alive:
            win.after(30, lambda: self.animate_dynamax_explosion(win, cv, alive))
        else:
            win.destroy()