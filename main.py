import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import sys
import random
import math
import time
import uuid 

# --- SUPRESIÓN ESTRICTA DE LA TERMINAL DE PYGAME ---
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

from PIL import Image, ImageTk, ImageOps

# --- GESTOR DE DATOS (SAVE MANAGER) ---
class SaveManager:
    def __init__(self, save_file="save_data.json"):
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        self.save_file = os.path.join(base_dir, save_file)
        
        self.default_data = {
            "inventory": [],
            "active_pets": [] 
        }
        self.data = self.load_save()

    def load_save(self):
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    if "pc_inventory" in data:
                        new_inv = []
                        for sp in data["pc_inventory"]:
                            new_inv.append({"id": str(uuid.uuid4()), "species": sp, "level": 1, "xp": 0, "is_shiny": False, "last_evolution_level": 1, "everstone": False})
                        data["inventory"] = new_inv
                        del data["pc_inventory"]
                        data["active_pets"] = [] 
                    
                    for p in data.get("inventory", []):
                        if "last_evolution_level" not in p:
                            p["last_evolution_level"] = p["level"]
                            
                    if "active_pets" not in data: data["active_pets"] = []
                    return data
            except json.JSONDecodeError:
                messagebox.showerror("Error Crítico", "save_data.json corrupto. Creando nueva partida.")
        
        self.save_data(self.default_data)
        return self.default_data

    def save_data(self, data_override=None):
        if data_override:
            self.data = data_override
        with open(self.save_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

    def reset_save(self, starter_species):
        is_shiny_roll = random.randint(1, 100) == 1
        self.data = {
            "inventory": [{"id": str(uuid.uuid4()), "species": starter_species, "level": 1, "xp": 0, "is_shiny": is_shiny_roll, "last_evolution_level": 1, "everstone": False}],
            "active_pets": []
        }
        self.save_data()

# --- CONFIGURACIÓN DPI DE WINDOWS ---
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try: ctypes.windll.user32.SetProcessDPIAware()
    except Exception: pass

# --- MOTOR DE ANIMACIÓN ---
class DesktopPetAnimator:
    def __init__(self, canvas_widget, config_img, size_idle, size_walk, pet_dir):
        self.canvas = canvas_widget
        self.current_frame_index = 0
        self.last_state = None
        self.tk_image_ref = None
        self.last_frame_time = time.time()

        self.invert_x_axis = config_img.get("invert_x_axis", False)
        self.idle_is_animated = config_img.get("idle_is_animated", True)
        self.directional_walk = config_img.get("directional_walk", True)
        self.fix_idle_direction = config_img.get("fix_idle_direction", True)

        scaling_filter = Image.Resampling.NEAREST 

        def clean_alpha(image):
            img = image.convert("RGBA")
            r, g, b, a = img.split()
            a = a.point(lambda p: 255 if p > 127 else 0) 
            return Image.merge("RGBA", (r, g, b, a))

        def load_frame(filename, size):
            path = os.path.join(pet_dir, filename)
            return clean_alpha(Image.open(path)).resize(size, scaling_filter)

        try:
            self.frames_idle = []
            if self.idle_is_animated:
                pref = config_img.get("idle_prefix", "idle_")
                suf = config_img.get("idle_suffix", ".png")
                for i in range(config_img.get("idle_frames", 4)):
                    self.frames_idle.append(load_frame(f"{pref}{i}{suf}", size_idle))
            
            suf = config_img.get("walk_suffix", ".png")
            if self.directional_walk:
                self.frames_walk_right = []
                pref_r = config_img.get("walk_right_prefix", "walk_r_")
                for i in range(config_img.get("walk_right_frames", 4)):
                    self.frames_walk_right.append(load_frame(f"{pref_r}{i}{suf}", size_walk))

                self.frames_walk_left = []
                pref_l = config_img.get("walk_left_prefix", "walk_l_")
                for i in range(config_img.get("walk_left_frames", 4)):
                    self.frames_walk_left.append(load_frame(f"{pref_l}{i}{suf}", size_walk))
                
        except FileNotFoundError as e:
            print(f"Error cargando assets: {e}")
            sys.exit(1)

    def update_animation(self, state, facing_right, canvas_image_id, animate_idle, fps_ms, blend_factor=0.0):
        if state == 'exiting': return

        current_time = time.time()
        elapsed_time_ms = (current_time - self.last_frame_time) * 1000
        state_changed = state != self.last_state

        if not state_changed and elapsed_time_ms < fps_ms:
            return 

        if state_changed:
            self.current_frame_index = 0
            self.last_state = state

        self.last_frame_time = current_time
        disable_mirror = False
        raw_image = None  

        render_state = 'idle' if state in ['falling', 'evolving_start', 'evolving_finish'] else state

        if render_state == 'walking':
            if self.directional_walk:
                disable_mirror = True
                active_matrix = self.frames_walk_right if facing_right else self.frames_walk_left
                if self.current_frame_index >= len(active_matrix): self.current_frame_index = 0
                
                raw_image = active_matrix[self.current_frame_index]
                self.current_frame_index = (self.current_frame_index + 1) % len(active_matrix)
            
        elif render_state == 'idle':
            if self.idle_is_animated:
                if self.current_frame_index >= len(self.frames_idle): self.current_frame_index = 0
                
                raw_image = self.frames_idle[self.current_frame_index]
                self.current_frame_index = (self.current_frame_index + 1) % len(self.frames_idle)

        if raw_image is None: raw_image = self.frames_idle[0]

        if disable_mirror:
            processed_image = raw_image
        else:
            effective_dir = True if (render_state == 'idle' and self.fix_idle_direction) else facing_right
            should_mirror = effective_dir if self.invert_x_axis else (not effective_dir)
            processed_image = ImageOps.mirror(raw_image) if should_mirror else raw_image

        if blend_factor > 0.0:
            white_layer = Image.new("RGBA", processed_image.size, (255, 255, 255, 255))
            white_layer.putalpha(processed_image.split()[3]) 
            processed_image = Image.blend(processed_image, white_layer, blend_factor)

        self.tk_image_ref = ImageTk.PhotoImage(processed_image)
        self.canvas.itemconfig(canvas_image_id, image=self.tk_image_ref)

# --- ENTIDAD FÍSICA ---
class DesktopPet:
    def __init__(self, parent_root, pet_data, is_wild, on_remove_callback, on_catch_callback, on_open_pc_callback, on_evolve_callback, spawn_coords=None, is_mid_evo=False, evo_channel=None):
        self.pet_data = pet_data
        self.pet_name = pet_data["species"]
        self.is_wild = is_wild
        self.is_egg = self.pet_data.get("is_egg", False)
        
        self.on_remove = on_remove_callback
        self.on_catch = on_catch_callback
        self.on_open_pc = on_open_pc_callback
        self.on_evolve = on_evolve_callback
        
        self.base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        self.pet_dir = os.path.join(self.base_dir, "game_env", "pets", self.pet_name)
        
        self.config = self.load_config()
        
        self.window = tk.Toplevel(parent_root)
        wild_tag = "(SALVAJE)" if is_wild else f"Lv.{self.pet_data['level']}"
        if self.is_egg: wild_tag = "(HUEVO)"
        self.window.title(f"{self.config.get('display_name', 'Pokemon')} {wild_tag}")
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)

        CHROMA_KEY = '#FF00FF'
        self.window.config(bg=CHROMA_KEY)
        try: self.window.wm_attributes('-transparentcolor', CHROMA_KEY)
        except tk.TclError: pass 

        multiplicador_tamaño = 1.55
        multiplicador_velocidad = 2
        physics = self.config.get("physics", {})
        
        self.size_w = int(physics.get("size", 64) * multiplicador_tamaño)
        self.size_h = int(physics.get("size", 64) * multiplicador_tamaño)
        
        base_speed = physics.get("movement_speed", 2)
        self.speed = max(1, int(base_speed * multiplicador_velocidad))
        self.is_flying = physics.get("is_flying", False)
        
        # --- NÚCLEO GEOMÉTRICO (CONTROL DE GRAVEDAD ESTRICTO) ---
        if self.is_egg:
            self.is_flying = False  # Supresión genética: Un huevo no puede volar
            
            # Un Pokémon normal usa offset -6, pero su lienzo tiene ~16px de aire transparente debajo.
            # Como al huevo le hemos recortado la transparencia a cero, un offset de 10 
            # alineará la base de la cáscara matemáticamente con los pies de un Pokémon terrestre.
            self.offset_y = 0      
            
        elif self.is_flying: 
            self.offset_y = 32
        else: 
            self.offset_y = -6 
            
        self.fly_amplitude = 0
        
        self.canvas = tk.Canvas(self.window, width=self.size_w, height=self.size_h, bg=CHROMA_KEY, highlightthickness=0)
        self.canvas.pack()
        self.canvas_image_id = self.canvas.create_image(self.size_w//2, self.size_h//2, anchor=tk.CENTER)
        
        self.is_shiny = self.pet_data.get("is_shiny", False)
        animator_dir = os.path.join(self.pet_dir, "shiny") if self.is_shiny else self.pet_dir
        
        if self.is_shiny and not os.path.exists(animator_dir):
            print(f"[!] Faltan assets shiny para {self.pet_name}. Usando normales.")
            animator_dir = self.pet_dir

        self.animator = DesktopPetAnimator(self.canvas, self.config.get("images", {}), (self.size_w, self.size_h), (self.size_w, self.size_h), animator_dir)

        user32 = ctypes.windll.user32
        self.v_x = user32.GetSystemMetrics(76) 
        self.v_y = user32.GetSystemMetrics(77)
        self.v_width = user32.GetSystemMetrics(78)
        self.v_height = user32.GetSystemMetrics(79)

        self.floor_y = (self.v_y + self.v_height) - self.size_h - self.offset_y
        
        if self.is_egg:
            self.canvas.coords(self.canvas_image_id, self.size_w // 2, self.size_h)
            self.canvas.itemconfig(self.canvas_image_id, anchor=tk.S)
            
            egg_path = os.path.join(self.base_dir, "game_env", "ui", "egg.png")
            try:
                raw_egg = Image.open(egg_path).convert("RGBA")
                r, g, b, a = raw_egg.split()
                a = a.point(lambda p: 255 if p > 127 else 0)
                raw_egg.putalpha(a)
                
                # RECORTE ESTRICTO POR CANAL ALFA
                bbox = a.getbbox()
                if bbox:
                    raw_egg = raw_egg.crop(bbox)
                
                # MOTOR DE ESCALADO FORZADO (Abandono de thumbnail en favor de resize estructurado)
                target_w = max(1, int(self.size_w * 0.35)) # Ajusta este porcentaje si deseas más o menos escala.
                target_h = max(1, int(self.size_h * 0.35))
                
                aspect = raw_egg.width / raw_egg.height
                if aspect > 1:
                    new_w = target_w
                    new_h = int(target_w / aspect)
                else:
                    new_h = target_h
                    new_w = int(target_h * aspect)
                    
                # Resize obliga a expandir la matriz si el recorte es pequeño.
                self.egg_base_img = raw_egg.resize((new_w, new_h), Image.Resampling.NEAREST)
                self.egg_tk = ImageTk.PhotoImage(self.egg_base_img)
                self.canvas.itemconfig(self.canvas_image_id, image=self.egg_tk)
                
            except Exception as e:
                print(f"[!] Error crítico cargando huevo desde '{egg_path}': {e}")
                
            hatch_time = random.randint(900000, 1800000) 
            self.window.after(hatch_time, self.hatch_egg)
            self.window.after(random.randint(45000, 75000), self.egg_wiggle_loop)
        
        if spawn_coords:
            self.x = spawn_coords[0]
            self.y = self.floor_y 
            
            if is_mid_evo:
                self.evo_channel = evo_channel
                self.current_state = 'evolving_finish'
                self.finish_evolution_vfx(step=0)
            else:
                self.current_state = 'egg_idle' if self.is_egg else 'idle'
        else:
            self.x = random.randint(self.v_x, self.v_x + self.v_width - self.size_w)
            
            if self.is_egg:
                self.y = self.v_y - self.size_h
                self.current_state = 'falling_egg'
                self.canvas.itemconfig(self.canvas_image_id, state='hidden')
                self.animate_egg_spawn(step=0)
            elif self.is_wild:
                self.y = self.floor_y
                self.current_state = 'spawning_wild'
                self.canvas.itemconfig(self.canvas_image_id, state='hidden')
                self.animate_wild_spawn(step=0)
            else:
                self.y = self.v_y - self.size_h 
                self.current_state = 'falling_pokeball'
                self.canvas.itemconfig(self.canvas_image_id, state='hidden')
                self.animate_owned_spawn(step=0)

        self.window.geometry(f"{self.size_w}x{self.size_h}+{self.x}+{self.y}")
        self.is_facing_right = random.choice([True, False])
        self.frame_rate_active = self.config.get("images", {}).get("frame_rate_active", 120)
        self.frame_rate_idle = self.config.get("images", {}).get("frame_rate_idle", 200)

        self.canvas.bind("<ButtonRelease-3>", self.handle_right_click)
        self.canvas.bind("<Double-Button-1>", self.handle_double_click)
        
        if self.is_wild and not self.is_egg:
            despawn_time = random.randint(120000, 300000) 
            self.despawn_timer = self.window.after(despawn_time, self.start_wild_despawn)
            
        self.keep_on_top()
        self.animate_loop()
        self.physics_loop()

    def egg_wiggle_loop(self):
        if not getattr(self, 'is_egg', False) or self.current_state == 'exiting': return
        
        if self.current_state == 'egg_idle':
            self.current_state = 'egg_wiggle'
            self.animate_egg_wiggle(step=0)
        else:
            self.window.after(random.randint(45000, 75000), self.egg_wiggle_loop)

    def animate_egg_wiggle(self, step=0):
        if self.current_state != 'egg_wiggle': return
        
        frames = [15, -15, 10, -10, 5, -5, 0]
        
        if step >= len(frames):
            self.current_state = 'egg_idle'
            if getattr(self, 'egg_tk', None):
                self.canvas.itemconfig(self.canvas_image_id, image=self.egg_tk)
            self.window.after(random.randint(45000, 75000), self.egg_wiggle_loop)
            return
            
        angle = frames[step]
        rotated = self.egg_base_img.rotate(angle, expand=True, resample=Image.NEAREST)
        self.egg_tk_wiggle = ImageTk.PhotoImage(rotated)
        self.canvas.itemconfig(self.canvas_image_id, image=self.egg_tk_wiggle)
        
        self.window.after(80, lambda: self.animate_egg_wiggle(step + 1))

    def play_shiny_sound(self):
        if not self.is_shiny: return
        try:
            snd_path = os.path.join(self.base_dir, "game_env", "sounds", "shiny.wav")
            if os.path.exists(snd_path):
                import pygame
                s = pygame.mixer.Sound(snd_path)
                s.set_volume(0.05)
                s.play()
        except: pass

    def start_evolution_vfx(self, target_species, step=0):
        self.current_state = 'evolving_start'
        
        if step == 0:
            try:
                snd_path = os.path.join(self.base_dir, "game_env", "sounds", "evolving.wav")
                if os.path.exists(snd_path):
                    import pygame
                    s = pygame.mixer.Sound(snd_path)
                    s.set_volume(0.03)
                    self.evo_channel = s.play()
            except: pass

        if step <= 60:
            self.evo_blend = step / 60.0
        elif step <= 100:
            self.evo_blend = 1.0
        else:
            self.on_evolve(self, target_species, is_mid_evo=True, evo_channel=getattr(self, 'evo_channel', None))
            return

        self.window.after(50, lambda: self.start_evolution_vfx(target_species, step+1))

    def finish_evolution_vfx(self, step=0):
        if step == 0 and getattr(self, 'evo_channel', None):
            try: self.evo_channel.fadeout(2000)
            except: pass

        if step == 40:
            try:
                snd_path = os.path.join(self.base_dir, "game_env", "sounds", "evolved.wav")
                if os.path.exists(snd_path):
                    import pygame
                    s = pygame.mixer.Sound(snd_path)
                    s.set_volume(0.03)
                    s.play()
            except: pass
            
            self.play_shiny_sound()

        if step <= 40:
            self.evo_blend = 1.0
        elif step <= 100:
            progress = (step - 40) / 60.0
            self.evo_blend = 1.0 - progress
        else:
            self.evo_blend = 0.0
            self.current_state = 'idle'
            return

        self.window.after(50, lambda: self.finish_evolution_vfx(step+1))

    def hatch_egg(self):
        if self.current_state == 'exiting': return
        self.start_evolution_vfx(self.pet_data["species"], step=0)

    def gain_xp(self, amount):
        if self.is_egg or self.pet_data["level"] >= 100:
            self.pet_data["xp"] = 0
            return

        self.pet_data["xp"] += amount
        xp_needed = self.pet_data["level"] * 30 
        
        leveled_up = False
        while self.pet_data["xp"] >= xp_needed:
            self.pet_data["xp"] -= xp_needed
            self.pet_data["level"] += 1
            
            if self.pet_data["level"] >= 100:
                self.pet_data["level"] = 100
                self.pet_data["xp"] = 0 
                leveled_up = True
                break
                
            xp_needed = self.pet_data["level"] * 30
            leveled_up = True
            
        if leveled_up:
            self.window.title(f"{self.config.get('display_name', 'Pokemon')} Lv.{self.pet_data['level']}")
            self.show_level_up_vfx()
            self.check_evolution()

    def show_level_up_vfx(self):
        txt = self.canvas.create_text(self.size_w//2, 15, text="LEVEL UP!", fill="#F1C40F", font=("Segoe UI", 10, "bold"), tags="vfx_lvl")
        def float_up(step):
            if step < 20 and self.current_state != 'exiting':
                self.canvas.move(txt, 0, -1)
                self.window.after(50, lambda: float_up(step+1))
            else:
                self.canvas.delete(txt)
        float_up(0)

    def check_evolution(self):
        if self.pet_data.get("everstone", False): return

        rpg = self.config.get("rpg_data", {})
        evo_level = rpg.get("evolution_level", 99)
        evolves_to = rpg.get("evolves_to", [])

        last_evo = self.pet_data.get("last_evolution_level", 1)
        
        if self.pet_data["level"] >= evo_level and (self.pet_data["level"] - last_evo) >= 5 and evolves_to and evolves_to[0] != "none":
            target_species = random.choice(evolves_to)
            self.start_evolution_vfx(target_species, step=0)

    def keep_on_top(self):
        if self.current_state != 'exiting':
            try: self.window.attributes('-topmost', True)
            except: pass
            self.window.after(2000, self.keep_on_top)

    def load_config(self):
        try:
            with open(os.path.join(self.pet_dir, "config.json"), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error crítico en {self.pet_dir}: {e}")
            sys.exit(1)

    def animate_egg_spawn(self, step):
        if self.current_state != 'falling_egg':
            return 

        if not getattr(self, 'egg_base_img', None):
            self.canvas.itemconfig(self.canvas_image_id, state='normal')
            self.current_state = 'egg_idle'
            return

        w, h = self.size_w, self.size_h
        rotation = step * -15 
        rotated = self.egg_base_img.rotate(rotation, expand=True, resample=Image.NEAREST)
        
        self.egg_tk_falling = ImageTk.PhotoImage(rotated)
        self.canvas.delete("spawn_egg")
        
        self.canvas.create_image(w//2, h, image=self.egg_tk_falling, anchor=tk.S, tags="spawn_egg")
        
        self.window.after(30, lambda: self.animate_egg_spawn(step + 1))

    def animate_vfx(self, action_type, step=0):
        frames = 15 
        if step == 0:
            self.current_state = 'exiting' 
            self.canvas.delete(self.canvas_image_id) 
            
            try:
                snd_file = "return.wav" if action_type == "return" else "catch.wav"
                snd_path = os.path.join(self.base_dir, "game_env", "sounds", snd_file)
                if os.path.exists(snd_path):
                    import pygame
                    self.current_sound = pygame.mixer.Sound(snd_path)
                    self.current_sound.set_volume(0.01) 
                    self.current_sound.play()
            except Exception: pass 

            try:
                pb_dir = os.path.join(self.base_dir, "game_env", "ui")
                available_pbs = [f for f in os.listdir(pb_dir) if f.startswith("pokeball") and f.endswith(".png")]
                pb_file = random.choice(available_pbs) if available_pbs else "pokeball.png"
                
                raw_img = Image.open(os.path.join(pb_dir, pb_file)).convert("RGBA")
                r, g, b, a = raw_img.split()
                a = a.point(lambda p: 255 if p > 127 else 0) 
                self.pb_base_img = Image.merge("RGBA", (r, g, b, a))
            except:
                self.pb_base_img = None

        if not getattr(self, 'pb_base_img', None):
            self.window.after(300, self.window.destroy)
            return

        if step <= frames:
            progress = step / frames 
            w_width, w_height = self.size_w, self.size_h
            center_x, center_y = w_width // 2, w_height // 2

            if action_type == "catch":
                cx, cy = center_x, center_y
                size = max(4, int(64 * progress))
                rotation = 360 * progress
            else:
                arc_height = 25
                parabola = -arc_height * (1 - (2 * progress - 1)**2)
                start_x, start_y = center_x, center_y
                end_x, end_y = 0, w_height
                cx = start_x + (end_x - start_x) * progress
                cy = start_y + (end_y - start_y) * progress + parabola
                size = max(4, int(64 * (1 - progress)))
                rotation = -360 * progress

            rotated = self.pb_base_img.rotate(rotation, expand=False, resample=Image.NEAREST)
            resized = rotated.resize((size, size), Image.Resampling.NEAREST)
            
            self.vfx_img = ImageTk.PhotoImage(resized)
            self.canvas.delete("vfx")
            self.canvas.create_image(cx, cy, image=self.vfx_img, anchor=tk.CENTER, tags="vfx")
            
            self.window.after(30, lambda: self.animate_vfx(action_type, step + 1))
        else:
            self.window.after(100, self.window.destroy)

    def start_wild_despawn(self):
        if self.current_state in ['exiting', 'evolving_start', 'evolving_finish', 'despawning_wild']: return
        self.current_state = 'despawning_wild'
        self.animate_wild_despawn(step=0)

    def animate_wild_despawn(self, step):
        frames_up = 15
        pause = 10
        frames_down = 15
        
        if step == 0:
            try:
                asset_name = "cloud.png" if self.is_flying else "tallGrass.png"
                vfx_path = os.path.join(self.base_dir, "game_env", "ui", asset_name)
                self.spawn_vfx_raw = Image.open(vfx_path).convert("RGBA")
            except Exception:
                self.spawn_vfx_raw = None

        if not getattr(self, 'spawn_vfx_raw', None):
            self.on_remove(self)
            return

        w, h = self.size_w, self.size_h
        total_steps = frames_up + pause + frames_down
        
        if step <= frames_up:
            progress = step / frames_up
            offset_y = h - int((h/1.5) * progress) 
        elif step <= frames_up + pause:
            offset_y = h - int(h/1.5)
            if step == frames_up + (pause // 2):
                self.canvas.itemconfig(self.canvas_image_id, state='hidden')
        elif step <= total_steps:
            progress = (step - frames_up - pause) / frames_down
            offset_y = (h - int(h/1.5)) + int((h/1.5) * progress) 
        else:
            self.canvas.delete("spawn_vfx")
            self.on_remove(self)
            return

        resized = self.spawn_vfx_raw.resize((w, int(h/1.5)), Image.Resampling.NEAREST)
        self.vfx_tk = ImageTk.PhotoImage(resized)
        self.canvas.delete("spawn_vfx")
        self.canvas.create_image(w//2, offset_y, image=self.vfx_tk, anchor=tk.N, tags="spawn_vfx")
        
        self.window.after(30, lambda: self.animate_wild_despawn(step + 1))

    def animate_wild_spawn(self, step):
        frames_up = 15
        pause = 10
        frames_down = 15
        
        if step == 0:
            try:
                asset_name = "cloud.png" if self.is_flying else "tallGrass.png"
                vfx_path = os.path.join(self.base_dir, "game_env", "ui", asset_name)
                self.spawn_vfx_raw = Image.open(vfx_path).convert("RGBA")
            except Exception:
                self.spawn_vfx_raw = None

        if not getattr(self, 'spawn_vfx_raw', None):
            self.canvas.itemconfig(self.canvas_image_id, state='normal')
            self.current_state = 'idle'
            self.play_shiny_sound()
            return

        w, h = self.size_w, self.size_h
        total_steps = frames_up + pause + frames_down
        
        if step <= frames_up:
            progress = step / frames_up
            offset_y = h - int((h/1.5) * progress) 
        elif step <= frames_up + pause:
            offset_y = h - int(h/1.5)
            if step == frames_up + (pause // 2):
                self.canvas.itemconfig(self.canvas_image_id, state='normal')
                self.canvas.tag_lower(self.canvas_image_id, "spawn_vfx")
                self.play_shiny_sound()
                
        elif step <= total_steps:
            progress = (step - frames_up - pause) / frames_down
            offset_y = (h - int(h/1.5)) + int((h/1.5) * progress) 
        else:
            self.canvas.delete("spawn_vfx")
            self.current_state = 'idle'
            return

        resized = self.spawn_vfx_raw.resize((w, int(h/1.5)), Image.Resampling.NEAREST)
        self.vfx_tk = ImageTk.PhotoImage(resized)
        self.canvas.delete("spawn_vfx")
        self.canvas.create_image(w//2, offset_y, image=self.vfx_tk, anchor=tk.N, tags="spawn_vfx")
        
        self.window.after(30, lambda: self.animate_wild_spawn(step + 1))

    def animate_owned_spawn(self, step):
        if self.current_state != 'falling_pokeball':
            return 

        if step == 0:
            try:
                pb_dir = os.path.join(self.base_dir, "game_env", "ui")
                available_pbs = [f for f in os.listdir(pb_dir) if f.startswith("pokeball") and f.endswith(".png")]
                pb_file = random.choice(available_pbs) if available_pbs else "pokeball.png"
                
                raw_img = Image.open(os.path.join(pb_dir, pb_file)).convert("RGBA")
                r, g, b, a = raw_img.split()
                a = a.point(lambda p: 255 if p > 127 else 0) 
                self.pb_raw = Image.merge("RGBA", (r, g, b, a))
            except:
                self.pb_raw = None

        if not getattr(self, 'pb_raw', None):
            self.canvas.itemconfig(self.canvas_image_id, state='normal')
            self.current_state = 'falling'
            return

        w, h = self.size_w, self.size_h
        rotation = step * -15 
        rotated = self.pb_raw.rotate(rotation, expand=False, resample=Image.NEAREST)
        target_w = max(1, w//2)
        target_h = max(1, h//2)
        resized = rotated.resize((target_w, target_h), Image.Resampling.NEAREST)
        
        self.pb_tk = ImageTk.PhotoImage(resized)
        self.canvas.delete("spawn_pb")
        self.canvas.create_image(w//2, h//2, image=self.pb_tk, anchor=tk.CENTER, tags="spawn_pb")
        
        self.window.after(30, lambda: self.animate_owned_spawn(step + 1))

    def handle_right_click(self, event):
        if self.is_egg: return
        if self.current_state not in ['exiting', 'evolving_start', 'evolving_finish', 'despawning_wild']:
            if self.is_wild:
                self.on_catch(self)
                self.animate_vfx("catch")
            else:
                self.on_remove(self)
                self.animate_vfx("return")

    def handle_double_click(self, event):
        if self.current_state not in ['exiting', 'evolving_start', 'evolving_finish', 'despawning_wild']:
            if getattr(self, 'is_egg', False):
                self.on_open_pc(None) 
            else:
                self.on_open_pc(self.pet_data)

    def update_position(self):
        self.window.geometry(f"+{int(self.x)}+{int(self.y)}")

    def animate_loop(self):
        if self.current_state == 'exiting': return 
        
        blend = getattr(self, 'evo_blend', 0.0)
        
        if self.is_egg:
            if blend > 0.0 and getattr(self, 'egg_base_img', None):
                white_layer = Image.new("RGBA", self.egg_base_img.size, (255, 255, 255, 255))
                white_layer.putalpha(self.egg_base_img.split()[3]) 
                blended = Image.blend(self.egg_base_img, white_layer, blend)
                self.egg_tk = ImageTk.PhotoImage(blended)
                self.canvas.itemconfig(self.canvas_image_id, image=self.egg_tk)
            elif getattr(self, 'egg_tk', None) and self.current_state != 'egg_wiggle':
                self.canvas.itemconfig(self.canvas_image_id, image=self.egg_tk)
        else:
            target_ms = self.frame_rate_active if self.current_state in ['walking', 'falling'] else self.frame_rate_idle
            self.animator.update_animation(self.current_state, self.is_facing_right, self.canvas_image_id, True, target_ms, blend_factor=blend)
            
        self.window.after(16, self.animate_loop)

    def physics_loop(self):
        if self.current_state in ['exiting', 'egg_idle', 'egg_wiggle']: return
        
        if self.current_state in ['evolving_start', 'evolving_finish', 'despawning_wild']:
            self.window.after(50, self.physics_loop)
            return
        
        if self.current_state == 'spawning_wild':
            self.window.after(50, self.physics_loop)
            return
            
        if self.current_state == 'falling_egg':
            self.y += 10
            if self.y >= self.floor_y:
                self.y = self.floor_y
                self.current_state = 'egg_idle'
                self.canvas.delete("spawn_egg")
                self.canvas.itemconfig(self.canvas_image_id, state='normal')
            self.update_position()
            self.window.after(20, self.physics_loop)
            return

        if self.current_state == 'falling_pokeball':
            self.y += 10
            if self.y >= self.floor_y:
                self.y = self.floor_y
                self.current_state = 'idle'
                self.canvas.delete("spawn_pb")
                self.canvas.itemconfig(self.canvas_image_id, state='normal')
                
                self.play_shiny_sound()
                
                try:
                    snd_path = os.path.join(self.base_dir, "game_env", "sounds", "return.wav")
                    if os.path.exists(snd_path):
                        import pygame
                        s = pygame.mixer.Sound(snd_path)
                        s.set_volume(0.01)
                        s.play()
                except: pass
            self.update_position()
            self.window.after(20, self.physics_loop)
            return

        if self.current_state == 'falling':
            self.y += 10
            if self.y >= self.floor_y:
                self.y = self.floor_y
                self.current_state = 'idle'
            self.update_position()
            self.window.after(20, self.physics_loop)
            return
            
        action_chance = random.randint(1, 100)
        
        if self.current_state == 'idle':
            if action_chance <= 5: 
                self.current_state = 'walking'
                self.is_facing_right = random.choice([True, False])
        elif self.current_state == 'walking':
            if action_chance <= 5: 
                self.current_state = 'idle'
            else:
                self.x += self.speed if self.is_facing_right else -self.speed
                if self.x <= self.v_x:
                    self.x = self.v_x
                    self.is_facing_right = True
                elif self.x >= (self.v_x + self.v_width) - self.size_w:
                    self.x = (self.v_x + self.v_width) - self.size_w
                    self.is_facing_right = False
        
        if self.is_flying and self.current_state != 'falling':
            self.fly_amplitude += 0.2
            onda = math.sin(self.fly_amplitude) * 10
            self.y = self.floor_y + onda
            
        self.update_position()
        self.window.after(50, self.physics_loop)

# --- UI: SELECTOR DE INICIALES ---
class StarterSelectionWindow:
    def __init__(self, parent, pets_dir, on_select_callback):
        self.window = tk.Toplevel(parent)
        self.window.title("Elige a tu compañero inicial")
        
        self.window.geometry("340x840") 
        self.window.config(bg="#ECF0F1")
        self.window.attributes('-topmost', True)
        self.window.grab_set() 
        self.window.resizable(False, False)

        tk.Label(self.window, text="Selecciona un Pokémon para reiniciar el sistema:", font=("Segoe UI", 10, "bold"), bg="#ECF0F1").pack(pady=10)

        canvas = tk.Canvas(self.window, bg="#ECF0F1", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg="#ECF0F1")

        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=320) 
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=5)
        scrollbar.pack(side="right", fill="y")

        self.btn_images = [] 
        installed_pets = [d for d in os.listdir(pets_dir) if os.path.isdir(os.path.join(pets_dir, d))]
        
        def create_icon_btn(container, species):
            if species not in installed_pets: return None
            try:
                cfg_path = os.path.join(pets_dir, species, "config.json")
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                
                img_cfg = cfg.get("images", {})
                idle_prefix = img_cfg.get("idle_prefix", "idle_")
                idle_suffix = img_cfg.get("idle_suffix", ".png")
                
                img_path = os.path.join(pets_dir, species, f"{idle_prefix}0{idle_suffix}")
                raw_img = Image.open(img_path).convert("RGBA")
                
                r, g, b, a = raw_img.split()
                a = a.point(lambda p: 255 if p > 127 else 0)
                clean_img = Image.merge("RGBA", (r, g, b, a)).resize((48, 48), Image.Resampling.NEAREST)
                
                tk_img = ImageTk.PhotoImage(clean_img)
                self.btn_images.append(tk_img) 

                btn = tk.Button(container, image=tk_img, bg="white", relief="ridge", bd=2, width=54, height=54,
                                command=lambda s=species: self.commit_selection(s, on_select_callback))
                return btn
            except Exception as e:
                print(f"[!] Imposible generar icono para {species}: {e}")
                return None

        special_frame = tk.Frame(self.scrollable_frame, bg="#ECF0F1")
        special_frame.pack(pady=(5, 15))

        pika_btn = create_icon_btn(special_frame, "pikachu")
        if pika_btn: pika_btn.pack(side=tk.LEFT, padx=15)
        
        eevee_btn = create_icon_btn(special_frame, "eevee")
        if eevee_btn: eevee_btn.pack(side=tk.LEFT, padx=15)

        grid_frame = tk.Frame(self.scrollable_frame, bg="#ECF0F1")
        grid_frame.pack()

        generations = [
            ("bulbasaur", "charmander", "squirtle"),     
            ("chikorita", "cyndaquil", "totodile"),      
            ("treecko", "torchic", "mudkip"),            
            ("turtwig", "chimchar", "piplup"),           
            ("snivy", "tepig", "oshawott"),              
            ("chespin", "fennekin", "froakie"),          
            ("rowlet", "litten", "popplio"),             
            ("grookey", "scorbunny", "sobble"),          
            ("sprigatito", "fuecoco", "quaxly")          
        ]

        found_any = False
        for r_idx, gen in enumerate(generations):
            for c_idx, species in enumerate(gen):
                btn = create_icon_btn(grid_frame, species)
                if btn:
                    found_any = True
                    btn.grid(row=r_idx, column=c_idx, padx=12, pady=8)

        if not found_any and not pika_btn and not eevee_btn:
            tk.Label(self.scrollable_frame, text="No tienes iniciales instalados en game_env/pets/", fg="red", bg="#ECF0F1").pack()

        self.window.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def commit_selection(self, species, callback):
        self.window.destroy()
        callback(species)

# --- CONTROLADOR CENTRAL DEL JUEGO ---
class GameController:
    def __init__(self):
        self.save_mgr = SaveManager()
        self.active_instances = [] 
        self.wild_instances = []
        
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        self.pets_directory = os.path.join(base_dir, "game_env", "pets")
        
        self.root = tk.Tk()
        self.root.title("Bill's PC")
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        
        w, h = 280, 115 
        screen_w = self.root.winfo_screenwidth()
        self.root.geometry(f"{w}x{h}+{screen_w - w - 20}+20")

        bg_main = "#ECF0F1"       
        bg_header = "#2C3E50"     
        fg_header = "#FFFFFF"     
        
        self.root.config(bg=bg_header)

        header_frame = tk.Frame(self.root, bg=bg_header, height=25)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False) 
        
        tk.Label(header_frame, text="Bill's PC", font=("Segoe UI", 9, "bold"), bg=bg_header, fg=fg_header).pack(side=tk.LEFT, padx=10)
        
        btn_power = tk.Button(header_frame, text="X", font=("Segoe UI", 8, "bold"), bg="#C0392B", fg="white", bd=0, width=3, command=self.exit_game)
        btn_power.pack(side=tk.RIGHT, padx=(0,0))
        
        btn_hide = tk.Button(header_frame, text="—", font=("Segoe UI", 8, "bold"), bg="#7F8C8D", fg="white", bd=0, width=3, command=self.hide_pc_ui)
        btn_hide.pack(side=tk.RIGHT, padx=(0,2))

        content_frame = tk.Frame(self.root, bg=bg_main)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        top_row = tk.Frame(content_frame, bg=bg_main)
        top_row.pack(fill=tk.X, padx=10, pady=(8, 4))
        
        self.combo_var = tk.StringVar()
        self.combo = ttk.Combobox(top_row, textvariable=self.combo_var, state="readonly", justify="center")
        self.combo.pack(fill=tk.X, expand=True)

        mid_row = tk.Frame(content_frame, bg=bg_main)
        mid_row.pack(fill=tk.X, padx=10, pady=(0, 4))
        self.everstone_var = tk.BooleanVar()
        self.chk_everstone = tk.Checkbutton(mid_row, text="Everstone", font=("Segoe UI", 8), variable=self.everstone_var, bg=bg_main, command=self.on_everstone_toggle)
        self.chk_everstone.pack(anchor=tk.CENTER)

        bottom_row = tk.Frame(content_frame, bg=bg_main)
        bottom_row.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        btn_spawn = tk.Button(bottom_row, text="Spawn", font=("Segoe UI", 8, "bold"), bg="#27AE60", fg="white", bd=0, pady=2, command=self.spawn_from_pc)
        btn_spawn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        # INYECCIÓN: Botón de purga de datos
        btn_release = tk.Button(bottom_row, text="Release", font=("Segoe UI", 8, "bold"), bg="#8E44AD", fg="white", bd=0, pady=2, command=self.release_from_pc)
        btn_release.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 2))

        btn_reset = tk.Button(bottom_row, text="Format PC", font=("Segoe UI", 8), bg="#E74C3C", fg="white", bd=0, pady=2, command=self.confirm_reset)
        btn_reset.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))

        self.combo.bind("<<ComboboxSelected>>", self.on_combo_select)

        self.update_pc_ui()
        self.restore_active_pets()
        self.build_spawn_pool()
        
        self.root.after(15000, self.wild_spawner_loop)
        self.root.after(10000, self.xp_tick_loop)
        self.root.after(600000, self.egg_laying_loop) 
        self.root.mainloop()

    def build_spawn_pool(self):
        self.spawn_pool_species = []
        self.spawn_pool_weights = []
        self.evo_parents = {}
        
        all_available = [d for d in os.listdir(self.pets_directory) if os.path.isdir(os.path.join(self.pets_directory, d))]
        
        for species in all_available:
            config_path = os.path.join(self.pets_directory, species, "config.json")
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                
                rpg_data = cfg.get("rpg_data", {})
                weight = rpg_data.get("spawn_rate", 10)
                
                self.spawn_pool_species.append(species)
                self.spawn_pool_weights.append(weight)

                evolves_to = rpg_data.get("evolves_to", [])
                if evolves_to and evolves_to[0] != "none":
                    for evo in evolves_to:
                        self.evo_parents[evo] = species

            except Exception as e:
                print(f"[!] Error leyendo config de {species}: {e}")

    def get_base_form(self, species):
        current = species
        visited = set()
        while current in self.evo_parents and current not in visited:
            visited.add(current)
            current = self.evo_parents[current]
        return current

    def hide_pc_ui(self):
        if len(self.active_instances) == 0 and len(self.wild_instances) == 0:
            import tkinter.messagebox as mb
            mb.showwarning("Seguridad", "No puedes ocultar el PC si no hay Pokémon en pantalla.\nTe quedarías sin forma de volver a abrirlo.")
            return
        self.root.withdraw()

    def show_pc_ui(self, preselect_pet_data=None):
        self.root.deiconify()
        
        if preselect_pet_data:
            shiny_tag = " ★" if preselect_pet_data.get("is_shiny", False) else ""
            target_str = f"{preselect_pet_data['species'].capitalize()}{shiny_tag} - lvl.{preselect_pet_data['level']}"
            
            for idx, val in enumerate(self.combo['values']):
                if val.startswith(target_str):
                    self.combo.current(idx)
                    self.on_combo_select()
                    break

    def get_selected_pet(self):
        selection = self.combo_var.get()
        if selection == "(Vacio)" or not selection: return None
        base_str = selection.split(" (x")[0]
        parts = base_str.split(" - lvl.")
        raw_species = parts[0]
        is_shiny_spawn = "★" in raw_species
        target_species = raw_species.replace(" ★", "").lower()
        target_level = int(parts[1])
        
        matches = [p for p in self.save_mgr.data["inventory"] if p["species"] == target_species and p["level"] == target_level and p.get("is_shiny", False) == is_shiny_spawn and not p.get("is_egg", False)]
        return matches[0] if matches else None

    def on_combo_select(self, event=None):
        pet = self.get_selected_pet()
        if pet:
            self.everstone_var.set(pet.get("everstone", False))
        else:
            self.everstone_var.set(False)

    def on_everstone_toggle(self):
        pet = self.get_selected_pet()
        if pet:
            selection = self.combo_var.get()
            base_str = selection.split(" (x")[0]
            parts = base_str.split(" - lvl.")
            raw_species = parts[0]
            is_shiny_spawn = "★" in raw_species
            target_species = raw_species.replace(" ★", "").lower()
            target_level = int(parts[1])
            new_state = self.everstone_var.get()
            
            for p in self.save_mgr.data["inventory"]:
                if p["species"] == target_species and p["level"] == target_level and p.get("is_shiny", False) == is_shiny_spawn and not p.get("is_egg", False):
                    p["everstone"] = new_state
            self.save_mgr.save_data()
            
            if not new_state:
                for active_pet in self.active_instances:
                    if active_pet.pet_data["species"] == target_species and active_pet.pet_data["level"] == target_level and active_pet.pet_data.get("is_shiny", False) == is_shiny_spawn:
                        active_pet.check_evolution()

    def confirm_reset(self):
        if messagebox.askyesno("Reinicio", "ALERTA: Esto borrará todos tus Pokémon y restablecerá los datos de fábrica.\n\n¿Proceder?"):
            StarterSelectionWindow(self.root, self.pets_directory, self.execute_reset)

    def execute_reset(self, chosen_species):
        for pet in self.active_instances + self.wild_instances:
            pet.window.destroy()
        self.active_instances.clear()
        self.wild_instances.clear()
        
        self.save_mgr.reset_save(chosen_species)
        
        self.update_pc_ui()
        self.restore_active_pets() 
        self.show_pc_ui()

    def update_pc_ui(self):
        current_selection = self.combo_var.get()
        
        if not self.save_mgr.data["inventory"]:
            self.combo['values'] = ["(Vacio)"]
            self.combo.current(0)
            self.on_combo_select()
        else:
            formatted_list = []
            for p in self.save_mgr.data["inventory"]:
                if p.get("is_egg", False): continue
                
                shiny_tag = " ★" if p.get("is_shiny", False) else ""
                formatted_list.append(f"{p['species'].capitalize()}{shiny_tag} - lvl.{p['level']}")
            
            if not formatted_list:
                self.combo['values'] = ["(Vacio)"]
                self.combo.current(0)
                self.on_combo_select()
                return

            unique_owned = sorted(list(set(formatted_list)))
            display_list = []
            
            for p_str in unique_owned:
                count = formatted_list.count(p_str)
                if count > 1: 
                    display_list.append(f"{p_str} (x{count})")
                else: 
                    display_list.append(p_str)
                    
            self.combo['values'] = display_list
            
            if current_selection in display_list:
                self.combo.set(current_selection)
            else:
                self.combo.current(0)
                
            self.on_combo_select()

    def spawn_from_pc(self):
        selection = self.combo_var.get()
        if selection == "(Vacio)" or not selection: return
        
        active_pets_only = len([p for p in self.active_instances if not getattr(p, 'is_egg', False)])
        if active_pets_only >= 6:
            import tkinter.messagebox as mb
            mb.showwarning("Límite de Equipo", "No puedes tener más de 6 Pokémon fuera del PC al mismo tiempo.")
            return

        base_str = selection.split(" (x")[0]
        parts = base_str.split(" - lvl.")
        raw_species = parts[0]
        
        is_shiny_spawn = "★" in raw_species
        target_species = raw_species.replace(" ★", "").lower()
        target_level = int(parts[1])
        
        owned_matches = [p for p in self.save_mgr.data["inventory"] if p["species"] == target_species and p["level"] == target_level and p.get("is_shiny", False) == is_shiny_spawn and not p.get("is_egg", False)]
        active_ids = [pet.pet_data["id"] for pet in self.active_instances]
        
        available_pet = next((p for p in owned_matches if p["id"] not in active_ids), None)
        
        if available_pet:
            self.spawn_entity(available_pet, is_wild=False)
        else:
            print(f"[!] Ya tienes todos tus {target_species} (lvl.{target_level}) en pantalla.")

    def release_from_pc(self):
        pet_to_release = self.get_selected_pet()
        if not pet_to_release: return
        
        # Filtro de seguridad: No puedes liberar un Pokémon que esté caminando por el escritorio
        active_ids = [pet.pet_data["id"] for pet in self.active_instances]
        if pet_to_release["id"] in active_ids:
            import tkinter.messagebox as mb
            mb.showwarning("Operación Denegada", "Debes guardar a este Pokémon en el PC antes de liberarlo.")
            return

        species_name = pet_to_release['species'].capitalize()
        if messagebox.askyesno("Liberar Entidad", f"¿Estás seguro de que quieres liberar a este {species_name}?\nEsta acción destruirá sus datos para siempre."):
            
            # Purga matemática del inventario
            self.save_mgr.data["inventory"] = [p for p in self.save_mgr.data["inventory"] if p["id"] != pet_to_release["id"]]
            self.save_mgr.save_data()
            self.update_pc_ui()
            
            print(f"[+] Entidad {species_name} eliminada de la base de datos local.")

    def restore_active_pets(self):
        active_ids = self.save_mgr.data.get("active_pets", [])
        spawn_index = 0 
        
        for pid in active_ids:
            pet_data = next((p for p in self.save_mgr.data["inventory"] if p["id"] == pid), None)
            if pet_data:
                delay = 100 + (spawn_index * 500)
                self.root.after(delay, lambda pd=pet_data: self.spawn_entity(pd, is_wild=False))
                spawn_index += 1

    def spawn_entity(self, pet_data, is_wild, coords=None, is_mid_evo=False, evo_channel=None):
        pet_dir = os.path.join(self.pets_directory, pet_data["species"])
        if not os.path.exists(os.path.join(pet_dir, "config.json")):
            print(f"Error: No existen assets para {pet_data['species']}")
            return
            
        pet = DesktopPet(self.root, pet_data, is_wild, self.on_pet_removed, self.on_pet_caught, self.show_pc_ui, self.on_pet_evolve, coords, is_mid_evo, evo_channel)
        
        if is_wild: self.wild_instances.append(pet)
        else: 
            self.active_instances.append(pet)
            self.sync_save_state()

    def wild_spawner_loop(self):
        if len(self.wild_instances) < 4:
            probabilidad_spawn = random.randint(1, 100)
            
            if probabilidad_spawn <= 20:
                if self.spawn_pool_species:
                    target = random.choices(
                        population=self.spawn_pool_species, 
                        weights=self.spawn_pool_weights, 
                        k=1
                    )[0]
                    
                    is_shiny_roll = random.randint(1, 100) == 1
                    lvl = random.randint(1, 10)
                    wild_data = {"id": str(uuid.uuid4()), "species": target, "level": lvl, "xp": 0, "is_shiny": is_shiny_roll, "last_evolution_level": lvl}
                    self.spawn_entity(wild_data, is_wild=True)
                    
        next_interval = random.randint(45000, 75000)
        self.root.after(next_interval, self.wild_spawner_loop)

    def xp_tick_loop(self):
        for pet in self.active_instances:
            if not pet.is_wild:
                pet.gain_xp(20) 
                
        self.save_mgr.save_data()
        self.update_pc_ui() 
        self.root.after(10000, self.xp_tick_loop)

    def egg_laying_loop(self):
        has_egg = any(getattr(p, 'is_egg', False) for p in self.active_instances)
        
        if not has_egg:
            fully_evolved_pets = []
            for pet in self.active_instances:
                if not pet.is_wild and not getattr(pet, 'is_egg', False):
                    rpg = pet.config.get("rpg_data", {})
                    evos = rpg.get("evolves_to", [])
                    if not evos or evos[0] == "none":
                        fully_evolved_pets.append(pet)
            
            for pet in fully_evolved_pets:
                if random.randint(1, 100) <= 12: 
                    base_form = self.get_base_form(pet.pet_name)
                    egg_data = {
                        "id": str(uuid.uuid4()), 
                        "species": base_form, 
                        "level": 1, 
                        "xp": 0, 
                        "is_shiny": random.randint(1, 100) <= 25, 
                        "last_evolution_level": 1,
                        "is_egg": True,
                        "everstone": False
                    }
                    self.save_mgr.data["inventory"].append(egg_data)
                    self.save_mgr.save_data()
                    
                    self.spawn_entity(egg_data, is_wild=False, coords=(pet.x, pet.y))
                    break

        self.root.after(600000, self.egg_laying_loop)

    def on_pet_evolve(self, pet_instance, new_species, is_mid_evo=False, evo_channel=None):
        if getattr(pet_instance, 'is_egg', False):
            pet_instance.pet_data["is_egg"] = False
            self.save_mgr.save_data()
            
            active_count = len([p for p in self.active_instances if not getattr(p, 'is_egg', False) and p != pet_instance])
            
            target_coords = (pet_instance.x, pet_instance.y)
            if pet_instance in self.active_instances:
                self.active_instances.remove(pet_instance)
            pet_instance.window.destroy()

            if active_count >= 6:
                try:
                    snd_path = os.path.join(pet_instance.base_dir, "game_env", "sounds", "evolved.wav")
                    if os.path.exists(snd_path):
                        import pygame
                        s = pygame.mixer.Sound(snd_path)
                        s.set_volume(0.03)
                        s.play()
                except: pass
                
                if pet_instance.is_shiny:
                    try:
                        snd_path = os.path.join(pet_instance.base_dir, "game_env", "sounds", "shiny.wav")
                        if os.path.exists(snd_path):
                            import pygame
                            s = pygame.mixer.Sound(snd_path)
                            s.set_volume(0.05)
                            s.play()
                    except: pass
                    
                self.save_mgr.save_data()
                self.update_pc_ui()
            else:
                self.spawn_entity(pet_instance.pet_data, is_wild=False, coords=target_coords, is_mid_evo=is_mid_evo, evo_channel=evo_channel)
                self.update_pc_ui()
            return

        pet_instance.pet_data["species"] = new_species
        pet_instance.pet_data["last_evolution_level"] = pet_instance.pet_data["level"]
        self.save_mgr.save_data()

        target_coords = (pet_instance.x, pet_instance.y)
        if pet_instance in self.active_instances:
            self.active_instances.remove(pet_instance)
        pet_instance.window.destroy()

        self.spawn_entity(pet_instance.pet_data, is_wild=False, coords=target_coords, is_mid_evo=is_mid_evo, evo_channel=evo_channel)
        self.update_pc_ui()

    def on_pet_removed(self, pet_instance):
        if pet_instance in self.active_instances:
            self.active_instances.remove(pet_instance)
            self.sync_save_state()
            if len(self.active_instances) == 0 and len(self.wild_instances) == 0:
                self.show_pc_ui()
        elif pet_instance in self.wild_instances:
            self.wild_instances.remove(pet_instance)
            if len(self.active_instances) == 0 and len(self.wild_instances) == 0:
                self.show_pc_ui()

    def on_pet_caught(self, pet_instance):
        if pet_instance in self.wild_instances:
            self.wild_instances.remove(pet_instance)
            pet_instance.pet_data["id"] = str(uuid.uuid4())
            self.save_mgr.data["inventory"].append(pet_instance.pet_data)
            self.save_mgr.save_data()
            self.update_pc_ui()
            if len(self.active_instances) == 0 and len(self.wild_instances) == 0:
                self.show_pc_ui()

    def sync_save_state(self):
        active_ids = [pet.pet_data["id"] for pet in self.active_instances]
        self.save_mgr.data["active_pets"] = active_ids
        self.save_mgr.save_data()

    def exit_game(self):
        self.sync_save_state()
        sys.exit()

if __name__ == '__main__':
    try:
        import pygame
        pygame.mixer.init()
    except: pass
    
    GameController()