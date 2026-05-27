import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import sys
import random
import math
import time
import uuid # NÚCLEO: Identificadores únicos para separar clones
from PIL import Image, ImageTk, ImageOps

# --- GESTOR DE DATOS (SAVE MANAGER) ---
class SaveManager:
    """Arquitectura de datos compleja (Soporta XP, Niveles e Instancias Únicas)"""
    def __init__(self, save_file="save_data.json"):
        self.save_file = save_file
        
        self.default_data = {
            "inventory": [
                {"id": str(uuid.uuid4()), "species": "pikachu", "level": 1, "xp": 0},
                {"id": str(uuid.uuid4()), "species": "regieleki", "level": 1, "xp": 0}
            ],
            "active_pets": [] # Ahora guarda UUIDs, no nombres
        }
        self.data = self.load_save()

    def load_save(self):
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    # SCRIPT DE MIGRACIÓN: Convierte partidas antiguas al nuevo estándar UUID
                    if "pc_inventory" in data:
                        new_inv = []
                        for sp in data["pc_inventory"]:
                            new_inv.append({"id": str(uuid.uuid4()), "species": sp, "level": 1, "xp": 0})
                        data["inventory"] = new_inv
                        del data["pc_inventory"]
                        data["active_pets"] = [] 
                        
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

    def reset_save(self):
        import copy
        self.data = copy.deepcopy(self.default_data)
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

    def update_animation(self, state, facing_right, canvas_image_id, animate_idle, fps_ms):
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

        render_state = 'idle' if state == 'falling' else state

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

        self.tk_image_ref = ImageTk.PhotoImage(processed_image)
        self.canvas.itemconfig(canvas_image_id, image=self.tk_image_ref)

