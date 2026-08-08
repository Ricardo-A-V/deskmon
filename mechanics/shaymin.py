import math
import random
import tkinter as tk
from PIL import Image, ImageTk
import os

class GracideaLeaf:
    def __init__(self, root, base_dir, screen_width, screen_height, target_pet, on_hit_callback, on_miss_callback=None):
        self.root = root
        self.target = target_pet
        self.on_hit = on_hit_callback
        self.on_miss = on_miss_callback
        
        # Spawn at random top border
        self.x = random.randint(50, screen_width - 50)
        self.y = -50
        
        # Load image
        img_path = os.path.join(base_dir, "game_env", "ui", "gracidea.png")
        self.base_img = Image.open(img_path).convert("RGBA")
        self.base_img = self.base_img.resize((40, 40), Image.Resampling.NEAREST)
        
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes('-topmost', True)
        TRANS_COLOR = '#010101'
        self.win.config(bg=TRANS_COLOR)
        try: self.win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass
        
        self.win.geometry(f"60x60+{int(self.x)}+{int(self.y)}")
        self.canvas = tk.Canvas(self.win, width=60, height=60, bg=TRANS_COLOR, highlightthickness=0)
        self.canvas.pack()
        
        self.image_id = self.canvas.create_image(30, 30, image=None)
        
        self.is_dragged = False
        self.on_floor = False
        self.floor_time = 0
        
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        self.time = 0
        self.active = True
        self.update_loop()
        
    def on_press(self, event):
        self.is_dragged = True
        self.on_floor = False
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_drag(self, event):
        if self.is_dragged:
            self.x = event.x_root - self.drag_start_x
            self.y = event.y_root - self.drag_start_y
            self.win.geometry(f"60x60+{int(self.x)}+{int(self.y)}")

    def on_release(self, event):
        self.is_dragged = False
        
    def update_loop(self):
        if not self.active: return
        if not self.win.winfo_exists(): return
        
        if not self.is_dragged and not self.on_floor:
            # Fall and sway like a leaf
            self.time += 0.05
            self.y += 2.0
            self.x += math.sin(self.time) * 4.0
            
            # Rotate image
            angle = math.sin(self.time * 2.0) * 30
            rotated = self.base_img.rotate(angle, expand=False, resample=Image.NEAREST)
            self.tk_img = ImageTk.PhotoImage(rotated)
            self.canvas.itemconfig(self.image_id, image=self.tk_img)
            
            self.win.geometry(f"60x60+{int(self.x)}+{int(self.y)}")
        elif self.on_floor:
            self.floor_time += 33
            if self.floor_time % 2000 < 33:
                try: self.win.attributes('-topmost', True)
                except: pass
            if self.floor_time > 15000:
                self.destroy(hit=False)
                return
        
        # Check collision with target
        if not hasattr(self.target, 'x') or not hasattr(self.target, 'v_x'):
            self.destroy(hit=False)
            return
            
        tx = self.target.x - self.target.v_x
        ty = self.target.y - self.target.v_y
        tw = self.target.size_w
        th = self.target.size_h
        
        if (self.x + 30 > tx and self.x + 30 < tx + tw and 
            self.y + 30 > ty and self.y + 30 < ty + th):
            self.on_hit()
            self.destroy(hit=True)
            return
            
        # Check floor
        if not self.is_dragged and not self.on_floor:
            if hasattr(self.target, 'v_height'):
                floor = self.target.v_height
                if self.y + 45 > floor: # land on floor
                    self.y = floor - 45
                    self.on_floor = True
                    self.win.geometry(f"60x60+{int(self.x)}+{int(self.y)}")
                    if getattr(self, 'on_miss', None):
                        self.on_miss()
                        self.on_miss = None # don't call it again to avoid repeated cleanup
                
        self.root.after(33, self.update_loop)
        
    def destroy(self, hit=False):
        self.active = False
        if self.win and self.win.winfo_exists():
            self.win.destroy()
        if not hit and getattr(self, 'on_miss', None):
            self.on_miss()
            
