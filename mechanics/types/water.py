import os
import time
import math
import random
import tkinter as tk
from PIL import Image, ImageTk

class BubbleMechanics:
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