# --- ENTIDAD FÍSICA ---
class DesktopPet:
    def __init__(self, parent_root, pet_data, is_wild, on_remove_callback, on_catch_callback, on_open_pc_callback, on_evolve_callback, spawn_coords=None):
        self.pet_data = pet_data # Ahora operamos con el diccionario completo (XP, Nivel, ID)
        self.pet_name = pet_data["species"]
        self.is_wild = is_wild
        
        self.on_remove = on_remove_callback
        self.on_catch = on_catch_callback
        self.on_open_pc = on_open_pc_callback
        self.on_evolve = on_evolve_callback
        
        self.base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        self.pet_dir = os.path.join(self.base_dir, "game_env", "pets", self.pet_name)
        
        self.config = self.load_config()
        
        self.window = tk.Toplevel(parent_root)
        wild_tag = "(SALVAJE)" if is_wild else f"Lv.{self.pet_data['level']}"
        self.window.title(f"{self.config.get('display_name', 'Pokemon')} {wild_tag}")
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)

        CHROMA_KEY = '#FF00FF'
        self.window.config(bg=CHROMA_KEY)
        try: self.window.wm_attributes('-transparentcolor', CHROMA_KEY)
        except tk.TclError: pass 

        multiplicador = 1.3
        physics = self.config.get("physics", {})
        
        size_w = int(physics.get("size", 64) * multiplicador)
        size_h = int(physics.get("size", 64) * multiplicador)
        base_speed = physics.get("movement_speed", 2)
        self.speed = max(1, int(base_speed * multiplicador))
        self.is_flying = physics.get("is_flying", False)
        
        if self.is_flying: self.offset_y = 40
        else: self.offset_y = -6 
            
        self.fly_amplitude = 0 
        
        self.canvas = tk.Canvas(self.window, width=size_w, height=size_h, bg=CHROMA_KEY, highlightthickness=0)
        self.canvas.pack()
        self.canvas_image_id = self.canvas.create_image(size_w//2, size_h//2, anchor=tk.CENTER)
        
        img_cfg = self.config.get("images", {})
        self.animator = DesktopPetAnimator(self.canvas, img_cfg, (size_w, size_h), (size_w, size_h), self.pet_dir)

        user32 = ctypes.windll.user32
        self.v_x = user32.GetSystemMetrics(76) 
        self.v_y = user32.GetSystemMetrics(77)
        self.v_width = user32.GetSystemMetrics(78)
        self.v_height = user32.GetSystemMetrics(79)

        self.floor_y = (self.v_y + self.v_height) - size_h - self.offset_y
        
        # Permitir spawns in-situ para no teletransportarse durante la evolución
        if spawn_coords:
            self.x, self.y = spawn_coords
            self.current_state = 'idle'
        else:
            self.x = random.randint(self.v_x, self.v_x + self.v_width - size_w)
            self.y = self.v_y - size_h 
            self.current_state = 'falling'

        self.window.geometry(f"{size_w}x{size_h}+{self.x}+{self.y}")
        self.is_facing_right = random.choice([True, False])
        self.frame_rate_active = img_cfg.get("frame_rate_active", 120)
        self.frame_rate_idle = img_cfg.get("frame_rate_idle", 200)

        self.canvas.bind("<ButtonRelease-3>", self.handle_right_click)
        self.canvas.bind("<Double-Button-1>", self.handle_double_click)
        
        self.keep_on_top()
        self.animate_loop()
        self.physics_loop()

    # --- LÓGICA RPG (NUEVO) ---
    def gain_xp(self, amount):
        """Inyecta XP, calcula niveles y evalúa evoluciones."""
        self.pet_data["xp"] += amount
        xp_needed = self.pet_data["level"] * 30 # Fórmula de progresión
        
        leveled_up = False
        while self.pet_data["xp"] >= xp_needed:
            self.pet_data["xp"] -= xp_needed
            self.pet_data["level"] += 1
            xp_needed = self.pet_data["level"] * 30
            leveled_up = True
            
        if leveled_up:
            self.window.title(f"{self.config.get('display_name', 'Pokemon')} Lv.{self.pet_data['level']}")
            self.show_level_up_vfx()
            self.check_evolution()

    def show_level_up_vfx(self):
        """Indicador visual de subida de nivel."""
        txt = self.canvas.create_text(self.window.winfo_width()//2, 15, text="LEVEL UP!", fill="#F1C40F", font=("Segoe UI", 10, "bold"), tags="vfx_lvl")
        def float_up(step):
            if step < 20 and self.current_state != 'exiting':
                self.canvas.move(txt, 0, -1)
                self.window.after(50, lambda: float_up(step+1))
            else:
                self.canvas.delete(txt)
        float_up(0)

    def check_evolution(self):
        """Consulta el config.json para comprobar ramas evolutivas."""
        rpg = self.config.get("rpg_data", {})
        evo_level = rpg.get("evolution_level", 99)
        evolves_to = rpg.get("evolves_to", [])

        if self.pet_data["level"] >= evo_level and evolves_to and evolves_to[0] != "none":
            self.current_state = 'exiting'
            target_species = random.choice(evolves_to)
            self.on_evolve(self, target_species)
    # --------------------------

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
                    self.current_sound.set_volume(0.05) 
                    self.current_sound.play()
            except Exception: pass 

            pb_path = os.path.join(self.base_dir, "game_env", "ui", "pokeball.png")
            try:
                raw_img = Image.open(pb_path).convert("RGBA")
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
            w_width = self.window.winfo_width()
            w_height = self.window.winfo_height()
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

    def handle_right_click(self, event):
        if self.current_state != 'exiting':
            if self.is_wild:
                self.on_catch(self)
                self.animate_vfx("catch")
            else:
                self.on_remove(self)
                self.animate_vfx("return")

    def handle_double_click(self, event):
        if self.current_state != 'exiting':
            self.on_open_pc()

    def update_position(self):
        self.window.geometry(f"+{int(self.x)}+{int(self.y)}")

    def animate_loop(self):
        if self.current_state == 'exiting': return 
        target_ms = self.frame_rate_active if self.current_state in ['walking', 'falling'] else self.frame_rate_idle
        self.animator.update_animation(self.current_state, self.is_facing_right, self.canvas_image_id, True, target_ms)
        self.window.after(16, self.animate_loop)

    def physics_loop(self):
        if self.current_state == 'exiting': return

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
                elif self.x >= (self.v_x + self.v_width) - self.window.winfo_width():
                    self.x = (self.v_x + self.v_width) - self.window.winfo_width()
                    self.is_facing_right = False
        
        if self.is_flying and self.current_state != 'falling':
            self.fly_amplitude += 0.2
            onda = math.sin(self.fly_amplitude) * 10
            self.y = self.floor_y + onda
            
        self.update_position()
        self.window.after(50, self.physics_loop)

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
        
        w, h = 260, 85 
        screen_w = self.root.winfo_screenwidth()
        self.root.geometry(f"{w}x{h}+{screen_w - w - 20}+20")

        bg_main = "#ECF0F1"       
        bg_header = "#2C3E50"     
        fg_header = "#FFFFFF"     
        
        self.root.config(bg=bg_header)

        header_frame = tk.Frame(self.root, bg=bg_header, height=25)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False) 
        
        tk.Label(header_frame, text="💻 Bill's PC", font=("Segoe UI", 9, "bold"), bg=bg_header, fg=fg_header).pack(side=tk.LEFT, padx=10)
        
        btn_power = tk.Button(header_frame, text="⏻", font=("Segoe UI", 8), bg="#C0392B", fg="white", bd=0, width=3, command=self.exit_game)
        btn_power.pack(side=tk.RIGHT, padx=(0,0))
        
        btn_hide = tk.Button(header_frame, text="—", font=("Segoe UI", 8, "bold"), bg="#7F8C8D", fg="white", bd=0, width=3, command=self.hide_pc_ui)
        btn_hide.pack(side=tk.RIGHT, padx=(0,2))

        content_frame = tk.Frame(self.root, bg=bg_main)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        top_row = tk.Frame(content_frame, bg=bg_main)
        top_row.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        tk.Label(top_row, text="Caja:", font=("Segoe UI", 9, "bold"), bg=bg_main).pack(side=tk.LEFT)
        
        self.combo_var = tk.StringVar()
        self.combo = ttk.Combobox(top_row, textvariable=self.combo_var, state="readonly", width=14)
        self.update_pc_ui()
        self.combo.pack(side=tk.LEFT, padx=5)

        btn_spawn = tk.Button(top_row, text="Spawn", font=("Segoe UI", 8, "bold"), bg="#27AE60", fg="white", bd=0, padx=8, command=self.spawn_from_pc)
        btn_spawn.pack(side=tk.LEFT)

        bottom_row = tk.Frame(content_frame, bg=bg_main)
        bottom_row.pack(fill=tk.X, padx=10)
        
        btn_reset = tk.Button(bottom_row, text="🗑️ Formatear Sistema", font=("Segoe UI", 8), bg="#E74C3C", fg="white", bd=0, padx=5, pady=2, command=self.confirm_reset)
        btn_reset.pack(side=tk.RIGHT)

        self.restore_active_pets()
        
        # BUCLES DE MOTOR (Salvajes y Progresión RPG)
        self.root.after(15000, self.wild_spawner_loop)
        self.root.after(10000, self.xp_tick_loop) # Motor de XP (10 segundos)
        self.root.mainloop()

    def hide_pc_ui(self):
        if len(self.active_instances) == 0 and len(self.wild_instances) == 0:
            import tkinter.messagebox as mb
            mb.showwarning("Seguridad", "No puedes ocultar el PC si no hay Pokémon en pantalla.\nTe quedarías sin forma de volver a abrirlo.")
            return
        self.root.withdraw()

    def show_pc_ui(self):
        self.root.deiconify()

    def confirm_reset(self):
        if messagebox.askyesno("Reinicio", "ALERTA: Esto borrará todos tus Pokémon y restablecerá los datos de fábrica.\n\n¿Proceder?"):
            self.save_mgr.reset_save()
            for pet in self.active_instances + self.wild_instances:
                pet.window.destroy()
            self.active_instances.clear()
            self.wild_instances.clear()
            self.update_pc_ui()
            self.restore_active_pets() 
            self.show_pc_ui()

    def update_pc_ui(self):
        owned_species = [p["species"] for p in self.save_mgr.data["inventory"]]
        if not owned_species:
            self.combo['values'] = ["(Vacio)"]
            self.combo.current(0)
        else:
            unique_owned = sorted(list(set(owned_species)))
            display_list = []
            for p in unique_owned:
                count = owned_species.count(p)
                if count > 1: display_list.append(f"{p.capitalize()} (x{count})")
                else: display_list.append(p.capitalize())
            self.combo['values'] = display_list
            self.combo.current(0)

    def spawn_from_pc(self):
        selection = self.combo_var.get()
        if selection == "(Vacio)" or not selection: return
        
        target_species = selection.split(" (x")[0].lower()
        owned_of_species = [p for p in self.save_mgr.data["inventory"] if p["species"] == target_species]
        active_ids = [pet.pet_data["id"] for pet in self.active_instances]
        
        # Filtra e invoca al primero que NO esté ya en pantalla
        available_pet = next((p for p in owned_of_species if p["id"] not in active_ids), None)
        
        if available_pet:
            self.spawn_entity(available_pet, is_wild=False)
        else:
            print(f"[!] Ya tienes todos tus {target_species} en pantalla.")

    def restore_active_pets(self):
        active_ids = self.save_mgr.data.get("active_pets", [])
        for pid in active_ids:
            pet_data = next((p for p in self.save_mgr.data["inventory"] if p["id"] == pid), None)
            if pet_data:
                self.root.after(100, lambda pd=pet_data: self.spawn_entity(pd, is_wild=False))

    def spawn_entity(self, pet_data, is_wild, coords=None):
        pet_dir = os.path.join(self.pets_directory, pet_data["species"])
        if not os.path.exists(os.path.join(pet_dir, "config.json")):
            print(f"Error: No existen assets para {pet_data['species']}")
            return
            
        pet = DesktopPet(self.root, pet_data, is_wild, self.on_pet_removed, self.on_pet_caught, self.show_pc_ui, self.on_pet_evolve, coords)
        
        if is_wild: self.wild_instances.append(pet)
        else: 
            self.active_instances.append(pet)
            self.sync_save_state()

    def wild_spawner_loop(self):
        if len(self.wild_instances) < 2:
            all_available = [d for d in os.listdir(self.pets_directory) if os.path.isdir(os.path.join(self.pets_directory, d))]
            if all_available:
                target = random.choice(all_available)
                wild_data = {"id": str(uuid.uuid4()), "species": target, "level": random.randint(1, 3), "xp": 0}
                self.spawn_entity(wild_data, is_wild=True)
        self.root.after(15000, self.wild_spawner_loop)

    def xp_tick_loop(self):
        """Inyecta experiencia a todas tus mascotas activas en pantalla."""
        for pet in self.active_instances:
            if not pet.is_wild:
                pet.gain_xp(20) # 20 XP cada 10 segundos
        self.save_mgr.save_data()
        self.root.after(10000, self.xp_tick_loop)

    def on_pet_evolve(self, pet_instance, new_species):
        """Destruye la instancia actual y la renace como la evolución."""
        # 1. Actualización en Base de Datos
        pet_instance.pet_data["species"] = new_species
        self.save_mgr.save_data()

        # 2. Reemplazo de Renderizado (Conserva coordenadas)
        target_coords = (pet_instance.x, pet_instance.y)
        if pet_instance in self.active_instances:
            self.active_instances.remove(pet_instance)
        pet_instance.window.destroy()

        self.spawn_entity(pet_instance.pet_data, is_wild=False, coords=target_coords)
        self.update_pc_ui()

    def on_pet_removed(self, pet_instance):
        if pet_instance in self.active_instances:
            self.active_instances.remove(pet_instance)
            self.sync_save_state()
            if len(self.active_instances) == 0 and len(self.wild_instances) == 0:
                self.show_pc_ui()

    def on_pet_caught(self, pet_instance):
        if pet_instance in self.wild_instances:
            self.wild_instances.remove(pet_instance)
            # Regenerar ID para asegurar que no haya colisiones y añadir al inventario
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
    # Inicializar audio global antes de arrancar
    try:
        import pygame
        pygame.mixer.init()
    except: pass
    
    GameController()