class GracideaFloor:
    def __init__(self, root, base_dir, x, y, get_pets_callback, on_consume_callback):
        self.root = root
        self.x = x
        self.y = y
        self.get_pets = get_pets_callback
        self.on_consume = on_consume_callback
        
        img_path = os.path.join(base_dir, "game_env", "ui", "gracidea.png")
        self.base_img = Image.open(img_path).convert("RGBA")
        # Resize small
        self.base_img = self.base_img.resize((30, 30), Image.Resampling.NEAREST)
        angle = random.randint(0, 360)
        self.base_img = self.base_img.rotate(angle, expand=False, resample=Image.NEAREST)
        self.tk_img = ImageTk.PhotoImage(self.base_img)
        
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes('-topmost', True)
        TRANS_COLOR = '#010101'
        self.win.config(bg=TRANS_COLOR)
        try: self.win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass
        
        self.win.geometry(f"40x40+{int(self.x-20)}+{int(self.y-30)}")
        self.canvas = tk.Canvas(self.win, width=40, height=40, bg=TRANS_COLOR, highlightthickness=0)
        self.canvas.pack()
        
        # Solo la flor, sin brillo dorado
        self.canvas.create_image(20, 20, image=self.tk_img)
        
        self.life = 60000 # 1 minute
        self.active = True
        self.update_loop()
        
    def update_loop(self):
        if not self.active: return
        if not self.win.winfo_exists(): return
        
        self.life -= 33
        if self.life % 2000 < 33:
            try: self.win.attributes('-topmost', True)
            except: pass
            
        if self.life <= 0:
            self.explode_and_destroy()
            return
            
        # Check collision with any pet EXCEPT shaymin
        for p in self.get_pets():
            if "shaymin" in p.pet_name.lower():
                continue
            if p.current_state in ['exiting', 'dragged']:
                continue
                
            px = p.x - p.v_x + p.size_w/2
            py = p.y - p.v_y + p.size_h
            
            # Simple distance
            if abs(px - (self.x - p.v_x)) < 40 and abs(py - (self.y - p.v_y)) < 40:
                self.on_consume(p)
                self.destroy()
                return
                
        self.root.after(33, self.update_loop)
        
    def explode_and_destroy(self):
        self.active = False
        if self.win and self.win.winfo_exists():
            self.canvas.delete("all")
            import time
            for i in range(1, 9):
                self.canvas.create_oval(20-i*2, 20-i*2, 20+i*2, 20+i*2, outline="#FFFFFF", width=2)
                self.canvas.update()
                time.sleep(0.02)
            self.win.destroy()
            
    def destroy(self):
        self.active = False
        if self.win and self.win.winfo_exists():
            self.win.destroy()

