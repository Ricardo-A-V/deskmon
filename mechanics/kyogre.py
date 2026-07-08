import time
from core.overlays import FloodOverlay
try:
    import win32api
    import win32con
except ImportError:
    pass

import random
import math
import os

class KyogreMechanics:
    def show_rain_vfx(self):
        particles = []
        w, h = self.size_w, self.size_h
        
        for _ in range(random.randint(3, 5)):
            x = random.randint(-w, w * 2)
            y = random.randint(-h, 0)
            length = random.randint(10, 20)
            color = random.choice(["#3498DB", "#5DADE2", "#85C1E9"]) 
            
            # Aesthetic diagonal of strong storm
            pid = self.canvas.create_line(x, y, x - length, y + length*2, fill=color, width=2, tags="vfx_rain")
            particles.append({'id': pid, 'vx': -6.0, 'vy': 12.0, 'life': 8})
            
        def animate_rain():
            if getattr(self, 'current_state', 'exiting') == 'exiting': return
            alive_count = 0
            for p in particles:
                if p['life'] > 0:
                    self.canvas.move(p['id'], p['vx'], p['vy'])
                    p['life'] -= 1
                    alive_count += 1
                elif p['life'] == 0:
                    self.canvas.delete(p['id'])
                    p['life'] = -1
                    
            if alive_count > 0:
                self.schedule_loop(30, animate_rain)
                
        animate_rain()

    def cancel_kyogre_arts(self):
        if self.current_state not in ['dragged', 'exiting']:
            self.current_state = 'falling'
            
        targets = getattr(self, 'kyogre_targets', [])
        self.kyogre_targets = []
        for target in targets:
            if target and target.window.winfo_exists():
                target.kyogre_master = None
                if target.current_state == 'deluge_float' and target.current_state not in ['dragged', 'exiting']:
                    target.current_state = 'falling'
                    
        if hasattr(self, 'flood_overlay') and self.flood_overlay:
            self.flood_overlay.destroy()
            self.flood_overlay = None
            
        master = getattr(self, 'kyogre_master', None)
        self.kyogre_master = None
        if master and master.window.winfo_exists():
            master.cancel_kyogre_arts()

    def _fsm_kyogre_channeling(self):
        if not hasattr(self, 'kyogre_target_x'):
            try:
                monitor = win32api.MonitorFromPoint((int(self.x), int(self.y)), win32con.MONITOR_DEFAULTTONEAREST)
                mon_info = win32api.GetMonitorInfo(monitor)
                self.kyogre_target_x = mon_info['Monitor'][0] + ((mon_info['Monitor'][2] - mon_info['Monitor'][0]) // 2) - self.size_w // 2
            except:
                self.kyogre_target_x = self.v_x + (self.v_width // 2) - self.size_w // 2

        target_y = self.v_y + 40 
        dx = self.kyogre_target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if getattr(self, 'kyogre_phase', 0) == 0:
            self.is_facing_right = (dx > 0)
            fly_speed = self.speed * 1.5
            
            if dist > fly_speed:
                self.x += (dx/dist) * fly_speed
                self.y += (dy/dist) * fly_speed
            else:
                self.x = self.kyogre_target_x
                self.y = target_y
                self.kyogre_phase = 1 
                
                if not hasattr(self, 'flood_overlay') or not self.flood_overlay:
                    self.flood_overlay = FloodOverlay(self.window.master, self.v_x, self.v_y, self.v_width, self.v_height)
                
                active_targets = []
                for target in getattr(self, 'kyogre_targets', []):
                    if target and target.window.winfo_exists() and target.current_state not in ['exiting', 'dragged', 'spawning_wild', 'despawning_wild', 'falling_pokeball', 'falling_egg']:
                        
                        if target.current_state.startswith('dark_'): target.cancel_dark_arts()
                        elif target.current_state.startswith('mewtwo_'): target.cancel_mewtwo_arts()
                        elif target.current_state in ['hooh_channeling', 'panic_run']: target.cancel_hooh_arts()
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
                        
                        target.current_state = 'deluge_float'
                        target.kyogre_master = self
                        target.anchored_hwnd = None
                        active_targets.append(target)
                
                self.kyogre_targets = active_targets
                
        elif self.kyogre_phase == 1:
            self.kyogre_timer -= 1
            self.y = target_y + math.sin(self.kyogre_timer * 0.2) * 5.0
            
            if self.kyogre_timer <= 0:
                self.kyogre_phase = 2 
                if hasattr(self, 'flood_overlay') and self.flood_overlay:
                    self.flood_overlay.is_draining = True
                    
        elif self.kyogre_phase == 2:
            self.kyogre_timer -= 1
            self.y = target_y + math.sin(self.kyogre_timer * 0.2) * 5.0
            
            if not hasattr(self, 'flood_overlay') or not self.flood_overlay or not getattr(self.flood_overlay, 'active', False):
                
                for target in getattr(self, 'kyogre_targets', []):
                    if target and target.window.winfo_exists():
                        target.kyogre_master = None
                        if target.current_state == 'deluge_float':
                            target.current_state = 'falling'
                self.kyogre_targets = []
                
                if getattr(self, 'is_flying', False) or self.pet_name.lower().replace("_", "").replace("-", "") == "kyogre":
                    # MATHEMATICAL FIX: Explicitly recalculate PC height percentage
                    pct = self.pet_data.get("flying_height_pct", 3.0)
                    max_offset = self.v_height - self.size_h
                    target_offset_y = int(max_offset * (pct / 100.0))
                    self.target_floor_y = (self.v_y + self.v_height) - self.size_h - target_offset_y
                    
                    self.floor_y = self.y 
                    self.current_state = 'ascending'
                else:
                    self.current_state = 'falling'
                    
                if hasattr(self, 'kyogre_target_x'): delattr(self, 'kyogre_target_x')
                
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_deluge_float(self):
        master = getattr(self, 'kyogre_master', None)
        if not master or master.current_state != 'kyogre_channeling' or not master.window.winfo_exists():
            self.cancel_kyogre_arts()
            self.schedule_loop(30, self.physics_loop)
            return

        if getattr(master, 'kyogre_phase', 0) == 0:
            self.update_position()
            self.schedule_loop(30, self.physics_loop)
            return

        overlay = getattr(master, 'flood_overlay', None)
        current_flood_h = overlay.current_flood_h if overlay and getattr(overlay, 'active', False) else 0
        
        flood_base_y = self.v_y + self.v_height - current_flood_h
        target_y = flood_base_y - self.size_h + 15
        
        t = time.time() * 3.0
        # FIX: Synchronized to 120-pixel Macro-blocks
        wave_res = overlay.wave_resolution if overlay else 120 
        block_idx = int(self.x) // wave_res
        aligned_x = block_idx * wave_res
        
        wave_offset = int(math.sin(t + (aligned_x * 0.005)) * 6.0) 
        
        water_surface_y = target_y + wave_offset

        if self.y < water_surface_y - 20: 
            self.v_y_velocity = getattr(self, 'v_y_velocity', 0.0) + 2.0
            self.y += self.v_y_velocity
            if self.y >= water_surface_y:
                self.y = water_surface_y
                self.v_y_velocity = 0.0
        else:
            self.y = water_surface_y
            self.v_y_velocity = 0.0
            
            if random.randint(1, 100) <= 8:
                self.is_facing_right = not self.is_facing_right
            drift = 2.5 if self.is_facing_right else -2.5
            self.x += drift

            if getattr(self, 'can_screen_wrap', False):
                if self.x <= self.v_x - self.size_w: self.x = self.v_x + self.v_width
                elif self.x >= self.v_x + self.v_width: self.x = self.v_x - self.size_w
            else:
                if self.x <= self.v_x:
                    self.x = self.v_x
                    self.is_facing_right = True
                elif self.x >= (self.v_x + self.v_width) - self.size_w:
                    self.x = (self.v_x + self.v_width) - self.size_w
                    self.is_facing_right = False

        self.update_position()
        self.schedule_loop(30, self.physics_loop)

