import random
import math
import tkinter as tk

class YveltalMechanics:
    def cancel_yveltal_arts(self):
        if hasattr(self, 'yveltal_win') and self.yveltal_win and self.yveltal_win.winfo_exists():
            self.yveltal_win.destroy()
            self.yveltal_win = None

        self.canvas.delete("yveltal_lightning")
        
        for attr in ['yveltal_phase', 'yveltal_timer', 'yveltal_channel_timer', 'yveltal_beam_step', 'yveltal_exploded', 'yveltal_energy_lines']:
            if hasattr(self, attr): delattr(self, attr)

        if self.current_state not in ['dragged', 'exiting']:
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0
            
            # Flying entities must transition into 'ascending' and bind their hover anchor to their current Y coordinate.
            # Defaulting to 'falling' forces the physics engine to apply gravity until the screen bottom is reached.
            if getattr(self, 'is_flying', False):
                self.floor_y = self.y
                self.current_state = 'ascending'
            else:
                self.current_state = 'falling'

    def _fsm_yveltal_channeling(self):
        if not hasattr(self, 'yveltal_phase'):
            self.yveltal_phase = 0
            self.yveltal_exploded = False
            
            sky_limit_y = self.v_y + (self.v_height // 8)
            self.yveltal_target_y = random.randint(self.v_y, sky_limit_y)
            self.yveltal_target_x = random.randint(self.v_x + 100, self.v_x + self.v_width - 100 - self.size_w)
            
        if self.yveltal_phase == 0:
            dx = self.yveltal_target_x - self.x
            dy = self.yveltal_target_y - self.y
            dist = math.hypot(dx, dy)
            
            self.is_facing_right = (dx > 0)
            
            if dist > 15:
                speed = 20.0
                self.x += (dx / dist) * speed
                self.y += (dy / dist) * speed
            else:
                self.yveltal_phase = 1
                self.yveltal_channel_timer = 100 
                
        elif self.yveltal_phase == 1:
            self.yveltal_channel_timer -= 1
            
            if self.yveltal_channel_timer % 3 == 0:
                px = self.size_w // 2
                py = (self.size_h // 2) + 25
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(80, 200)
                end_x = px + math.cos(angle) * dist
                end_y = py + math.sin(angle) * dist
                
                pts = []
                curr_x, curr_y = end_x, end_y
                steps = 4
                for i in range(steps):
                    pts.extend([curr_x, curr_y])
                    frac = (i + 1) / steps
                    cx = end_x + (px - end_x) * frac
                    cy = end_y + (py - end_y) * frac
                    curr_x = cx + random.randint(-15, 15)
                    curr_y = cy + random.randint(-15, 15)
                pts.extend([px, py])
                
                color = random.choice(["#3B1348", "#8B0000", "#FF0000", "#000000"])
                pid = self.canvas.create_line(*pts, fill=color, width=random.randint(2, 4), tags="yveltal_lightning")
                self.window.after(100, lambda p=pid: self.canvas.delete(p))
                
            if self.yveltal_channel_timer <= 0:
                self.yveltal_phase = 2
                self.yveltal_beam_step = 0
                self.yveltal_timer = 100 
                
                t = self.get_random_valid_target()
                if t:
                    self.beam_target_x = t.x + t.size_w // 2
                else:
                    self.beam_target_x = random.randint(self.v_x, self.v_x + self.v_width)
                self.beam_target_y = self.v_y + self.v_height + 150 
                
                self.is_facing_right = (self.beam_target_x > self.x)
                self.spawn_yveltal_beam_vfx()
                
        elif self.yveltal_phase == 2:
            self.yveltal_timer -= 1
            self.yveltal_beam_step += 1
            
            self.yveltal_apply_oblivion_hitbox()
            
            if self.yveltal_beam_step == 8 and not getattr(self, 'yveltal_exploded', False):
                self.yveltal_explode()
                self.yveltal_exploded = True
            
            if self.yveltal_timer <= 0:
                self.yveltal_phase = 3
                self.yveltal_timer = 10 
                
        elif self.yveltal_phase == 3:
            self.yveltal_timer -= 1
            if self.yveltal_timer <= 0:
                self.cancel_yveltal_arts()
                self.yveltal_cooldown = 72000 

        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def spawn_yveltal_beam_vfx(self):
        self.yveltal_win = tk.Toplevel(self.window.master)
        self.yveltal_win.title("VFX_Yveltal_Ignore")
        self.yveltal_win.overrideredirect(True)
        self.yveltal_win.attributes('-topmost', True)
        
        TRANS_COLOR = '#010101'
        self.yveltal_win.config(bg=TRANS_COLOR)
        try: self.yveltal_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass

        self.yveltal_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        self.yveltal_canvas = tk.Canvas(self.yveltal_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
        self.yveltal_canvas.pack()
        
        self.yveltal_beam_loop()

    def yveltal_beam_loop(self):
        if getattr(self, 'current_state', '') != 'yveltal_channeling': return
        if not hasattr(self, 'yveltal_win') or not self.yveltal_win or not self.yveltal_win.winfo_exists(): return

        self.yveltal_canvas.delete("vfx_y_beam")
        
        offset_x = (self.size_w * 0.8) if getattr(self, 'is_facing_right', True) else (self.size_w * 0.2)
        start_x = (self.x + offset_x) - self.v_x
        start_y = (self.y + self.size_h * 0.85) - self.v_y
        
        end_x = self.beam_target_x - self.v_x
        end_y = self.beam_target_y - self.v_y
        
        progress = min(1.0, getattr(self, 'yveltal_beam_step', 0) / 8.0)
        
        current_x = start_x + (end_x - start_x) * progress
        current_y = start_y + (end_y - start_y) * progress
        
        if progress > 0.01:
            # The outer shell width is reduced to 104 to provide a tight 12px dark border around the 80px core.
            self.yveltal_canvas.create_line(start_x, start_y, current_x, current_y, fill="#1A0000", width=104, capstyle=tk.ROUND, tags="vfx_y_beam")
            self.yveltal_canvas.create_line(start_x, start_y, current_x, current_y, fill="#E60000", width=80, capstyle=tk.ROUND, tags="vfx_y_beam")
            self.yveltal_canvas.create_line(start_x, start_y, current_x, current_y, fill="#FF4D79", width=32, capstyle=tk.ROUND, tags="vfx_y_beam")

            if not hasattr(self, 'yveltal_energy_lines'):
                self.yveltal_energy_lines = []
                
            if random.randint(1, 100) <= 60:
                self.yveltal_energy_lines.append({
                    'progress': 0.0,
                    'speed': random.uniform(0.04, 0.12),
                    'length': random.uniform(0.05, 0.15),
                    'offset_x': random.uniform(-25, 25),
                    'offset_y': random.uniform(-25, 25)
                })

            alive_lines = []
            for line in self.yveltal_energy_lines:
                line['progress'] += line['speed']
                
                # Constrain the kinetic energy flow so it never surpasses the main beam's current rendering progress
                if line['progress'] <= progress:
                    p_start = max(0.0, line['progress'] - line['length'])
                    p_end = line['progress']
                    
                    lx1 = start_x + (end_x - start_x) * p_start + line['offset_x']
                    ly1 = start_y + (end_y - start_y) * p_start + line['offset_y']
                    lx2 = start_x + (end_x - start_x) * p_end + line['offset_x']
                    ly2 = start_y + (end_y - start_y) * p_end + line['offset_y']
                    
                    color = random.choice(["#FFFFFF", "#FFB3C6", "#FFD9E2"])
                    self.yveltal_canvas.create_line(lx1, ly1, lx2, ly2, fill=color, width=4, capstyle=tk.ROUND, tags="vfx_y_beam")
                    alive_lines.append(line)
            self.yveltal_energy_lines = alive_lines

        self.window.after(30, self.yveltal_beam_loop)

    def yveltal_apply_oblivion_hitbox(self):
        if not getattr(self, 'get_all_pets', None): return
        
        offset_x = (self.size_w * 0.8) if getattr(self, 'is_facing_right', True) else (self.size_w * 0.2)
        start_x = self.x + offset_x
        start_y = self.y + self.size_h * 0.85
        
        end_x = self.beam_target_x
        end_y = self.beam_target_y
        
        progress = min(1.0, getattr(self, 'yveltal_beam_step', 0) / 8.0)
        current_end_x = start_x + (end_x - start_x) * progress
        current_end_y = start_y + (end_y - start_y) * progress
        
        for target in self.get_all_pets():
            if target != self and target.current_state != 'exiting' and target.current_state != 'yveltal_petrified' and not getattr(target, 'is_egg', False):
                target_cx = target.x + target.size_w / 2
                target_cy = target.y + target.size_h / 2
                
                line_dx = current_end_x - start_x
                line_dy = current_end_y - start_y
                line_length_sq = line_dx**2 + line_dy**2
                
                if line_length_sq == 0:
                    dist = math.hypot(target_cx - start_x, target_cy - start_y)
                else:
                    t = max(0, min(1, ((target_cx - start_x) * line_dx + (target_cy - start_y) * line_dy) / line_length_sq))
                    proj_x = start_x + t * line_dx
                    proj_y = start_y + t * line_dy
                    dist = math.hypot(target_cx - proj_x, target_cy - proj_y)
                    
                if dist < 160:
                    self.apply_petrification(target)

    def yveltal_explode(self):
        impact_radius = 600 
        
        if hasattr(self, 'yveltal_canvas'):
            cx = self.beam_target_x - self.v_x
            cy = self.v_height 
            
            exp_state = {'radius': 100.0, 'width': 60.0}
            
            def animate_yveltal_shockwave():
                if not hasattr(self, 'yveltal_canvas') or getattr(self, 'current_state', '') != 'yveltal_channeling': return
                try:
                    self.yveltal_canvas.delete("vfx_y_exp")
                    exp_state['radius'] += 150.0
                    exp_state['width'] *= 0.6 
                    
                    if exp_state['radius'] >= impact_radius or exp_state['width'] < 1.0:
                        return 
                        
                    r = exp_state['radius']
                    w = int(exp_state['width'])
                    self._draw_pixel_circle_bbox(self.yveltal_canvas, cx-r, cy-r, cx+r, cy+r, outline="#1A0000", width=w, tags="vfx_y_exp")
                    self._draw_pixel_circle_bbox(self.yveltal_canvas, cx-r*0.9, cy-r*0.9, cx+r*0.9, cy+r*0.9, outline="#E60000", width=max(1, w//2), tags="vfx_y_exp")
                    
                    self.window.after(30, animate_yveltal_shockwave)
                except:
                    pass
                
            animate_yveltal_shockwave()

        if getattr(self, 'get_all_pets', None):
            for target in self.get_all_pets():
                if target != self and target.current_state != 'exiting' and target.current_state != 'yveltal_petrified' and not getattr(target, 'is_egg', False):
                    dist = math.hypot(self.beam_target_x - target.x, self.beam_target_y - target.y)
                    if dist <= impact_radius:
                        self.apply_petrification(target)

    def apply_petrification(self, target):
        # Cleans up active FSM states strictly to prevent overlapping timer logic when petrification ends.
        if target.current_state.startswith('dark_'): target.cancel_dark_arts()
        elif target.current_state == 'tk_channeling':
            target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
            if getattr(target, 'tk_target', None):
                t_targ = target.tk_target
                target.manage_tk_aura(t_targ.canvas, t_targ.size_w if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size, t_targ.size_h if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size, False)
                if hasattr(t_targ, 'interrupt_current_state'): t_targ.interrupt_current_state()
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
            # FIX: Properly set the cooldown to prevent the thread from misfiring right after thawing.
            target.glitch_cooldown = 12000 
            
        for prefix, cancel_func in [('mewtwo_', 'cancel_mewtwo_arts'), ('hooh_', 'cancel_hooh_arts'), ('kyogre_', 'cancel_kyogre_arts'), ('groudon_', 'cancel_groudon_arts'), ('lugia_', 'cancel_lugia_arts'), ('rayquaza_', 'cancel_rayquaza_arts'), ('dialga_', 'cancel_dialga_arts'), ('palkia_', 'cancel_palkia_arts'), ('giratina_', 'cancel_giratina_arts'), ('zekrom_', 'cancel_zekrom_arts'), ('reshiram_', 'cancel_reshiram_arts'), ('kyurem_', 'cancel_kyurem_arts'), ('xerneas_', 'cancel_xerneas_arts')]:
            if target.current_state.startswith(prefix) and hasattr(target, cancel_func): getattr(target, cancel_func)()

        # FIX: Forces alpha channel restoration. Prevents targets from turning into transparent stone if caught mid-teleport.
        target.canvas.itemconfig(target.canvas_image_id, state='normal')
        try: target.window.attributes('-alpha', 1.0)
        except: pass

        if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
        target.current_state = 'yveltal_petrified'
        target.yveltal_petrified_timer = random.randint(300, 500)
        
        target.v_x_velocity = 0.0
        target.v_y_velocity = 0.0
        
        target.yveltal_stone_vfx_loop()

    def _fsm_yveltal_petrified(self):
        self.v_x_velocity = 0.0
        self.v_y_velocity = 0.0
        
        self.yveltal_petrified_timer -= 1
        if self.yveltal_petrified_timer <= 0:
            self.canvas.delete("vfx_y_stone")
            
            self.canvas.itemconfig(self.canvas_image_id, state='normal')
            self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
            if hasattr(self, 'dark_mode'): self.dark_mode = False 
            try: self.window.attributes('-alpha', 1.0)
            except: pass
            
            if getattr(self, 'is_flying', False):
                self.floor_y = self.y
                self.current_state = 'ascending'
            else:
                self.current_state = 'falling'
                
            self.schedule_loop(50, self.physics_loop)
            return
            
        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def yveltal_stone_vfx_loop(self):
        if getattr(self, 'current_state', 'exiting') != 'yveltal_petrified': 
            self.canvas.delete("vfx_y_stone")
            return
            
        cx = self.size_w / 2
        cy = self.size_h / 2
        
        if random.randint(1, 100) <= 60:
            offset_x = random.uniform(-self.size_w * 0.4, self.size_w * 0.4)
            offset_y = random.uniform(-self.size_h * 0.4, 0)
            px = cx + offset_x
            py = cy + offset_y
            
            color = random.choice(["#000000", "#1A1A1A", "#2B2B2B"])
            pid = self.canvas.create_rectangle(px-1, py-3, px+1, py+3, fill=color, outline=color, tags="vfx_y_stone")
            
            if not hasattr(self, 'yveltal_particles'):
                self.yveltal_particles = []
            self.yveltal_particles.append({'id': pid, 'vy': random.uniform(1.0, 2.5), 'life': 20})
            
        if hasattr(self, 'yveltal_particles'):
            alive = []
            for p in self.yveltal_particles:
                if p['life'] > 0:
                    self.canvas.move(p['id'], 0, p['vy']) 
                    p['life'] -= 1
                    alive.append(p)
                else:
                    self.canvas.delete(p['id'])
            self.yveltal_particles = alive
            
        self.window.after(50, self.yveltal_stone_vfx_loop)