import random
import math
import tkinter as tk
import os

class TapusMechanics:
    def get_tapu_type(self):
        name = self.pet_name.lower().replace("_", "").replace("-", "")
        if name in ["tapukoko", "tapukoko1"]: return "electric"
        if name in ["tapulele", "tapulele1"]: return "psychic"
        if name in ["tapubulu", "tapubulu1"]: return "grassy"
        if name in ["tapufini", "tapufini1"]: return "misty"
        return None

    def start_tapu_mechanic(self):
        if getattr(self, 'current_state', '') in ['dragged', 'exiting']: return
        self.current_state = 'tapu_channeling'
        self.tapu_channel_timer = 90 # 3 seconds
        self.tapu_type = self.get_tapu_type()
        
        self.tapu_target_x = self.v_x + self.v_width / 2 - self.size_w / 2
        self.tapu_target_y = self.v_y + (self.v_height * 3 / 4) - self.size_h / 2
        
        self.tapu_color = {"electric": "#FFFF00", "psychic": "#FF69B4", "grassy": "#00FF01", "misty": "#DA70D6"}.get(self.tapu_type, "#FFFFFF")

    def _fsm_tapu_channeling(self):
        if not hasattr(self, 'tapu_channel_timer'):
            self.current_state = 'idle'
            self.schedule_loop(33, self.physics_loop)
            return

        if self.tapu_channel_timer > 0:
            self.tapu_channel_timer -= 1
            self.v_x_velocity = 0
            self.v_y_velocity = 0
            
            # Channeling particles inward
            for _ in range(3):
                cx = self.x - self.v_x + self.size_w/2 + random.uniform(-150, 150)
                cy = self.y - self.v_y + self.size_h/2 + random.uniform(-150, 150)
                vx = (self.x - self.v_x + self.size_w/2 - cx) / 10
                vy = (self.y - self.v_y + self.size_h/2 - cy) / 10
                self.spawn_tapu_particle(cx, cy, self.tapu_color, 12, vx, vy)
                
            self.update_position()
            self.schedule_loop(33, self.physics_loop)
        else:
            self.is_facing_right = (self.tapu_target_x - self.x) > 0
            self.current_state = 'tapu_positioning'
            self.schedule_loop(33, self.physics_loop)

    def _fsm_tapu_positioning(self):
        dx = self.tapu_target_x - self.x
        dy = self.tapu_target_y - self.y
        dist = math.hypot(dx, dy)
        
        if dist < 12:
            self.x = self.tapu_target_x
            self.y = self.tapu_target_y
            self.current_state = 'tapu_active'
            self.tapu_field_timer = 900 # 30 seconds
            
            # Explosion of rays
            for _ in range(40):
                cx = self.size_w/2
                cy = self.size_h/2
                angle = random.uniform(0, 2*math.pi)
                speed = random.uniform(5, 25)
                length = random.uniform(10, 40)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                abs_cx = self.x - self.v_x + cx
                abs_cy = self.y - self.v_y + cy
                self.spawn_tapu_particle(abs_cx, abs_cy, self.tapu_color, random.randint(15, 30), vx, vy, p_type="ray", length=length, angle=angle)
                
            self._init_tapu_field_win()
            self.schedule_loop(33, self.physics_loop)
            return

        speed = 10.0
        self.x += (dx / dist) * speed
        self.y += (dy / dist) * speed
        self.is_facing_right = dx > 0
        self.update_position()
        self.schedule_loop(33, self.physics_loop)

    def _fsm_tapu_active(self):
        if not hasattr(self, 'tapu_field_timer'):
            self.current_state = 'idle'
            self.schedule_loop(33, self.physics_loop)
            return

        if self.tapu_field_timer > 0:
            self.tapu_field_timer -= 1
            
            # Hover slowly
            self.x = self.tapu_target_x + math.sin(self.tapu_field_timer / 10.0) * 10
            self.y = self.tapu_target_y + math.cos(self.tapu_field_timer / 15.0) * 5
            
            self._spawn_field_edge_particles()
            
            # Apply effect globally
            if hasattr(self, 'get_all_pets'):
                for p in self.get_all_pets():
                    if p != self and p.current_state not in ['exiting', 'dragged']:
                        self._apply_tapu_effect_to_pet(p)
            
            self.update_position()
            self.schedule_loop(33, self.physics_loop)
        else:
            self.current_state = 'thrown' if getattr(self, 'is_flying', False) else 'falling'
            self.cancel_tapu_mechanic()
            self.schedule_loop(33, self.physics_loop)
            
    def cancel_tapu_mechanic(self):
        if getattr(self, 'tapu_type', None):
            for _ in range(20):
                cx = self.x - self.v_x + self.size_w/2
                cy = self.y - self.v_y + self.size_h/2
                angle = random.uniform(0, 2*math.pi)
                speed = random.uniform(3, 10)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                self.spawn_tapu_particle(cx, cy, getattr(self, 'tapu_color', '#FFFFFF'), random.randint(10, 20), vx, vy, p_type="particle")
                
        if hasattr(self, 'tapu_field_timer'):
            self.tapu_field_timer = 0
        self._cleanup_tapu_field()
        if hasattr(self, 'get_all_pets'):
            for p in self.get_all_pets():
                if hasattr(p, 'tapu_field_timeout'):
                    p.tapu_field_timeout = 0
                try: p.canvas.delete("tapu_pet_particle")
                except: pass
            
    def _apply_tapu_effect_to_pet(self, pet):
        pet.tapu_field_effect = self.tapu_type
        pet.tapu_field_timeout = 5 # frames until expires naturally
        
        if not hasattr(pet, 'original_speed'):
            pet.original_speed = pet.speed
            
        if self.tapu_type == "electric":
            pet.speed = max(1, int(pet.original_speed * 1.5))
        elif self.tapu_type == "misty":
            pet.speed = max(1, int(pet.original_speed * 0.5))
        elif self.tapu_type == "grassy":
            pet.scale_mod = getattr(pet, 'scale_mod', 1.0) # We will handle gradual scale up in pet's loop or here
            pet.scale_mod = min(1.2, pet.scale_mod + 0.05)
        elif self.tapu_type == "psychic":
            # Low gravity
            if pet.current_state in ['thrown', 'falling', 'jumping_arc'] and getattr(pet, 'v_y_velocity', 0) > -15:
                pet.v_y_velocity -= 1.3 # counteract gravity

        # Particles on pet
        if random.random() < 0.1:
            try:
                cx = pet.size_w // 2 + random.randint(-20, 20)
                cy = pet.size_h // 2 + random.randint(-20, 20)
                # Tapu Koko pixelated, others regular
                if self.tapu_type == "electric":
                    pid = pet.canvas.create_rectangle(cx-2, cy-2, cx+2, cy+2, fill=self.tapu_color, outline="", tags="tapu_pet_particle")
                else:
                    pid = pet.canvas.create_oval(cx-2, cy-2, cx+2, cy+2, fill=self.tapu_color, outline="", tags="tapu_pet_particle")
                pet.schedule_loop(500, lambda id=pid: pet.canvas.delete(id))
            except: pass

    def _init_tapu_field_win(self):
        if hasattr(self, 'tapu_vfx_win') and self.tapu_vfx_win and self.tapu_vfx_win.winfo_exists():
            return
        self.tapu_vfx_win = tk.Toplevel(self.window.master)
        self.tapu_vfx_win.overrideredirect(True)
        self.tapu_vfx_win.attributes('-topmost', True)
        TRANS_COLOR = '#010101'
        self.tapu_vfx_win.config(bg=TRANS_COLOR)
        try: self.tapu_vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass
        self.tapu_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        self.tapu_canvas = tk.Canvas(self.tapu_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
        self.tapu_canvas.pack()
        self.tapu_field_particles = []
        
    def _spawn_field_edge_particles(self):
        if not hasattr(self, 'tapu_canvas') or not self.tapu_vfx_win.winfo_exists(): return
        
        # Edges
        for _ in range(2):
            edge = random.choice(['top', 'bottom', 'left', 'right'])
            if edge == 'top': px, py = random.randint(0, self.v_width), 5
            elif edge == 'bottom': px, py = random.randint(0, self.v_width), self.v_height - 5
            elif edge == 'left': px, py = 5, random.randint(0, self.v_height)
            else: px, py = self.v_width - 5, random.randint(0, self.v_height)
            
            size = 2 if self.tapu_type == "electric" else 3
            if self.tapu_type == "electric":
                pid = self.tapu_canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=self.tapu_color, outline="")
            else:
                pid = self.tapu_canvas.create_oval(px-size, py-size, px+size, py+size, fill=self.tapu_color, outline="")
                
            vx = random.uniform(-1, 1)
            vy = random.uniform(-1, 1)
            self.tapu_field_particles.append({'id': pid, 'x': px, 'y': py, 'vx': vx, 'vy': vy, 'life': random.randint(20, 40), 'type': 'edge'})
                
        # Update particles
        alive = []
        for p in self.tapu_field_particles:
            p['life'] -= 1
            if p['life'] > 0:
                p['x'] += p['vx']
                p['y'] += p['vy']
                self.tapu_canvas.move(p['id'], p['vx'], p['vy'])
                alive.append(p)
            else:
                self.tapu_canvas.delete(p['id'])
        self.tapu_field_particles = alive

    def _cleanup_tapu_field(self):
        if hasattr(self, 'tapu_vfx_win') and self.tapu_vfx_win:
            self.tapu_vfx_win.destroy()
            self.tapu_vfx_win = None
            
    def spawn_tapu_particle(self, cx, cy, color, life, vx, vy, p_type="particle", length=0, angle=0):
        self._init_tapu_vfx()
        if p_type == "ray":
            x2 = cx + math.cos(angle) * length
            y2 = cy + math.sin(angle) * length
            pid = self.tapu_vfx_canvas.create_line(cx, cy, x2, y2, fill=color, width=2)
        else:
            pid = self.tapu_vfx_canvas.create_rectangle(cx-2, cy-2, cx+2, cy+2, fill=color, outline="")
        self.tapu_particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': life})
        if len(self.tapu_particles) == 1:
            self._process_tapu_particles()
            
    def _init_tapu_vfx(self):
        if not hasattr(self, 'tapu_vfx_win_particles') or not self.tapu_vfx_win_particles or not self.tapu_vfx_win_particles.winfo_exists():
            self.tapu_vfx_win_particles = tk.Toplevel(self.window.master)
            self.tapu_vfx_win_particles.overrideredirect(True)
            self.tapu_vfx_win_particles.attributes('-topmost', True)
            TRANS_COLOR = '#010101'
            self.tapu_vfx_win_particles.config(bg=TRANS_COLOR)
            try: self.tapu_vfx_win_particles.wm_attributes('-transparentcolor', TRANS_COLOR)
            except: pass
            self.tapu_vfx_win_particles.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
            self.tapu_vfx_canvas = tk.Canvas(self.tapu_vfx_win_particles, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
            self.tapu_vfx_canvas.pack()
            self.tapu_particles = []
            
    def _process_tapu_particles(self):
        if not hasattr(self, 'tapu_vfx_win_particles') or not self.tapu_vfx_win_particles: return
        alive = []
        for p in self.tapu_particles:
            p['life'] -= 1
            if p['life'] > 0:
                self.tapu_vfx_canvas.move(p['id'], p['vx'], p['vy'])
                alive.append(p)
            else:
                self.tapu_vfx_canvas.delete(p['id'])
        self.tapu_particles = alive
        if self.tapu_particles:
            self.schedule_loop(33, self._process_tapu_particles)
        elif hasattr(self, 'tapu_vfx_win_particles') and self.tapu_vfx_win_particles:
            self.tapu_vfx_win_particles.destroy()
            self.tapu_vfx_win_particles = None

