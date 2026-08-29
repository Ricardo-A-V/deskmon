import random
import math
import tkinter as tk

class MelmetalMechanics:
    def cancel_melmetal_arts(self):
        # Cancel if interrupted
        for attr in ['mel_phase', 'mel_timer', 'mel_target', 'mel_particles', 'mel_tossed', 'mel_original_scale']:
            if hasattr(self, attr):
                delattr(self, attr)
                
        if hasattr(self, 'mel_vfx_win') and self.mel_vfx_win:
            try:
                if hasattr(self, 'mel_canvas') and self.mel_canvas:
                    self.mel_canvas.delete("all")
                    self.mel_canvas.destroy()
                self.mel_vfx_win.destroy()
            except: pass
            self.mel_vfx_win = None
            self.mel_canvas = None

        if self.current_state not in ['dragged', 'exiting']:
            self.current_state = 'falling'
            
        self.scale_mod = 1.0
        if hasattr(self, 'animator'):
            self.animator.current_frame_index = 0

    def _fsm_melmetal_channeling(self):
        if not hasattr(self, 'mel_particles'):
            if not hasattr(self, 'mel_phase'):
                self.mel_phase = 'absorbing'
                self.mel_timer = 150
            self.mel_original_scale = getattr(self, 'scale_mod', 1.0)
            self.mel_particles = []
            
        if self.mel_phase == 'jumping_down':
            vel_y = getattr(self, 'v_y_velocity', 0)
            self.y += vel_y
            self.v_y_velocity = vel_y + 1.2 # Gravity

            if self.y >= self.default_floor_y:
                self.y = self.default_floor_y
                self.v_y_velocity = 0
                if hasattr(self, 'trigger_landing_shake'):
                    self.trigger_landing_shake()
                self.mel_phase = 'absorbing'
                self.mel_timer = 150
            
        elif self.mel_phase == 'absorbing':
            self.mel_timer -= 1
            
            # Growth from original to 1.5x
            progress = 1.0 - (max(0, self.mel_timer) / 150.0)
            self.scale_mod = self.mel_original_scale * (1.0 + progress * 0.5)
            
            # Create molten metal absorbing particles around Melmetal
            if self.mel_timer % 3 == 0:
                if not hasattr(self, 'mel_vfx_win') or not self.mel_vfx_win or not self.mel_vfx_win.winfo_exists():
                    self.mel_vfx_win = tk.Toplevel(self.window.master)
                    self.mel_vfx_win.title("VFX_Melmetal_Ignore")
                    self.mel_vfx_win.overrideredirect(True)
                    self.mel_vfx_win.attributes('-topmost', True)
                    TRANS_COLOR = '#010101'
                    self.mel_vfx_win.config(bg=TRANS_COLOR)
                    try: self.mel_vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
                    except: pass
                    self.mel_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
                    self.mel_canvas = tk.Canvas(self.mel_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0, bd=0)
                    self.mel_canvas.pack()

                cx = self.x + self.size_w / 2 - self.v_x
                cy = self.y + self.size_h / 2 - self.v_y
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(80, 180)
                px = cx + math.cos(angle) * dist
                py = cy + math.sin(angle) * dist
                color = random.choice(["#B0BEC5", "#90A4AE", "#78909C", "#607D8B", "#CFD8DC"])
                size = random.choice([2, 4, 6])
                pid = self.mel_canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color, tags="mel_absorb")
                self.mel_particles.append({'id': pid, 'x': px, 'y': py, 'cx': cx, 'cy': cy})
                
            if hasattr(self, 'mel_canvas') and self.mel_canvas:
                alive = []
                for p in self.mel_particles:
                    p['cx'] = self.x + self.size_w / 2 - self.v_x
                    p['cy'] = self.y + self.size_h / 2 - self.v_y
                    dx = p['cx'] - p['x']
                    dy = p['cy'] - p['y']
                    d = math.sqrt(dx**2 + dy**2)
                    if d > 15.0:
                        speed = 8.0 + (150 - self.mel_timer) * 0.1
                        move_x = (dx/d) * speed
                        move_y = (dy/d) * speed
                        self.mel_canvas.move(p['id'], move_x, move_y)
                        p['x'] += move_x
                        p['y'] += move_y
                        alive.append(p)
                    else:
                        self.mel_canvas.delete(p['id'])
                self.mel_particles = alive

            if self.mel_timer <= 0:
                if hasattr(self, 'mel_vfx_win') and self.mel_vfx_win:
                    self.mel_vfx_win.destroy()
                    self.mel_vfx_win = None
                
                # Pick a random target at reach (floor level)
                self.mel_target = None
                if getattr(self, 'get_all_pets', None):
                    valid_targets = []
                    for p in self.get_all_pets():
                        if p != self and p.current_state not in ['exiting', 'dragged', 'falling_pokeball'] and not getattr(p, 'is_egg', False):
                            if abs(p.y + p.size_h - (self.y + self.size_h)) < 150: # roughly same floor
                                valid_targets.append(p)
                    if valid_targets:
                        self.mel_target = random.choice(valid_targets)

                if self.mel_target:
                    self.mel_phase = 'running'
                    self.mel_tossed = []
                else:
                    self.current_state = 'idle'
                    self.scale_mod = self.mel_original_scale
                    self.cancel_melmetal_arts()
                    
        elif self.mel_phase == 'running':
            if not self.mel_target or self.mel_target.current_state == 'exiting':
                self.mel_phase = 'shrinking'
                self.mel_timer = 90
                self.update_position()
                self.schedule_loop(30, self.physics_loop)
                return

            # Move towards target
            cx = self.x + self.size_w / 2
            tcx = self.mel_target.x + self.mel_target.size_w / 2
            speed = self.speed * 4 # fast running
            
            if cx < tcx - 10:
                self.x += speed
                self.is_facing_right = True
            elif cx > tcx + 10:
                self.x -= speed
                self.is_facing_right = False
            else:
                # Reached target
                self.trigger_melmetal_explosion(tcx, self.mel_target.y + self.mel_target.size_h / 2)
                self.mel_target.v_x_velocity = random.uniform(-20, 20)
                self.mel_target.v_y_velocity = random.uniform(-40, -60)
                if hasattr(self.mel_target, 'interrupt_current_state'): self.mel_target.interrupt_current_state()
                self.mel_target.current_state = 'thrown'
                self.mel_target.y -= 10
                self.mel_phase = 'shrinking'
                self.mel_timer = 90
                self.update_position()
                self.schedule_loop(30, self.physics_loop)
                return

            # Check collision with other pokemon
            if getattr(self, 'get_all_pets', None):
                for p in self.get_all_pets():
                    if p != self and p not in getattr(self, 'mel_tossed', []) and p.current_state not in ['exiting', 'dragged']:
                        if not getattr(p, 'is_egg', False):
                            pcx = p.x + p.size_w / 2
                            pcy = p.y + p.size_h / 2
                            mcx = self.x + self.size_w / 2
                            mcy = self.y + self.size_h / 2
                            if abs(pcx - mcx) < self.size_w / 2 + p.size_w / 2 and abs(pcy - mcy) < self.size_h / 2 + p.size_h / 2:
                                self.mel_tossed.append(p)
                                self.trigger_melmetal_explosion(pcx, pcy)
                                p.v_x_velocity = (pcx - mcx) / 1.5 + random.uniform(-10, 10)
                                p.v_y_velocity = random.uniform(-40, -60)
                                if hasattr(p, 'interrupt_current_state'): p.interrupt_current_state()
                                p.current_state = 'thrown'
                                p.y -= 10
                                if p == self.mel_target:
                                    self.mel_phase = 'shrinking'
                                    self.mel_timer = 90
                                    self.update_position()
                                    self.schedule_loop(30, self.physics_loop)
                                    return

        elif self.mel_phase == 'shrinking':
            self.mel_timer -= 1
            
            # Shrink from 1.5x back to original
            progress = max(0, self.mel_timer) / 90.0
            self.scale_mod = self.mel_original_scale * (1.0 + progress * 0.5)
            
            if self.mel_timer % 4 == 0:
                if not hasattr(self, 'mel_vfx_win') or not self.mel_vfx_win or not self.mel_vfx_win.winfo_exists():
                    self.mel_vfx_win = tk.Toplevel(self.window.master)
                    self.mel_vfx_win.title("VFX_Melmetal_Ignore")
                    self.mel_vfx_win.overrideredirect(True)
                    self.mel_vfx_win.attributes('-topmost', True)
                    TRANS_COLOR = '#010101'
                    self.mel_vfx_win.config(bg=TRANS_COLOR)
                    try: self.mel_vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
                    except: pass
                    self.mel_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
                    self.mel_canvas = tk.Canvas(self.mel_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0, bd=0)
                    self.mel_canvas.pack()
                    
                cx = self.x + self.size_w / 2 - self.v_x
                cy = self.y + self.size_h / 2 - self.v_y
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(20, 80)
                px = cx + math.cos(angle) * dist
                py = cy + math.sin(angle) * dist
                color = random.choice(["#B0BEC5", "#90A4AE", "#78909C", "#607D8B", "#CFD8DC"])
                size = random.choice([2, 4, 6])
                pid = self.mel_canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color, tags="mel_shed")
                self.mel_particles.append({'id': pid, 'x': px, 'y': py, 'vx': math.cos(angle) * random.uniform(2, 5), 'vy': random.uniform(2, 6)})
                
            if hasattr(self, 'mel_canvas') and self.mel_canvas:
                alive = []
                for p in self.mel_particles:
                    if 'vx' in p: # Only process shedding particles this way
                        p['x'] += p['vx']
                        p['y'] += p['vy']
                        self.mel_canvas.move(p['id'], p['vx'], p['vy'])
                        if p['y'] < self.v_height:
                            alive.append(p)
                        else:
                            self.mel_canvas.delete(p['id'])
                # Only keep shedding particles, since absorbing ones might have no 'vx'
                self.mel_particles = [p for p in alive if 'vx' in p] + [p for p in self.mel_particles if 'vx' not in p]

            if self.mel_timer <= 0:
                self.scale_mod = getattr(self, 'mel_original_scale', 1.0)
                self.cancel_melmetal_arts()
                self.current_state = 'idle'
                self.update_position()
                self.schedule_loop(30, self.physics_loop)
                return

        self.update_position()
        self.schedule_loop(30, self.physics_loop)
        
    def trigger_melmetal_explosion(self, cx, cy):
        exp_win = tk.Toplevel(self.window.master)
        exp_win.title("VFX_MelmetalExp_Ignore")
        exp_win.overrideredirect(True)
        exp_win.attributes('-topmost', True)
        TRANS_COLOR = '#010101'
        exp_win.config(bg=TRANS_COLOR)
        try: exp_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass
        
        size = 150
        exp_win.geometry(f"{size}x{size}+{int(cx-size/2)}+{int(cy-size/2)}")
        c = tk.Canvas(exp_win, width=size, height=size, bg=TRANS_COLOR, highlightthickness=0, bd=0)
        c.pack()
        
        particles = []
        for _ in range(12):
            particles.append({
                'x': size/2, 'y': size/2,
                'vx': random.uniform(-10, 10),
                'vy': random.uniform(-10, 10),
                'life': random.randint(10, 20),
                'color': random.choice(["#FFFFFF", "#FFD700", "#FF4500", "#A9A9A9"])
            })
            
        def anim():
            if not exp_win.winfo_exists(): return
            c.delete("exp")
            alive = []
            for p in particles:
                if p['life'] > 0:
                    p['x'] += p['vx']
                    p['y'] += p['vy']
                    psize = random.randint(2, 6)
                    c.create_rectangle(p['x']-psize, p['y']-psize, p['x']+psize, p['y']+psize, fill=p['color'], outline=p['color'], tags="exp")
                    p['life'] -= 1
                    alive.append(p)
            
            if len(alive) > 0:
                particles.clear()
                particles.extend(alive)
                exp_win.after(30, anim)
            else:
                exp_win.destroy()
                
        anim()
