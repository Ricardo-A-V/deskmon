import time
import tkinter as tk
from PIL import Image, ImageTk

import random
import math
import os

class TelekinesisMechanics:
    def manage_tk_aura(self, canvas, w, h, is_active):
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

    def manage_bubble_vfx(self, is_active, progress=1.0):
        if is_active:
            self.canvas.delete("vfx_bubble")
            
            # Image loading and cleanup in memory
            if not getattr(self, 'bubble_base_img', None):
                try:
                    ui_dir = os.path.join(self.base_dir, "game_env", "ui")
                    raw_img = Image.open(os.path.join(ui_dir, "bubble.png")).convert("RGBA")
                    
                    r, g, b, a = raw_img.split()
                    a = a.point(lambda p: 255 if p > 127 else 0)
                    self.bubble_base_img = Image.merge("RGBA", (r, g, b, a))
                except Exception as e:
                    print(f"[-] Error: Missing bubble.png in game_env/ui. {e}")
                    return

            # GEOMETRIC FIX: Strict mathematical limit to the canvas edge
            canvas_limit = min(self.size_w, self.size_h)
            # Reserve 6 pixels margin (3 per side) so oscillation doesn't touch edge
            base_max_size = canvas_limit - 6 
            
            # ORGANIC PULSE: Injected oscillation if growth phase ended
            pulse_offset = 0
            if progress >= 1.0:
                # math.sin generates a fluid curve between -1 and 1. 
                # Multiplied by 3 gives a dynamic +/- 3 pixel growth/shrink in loop.
                pulse_offset = int(math.sin(time.time() * 6.0) * 3)

            current_size = max(10, int(base_max_size * progress) + pulse_offset)
            
            # Real-time rendering
            resized_bubble = self.bubble_base_img.resize((current_size, current_size), Image.Resampling.NEAREST)
            self.bubble_tk = ImageTk.PhotoImage(resized_bubble)
            
            cx = self.size_w // 2
            # FIX: Visual gravity compensation. Lower the bubble 15% to center it on body.
            cy = (self.size_h // 2) + int(self.size_h * 0.05)
            
            self.canvas.create_image(cx, cy, image=self.bubble_tk, anchor=tk.CENTER, tags="vfx_bubble")
            self.canvas.tag_raise("vfx_bubble")
        else:
            self.canvas.delete("vfx_bubble")
            # Release Tkinter pointers to avoid memory leaks
            if hasattr(self, 'bubble_tk'):
                delattr(self, 'bubble_tk')

    def show_bubble_burst_vfx(self):
        particles = []
        cx = self.size_w // 2
        cy = (self.size_h // 2) + int(self.size_h * 0.15)
        
        # Generate 8 drops/sparks of explosion
        for _ in range(8):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3.0, 6.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.choice([1, 2])
            color = random.choice(["#FFFFFF", "#D4E6F1", "#A9CCE3"]) # White and water tones
            
            pid = self.canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline=color, tags="vfx_bubble_burst")
            particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': random.randint(10, 18)})
            
        def animate_burst():
            if getattr(self, 'current_state', 'exiting') == 'exiting': return
            
            alive_count = 0
            for p in particles:
                if p['life'] > 0:
                    self.canvas.move(p['id'], p['vx'], p['vy'])
                    p['vy'] += 0.4 # Individual gravity so they fall like water
                    p['life'] -= 1
                    alive_count += 1
                elif p['life'] == 0:
                    self.canvas.delete(p['id'])
                    p['life'] = -1
                    
            if alive_count > 0:
                self.schedule_loop(30, animate_burst)
                
        animate_burst()

    def _fsm_bubbled(self):
        max_time = getattr(self, 'bubble_max_time', 150)
        elapsed = max_time - self.bubble_timer
        
        # PHASE 1: Growth and absorption
        if elapsed < 20: 
            self.manage_bubble_vfx(True, elapsed / 20.0)
        else:
            self.manage_bubble_vfx(True, 1.0)
            
        self.bubble_timer -= 1
        
        # PHASE 2: Elevation with fluid turbulence
        self.y -= 1.8 
        self.x += math.sin(self.bubble_timer * 0.1) * 2.0 
        
        if self.y < self.v_y:
            self.y = self.v_y

        # PHASE 3: Explosion and reentry to gravity engine
        if self.bubble_timer <= 0:
            self.manage_bubble_vfx(False)
            self.show_bubble_burst_vfx() 
            # FIX: If flying, flight recovery ("thrown") activates instead of free fall ("falling")
            self.current_state = 'thrown' if getattr(self, 'is_flying', False) else 'falling'
            self.v_y_velocity = 0.0 
            self.v_x_velocity = 0.0
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_tk_lifted(self):
        if not hasattr(self, 'tk_master') or not self.tk_master.window.winfo_exists() or self.tk_master.current_state != 'tk_channeling':
            self.current_state = 'falling'
            self.manage_tk_aura(self.canvas, self.size_w, self.size_h, False)
        self.schedule_loop(30, self.physics_loop)

    def _fsm_tk_channeling(self):
        target = getattr(self, 'tk_target', None)
        
        if not target or getattr(target, 'current_state', '') not in ['tk_controlled', 'tk_lifted']:
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
                    # FIX: Organic launch in upper half of orbit (math.sin < -0.1)
                    # 20% probability makes it release object in different point each time
                    if math.sin(angle) < -0.1 and (random.randint(1, 100) <= 20 or math.cos(angle) > 0.9):
                        self.current_state = 'idle'
                        self.tk_cooldown = 12000
                        target.current_state = 'thrown'
                        
                        # Calculate strictly superior parabolic arc (between 180 and 360 degrees)
                        launch_angle = random.uniform(math.pi + 0.2, 2 * math.pi - 0.2)
                        # If inverted, force shot towards natural floor
                        if getattr(self, 'gravity_inverted', False):
                            launch_angle = random.uniform(0.2, math.pi - 0.2)
                        
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

