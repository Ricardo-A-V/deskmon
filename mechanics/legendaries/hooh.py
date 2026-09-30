import win32api
import win32con

import random
import math
import os

import math
import random

class HoOhMechanics:
    def show_fire_vfx(self, is_master=True):
        if not hasattr(self, 'hooh_particles'): self.hooh_particles = []
        cx = self.size_w / 2
        cy = self.size_h / 2
        
        for _ in range(3 if is_master else 1):
            rx = cx + random.randint(-40, 40)
            ry = cy + random.randint(-40, 40)
            color = random.choice(["#FF4500", "#FFA500", "#FFD700", "#FFFFFF"])
            pid = self.canvas.create_rectangle(rx-4, ry-4, rx+4, ry+4, fill=color, outline="")
            self.hooh_particles.append({'id': pid, 'x': rx, 'y': ry, 'life': 15, 'color': color})
            
        alive = []
        for p in self.hooh_particles:
            p['life'] -= 1
            if p['life'] <= 0:
                self.canvas.delete(p['id'])
            else:
                p['y'] -= 5
                p['x'] += random.randint(-2, 2)
                s = 1 + (p['life'] // 4)
                self.canvas.coords(p['id'], p['x']-s, p['y']-s, p['x']+s, p['y']+s)
                alive.append(p)
        self.hooh_particles = alive

    def cancel_hooh_arts(self):
        if hasattr(self, 'hooh_particles'):
            for p in self.hooh_particles:
                try: self.canvas.delete(p['id'])
                except: pass
            self.hooh_particles = []
        if hasattr(self, 'hooh_absorb_particles'):
            for p in self.hooh_absorb_particles:
                self.canvas.delete(p['id'])
            self.hooh_absorb_particles = []
        if hasattr(self, 'hooh_trail_particles'):
            for p in self.hooh_trail_particles:
                self.canvas.delete(p['id'])
            self.hooh_trail_particles = []
            
        if self.current_state not in ['dragged', 'exiting']:
            self.current_state = 'falling'
            
        targets = getattr(self, 'hooh_targets', [])
        self.hooh_targets = []
        for target in targets:
            if target and target.window.winfo_exists():
                target.hooh_master = None
                # FIX: Only cancel victim's action if they had already started running
                if target.current_state == 'burning' and target.current_state not in ['dragged', 'exiting']:
                    if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
                    target.current_state = 'falling'
                    
        master = getattr(self, 'hooh_master', None)
        self.hooh_master = None
        if master and master.window.winfo_exists():
            master.cancel_hooh_arts()

    def _fsm_hooh_channeling(self):
        if not hasattr(self, 'hooh_target_x'):
            try:
                monitor = win32api.MonitorFromPoint((int(self.x), int(self.y)), win32con.MONITOR_DEFAULTTONEAREST)
                mon_info = win32api.GetMonitorInfo(monitor)
                mon_rect = mon_info['Monitor']
                mon_x = mon_rect[0]
                mon_w = mon_rect[2] - mon_rect[0]
            except:
                mon_x = self.v_x
                mon_w = self.v_width
            self.hooh_target_x = mon_x + (mon_w // 2) - self.size_w // 2

        target_y = self.v_y + 40 
        
        dx = self.hooh_target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if getattr(self, 'hooh_phase', 0) == 0:
            self.is_facing_right = (dx > 0)
            fly_speed = self.speed * 1.5
            
            if dist > fly_speed:
                self.x += (dx/dist) * fly_speed
                self.y += (dy/dist) * fly_speed
                
                if not hasattr(self, 'hooh_trail_timer'):
                    self.hooh_trail_timer = 0
                    self.hooh_trail_particles = []
                self.hooh_trail_timer += 1
                
                if self.hooh_trail_timer % 2 == 0:
                    colors = ["#FF0000", "#FF7F00", "#FFFF00", "#00FF00", "#00BFFF", "#4B0082", "#9400D3"]
                    for i, color in enumerate(colors):
                        offset_y = (i - 3) * 6  # Spread vertically (-18 to +18)
                        
                        start_x = self.size_w//2
                        start_y = (self.size_h//2 + 25) + offset_y
                        
                        size = 3
                        pid = self.canvas.create_rectangle(start_x-size, start_y-size, start_x+size, start_y+size, fill=color, outline=color, tags="vfx_hooh_trail")
                        
                        # Move backwards relative to flight, plus some outward spread
                        vx = -(dx/dist) * random.uniform(1.5, 2.5) + random.uniform(-0.5, 0.5)
                        vy = -(dy/dist) * random.uniform(1.5, 2.5) + (offset_y * 0.05) + random.uniform(-0.5, 0.5)
                        self.hooh_trail_particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': 25})
                    
                alive = []
                for p in self.hooh_trail_particles:
                    p['life'] -= 1
                    if p['life'] > 0:
                        self.canvas.move(p['id'], p['vx'], p['vy'])
                        alive.append(p)
                    else:
                        self.canvas.delete(p['id'])
                self.hooh_trail_particles = alive
                
            else:
                self.x = self.hooh_target_x
                self.y = target_y
                self.hooh_phase = 0.5 
                self.hooh_absorb_timer = 100
                self.hooh_absorb_particles = []
                
        elif self.hooh_phase == 0.5:
            if hasattr(self, 'hooh_trail_particles'):
                alive = []
                for p in self.hooh_trail_particles:
                    p['life'] -= 1
                    if p['life'] > 0:
                        self.canvas.move(p['id'], p['vx'], p['vy'])
                        alive.append(p)
                    else:
                        self.canvas.delete(p['id'])
                self.hooh_trail_particles = alive

            self.hooh_absorb_timer -= 1
            
            if self.hooh_absorb_timer % 3 == 0:
                angle = random.uniform(0, 2 * math.pi)
                dist_p = random.uniform(80, 150)
                cx = self.size_w // 2
                cy = self.size_h // 2
                px = cx + math.cos(angle) * dist_p
                py = cy + math.sin(angle) * dist_p
                
                color = random.choice(["#FF0000", "#FF7F00", "#FFFF00", "#00FF00", "#00BFFF", "#4B0082", "#9400D3"])
                size = random.choice([2, 3])
                
                pid = self.canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color, tags="vfx_hooh_absorb")
                self.hooh_absorb_particles.append({'id': pid, 'x': px, 'y': py, 'cx': cx, 'cy': cy})
                
            alive = []
            for p in self.hooh_absorb_particles:
                dx_p = p['cx'] - p['x']
                dy_p = p['cy'] - p['y']
                d_p = math.sqrt(dx_p**2 + dy_p**2)
                if d_p > 10.0:
                    speed = 6.0 + (100 - self.hooh_absorb_timer) * 0.05
                    move_x = (dx_p/d_p) * speed
                    move_y = (dy_p/d_p) * speed
                    self.canvas.move(p['id'], move_x, move_y)
                    p['x'] += move_x
                    p['y'] += move_y
                    alive.append(p)
                else:
                    self.canvas.delete(p['id'])
            self.hooh_absorb_particles = alive
            
            if self.hooh_absorb_timer <= 0:
                for p in self.hooh_absorb_particles:
                    self.canvas.delete(p['id'])
                self.hooh_absorb_particles = []
                self.hooh_phase = 1
                
                # STRUCTURAL FIX: Hijack at Moment Zero.
                # Now that Ho-Oh is in position, violently interrupt all targets.
                active_targets = []
                for target in getattr(self, 'hooh_targets', []):
                    # Re-validate in case they were caught/deleted during Ho-Oh's flight
                    if target and target.window.winfo_exists() and target.current_state not in ['exiting', 'dragged', 'spawning_wild', 'despawning_wild', 'falling_pokeball', 'falling_egg']:
                        
                        if target.current_state.startswith('dark_'):
                            target.cancel_dark_arts()
                        elif target.current_state.startswith('mewtwo_'):
                            target.cancel_mewtwo_arts()
                        elif target.current_state == 'tk_channeling':
                            target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
                            if getattr(target, 'tk_target', None):
                                if getattr(target.tk_target, 'current_state', '') in ['tk_controlled', 'tk_lifted']:
                                    
                                    # FIX: Force cleanup of floating object/victim particles
                                    t_targ = target.tk_target
                                    t_w = t_targ.size_w if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size
                                    t_h = t_targ.size_h if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size
                                    target.manage_tk_aura(t_targ.canvas, t_w, t_h, False)
                                    
                                    if hasattr(t_targ, 'interrupt_current_state'): t_targ.interrupt_current_state()
                                    t_targ.current_state = 'falling'
                                    if hasattr(t_targ, 'tk_master'):
                                        t_targ.tk_master = None
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
                        
                        if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
                        target.current_state = 'burning'
                        target.burning_timer = self.hooh_timer 
                        target.hooh_master = self
                        target.is_facing_right = random.choice([True, False])
                        active_targets.append(target)
                
                self.hooh_targets = active_targets
        else:
            self.hooh_timer -= 1
            self.y = target_y + math.sin(self.hooh_timer * 0.2) * 5.0
            
            if self.hooh_timer % 3 == 0:
                self.show_fire_vfx(is_master=True)
                
            if self.hooh_timer <= 0:
                if hasattr(self, 'hooh_particles'):
                    for p in self.hooh_particles:
                        try: self.canvas.delete(p['id'])
                        except: pass
                    self.hooh_particles = []
                if getattr(self, 'is_flying', False):
                    # FIX: Remove defective recalculation. 
                    # The Pokemon already perfectly remembers its original 'target_floor_y'.
                    self.floor_y = self.y 
                    self.current_state = 'ascending'
                else:
                    self.current_state = 'falling'
                    
                self.hooh_targets = []
                if hasattr(self, 'hooh_target_x'): delattr(self, 'hooh_target_x')
                
        self.update_position()
        self.schedule_loop(30, self.physics_loop)


