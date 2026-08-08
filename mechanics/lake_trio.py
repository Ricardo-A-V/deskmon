import math
import random
import tkinter as tk
import time

class LakeTrioMechanics:
    def get_lake_color(self):
        name = self.pet_name.lower().replace("_", "")
        if "azelf" in name: return "#0088FF" # Blue
        if "mesprit" in name: return "#FF0088" # Pink/Magenta
        if "uxie" in name: return "#FFDD00" # Yellow
        return "#FFFFFF"
        
    def get_lake_offset(self):
        name = self.pet_name.lower().replace("_", "")
        if "azelf" in name: return 0.0
        if "mesprit" in name: return math.pi * (2.0 / 3.0) # 120 degrees
        if "uxie" in name: return math.pi * (4.0 / 3.0) # 240 degrees
        return 0.0

    def cancel_lake_arts(self):
        if hasattr(self, 'lake_vfx_win') and self.lake_vfx_win and self.lake_vfx_win.winfo_exists():
            self.lake_vfx_win.destroy()
            self.lake_vfx_win = None
            
        for attr in ['lake_timer', 'lake_vfx_win', 'lake_canvas', 'lake_global_angle']:
            if hasattr(self, attr): delattr(self, attr)
            
        self.lake_particles = []

        self.surface_angle = 0
        if self.current_state not in ['dragged', 'exiting']:
            self.current_state = 'falling'
            self.v_y_velocity = 0

    def _fsm_lake_channeling(self):
        if not hasattr(self, 'lake_timer'):
            self.lake_timer = 100 # ~3.3 seconds (at 30ms tick)
            self.v_y_velocity = 0
            
            self.lake_vfx_win = tk.Toplevel(self.window.master)
            self.lake_vfx_win.title(f"VFX_Lake_{self.pet_name}")
            self.lake_vfx_win.overrideredirect(True)
            self.lake_vfx_win.attributes('-topmost', True)
            TRANS_COLOR = '#010101'
            self.lake_vfx_win.config(bg=TRANS_COLOR)
            try: self.lake_vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
            except: pass
            
            self.lake_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
            self.lake_canvas = tk.Canvas(self.lake_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
            self.lake_canvas.pack()
            self.lake_particles = []
            self.lake_vfx_loop()
            
        self.lake_timer -= 1
        
        # Float up slowly
        if self.lake_timer % 3 == 0:
            self.y -= 1
        
        # Circumference particles absorbing inwards
        if self.lake_timer % 24 == 0:
            cx = self.x - self.v_x + self.size_w/2
            cy = self.y - self.v_y + self.size_h/2
            r = random.uniform(30, 60)
            color = self.get_lake_color()
            self.lake_particles.append({
                'id': self.lake_canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline=color, width=2, tags="pt"),
                'type': 'absorb_ring', 'x': cx, 'y': cy, 'r': r, 'speed': random.uniform(1.0, 2.0)
            })
            
        if self.lake_timer <= 0:
            self.current_state = 'lake_rotating'
            self.surface_angle = 0
            self.lake_timer = 900 # 30 seconds
            
            # Restart other active lake trio timers to 30s
            if getattr(self, 'get_all_pets', None):
                for p in self.get_all_pets():
                    if p != self and getattr(p, 'current_state', '') == 'lake_rotating':
                        p.lake_timer = 900
                        
        self.update_position()
        self.schedule_loop(33, self.physics_loop)
        
    def _fsm_lake_rotating(self):
        self.lake_timer -= 1
        
        if self.lake_timer <= 0:
            # End explosion on mouse
            mx = self.window.winfo_pointerx() - self.v_x
            my = self.window.winfo_pointery() - self.v_y
            colors = ["#0088FF", "#FF0088", "#FFDD00"]
            for _ in range(30):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(5.0, 15.0)
                color = random.choice(colors)
                self.lake_particles.append({
                    'id': self.lake_canvas.create_oval(mx-3, my-3, mx+3, my+3, fill=color, outline=color, tags="pt"),
                    'type': 'explosion', 'x': mx, 'y': my, 'vx': math.cos(angle)*speed, 'vy': math.sin(angle)*speed, 'life': 20
                })
            self.current_state = 'thrown'
            
            dx = (self.x + self.size_w/2) - mx
            dy = (self.y + self.size_h/2) - my
            dist = max(1, math.hypot(dx, dy))
            self.v_x_velocity = (dx/dist) * 15
            self.v_y_velocity = (dy/dist) * 15 - 10
            self.surface_angle = 0
            self.lake_cooldown = 72000
            
            # Cleanup later via the vfx loop which handles exiting particles
            self.schedule_loop(33, self.physics_loop)
            return
            
        # Follow Mouse
        mx = self.window.winfo_pointerx()
        my = self.window.winfo_pointery()
            
        self.lake_global_angle = (time.time() * 2.0)
        
        # Calculate target position around mouse
        offset_angle = self.get_lake_offset()
        total_angle = self.lake_global_angle + offset_angle
        radius = 120
        
        target_x = mx + math.cos(total_angle) * radius
        target_y = my + math.sin(total_angle) * radius
        
        # Smoothly interpolate position towards target
        # Smoothly interpolate position towards target
        self.x += (target_x - (self.size_w/2) - self.x) * 0.2
        self.y += (target_y - (self.size_h/2) - self.y) * 0.2
        
        # Force facing right to keep rotation math consistent
        self.is_facing_right = True
        
        # Sprite rotation: orient towards cursor
        dx = mx - (self.x + self.size_w/2)
        dy = my - (self.y + self.size_h/2)
        target_surface_angle = -math.degrees(math.atan2(dy, dx)) + 30
        
        # Interpolate rotation from current (starts at 0 / facing right)
        diff = (target_surface_angle - getattr(self, 'surface_angle', 0)) % 360
        if diff > 180: diff -= 360
        self.surface_angle = (getattr(self, 'surface_angle', 0) + diff * 0.2) % 360
        
        # Trail particles
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        color = self.get_lake_color()
        self.lake_particles.append({
            'id': self.lake_canvas.create_oval(cx-4, cy-4, cx+4, cy+4, fill=color, outline=color, tags="pt"),
            'type': 'trail', 'life': 10
        })
        
        # Check if all 3 are rotating
        rotating_count = 1
        if getattr(self, 'get_all_pets', None):
            for p in self.get_all_pets():
                if p != self and p.pet_name.lower().replace("_", "") in ["azelf", "mesprit", "uxie"] and getattr(p, 'current_state', '') == 'lake_rotating':
                    rotating_count += 1
                    
        # Apply repel if all 3 are rotating
        if rotating_count >= 3:
            if getattr(self, 'get_all_pets', None):
                for p in self.get_all_pets():
                    if p.pet_name.lower().replace("_", "") not in ["azelf", "mesprit", "uxie"] and p.current_state not in ['exiting', 'dragged']:
                        if p.current_state == 'bubbled':
                            if hasattr(p, 'manage_bubble_vfx'): p.manage_bubble_vfx(False)
                            if hasattr(p, 'show_bubble_burst_vfx'): p.show_bubble_burst_vfx()
                        elif p.current_state.startswith('dark_'):
                            if hasattr(p, 'cancel_dark_arts'): p.cancel_dark_arts()
                        elif p.current_state in ['lugia_channeling', 'lugia_dash']:
                            if hasattr(p, 'cancel_lugia_arts'): p.cancel_lugia_arts()
                            
                        p_cx = p.x + p.size_w/2
                        p_cy = p.y + p.size_h/2
                        dist = math.hypot(mx - p_cx, my - p_cy)
                        if dist < 200: # Repel radius from mouse
                            p.current_state = 'thrown'
                            push_force = (200 - dist) * 0.3
                            p.v_x_velocity = -push_force if p_cx < mx else push_force
                            p.v_y_velocity = -push_force if p_cy < my else push_force
                            
                            # Add barrier particles at the collision point
                            collision_x = mx + ((p_cx - mx) * (200 / max(1, dist))) - self.v_x
                            collision_y = my + ((p_cy - my) * (200 / max(1, dist))) - self.v_y
                            for _ in range(3):
                                bcolor = random.choice(["#0088FF", "#FF0088", "#FFDD00"])
                                self.lake_particles.append({
                                    'id': self.lake_canvas.create_oval(collision_x-2, collision_y-2, collision_x+2, collision_y+2, fill=bcolor, outline=bcolor, tags="pt"),
                                    'type': 'explosion', 'x': collision_x, 'y': collision_y, 'vx': random.uniform(-1.5, 1.5), 'vy': random.uniform(-1.5, 1.5), 'life': 6
                                })

        self.update_position()
        self.schedule_loop(33, self.physics_loop)
        
    def lake_vfx_loop(self):
        if self.current_state not in ['lake_channeling', 'lake_rotating'] and not (self.current_state in ['falling', 'thrown'] and len(getattr(self, 'lake_particles', [])) > 0): 
            if hasattr(self, 'lake_vfx_win') and self.lake_vfx_win:
                self.lake_vfx_win.destroy()
                self.lake_vfx_win = None
            return
            
        if not hasattr(self, 'lake_vfx_win') or not self.lake_vfx_win or not self.lake_vfx_win.winfo_exists(): return
        
        alive = []
        for p in self.lake_particles:
            if p.get('type') == 'absorb_ring':
                p['r'] -= p['speed']
                if p['r'] > 5:
                    self.lake_canvas.coords(p['id'], p['x']-p['r'], p['y']-p['r'], p['x']+p['r'], p['y']+p['r'])
                    alive.append(p)
                else:
                    self.lake_canvas.delete(p['id'])
            elif p.get('type') == 'trail':
                if p['life'] > 0:
                    p['life'] -= 1
                    coords = self.lake_canvas.coords(p['id'])
                    if coords:
                        # shrink
                        self.lake_canvas.coords(p['id'], coords[0]+0.5, coords[1]+0.5, coords[2]-0.5, coords[3]-0.5)
                        alive.append(p)
                else:
                    self.lake_canvas.delete(p['id'])
            elif p.get('type') == 'explosion':
                if p['life'] > 0:
                    p['life'] -= 1
                    p['x'] += p['vx']
                    p['y'] += p['vy']
                    p['vy'] += 0.5 # gravity
                    self.lake_canvas.coords(p['id'], p['x']-3, p['y']-3, p['x']+3, p['y']+3)
                    alive.append(p)
                else:
                    self.lake_canvas.delete(p['id'])
                    
        self.lake_particles = alive
        self.window.after(33, self.lake_vfx_loop)
