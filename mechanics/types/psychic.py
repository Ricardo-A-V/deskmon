import time
import tkinter as tk
from PIL import Image, ImageTk

import random
import math
import os

class TelekinesisMechanics:
    def manage_tk_aura(self, canvas, w, h, is_active):
        try:
            if is_active:
                canvas.delete("tk_aura") 
                t = time.time()
                cx, cy = w / 2, h / 2
                base_radius = max(w, h) * 0.6
                
                # Swarm of 24 psychic particles generated mathematically in real time
                for i in range(24):
                    # 1. Asymmetrical speed (Some particles go fast, others slow, others backwards)
                    speed = 1.5 + (math.sin(i * 7.1) * 2.0)
                    angle = (t * speed) + (i * 0.8)
                    
                    # 2. Radius dispersion (Breaks the circumference to create a chaotic cloud)
                    scatter = math.cos(i * 13.3) * (base_radius * 0.5)
                    r = base_radius + scatter
                    
                    px = cx + math.cos(angle) * r
                    py = cy + math.sin(angle) * r
                    
                    # 3. Individual time-based blinking phase
                    blink_phase = math.sin(t * 12.0 + i * 3.14)
                    
                    if blink_phase > 0.5:
                        color = "#FFFFFF" # Intense white flash
                        size = 2
                    elif blink_phase > -0.3:
                        color = "#D24DFF" # Base energy purple
                        size = 1
                    else:
                        continue # Invisible particle (simulates completely turning off)
                    
                    canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color, tags="tk_aura")
                    
                canvas.tag_lower("tk_aura") # Force cloud behind the sprite
            else:
                canvas.delete("tk_aura")
        except:
            pass

    def _fsm_tk_lifted(self):
        if not hasattr(self, 'tk_master') or not self.tk_master.window.winfo_exists() or self.tk_master.current_state != 'tk_channeling':
            self.current_state = 'falling'
            self.manage_tk_aura(self.canvas, self.size_w, self.size_h, False)
        self.schedule_loop(30, self.physics_loop)

    def _fsm_tk_channeling(self):
        target = getattr(self, 'tk_target', None)
        
        if not target or getattr(target, 'current_state', '') not in ['tk_controlled', 'tk_lifted'] or not getattr(target, 'window', None) or not target.window.winfo_exists():
            self.current_state = 'idle'
            self.tk_cooldown = 600
            self.manage_tk_aura(self.canvas, self.size_w, self.size_h, False)
            if target: 
                t_w = target.size_w if target.__class__.__name__ == 'DesktopPet' else target.size
                t_h = target.size_h if target.__class__.__name__ == 'DesktopPet' else target.size
                self.manage_tk_aura(target.canvas, t_w, t_h, False)
                target.tk_master = None
            self.tk_target = None
            self.schedule_loop(30, self.physics_loop) 
            return

        self.tk_timer -= 1
        
        is_berry = target.__class__.__name__ == 'InteractiveBerry'
        is_toy = target.__class__.__name__ == 'InteractivePokeball'
        is_pet = target.__class__.__name__ == 'DesktopPet'

        t_w = target.size_w if is_pet else target.size
        t_h = target.size_h if is_pet else target.size

        self.manage_tk_aura(self.canvas, self.size_w, self.size_h, True)
        self.manage_tk_aura(target.canvas, t_w, t_h, True)

        my_cx = self.x + self.size_w / 2
        my_cy = self.y + self.size_h / 2
        t_cx = target.x + t_w / 2
        t_cy = target.y + t_h / 2

        if is_berry:
            dx = my_cx - t_cx
            dy = my_cy - t_cy
            dist = math.sqrt(dx**2 + dy**2)
            if dist < 30:
                self.current_state = 'eating'
                self.eating_timer = 30
                self.interaction_target = target
                self.manage_tk_aura(self.canvas, self.size_w, self.size_h, False)
                target.destroy()
                self.show_heart_vfx()
                self.schedule_loop(30, self.physics_loop)
                return
            else:
                self.tk_timer += 1 
                target.x += (dx / max(1, dist)) * 12.0
                target.y += (dy / max(1, dist)) * 12.0
        
        elif is_toy or is_pet:
            if not getattr(self, 'tk_orbit_started', False):
                dx_center = my_cx - t_cx
                dy_center = my_cy - t_cy
                dist_to_center = math.sqrt(dx_center**2 + dy_center**2)
                
                if dist_to_center > 40:
                    self.tk_timer += 1 
                    target.x += (dx_center / max(1, dist_to_center)) * 18.0
                    target.y += (dy_center / max(1, dist_to_center)) * 18.0
                else:
                    self.tk_orbit_started = True
                    self.tk_orbit_angle = 0.0 
            else:
                self.tk_orbit_angle += 0.12
                angle = self.tk_orbit_angle % (2 * math.pi)
                radius = self.size_w * 1.3
                
                target.x = my_cx + math.cos(angle) * radius - t_w / 2
                target.y = my_cy + math.sin(angle) * radius - t_h / 2 - 20

                if self.tk_timer <= 0:
                    self.current_state = 'idle'
                    self.tk_cooldown = self.get_type_cooldown(12000)
                    if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
                    target.current_state = 'thrown'
                    
                    # Launch outward relative to where it is in the orbit
                    launch_angle = angle
                    
                    # MASSIVE FORCE ASSIGNMENT ACCORDING TO TARGET MASS
                    if is_toy:
                        force = random.uniform(40.0, 55.0)
                    else:
                        force = random.uniform(22.0, 32.0)
                        
                    target.v_x_velocity = math.cos(launch_angle) * force
                    target.v_y_velocity = math.sin(launch_angle) * force
                            
                    self.manage_tk_aura(self.canvas, self.size_w, self.size_h, False)
                    self.manage_tk_aura(target.canvas, t_w, t_h, False)
                    target.tk_master = None

        target.update_position()
        self.update_position()
        self.schedule_loop(30, self.physics_loop)


    def _fsm_teleporting_out(self):
        self.teleport_step -= 0.15
        if self.teleport_step <= 0:
            self.window.attributes('-alpha', 0.0)
            
            import random
            # 1. We choose the new X coordinate at random
            self.x = random.randint(self.v_x, self.v_x + self.v_width - self.size_w)
            
            # 2. Y relocation logic
            if getattr(self, 'is_flying', False):
                self.y = getattr(self, 'target_floor_y', self.default_floor_y)
                self.floor_y = self.y
                self.anchored_hwnd = None
                self.anchored_rect = None
            else:
                self.y = self.v_y 
                current_env, _ = self.get_window_environment()
                
                if current_env['hwnd']:
                    self.anchored_hwnd = current_env['hwnd']
                    self.anchored_rect = current_env['rect']
                    self.floor_y = self.anchored_rect[1] - self.size_h - getattr(self, 'offset_y', 0)
                    self.y = self.floor_y
                else:
                    self.anchored_hwnd = None
                    self.anchored_rect = None
                    self.floor_y = self.default_floor_y
                    self.y = self.default_floor_y
                    
            self.current_state = 'teleporting_in'
        else:
            self.window.attributes('-alpha', self.teleport_step)
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_teleporting_in(self):
        self.teleport_step += 0.15
        if self.teleport_step >= 1.0:
            self.teleport_step = 1.0
            self.window.attributes('-alpha', 1.0)
            self.current_state = 'idle'
        else:
            self.window.attributes('-alpha', self.teleport_step)
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)