class ShayminMechanics:
    def cancel_shaymin_arts(self):
        if getattr(self, 'shaymin_leaf', None):
            self.shaymin_leaf.destroy()
            self.shaymin_leaf = None
            
        if hasattr(self, 'shaymin_vfx_win') and self.shaymin_vfx_win and self.shaymin_vfx_win.winfo_exists():
            self.shaymin_vfx_win.destroy()
            self.shaymin_vfx_win = None
            
        if getattr(self, 'shaymin_jump_count', 0) > 0:
            delattr(self, 'shaymin_jump_count')
            
        if self.current_state not in ['dragged', 'exiting']:
            self.current_state = 'falling'
            
    def _init_shaymin_vfx(self):
        if not hasattr(self, 'shaymin_vfx_win') or not self.shaymin_vfx_win or not self.shaymin_vfx_win.winfo_exists():
            self.shaymin_vfx_win = tk.Toplevel(self.window.master)
            self.shaymin_vfx_win.overrideredirect(True)
            self.shaymin_vfx_win.attributes('-topmost', True)
            TRANS_COLOR = '#010101'
            self.shaymin_vfx_win.config(bg=TRANS_COLOR)
            try: self.shaymin_vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
            except: pass
            self.shaymin_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
            self.shaymin_canvas = tk.Canvas(self.shaymin_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
            self.shaymin_canvas.pack()
            self.shaymin_particles = []

    def spawn_shaymin_particle(self, cx, cy, color, type_p, life, v_x, v_y):
        self._init_shaymin_vfx()
        size = 2 if type_p == 'air' else (1 if type_p == 'small_sparkle' else 4)
        if type_p == 'joy_sparkle':
            pid = self.shaymin_canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline="", tags="pt")
        else:
            pid = self.shaymin_canvas.create_oval(cx-size, cy-size, cx+size, cy+size, fill=color, outline="", tags="pt")
        self.shaymin_particles.append({'id': pid, 'vx': v_x, 'vy': v_y, 'life': life})
        if len(self.shaymin_particles) == 1:
            self._process_shaymin_particles()

    def _process_shaymin_particles(self):
        if not hasattr(self, 'shaymin_particles'): return
        if not hasattr(self, 'shaymin_vfx_win') or not self.shaymin_vfx_win or not self.shaymin_vfx_win.winfo_exists(): return
        
        alive = []
        for p in self.shaymin_particles:
            p['life'] -= 1
            if p['life'] <= 0:
                self.shaymin_canvas.delete(p['id'])
            else:
                self.shaymin_canvas.move(p['id'], p['vx'], p['vy'])
                alive.append(p)
                
        self.shaymin_particles = alive
        if self.shaymin_particles:
            self.schedule_loop(33, self._process_shaymin_particles)
        elif hasattr(self, 'shaymin_vfx_win') and self.shaymin_vfx_win:
            self.shaymin_vfx_win.destroy()
            self.shaymin_vfx_win = None

    def _fsm_shaymin_summon(self):
        if not hasattr(self, 'shaymin_leaf') or not self.shaymin_leaf:
            # We don't pass cancel_shaymin_arts anymore, so the leaf doesn't destroy itself when hitting the floor
            self.shaymin_leaf = GracideaLeaf(self.window.master, self.base_dir, self.v_width, self.v_height, self, self.trigger_shaymin_transform)
            
            lx = self.shaymin_leaf.x + 30
            ly = 50
            for _ in range(25):
                color = random.choice(["#FFFFAA", "#FFFFFF", "#FFFF00"])
                self.spawn_shaymin_particle(lx, ly, color, 'sparkle', random.randint(15, 30), random.uniform(-4, 4), random.uniform(2, 6))
            
        self.current_state = 'falling'
        self.schedule_loop(33, self.physics_loop)
        
    def trigger_shaymin_transform(self):
        self.shaymin_leaf = None
        
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        
        for _ in range(40):
            color = random.choice(["#FFFFFF", "#00FF00", "#AAFF00"])
            self.spawn_shaymin_particle(cx, cy, color, 'sparkle', random.randint(15, 30), random.uniform(-8, 8), random.uniform(-8, 8))
            
        # Change pet to shaymin sky form
        self.pet_name = "shaymin_1"
        self.pet_data["species"] = "shaymin_1"
        
        from entities.animator import DesktopPetAnimator
        anim_dir = os.path.join(self.base_dir, "game_env", "pets", "shaymin_1")
        if self.is_shiny and os.path.exists(os.path.join(anim_dir, "shiny")):
            anim_dir = os.path.join(anim_dir, "shiny")
        
        self.animator = DesktopPetAnimator(
            self.canvas, self.config.get("images", {}), 
            (self.size_w, self.size_h), (self.size_w, self.size_h), anim_dir
        )
        self.play_shiny_sound()
        
        # Start sky jump mechanic (handled by the jump function's initial cooldown)
        self.current_state = 'falling'
        self.window.after(100, self.start_shaymin_sky_jump)

    def start_shaymin_sky_jump(self):
        if self.current_state in ['dragged', 'exiting']: return
        self.current_state = 'shaymin_channeling'
        self.shaymin_jump_count = 0
        self.shaymin_jump_target = random.randint(30, 50)
        self.shaymin_jump_cooldown = 90 # 3 seconds of channeling

    def _fsm_shaymin_channeling(self):
        if getattr(self, 'shaymin_jump_cooldown', 0) > 0:
            self.shaymin_jump_cooldown -= 1
            # Fase de canalización de energía en el suelo
            self.v_x_velocity = 0
            self.v_y_velocity = 0
            floor_abs = self.v_height
            self.y = floor_abs - self.size_h
            
            for _ in range(5): # Muchas partículas para que sea muy visible
                cx = self.x - self.v_x + self.size_w/2 + random.uniform(-150, 150)
                cy = self.y - self.v_y + self.size_h/2 + random.uniform(-150, 150)
                vx = (self.x - self.v_x + self.size_w/2 - cx) / 10
                vy = (self.y - self.v_y + self.size_h/2 - cy) / 10
                self.spawn_shaymin_particle(cx, cy, random.choice(["#FFFFFF", "#DDFFDD", "#AAFFDD"]), 'air', 15, vx, vy)
                
            self.update_position()
            self.schedule_loop(33, self.physics_loop)
        else:
            self.current_state = 'shaymin_sky_jump'
            self._fsm_shaymin_sky_jump()

    def _fsm_shaymin_sky_jump(self):
        if not hasattr(self, 'shaymin_jump_count'):
            self.shaymin_jump_count = 0
            self.shaymin_jump_target = random.randint(30, 50)
            self.shaymin_jump_cooldown = 0
            
        mid_screen = self.v_y + self.v_height / 2
        
        if getattr(self, 'shaymin_jump_cooldown', 0) > 0:
            self.shaymin_jump_cooldown -= 1
            
        if getattr(self, 'shaymin_jump_cooldown', 0) <= 0:
            if self.shaymin_jump_count >= getattr(self, 'shaymin_jump_target', 30):
                self.current_state = 'falling'
                if hasattr(self, 'cancel_shaymin_arts'):
                    self.cancel_shaymin_arts()
                self.shaymin_cooldown = 108000
                self.schedule_loop(33, self.physics_loop)
                return
                
            self.shaymin_jump_count += 1
            # Cooldown mucho más corto para que salte antes de empezar a caer o justo al caer, logrando escalar
            self.shaymin_jump_cooldown = random.randint(15, 20)
            
            # Movimiento grácil, lento y largo
            dir_x = random.choice([-1, 1])
            self.v_x_velocity = dir_x * random.uniform(8.0, 15.0)
            self.is_facing_right = (dir_x == 1)
            
            # Pequeña explosión de aire en los pies
            for _ in range(8):
                cx = self.x - self.v_x + self.size_w/2 + random.uniform(-10, 10)
                cy = self.y - self.v_y + self.size_h - 10 + random.uniform(-5, 5)
                vx = random.uniform(-3, 3)
                vy = random.uniform(1, 3)
                self.spawn_shaymin_particle(cx, cy, random.choice(["#EEEEEE", "#FFFFFF"]), 'air', 10, vx, vy)
            
            if self.y > mid_screen:
                # Subiendo muy rápido hasta llegar a la mitad
                self.v_y_velocity = -18.0 - (self.shaymin_jump_count * 0.3)
            else:
                # Arriba de la mitad, sube y baja aleatoriamente
                self.v_y_velocity = random.uniform(-12.0, 12.0)
                
            # Gracídea aleatoria en el suelo cada 10 saltos
            if self.shaymin_jump_count % 10 == 0:
                floor = self.v_height
                px = random.randint(self.v_x + 50, self.v_x + self.v_width - 50)
                GracideaFloor(self.window.master, self.base_dir, px, floor, self.get_all_pets, self.trigger_gracidea_joy)
                
                # Explosión de partículas verdes (más pequeñas)
                for _ in range(15):
                    self.spawn_shaymin_particle(px - self.v_x, floor - self.v_y, "#00FF00", 'small_sparkle', random.randint(10, 20), random.uniform(-5, 5), random.uniform(-5, 0))

        # Gravity and Movement (Más grácil y lento)
        self.v_y_velocity += 1.0
        self.y += self.v_y_velocity
        self.x += getattr(self, 'v_x_velocity', 0)
        
        # Estela blanca ligeramente dorada que desaparece en medio segundo (15 frames)
        if self.shaymin_jump_count > 0:
            cx = self.x - self.v_x + self.size_w/2 + random.uniform(-10, 10)
            cy = self.y - self.v_y + self.size_h/2 + random.uniform(-10, 10)
            self.spawn_shaymin_particle(cx, cy, "#FFFFDD", 'air', 15, 0, 0)
        
        # Screen bounds for horizontal movement
        if self.x < self.v_x:
            self.x = self.v_x
            self.v_x_velocity = abs(self.v_x_velocity)
        elif self.x + self.size_w > self.v_x + self.v_width:
            self.x = self.v_x + self.v_width - self.size_w
            self.v_x_velocity = -abs(self.v_x_velocity)
            
        # Floor collision
        floor = self.v_height
        
        if self.y + self.size_h >= floor and self.v_y_velocity > 0:
            self.y = floor - self.size_h
            self.v_y_velocity = -15.0 # Bounce if it touches floor

            
        self.update_position()
        self.schedule_loop(33, self.physics_loop)
        
    def trigger_gracidea_joy(self, pet):
        if pet.current_state in ['exiting', 'dragged']: return
        
        # Limpiar estados anómalos o mecánicas previas
        if hasattr(pet, 'is_glitching'): pet.is_glitching = False
        pet.custom_crop = None
        pet.scale_mod = 1.0
        pet.darkness_mod = 0.0
        pet.nightmare_filter = False
        try: pet.window.attributes('-alpha', 1.0)
        except: pass
        try: pet.canvas.itemconfig(pet.canvas_image_id, state='normal')
        except: pass
        
        if hasattr(pet, 'animator'):
            pet.animator.custom_crop = None
            
        pet.current_state = 'joy_jump'
        pet.joy_timer = int(15000 / 33) # 15 seconds
        
    def _fsm_joy_jump(self):
        # Joy state logic for other pets
        if not hasattr(self, 'joy_timer'):
            self.current_state = 'idle'
            self.schedule_loop(33, self.physics_loop)
            return
            
        self.joy_timer -= 1
        if self.joy_timer <= 0:
            self.current_state = 'falling'
            delattr(self, 'joy_timer')
            self.schedule_loop(33, self.physics_loop)
            return
            
        if getattr(self, 'v_y_velocity', 0) == 0:
            if random.random() < 0.1:
                self.v_y_velocity = -8.0
                
        # Sparkle particles
        if self.joy_timer % 3 == 0:
            cx = self.x - self.v_x + self.size_w/2 + random.randint(-15, 15)
            cy = self.y - self.v_y + self.size_h + random.randint(-15, 15)
            self.spawn_shaymin_particle(cx, cy, "#FFFFAA", 'joy_sparkle', 15, 0, -1.0)
            
        self.v_y_velocity += 1.5
        self.y += self.v_y_velocity
        
        floor = getattr(self, 'floor_y', getattr(self, 'default_floor_y', self.v_y + self.v_height - self.size_h))
        if self.y >= floor and self.v_y_velocity > 0:
            self.y = floor
            self.v_y_velocity = 0
            
        self.update_position()
        self.schedule_loop(33, self.physics_loop)
