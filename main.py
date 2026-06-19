import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import sys
import random
import math
import time
import uuid
import threading 

try:
    import win32gui
    import win32con
    import win32process
    import win32api
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    print("[!] Advertencia: Falta la librería 'pywin32'. Ejecuta 'pip install pywin32'.")

# --- SUPRESIÓN ESTRICTA DE LA TERMINAL DE PYGAME ---
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

try:
    from pypresence import Presence
    HAS_DISCORD = True
except ImportError:
    HAS_DISCORD = False
    print("[!] Advertencia: Falta la librería 'pypresence'. Ejecuta 'pip install pypresence' para habilitar Discord RPC.")

import threading # Obligatorio para evitar micro-tirones en Tkinter

# --- GESTOR DE DISCORD RICH PRESENCE ---
class DiscordRPC:
    def __init__(self, client_id):
        self.client_id = client_id
        self.RPC = None
        self.connected = False
        self.target_pet = None
        if HAS_DISCORD:
            self.connect()

    def connect(self):
        try:
            self.RPC = Presence(self.client_id)
            self.RPC.connect()
            self.connected = True
            print("[+] Discord RPC Connected.")
        except Exception as e:
            print(f"[-] Error conectando a Discord: {e}")
            self.connected = False

    def set_target(self, pet):
        # Ignora huevos para no arruinar la sorpresa
        if getattr(pet, 'is_egg', False): return
        self.target_pet = pet

    def update_loop(self, root):
        if self.connected and self.target_pet and self.target_pet.window.winfo_exists():
            pet = self.target_pet
            
            # 1. Parsear Nombre y Nivel
            name = pet.pet_data['species'].capitalize()
            if getattr(pet, 'is_shiny', False):
                name += " ★"
            level = pet.pet_data['level']

            # 2. Parsear Actividad y Entorno (Conciencia del Sistema Operativo)
            window_title = ""
            if getattr(pet, 'anchored_hwnd', None):
                try:
                    raw_title = win32gui.GetWindowText(pet.anchored_hwnd)
                    if raw_title:
                        # Extraemos el nombre del programa principal para que quede limpio
                        parts = raw_title.split('-')
                        window_title = parts[-1].strip()
                        if len(window_title) > 20:
                            window_title = window_title[:17] + "..."
                except: pass

            is_climbing = getattr(pet, 'is_climbing', False) and getattr(pet, 'climbing_surface', 'floor') != 'floor'
            
            if getattr(pet, 'is_flying', False):
                activity = f"Flotando sobre {window_title}" if window_title else "Flotando por la pantalla"
            elif is_climbing:
                activity = f"Trepando por {window_title}" if window_title else "Trepando por los bordes"
            elif window_title:
                if pet.current_state == 'idle':
                    activity = f"Descansando en {window_title}"
                else:
                    activity = f"Explorando {window_title}"
            else:
                if pet.current_state == 'idle': activity = "Descansando en el escritorio"
                elif pet.current_state == 'jumping_arc': activity = "Dando saltos"
                elif pet.current_state == 'falling': activity = "Cayendo al vacío"
                elif pet.current_state == 'attacking': activity = "Luchando con otro pokémon"
                elif pet.current_state == 'socializing': activity = "Charlando con otro pokémon"
                elif pet.current_state == 'eating': activity = "Comiendo una baya"
                else: activity = "De paseo por el escritorio"

            # 3. Envío Asíncrono del Payload
            def send_payload():
                try:
                    self.RPC.update(
                        state=activity,
                        details=f"Nv. {level} | {name}",
                        # En lugar de buscar un asset por cada especie, cargamos siempre el logo principal.
                        large_image="app_logo", 
                        large_text="Deskmon",
                        # Opcional: Ponemos el nombre del Pokémon al pasar el ratón por encima del logo
                        small_image="shiny_star" if getattr(pet, 'is_shiny', False) else None,
                        small_text=name if getattr(pet, 'is_shiny', False) else None
                    )
                except:
                    self.connected = False 
            
            # Disparamos en hilo fantasma para que la espera de red no congele la animación a 60FPS
            threading.Thread(target=send_payload, daemon=True).start()
        
        # Refresco cada 15 segundos (Límite estricto de la API de Discord)
        root.after(15000, lambda: self.update_loop(root))

from PIL import Image, ImageTk, ImageOps

# --- GESTOR DE DATOS (SAVE MANAGER) ---
class SaveManager:
    def __init__(self, save_file="save_data.json"):
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        self.save_file = os.path.join(base_dir, save_file)
        
        self.default_data = {
            "inventory": [],
            "active_pets": [],
            "settings": {
                "allow_wild": True,
                "allow_breeding": True
            }
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
                            new_inv.append({
                                "id": str(uuid.uuid4()), "species": sp, "level": 1, "xp": 0, 
                                "is_shiny": False, "last_evolution_level": 1, "everstone": False,
                                "flying_height_pct": 3.0, "xp_boost_expiry": 0
                            })
                        data["inventory"] = new_inv
                        del data["pc_inventory"]
                        data["active_pets"] = [] 
                    
                    for p in data.get("inventory", []):
                        if "last_evolution_level" not in p: p["last_evolution_level"] = p["level"]
                        if "flying_height_pct" not in p: p["flying_height_pct"] = 3.0
                        if "xp_boost_expiry" not in p: p["xp_boost_expiry"] = 0
                            
                    if "active_pets" not in data: data["active_pets"] = []
                    if "settings" not in data: data["settings"] = {"allow_wild": True, "allow_breeding": True}
                    if "flying_height_pct" in data["settings"]: del data["settings"]["flying_height_pct"]
                        
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
            "inventory": [{
                "id": str(uuid.uuid4()), "species": starter_species, "level": 1, "xp": 0, 
                "is_shiny": is_shiny_roll, "last_evolution_level": 1, "everstone": False,
                "flying_height_pct": 3.0, "xp_boost_expiry": 0
            }],
            "active_pets": [],
            "settings": {"allow_wild": True, "allow_breeding": True}
        }
        self.save_data()

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

    def update_animation(self, state, facing_right, canvas_image_id, animate_idle, fps_ms, blend_factor=0.0, rotation_angle=0):
        # FIX: Congelar el motor visual durante el temblor para evitar inversiones
        if state in ['exiting', 'landing_shake']: return

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

        render_state = state
        # FIX: Añadimos los estados telequinéticos a la lista de renderizado estático
        if render_state in ['falling', 'evolving_start', 'evolving_finish', 'ascending', 'falling_pokeball', 'falling_egg', 'dragged', 'thrown', 'falling_legendary', 'legendary_bounce', 'climbing', 'eating', 'tk_channeling', 'tk_lifted', 'tk_controlled']:
            render_state = 'idle'
        elif render_state in ['walking_away', 'jumping_arc', 'socializing', 'attacking']:
            render_state = 'walking'

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
            effective_dir = True if (render_state == 'idle' and self.fix_idle_direction and state not in ['socializing', 'attacking', 'eating']) else facing_right
            should_mirror = effective_dir if self.invert_x_axis else (not effective_dir)
            processed_image = ImageOps.mirror(raw_image) if should_mirror else raw_image

        if rotation_angle != 0:
            processed_image = processed_image.rotate(rotation_angle, expand=False, resample=Image.NEAREST)

        if blend_factor > 0.0:
            white_layer = Image.new("RGBA", processed_image.size, (255, 255, 255, 255))
            white_layer.putalpha(processed_image.split()[3]) 
            processed_image = Image.blend(processed_image, white_layer, blend_factor)

        self.tk_image_ref = ImageTk.PhotoImage(processed_image)
        self.canvas.itemconfig(canvas_image_id, image=self.tk_image_ref)

# --- ENTIDAD FÍSICA (REFACCIONADA A MÁQUINA DE ESTADOS) ---
class DesktopPet:
    def __init__(self, parent_root, pet_data, is_wild, on_remove_callback, on_catch_callback, on_open_pc_callback, on_evolve_callback, spawn_coords=None, is_mid_evo=False, evo_channel=None, is_overflow=False, get_all_pets_callback=None, game_controller_ref=None):
        self.pet_data = pet_data
        self.pet_name = pet_data["species"]
        self.is_wild = is_wild
        self.is_egg = self.pet_data.get("is_egg", False)
        self.is_overflow = is_overflow
        self.game_controller = game_controller_ref
        
        # CONFIGURADOR DE ESCALADA
        self.climb_offset_x = 0  
        self.climb_offset_y = 0  

        self.get_all_pets = get_all_pets_callback
        self.social_cooldown = 0
        self.social_timer = 0
        self.attack_cooldown = 0
        self.attack_timer = 0
        self.eating_timer = 0
        self.jump_cooldown = 0 
        self.interaction_target = None
        
        self.on_remove = on_remove_callback
        self.on_catch = on_catch_callback
        self.on_open_pc = on_open_pc_callback
        self.on_evolve = on_evolve_callback
        
        self.base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        self.pet_dir = os.path.join(self.base_dir, "game_env", "pets", self.pet_name)
        
        self.config = self.load_config()
        
        normalized_name = self.pet_name.lower().replace("_", "").replace("-", "").replace(" ", "")
        
        LEGENDARY_MATRIX = {
            "articuno", "zapdos", "moltres", "mewtwo", "mew", "raikou", "entei", "suicune", "lugia", "hooh", "celebi",
            "regirock", "regice", "registeel", "latias", "latios", "kyogre", "groudon", "rayquaza", "jirachi", "deoxys",
            "uxie", "mesprit", "azelf", "dialga", "palkia", "heatran", "regigigas", "giratina", "cresselia", "manaphy", "phione", "darkrai", "shaymin", "arceus",
            "victini", "cobalion", "terrakion", "virizion", "tornadus", "thundurus", "reshiram", "zekrom", "landorus", "kyurem", "keldeo", "meloetta", "genesect",
            "xerneas", "yveltal", "zygarde", "diancie", "hoopa", "volcanion",
            "tapukoko", "tapulele", "tapubulu", "tapufini", "cosmog", "cosmoem", "solgaleo", "lunala", "nihilego", "buzzwole", "pheromosa", "xurkillree", "celesteela", "kartana", "guzzlord", "necrozma", "magearna", "marshadow", "poipole", "naganadel", "stakataka", "blacephalon", "zeraora", "melmetal",
            "zacian", "zamazenta", "eternatus", "kubfu", "urshifu", "zarude", "regieleki", "regidrago", "glastrier", "spectrier", "calyrex", "enamorus",
            "tinglu", "chienpao", "wochien", "chiyu", "koraidon", "miraidon", "walkingwake", "ironleaves", "okidogi", "munkidori", "fezandipiti", "ogerpon", "terapagos", "pecharunt"
        }
        
        rpg_data = self.config.get("rpg_data", {})
        rarity_str = rpg_data.get("rarity", "").lower()
        self.is_legendary = (normalized_name in LEGENDARY_MATRIX) or rpg_data.get("is_legendary", False) or (rarity_str in ["legendary", "mythical", "legendario", "singular"])

        self.window = tk.Toplevel(parent_root)
        wild_tag = "(SALVAJE)" if is_wild else f"Lv.{self.pet_data['level']}"
        if self.is_egg: wild_tag = "(HUEVO)"
        self.window.title(f"{self.config.get('display_name', 'Pokemon')} {wild_tag}")
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)

        CHROMA_KEY = '#00FF00'
        self.window.config(bg=CHROMA_KEY)
        try: self.window.wm_attributes('-transparentcolor', CHROMA_KEY)
        except tk.TclError: pass 

        multiplicador_tamaño = 1.55
        if self.is_legendary:
            multiplicador_tamaño *= 1.2 

        multiplicador_velocidad = 2
        physics = self.config.get("physics", {})
        
        self.size_w = int(physics.get("size", 64) * multiplicador_tamaño)
        self.size_h = int(physics.get("size", 64) * multiplicador_tamaño)
        
        base_speed = physics.get("movement_speed", 2)
        self.speed = max(1, int(base_speed * multiplicador_velocidad))
        self.is_flying = physics.get("is_flying", False)
        self.is_climbing = physics.get("is_climbing", False) and not self.is_flying 
        
        # --- MECÁNICAS DE COMPORTAMIENTO HARDCODEADAS ---
        self.can_screen_wrap = physics.get("can_screen_wrap", False)
        self.can_teleport = physics.get("can_teleport", False)
        self.heavy_fall = physics.get("heavy_fall", False)
        self.telekinetic = physics.get("telekinetic", False)
        self.aggressive = physics.get("aggressive", False)
        self.teleport_cooldown = 0

        self.climbing_surface = 'floor' 
        self.surface_angle = 0
        
        user32 = ctypes.windll.user32
        self.v_x = user32.GetSystemMetrics(76) 
        self.v_y = user32.GetSystemMetrics(77)
        self.v_width = user32.GetSystemMetrics(78)
        self.v_height = user32.GetSystemMetrics(79)
        
        self.v_x_velocity = 0.0
        self.v_y_velocity = 0.0
        
        if self.is_egg:
            self.is_flying = False  
            self.offset_y = 0      
        elif self.is_flying: 
            if self.is_wild and getattr(self, 'is_legendary', False):
                self.pet_data["flying_height_pct"] = 100.0
                
            fly_height_pct = self.pet_data.get("flying_height_pct", 3.0)
            max_offset = self.v_height - self.size_h
            self.target_offset_y = int(max_offset * (fly_height_pct / 100.0))
            self.target_floor_y = (self.v_y + self.v_height) - self.size_h - self.target_offset_y
            self.offset_y = -6 
        else: 
            self.offset_y = -6 
            
        self.fly_amplitude = 0
        self.default_floor_y = (self.v_y + self.v_height) - self.size_h - self.offset_y
        self.floor_y = self.default_floor_y
        
        if not hasattr(self, 'target_floor_y'):
            self.target_floor_y = self.floor_y
            
        self.canvas = tk.Canvas(self.window, width=self.size_w, height=self.size_h, bg=CHROMA_KEY, highlightthickness=0)
        self.canvas.pack()
        self.canvas_image_id = self.canvas.create_image(self.size_w//2, self.size_h//2, anchor=tk.CENTER)
        
        self.is_shiny = self.pet_data.get("is_shiny", False)
        animator_dir = os.path.join(self.pet_dir, "shiny") if self.is_shiny else self.pet_dir
        if self.is_shiny and not os.path.exists(animator_dir):
            animator_dir = self.pet_dir

        self.animator = DesktopPetAnimator(self.canvas, self.config.get("images", {}), (self.size_w, self.size_h), (self.size_w, self.size_h), animator_dir)
        
        if self.is_egg:
            if "hatch_time_remaining" not in self.pet_data:
                self.pet_data["hatch_time_remaining"] = random.randint(900000, 1800000)

            self.canvas.coords(self.canvas_image_id, self.size_w // 2, self.size_h)
            self.canvas.itemconfig(self.canvas_image_id, anchor=tk.S)
            
            egg_path = os.path.join(self.base_dir, "game_env", "ui", "egg.png")
            try:
                raw_egg = Image.open(egg_path).convert("RGBA")
                r, g, b, a = raw_egg.split()
                a = a.point(lambda p: 255 if p > 127 else 0)
                raw_egg.putalpha(a)
                bbox = a.getbbox()
                if bbox: raw_egg = raw_egg.crop(bbox)
                
                target_w = max(1, int(self.size_w * 0.35))
                target_h = max(1, int(self.size_h * 0.35))
                aspect = raw_egg.width / raw_egg.height
                if aspect > 1:
                    new_w = target_w
                    new_h = int(target_w / aspect)
                else:
                    new_h = target_h
                    new_w = int(target_h * aspect)
                    
                self.egg_base_img = raw_egg.resize((new_w, new_h), Image.Resampling.NEAREST)
                self.egg_tk = ImageTk.PhotoImage(self.egg_base_img)
                self.canvas.itemconfig(self.canvas_image_id, image=self.egg_tk)
            except: pass
            self.window.after(random.randint(45000, 75000), self.egg_wiggle_loop)
        
        if spawn_coords:
            self.x = spawn_coords[0]
            self.y = spawn_coords[1]
            self.floor_y = spawn_coords[1] # FIX CRÍTICO: Sincronizar el suelo local con la altura de aparición
            if is_mid_evo:
                self.evo_channel = evo_channel
                self.current_state = 'evolving_finish'
                self.finish_evolution_vfx(step=0)
            else:
                if self.is_egg:
                    # FIX: Inyectamos el huevo en el estado 'thrown' para que tenga gravedad y rebotes reales
                    self.current_state = 'thrown'
                    self.v_x_velocity = random.choice([-2.0, 2.0])
                    self.v_y_velocity = -4.0 # Pequeño salto parabólico al ser puesto por la madre
                else:
                    self.current_state = 'idle'
        else:
            self.x = random.randint(self.v_x, self.v_x + self.v_width - self.size_w)
            if self.is_egg:
                self.y = self.v_y - self.size_h
                self.current_state = 'thrown' # Cae rebotando al iniciar la app
                self.v_x_velocity = random.choice([-2.0, 2.0])
                self.v_y_velocity = 2.0
            elif self.is_wild:
                if self.is_legendary and not self.is_flying:
                    self.y = self.v_y - self.size_h
                    self.current_state = 'falling_legendary'
                elif self.is_legendary and self.is_flying:
                    self.y = self.v_y - self.size_h
                    self.floor_y = self.y 
                    self.current_state = 'ascending' 
                    self.play_shiny_sound() 
                else:
                    # FIX: Los voladores salvajes ahora aparecen en el cielo (target_floor_y), no en el suelo
                    self.y = getattr(self, 'target_floor_y', self.floor_y) if self.is_flying else self.floor_y
                    self.current_state = 'spawning_wild'
                    self.canvas.itemconfig(self.canvas_image_id, state='hidden')
                    self.animate_wild_spawn(step=0)
            else:
                self.y = self.v_y - self.size_h 
                self.current_state = 'falling_pokeball'
                self.canvas.itemconfig(self.canvas_image_id, state='hidden')
                self.animate_owned_spawn(step=0)

        self.window.geometry(f"{self.size_w}x{self.size_h}+{int(self.x)}+{int(self.y)}")
        self.is_facing_right = random.choice([True, False])
        self.frame_rate_active = self.config.get("images", {}).get("frame_rate_active", 120)
        self.frame_rate_idle = self.config.get("images", {}).get("frame_rate_idle", 200)

        self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self.on_drag_release)
        self.canvas.bind("<ButtonRelease-3>", self.handle_right_click)
        self.canvas.bind("<Double-Button-1>", self.handle_double_click)
        
        if self.is_wild and not self.is_egg:
            despawn_time = random.randint(120000, 300000) 
            self.despawn_timer = self.window.after(despawn_time, self.start_wild_despawn)
            
        # DICCIONARIO FSM (Finite State Machine)
        self.fsm = {
            'exiting': self._fsm_exiting,
            'egg_idle': self._fsm_wait,
            'egg_wiggle': self._fsm_wait,
            'dragged': self._fsm_wait,
            'evolving_start': self._fsm_wait,
            'evolving_finish': self._fsm_wait,
            'despawning_wild': self._fsm_wait,
            'spawning_wild': self._fsm_wait,
            'thrown': self._fsm_thrown,
            'legendary_bounce': self._fsm_legendary_bounce,
            'jumping_arc': self._fsm_jumping_arc,
            'ascending': self._fsm_ascending,
            'walking_away': self._fsm_walking_away,
            'falling': self._fsm_falling,
            'falling_pokeball': self._fsm_falling,
            'falling_legendary': self._fsm_falling,
            'socializing': self._fsm_socializing,
            'attacking': self._fsm_attacking,
            'eating': self._fsm_eating,
            'idle': self._fsm_active,
            'walking': self._fsm_active,
            'climbing': self._fsm_active,
            'teleporting_out': self._fsm_teleporting_out,
            'teleporting_in': self._fsm_teleporting_in
        }
            
        self.keep_on_top()
        self.animate_loop()
        self.physics_loop()

    def keep_on_top(self):
        if self.current_state != 'exiting':
            try: self.window.attributes('-topmost', True)
            except: pass
            self.window.after(2000, self.keep_on_top)

    def on_drag_start(self, event):
        if self.current_state in ['exiting', 'falling_pokeball', 'falling_egg', 'spawning_wild', 'despawning_wild']: return
        
        # FIX: Destrucción total del vínculo telequinético si se hace clic en el Maestro
        if self.current_state == 'tk_channeling':
            self.current_state = 'idle'
            self.manage_tk_aura(self.canvas, self.size_w, self.size_h, False)
            target = getattr(self, 'tk_target', None)
            if target:
                t_w = target.size_w if target.__class__.__name__ == 'DesktopPet' else target.size
                t_h = target.size_h if target.__class__.__name__ == 'DesktopPet' else target.size
                self.manage_tk_aura(target.canvas, t_w, t_h, False)
                target.current_state = 'falling'
                target.tk_master = None
            self.tk_target = None
                
        # FIX: Destrucción del vínculo si se hace clic en la víctima (Pokémon)
        if self.current_state == 'tk_lifted':
            self.current_state = 'falling'
            self.manage_tk_aura(self.canvas, self.size_w, self.size_h, False)
            master = getattr(self, 'tk_master', None)
            if master and master.current_state == 'tk_channeling':
                master.current_state = 'idle'
                master.manage_tk_aura(master.canvas, master.size_w, master.size_h, False)
                master.tk_target = None
            self.tk_master = None
                
        self.drag_offset_x = event.x
        self.drag_offset_y = event.y
        self.drag_start_x = self.window.winfo_pointerx()
        self.drag_start_y = self.window.winfo_pointery()
        self.is_dragging = False

    def on_drag_motion(self, event):
        if self.current_state in ['exiting', 'falling_pokeball', 'falling_egg', 'spawning_wild', 'despawning_wild']: return
        pointer_x = self.window.winfo_pointerx()
        pointer_y = self.window.winfo_pointery()

        if not getattr(self, 'is_dragging', False):
            if abs(pointer_x - getattr(self, 'drag_start_x', pointer_x)) > 5 or \
               abs(pointer_y - getattr(self, 'drag_start_y', pointer_y)) > 5:
                self.is_dragging = True
                self.current_state = 'dragged'
                self.v_x_velocity = 0.0
                self.v_y_velocity = 0.0
                self.climbing_surface = 'floor'
                self.surface_angle = 0
                self.last_drag_time = time.time()
                self.last_mouse_x = pointer_x
                self.last_mouse_y = pointer_y
            else:
                return

        self.x = pointer_x - self.drag_offset_x
        self.y = pointer_y - self.drag_offset_y
        self.update_position()

        current_time = time.time()
        dt = current_time - getattr(self, 'last_drag_time', current_time)
        if dt > 0:
            self.v_x_velocity = (pointer_x - self.last_mouse_x) / (dt * 150.0) 
            self.v_y_velocity = (pointer_y - self.last_mouse_y) / (dt * 150.0)
        
        self.last_mouse_x = pointer_x
        self.last_mouse_y = pointer_y
        self.last_drag_time = current_time

    def on_drag_release(self, event):
        if getattr(self, 'is_dragging', False):
            self.is_dragging = False
            self.anchored_hwnd = None
            v_x = getattr(self, 'v_x_velocity', 0.0)
            v_y = getattr(self, 'v_y_velocity', 0.0)
            if math.isnan(v_x) or math.isinf(v_x): v_x = 0.0
            if math.isnan(v_y) or math.isinf(v_y): v_y = 0.0
            self.v_x_velocity = max(-40.0, min(40.0, v_x))
            self.v_y_velocity = max(-40.0, min(40.0, v_y))
            self.current_state = 'thrown'

    def get_window_environment(self):
        current_env = {'y': self.default_floor_y, 'hwnd': None, 'rect': None}
        ahead_env = {'hwnd': None, 'rect': None, 'y': None}
        if not HAS_WIN32: return current_env, ahead_env
        
        pet_center_x = self.x + self.size_w // 2
        pet_feet_y = self.y
        CURRENT_PID = os.getpid()
        valid_windows = []
        
        fall_tolerance = 15
        if self.current_state in ['falling', 'falling_pokeball', 'falling_egg', 'falling_legendary']:
            f_speed = 12
            if self.current_state == 'falling' and getattr(self, 'heavy_fall', False):
                f_speed = 25
            elif self.current_state == 'falling_legendary': 
                f_speed = 20
            fall_tolerance = max(15, f_speed + 15)
        elif self.current_state in ['thrown', 'jumping_arc'] and getattr(self, 'v_y_velocity', 0) > 0:
            fall_tolerance = max(15, int(self.v_y_velocity) + 15)
        
        def win_enum_handler(hwnd, ctx):
            if not win32gui.IsWindowVisible(hwnd): return
            if win32gui.IsIconic(hwnd): return 
            try: _, pid = win32process.GetWindowThreadProcessId(hwnd)
            except: return
            
            if pid == CURRENT_PID:
                # FIX EXCEPCIÓN: Permitir colisión con Bill's PC ignorando el resto de las mascotas
                title = win32gui.GetWindowText(hwnd)
                if title != "Bill's PC":
                    return

            try:
                is_cloaked = ctypes.c_int(0)
                ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(is_cloaked), ctypes.sizeof(is_cloaked))
                if is_cloaked.value != 0: return
            except: pass
            try:
                ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                if ex_style & win32con.WS_EX_TRANSPARENT: return
            except: pass
            class_name = win32gui.GetClassName(hwnd)
            if class_name in ("Progman", "WorkerW", "Shell_TrayWnd", "EdgeUiInputTopWndClass", "DummyDWMWindow", "PopupHost"): return
            title = win32gui.GetWindowText(hwnd)
            if not title: return 
            rect = win32gui.GetWindowRect(hwnd)
            w_width = rect[2] - rect[0]
            w_height = rect[3] - rect[1]
            if w_width < 100 or w_height < 100: return
            placement = win32gui.GetWindowPlacement(hwnd)
            is_fullscreen = False
            if placement[1] == win32con.SW_SHOWMAXIMIZED: is_fullscreen = True
            else:
                try:
                    monitor = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
                    mon_info = win32api.GetMonitorInfo(monitor)
                    mon_w = mon_info['Monitor'][2] - mon_info['Monitor'][0]
                    mon_h = mon_info['Monitor'][3] - mon_info['Monitor'][1]
                    if w_width >= mon_w - 10 and w_height >= mon_h - 10: is_fullscreen = True
                except:
                    if w_width >= self.v_width and w_height >= (self.v_height - 10): is_fullscreen = True
            
            win_floor = rect[1] - self.size_h - self.offset_y
            valid_windows.append({'hwnd': hwnd, 'rect': rect, 'floor': win_floor, 'z': len(valid_windows), 'walkable': not is_fullscreen})
            
        win32gui.EnumWindows(win_enum_handler, None)
        
        under_windows = [w for w in valid_windows if w['walkable'] and w['rect'][0] <= pet_center_x <= w['rect'][2] and w['floor'] >= pet_feet_y - fall_tolerance]
        if under_windows:
            under_windows.sort(key=lambda w: w['floor'])
            for uw in under_windows:
                is_occluded = False
                check_y = uw['rect'][1] + 5
                for ow in valid_windows:
                    if ow['z'] < uw['z'] and ow['rect'][0] <= pet_center_x <= ow['rect'][2] and ow['rect'][1] <= check_y <= ow['rect'][3]:
                        is_occluded = True
                        break
                if not is_occluded:
                    current_env['y'] = uw['floor']
                    current_env['hwnd'] = uw['hwnd']
                    current_env['rect'] = uw['rect']
                    break
                    
        check_x = pet_center_x + (20 if self.is_facing_right else -20)
        step_windows = [w for w in valid_windows if w['walkable'] and w['rect'][0] <= check_x <= w['rect'][2] and abs(w['floor'] - pet_feet_y) > 30 and (pet_feet_y - 750) <= w['floor'] <= (pet_feet_y + 750)]
        if step_windows:
            random.shuffle(step_windows) 
            for sw in step_windows:
                is_occluded = False
                check_y = sw['rect'][1] + 5
                for ow in valid_windows:
                    if ow['z'] < sw['z'] and ow['rect'][0] <= check_x <= ow['rect'][2] and ow['rect'][1] <= check_y <= ow['rect'][3]:
                        is_occluded = True
                        break
                if not is_occluded:
                    ahead_env['y'] = sw['floor']
                    ahead_env['hwnd'] = sw['hwnd']
                    ahead_env['rect'] = sw['rect']
                    break
                    
        return current_env, ahead_env

    def recalculate_floor(self, pct):
        if self.is_flying and not getattr(self, 'is_egg', False):
            max_offset = self.v_height - self.size_h
            self.target_offset_y = int(max_offset * (pct / 100.0))
            self.target_floor_y = (self.v_y + self.v_height) - self.size_h - self.target_offset_y
            if self.current_state in ['idle', 'walking']: self.current_state = 'ascending'

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
            if getattr(self, 'egg_tk', None): self.canvas.itemconfig(self.canvas_image_id, image=self.egg_tk)
            self.window.after(random.randint(45000, 75000), self.egg_wiggle_loop)
            return
        rotated = self.egg_base_img.rotate(frames[step], expand=True, resample=Image.NEAREST)
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
        if step <= 60: self.evo_blend = step / 60.0
        elif step <= 100: self.evo_blend = 1.0
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
        if step <= 40: self.evo_blend = 1.0
        elif step <= 100: self.evo_blend = 1.0 - ((step - 40) / 60.0)
        else:
            self.evo_blend = 0.0
            if getattr(self, 'is_overflow', False):
                self.current_state = 'walking_away'
                self.is_facing_right = True
            else: self.current_state = 'idle'
            return
        self.window.after(50, lambda: self.finish_evolution_vfx(step+1))

    def hatch_egg(self):
        if self.current_state == 'exiting': return
        self.start_evolution_vfx(self.pet_data["species"], step=0)

    def gain_xp(self, amount):
        if self.is_egg or self.pet_data["level"] >= 100:
            self.pet_data["xp"] = 0
            return
        
        if time.time() < self.pet_data.get("xp_boost_expiry", 0):
            amount = int(amount * 1.5)
            
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
        font_config = ("Segoe UI", 10, "bold")
        x, y = self.size_w // 2, 15
        
        # Agrupamos el borde y el centro bajo el mismo tag ("vfx_lvl_group")
        offsets = [(-1, -1), (1, -1), (-1, 1), (1, 1)]
        for ox, oy in offsets:
            self.canvas.create_text(x + ox, y + oy, text="LEVEL UP!", fill="#000000", font=font_config, tags="vfx_lvl_group")
            
        self.canvas.create_text(x, y, text="LEVEL UP!", fill="#F10F0F", font=font_config, tags="vfx_lvl_group")
        
        def float_up(step):
            if step < 20 and self.current_state != 'exiting':
                self.canvas.move("vfx_lvl_group", 0, -1)
                
                # SOLUCIÓN MATEMÁTICA: Parpadeo de bloque entero.
                # Al ocultar y mostrar ambos elementos a la vez, el rojo nunca interactúa con el verde.
                estado = 'hidden' if (step // 2) % 2 == 0 else 'normal'
                self.canvas.itemconfig("vfx_lvl_group", state=estado)
                    
                self.window.after(50, lambda: float_up(step+1))
            else:
                self.canvas.delete("vfx_lvl_group")
        float_up(0)

    def show_heart_vfx(self):
        # Matriz estructurada: 0 = Vacío, 1 = Rojo (Relleno), 2 = Negro (Borde)
        heart_matrix = [
            [0, 2, 2, 0, 2, 2, 0],
            [2, 1, 1, 2, 1, 1, 2],
            [2, 1, 1, 1, 1, 1, 2],
            [0, 2, 1, 1, 1, 2, 0],
            [0, 0, 2, 1, 2, 0, 0],
            [0, 0, 0, 2, 0, 0, 0]
        ]
        pixel_size = 2 
        start_x = (self.size_w // 2) - ((7 * pixel_size) // 2)
        start_y = 10
        
        for row_idx, row in enumerate(heart_matrix):
            for col_idx, val in enumerate(row):
                if val != 0:
                    px = start_x + (col_idx * pixel_size)
                    py = start_y + (row_idx * pixel_size)
                    color = "#E74C3C" if val == 1 else "#000000"
                    self.canvas.create_rectangle(px, py, px+pixel_size, py+pixel_size, fill=color, outline=color, tags="vfx_heart")

        def float_up(step):
            if step < 20 and self.current_state != 'exiting':
                self.canvas.move("vfx_heart", 0, -1)
                self.window.after(50, lambda: float_up(step+1))
            else: 
                self.canvas.delete("vfx_heart")
        float_up(0)

    def manage_tk_aura(self, canvas, w, h, is_active):
        if is_active:
            canvas.delete("tk_aura") 
            t = time.time()
            cx, cy = w / 2, h / 2
            base_radius = max(w, h) * 0.6
            
            # Enjambre de 24 partículas psíquicas generadas matemáticamente en tiempo real
            for i in range(24):
                # 1. Velocidad asimétrica (Algunas partículas van rápido, otras lento, otras al revés)
                speed = 1.5 + (math.sin(i * 7.1) * 2.0)
                angle = (t * speed) + (i * 0.8)
                
                # 2. Dispersión del radio (Rompe la circunferencia para crear una nube caótica)
                scatter = math.cos(i * 13.3) * (base_radius * 0.5)
                r = base_radius + scatter
                
                px = cx + math.cos(angle) * r
                py = cy + math.sin(angle) * r
                
                # 3. Fase de parpadeo individual basada en el tiempo
                blink_phase = math.sin(t * 12.0 + i * 3.14)
                
                if blink_phase > 0.5:
                    color = "#FFFFFF" # Destello blanco intenso
                    size = 2
                elif blink_phase > -0.3:
                    color = "#D24DFF" # Morado de energía base
                    size = 1
                else:
                    continue # Partícula invisible (simula que se apaga del todo)
                
                canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color, tags="tk_aura")
                
            canvas.tag_lower("tk_aura") # Forzar la nube por detrás del sprite
        else:
            canvas.delete("tk_aura")

    def trigger_landing_shake(self):
        self.current_state = 'landing_shake'
        self.shake_timer = 25
        
        # ONDA SÍSMICA (Seismic Shockwave)
        if getattr(self, 'get_all_pets', None):
            for other in self.get_all_pets():
                if other != self and other.current_state in ['idle', 'walking', 'socializing', 'attacking'] and not getattr(other, 'is_flying', False) and not getattr(other, 'is_egg', False):
                    # FIX: Calcular el suelo físico real (las suelas de los pies), no el anclaje superior
                    my_floor = self.floor_y + self.size_h + getattr(self, 'offset_y', 0)
                    other_floor = other.floor_y + other.size_h + getattr(other, 'offset_y', 0)
                    
                    # Rango de impacto aumentado a 400px para que se note el efecto de masa
                    if abs(my_floor - other_floor) < 25 and abs(other.x - self.x) < 400:
                        other.current_state = 'jumping_arc'
                        other.jump_target_y = other.floor_y
                        other.v_y_velocity = -5.0 
                        other.v_x_velocity = 0.0
                        other.anchored_hwnd = None

    def _fsm_tk_lifted(self):
        if not hasattr(self, 'tk_master') or not self.tk_master.window.winfo_exists() or self.tk_master.current_state != 'tk_channeling':
            self.current_state = 'falling'
            self.manage_tk_aura(self.canvas, self.size_w, self.size_h, False)
        self.window.after(30, self.physics_loop)

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
            self.window.after(30, self.physics_loop) 
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
                self.window.after(30, self.physics_loop)
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
                    # FIX: Lanzamiento orgánico en la mitad superior de la órbita (math.sin < -0.1)
                    # El 20% de probabilidad hace que suelte el objeto en un punto distinto cada vez
                    if math.sin(angle) < -0.1 and (random.randint(1, 100) <= 20 or math.cos(angle) > 0.9):
                        self.current_state = 'idle'
                        self.tk_cooldown = 3000
                        target.current_state = 'thrown'
                        
                        # Calcula un arco parabólico estrictamente superior (entre 180 y 360 grados)
                        launch_angle = random.uniform(math.pi + 0.2, 2 * math.pi - 0.2)
                        
                        # ASIGNACIÓN DE FUERZA MASIVA SEGÚN LA MASA DEL OBJETIVO
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
        self.window.after(30, self.physics_loop)

    def check_evolution(self):
        if self.pet_data.get("everstone", False): return
        rpg = self.config.get("rpg_data", {})
        evo_level = rpg.get("evolution_level", 99)
        evolves_to = rpg.get("evolves_to", [])
        last_evo = self.pet_data.get("last_evolution_level", 1)
        if self.pet_data["level"] >= evo_level and (self.pet_data["level"] - last_evo) >= 5 and evolves_to and evolves_to[0] != "none":
            self.start_evolution_vfx(random.choice(evolves_to), step=0)

    def load_config(self):
        try:
            with open(os.path.join(self.pet_dir, "config.json"), "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            sys.exit(1)

    def animate_egg_spawn(self, step):
        if self.current_state != 'falling_egg': return 
        if not getattr(self, 'egg_base_img', None):
            self.canvas.itemconfig(self.canvas_image_id, state='normal')
            self.current_state = 'egg_idle'
            return
        w, h = self.size_w, self.size_h
        rotated = self.egg_base_img.rotate(step * -15, expand=True, resample=Image.NEAREST)
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
            except: pass 
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
                cx = center_x - (center_x * progress)
                cy = center_y + (w_height - center_y) * progress + parabola
                size = max(4, int(64 * (1 - progress)))
                rotation = -360 * progress

            rotated = self.pb_base_img.rotate(rotation, expand=False, resample=Image.NEAREST).resize((size, size), Image.Resampling.NEAREST)
            self.vfx_img = ImageTk.PhotoImage(rotated)
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
        frames_up, pause, frames_down = 15, 10, 15
        if step == 0:
            try:
                asset_name = "cloud.png" if self.is_flying else "tallGrass.png"
                self.spawn_vfx_raw = Image.open(os.path.join(self.base_dir, "game_env", "ui", asset_name)).convert("RGBA")
            except: self.spawn_vfx_raw = None

        if not getattr(self, 'spawn_vfx_raw', None):
            self.on_remove(self)
            return

        w, h = self.size_w, self.size_h
        if step <= frames_up: offset_y = h - int((h/1.5) * (step / frames_up))
        elif step <= frames_up + pause:
            offset_y = h - int(h/1.5)
            if step == frames_up + (pause // 2): self.canvas.itemconfig(self.canvas_image_id, state='hidden')
        elif step <= frames_up + pause + frames_down: offset_y = (h - int(h/1.5)) + int((h/1.5) * ((step - frames_up - pause) / frames_down))
        else:
            self.canvas.delete("spawn_vfx")
            self.on_remove(self)
            return

        self.vfx_tk = ImageTk.PhotoImage(self.spawn_vfx_raw.resize((w, int(h/1.5)), Image.Resampling.NEAREST))
        self.canvas.delete("spawn_vfx")
        self.canvas.create_image(w//2, offset_y, image=self.vfx_tk, anchor=tk.N, tags="spawn_vfx")
        self.window.after(30, lambda: self.animate_wild_despawn(step + 1))

    def animate_wild_spawn(self, step):
        frames_up, pause, frames_down = 15, 10, 15
        if step == 0:
            try:
                asset_name = "cloud.png" if self.is_flying else "tallGrass.png"
                self.spawn_vfx_raw = Image.open(os.path.join(self.base_dir, "game_env", "ui", asset_name)).convert("RGBA")
            except: self.spawn_vfx_raw = None

        if not getattr(self, 'spawn_vfx_raw', None):
            self.canvas.itemconfig(self.canvas_image_id, state='normal')
            self.current_state = 'idle'
            self.play_shiny_sound()
            return

        w, h = self.size_w, self.size_h
        if step <= frames_up: offset_y = h - int((h/1.5) * (step / frames_up))
        elif step <= frames_up + pause:
            offset_y = h - int(h/1.5)
            if step == frames_up + (pause // 2):
                self.canvas.itemconfig(self.canvas_image_id, state='normal')
                self.canvas.tag_lower(self.canvas_image_id, "spawn_vfx")
                self.play_shiny_sound()
        elif step <= frames_up + pause + frames_down: offset_y = (h - int(h/1.5)) + int((h/1.5) * ((step - frames_up - pause) / frames_down))
        else:
            self.canvas.delete("spawn_vfx")
            self.current_state = 'idle'
            return

        self.vfx_tk = ImageTk.PhotoImage(self.spawn_vfx_raw.resize((w, int(h/1.5)), Image.Resampling.NEAREST))
        self.canvas.delete("spawn_vfx")
        self.canvas.create_image(w//2, offset_y, image=self.vfx_tk, anchor=tk.N, tags="spawn_vfx")
        self.window.after(30, lambda: self.animate_wild_spawn(step + 1))

    def animate_owned_spawn(self, step):
        if self.current_state != 'falling_pokeball': return 
        if step == 0:
            try:
                pb_dir = os.path.join(self.base_dir, "game_env", "ui")
                available_pbs = [f for f in os.listdir(pb_dir) if f.startswith("pokeball") and f.endswith(".png")]
                pb_file = random.choice(available_pbs) if available_pbs else "pokeball.png"
                raw_img = Image.open(os.path.join(pb_dir, pb_file)).convert("RGBA")
                r, g, b, a = raw_img.split()
                a = a.point(lambda p: 255 if p > 127 else 0) 
                self.pb_raw = Image.merge("RGBA", (r, g, b, a))
            except: self.pb_raw = None

        if not getattr(self, 'pb_raw', None):
            self.canvas.itemconfig(self.canvas_image_id, state='normal')
            self.current_state = 'falling_pokeball'
            return

        w, h = self.size_w, self.size_h
        rotated = self.pb_raw.rotate(step * -15, expand=False, resample=Image.NEAREST)
        self.pb_tk = ImageTk.PhotoImage(rotated.resize((max(1, w//2), max(1, h//2)), Image.Resampling.NEAREST))
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
                # FIX: Al hacerle doble clic, se vuelve la estrella de Discord
                if self.game_controller and hasattr(self.game_controller, 'discord_rpc'):
                    self.game_controller.discord_rpc.set_target(self)

    def update_position(self):
        self.window.geometry(f"+{int(self.x)}+{int(self.y)}")

    def animate_loop(self):
        if self.current_state == 'exiting': return 
        
        # Sincronización de Anclaje a 60 FPS (Física de Arrastre de Ventana)
        if getattr(self, 'anchored_hwnd', None) and self.current_state in ['idle', 'walking', 'socializing', 'attacking']:
            try:
                if HAS_WIN32 and win32gui.IsWindowVisible(self.anchored_hwnd) and not win32gui.IsIconic(self.anchored_hwnd):
                    new_rect = win32gui.GetWindowRect(self.anchored_hwnd)
                    old_rect = getattr(self, 'anchored_rect', new_rect)
                    
                    delta_l = new_rect[0] - old_rect[0]
                    delta_t = new_rect[1] - old_rect[1]
                    delta_r = new_rect[2] - old_rect[2]
                    delta_b = new_rect[3] - old_rect[3]

                    # FILTRO ANTI-TELETRANSPORTE (Si la ventana se minimiza o cambia de escritorio virtual)
                    if abs(delta_l) > 2000 or abs(delta_t) > 2000:
                        self.anchored_hwnd = None
                        self.anchored_rect = None
                    elif delta_l != 0 or delta_t != 0 or delta_r != 0 or delta_b != 0:
                        surface = getattr(self, 'climbing_surface', 'floor')

                        if surface == 'floor':
                            self.x += delta_l
                            self.y += delta_t
                            self.floor_y += delta_t
                        elif surface == 'wall_l':
                            self.x += delta_l
                            self.y += delta_t
                        elif surface == 'wall_r':
                            self.x += delta_r
                            self.y += delta_t
                        elif surface == 'ceiling':
                            self.x += delta_l
                            self.y += delta_b

                        self.update_position()
                        self.anchored_rect = new_rect
                else: 
                    self.anchored_hwnd = None
                    self.anchored_rect = None 
            except: 
                pass 

        blend = getattr(self, 'evo_blend', 0.0)
        
        # INVERSIÓN VISUAL
        render_facing_right = self.is_facing_right
        if getattr(self, 'is_climbing', False):
            surface = getattr(self, 'climbing_surface', 'floor')
            if surface in ['screen_l', 'screen_r']:
                render_facing_right = not self.is_facing_right

        if getattr(self, 'is_egg', False):
            if blend > 0.0 and getattr(self, 'egg_base_img', None):
                white_layer = Image.new("RGBA", self.egg_base_img.size, (255, 255, 255, 255))
                white_layer.putalpha(self.egg_base_img.split()[3]) 
                blended = Image.blend(self.egg_base_img, white_layer, blend)
                self.egg_tk = ImageTk.PhotoImage(blended)
                self.canvas.itemconfig(self.canvas_image_id, image=self.egg_tk)
            elif getattr(self, 'egg_tk', None) and self.current_state != 'egg_wiggle':
                self.canvas.itemconfig(self.canvas_image_id, image=self.egg_tk)
        else:
            target_ms = self.frame_rate_active if self.current_state in ['walking', 'falling', 'walking_away', 'jumping_arc', 'climbing', 'attacking', 'eating'] else self.frame_rate_idle
            self.animator.update_animation(self.current_state, render_facing_right, self.canvas_image_id, True, target_ms, blend_factor=blend, rotation_angle=self.surface_angle)
        self.window.after(16, self.animate_loop)

    def physics_loop(self):
        # Motor dinámico: Si el estado no está en el diccionario, lo busca por nombre
        handler = self.fsm.get(self.current_state)
        if handler:
            handler()
        elif hasattr(self, f"_fsm_{self.current_state}"):
            getattr(self, f"_fsm_{self.current_state}")()
        else:
            self._fsm_active()

    def _fsm_exiting(self):
        pass 

    def _fsm_wait(self):
        self.window.after(50, self.physics_loop)

    def _fsm_thrown(self):
        if getattr(self, 'is_flying', False):
            self.v_x_velocity *= 0.92 
            self.v_y_velocity *= 0.92 
            self.y += self.v_y_velocity
            self.x += self.v_x_velocity

            if getattr(self, 'can_screen_wrap', False):
                if self.x <= self.v_x - self.size_w: self.x = self.v_x + self.v_width
                elif self.x >= self.v_x + self.v_width: self.x = self.v_x - self.size_w
            else:
                if self.x <= self.v_x:
                    self.x = self.v_x
                    self.v_x_velocity *= -0.7 
                    self.is_facing_right = True
                elif self.x >= (self.v_x + self.v_width) - self.size_w:
                    self.x = (self.v_x + self.v_width) - self.size_w
                    self.v_x_velocity *= -0.7
                    self.is_facing_right = False
                
            current_env, _ = self.get_window_environment()
            fall_tolerance = max(15, int(self.v_y_velocity) + 15) if getattr(self, 'v_y_velocity', 0) > 0 else 15
            physical_floor = current_env['y'] if self.y <= current_env['y'] + fall_tolerance else self.default_floor_y

            if self.y >= physical_floor and self.v_y_velocity > 0:
                self.y = physical_floor
                self.v_y_velocity *= -0.5
                
            if self.y < self.v_y:
                self.y = self.v_y
                self.v_y_velocity *= -0.5

            if abs(self.v_x_velocity) < 1.0 and abs(self.v_y_velocity) < 1.0:
                self.v_x_velocity = 0
                self.v_y_velocity = 0
                self.floor_y = self.y 
                if getattr(self, 'is_overflow', False):
                    self.current_state = 'walking_away'
                    self.is_facing_right = True
                else:
                    self.current_state = 'ascending'

        elif getattr(self, 'is_climbing', False) or self.config.get("physics", {}).get("is_climbing", False):
            self.is_climbing = True
            self.v_y_velocity += 1.5 
            self.v_x_velocity *= 0.95 
            self.y += self.v_y_velocity
            self.x += self.v_x_velocity
            
            wall_offset = getattr(self, 'climb_offset_x', 0)
            ceil_offset = getattr(self, 'climb_offset_y', 0)
            current_env, _ = self.get_window_environment()
            
            if self.y <= self.v_y + 15:
                self.y = self.v_y + ceil_offset
                self.v_x_velocity = 0; self.v_y_velocity = 0
                self.climbing_surface = 'screen_ceiling'
                self.surface_angle = 180
                if getattr(self, 'is_overflow', False):
                    self.current_state = 'walking_away'
                    self.is_facing_right = True
                else:
                    self.current_state = 'idle'
            elif self.x <= self.v_x:
                self.x = self.v_x + wall_offset
                self.v_x_velocity = 0; self.v_y_velocity = 0
                self.climbing_surface = 'screen_l'
                self.surface_angle = 270
                if getattr(self, 'is_overflow', False):
                    self.current_state = 'walking_away'
                    self.is_facing_right = True
                else:
                    self.current_state = 'idle'
            elif self.x >= (self.v_x + self.v_width) - self.size_w:
                self.x = self.v_x + self.v_width - self.size_w - wall_offset
                self.v_x_velocity = 0; self.v_y_velocity = 0
                self.climbing_surface = 'screen_r'
                self.surface_angle = 90
                if getattr(self, 'is_overflow', False):
                    self.current_state = 'walking_away'
                    self.is_facing_right = True
                else:
                    self.current_state = 'idle'
            else:
                fall_tolerance = max(15, int(self.v_y_velocity) + 15) if self.v_y_velocity > 0 else 15
                physical_floor = current_env['y'] if self.y <= current_env['y'] + fall_tolerance else self.default_floor_y
                if self.v_y_velocity > 0 and self.y >= physical_floor:
                    self.y = physical_floor
                    self.floor_y = physical_floor
                    self.v_x_velocity = 0; self.v_y_velocity = 0
                    self.climbing_surface = 'floor'
                    self.surface_angle = 0
                    
                    if getattr(self, 'is_overflow', False):
                        self.current_state = 'walking_away'
                        self.is_facing_right = True
                    else:
                        self.current_state = 'idle'
                        
                    if current_env['hwnd']:
                        self.anchored_hwnd = current_env['hwnd']
                        self.anchored_rect = current_env['rect']
        else:
            gravity = 4.0 if getattr(self, 'heavy_fall', False) and self.v_y_velocity >= -0.5 else 1.5
            self.v_y_velocity += gravity
            self.v_x_velocity *= 0.95 
            self.y += self.v_y_velocity
            self.x += self.v_x_velocity

            if getattr(self, 'can_screen_wrap', False):
                if self.x <= self.v_x - self.size_w: self.x = self.v_x + self.v_width
                elif self.x >= self.v_x + self.v_width: self.x = self.v_x - self.size_w
            else:
                if self.x <= self.v_x:
                    self.x = self.v_x
                    self.v_x_velocity *= -0.7 
                    self.is_facing_right = True
                elif self.x >= (self.v_x + self.v_width) - self.size_w:
                    self.x = (self.v_x + self.v_width) - self.size_w
                    self.v_x_velocity *= -0.7
                    self.is_facing_right = False

            current_env, _ = self.get_window_environment()
            
            # FIX ANTITRASPASO: Absorbe la tolerancia calculada en get_window_environment
            fall_tolerance = max(15, int(self.v_y_velocity) + 15) if self.v_y_velocity > 0 else 15
            physical_floor = current_env['y'] if self.y <= current_env['y'] + fall_tolerance else self.default_floor_y

            # (El resto de _fsm_thrown queda igual, cambia solo este último bloque)
            if self.v_y_velocity > 0 and self.y >= physical_floor:
                self.y = physical_floor
                self.floor_y = physical_floor
                self.v_x_velocity = 0
                
                # GATILLO DE VIBRACIÓN INTERNA DEL POKÉMON (Ajustado a 0.75s)
                if getattr(self, 'heavy_fall', False) and self.v_y_velocity > 15:
                    self.trigger_landing_shake()
                else:
                    if getattr(self, 'is_overflow', False):
                        self.current_state = 'walking_away'
                        self.is_facing_right = True
                    else:
                        self.current_state = 'egg_idle' if getattr(self, 'is_egg', False) else 'idle'
            
        self.update_position()
        self.window.after(20, self.physics_loop)

    def _fsm_jumping_arc(self):
        gravity = 1.5
        if getattr(self, 'heavy_fall', False) and self.v_y_velocity >= -0.5:
            gravity = 4.0

        self.v_y_velocity += gravity
        self.y += self.v_y_velocity
        self.x += (self.speed * 1.5) if self.is_facing_right else -(self.speed * 1.5)
        
        if getattr(self, 'can_screen_wrap', False):
            if self.x <= self.v_x - self.size_w: self.x = self.v_x + self.v_width
            elif self.x >= self.v_x + self.v_width: self.x = self.v_x - self.size_w
        else:
            self.x = max(self.v_x, min(self.x, (self.v_x + self.v_width) - self.size_w))

        target_y = getattr(self, 'jump_target_y', getattr(self, 'floor_y', self.default_floor_y))
        
        if self.v_y_velocity > 0 and self.y >= target_y:
            self.y = target_y
            self.floor_y = target_y
            
            # GATILLO DE VIBRACIÓN INTERNA DEL POKÉMON
            if getattr(self, 'heavy_fall', False) and self.v_y_velocity > 15:
                    self.trigger_landing_shake()
            else:
                if getattr(self, 'is_overflow', False):
                    self.current_state = 'walking_away'
                    self.is_facing_right = True
                else:
                    self.current_state = 'walking' 
            
            current_env, _ = self.get_window_environment()
            if current_env['hwnd']:
                self.anchored_hwnd = current_env['hwnd']
                self.anchored_rect = current_env['rect']
            else:
                self.anchored_hwnd = None
                
            if hasattr(self, 'jump_target_y'): delattr(self, 'jump_target_y')
            
        self.update_position()
        self.window.after(30, self.physics_loop)

    def _fsm_ascending(self):
        if self.floor_y > getattr(self, 'target_floor_y', self.floor_y):
            self.floor_y -= 5
            if self.floor_y <= getattr(self, 'target_floor_y', self.floor_y):
                self.floor_y = self.target_floor_y
                if getattr(self, 'is_overflow', False):
                    self.current_state = 'walking_away'
                    self.is_facing_right = True
                else:
                    self.current_state = 'idle'
        elif self.floor_y < getattr(self, 'target_floor_y', self.floor_y):
            self.floor_y += 5
            if self.floor_y >= getattr(self, 'target_floor_y', self.floor_y):
                self.floor_y = self.target_floor_y
                if getattr(self, 'is_overflow', False):
                    self.current_state = 'walking_away'
                    self.is_facing_right = True
                else:
                    self.current_state = 'idle'
        else:
            if getattr(self, 'is_overflow', False):
                self.current_state = 'walking_away'
                self.is_facing_right = True
            else:
                self.current_state = 'idle'
            
        self.fly_amplitude += 0.2
        self.y = self.floor_y + math.sin(self.fly_amplitude) * 10
        self.update_position()
        self.window.after(50, self.physics_loop)

    def _fsm_teleporting_out(self):
        self.teleport_step -= 0.15
        if self.teleport_step <= 0:
            self.window.attributes('-alpha', 0.0)
            
            # 1. Elegimos la nueva coordenada X al azar
            self.x = random.randint(self.v_x, self.v_x + self.v_width - self.size_w)
            
            # 2. Lógica de reubicación en Y
            if getattr(self, 'is_flying', False):
                self.y = getattr(self, 'target_floor_y', self.default_floor_y)
                self.floor_y = self.y
                self.anchored_hwnd = None
                self.anchored_rect = None
            else:
                # TRUCO DEL RADAR: Movemos temporalmente al Pokémon al límite superior del monitor 
                # para que el escáner barra toda la pantalla hacia abajo buscando ventanas.
                self.y = self.v_y 
                current_env, _ = self.get_window_environment()
                
                if current_env['hwnd']:
                    # Ha encontrado una ventana en esta X. Se ancla y aparece encima.
                    self.anchored_hwnd = current_env['hwnd']
                    self.anchored_rect = current_env['rect']
                    self.floor_y = self.anchored_rect[1] - self.size_h - getattr(self, 'offset_y', 0)
                    self.y = self.floor_y
                else:
                    # No hay ninguna ventana. Va al suelo base.
                    self.anchored_hwnd = None
                    self.anchored_rect = None
                    self.floor_y = self.default_floor_y
                    self.y = self.default_floor_y
                    
            self.current_state = 'teleporting_in'
        else:
            self.window.attributes('-alpha', self.teleport_step)
            
        self.update_position()
        self.window.after(30, self.physics_loop)

    def _fsm_teleporting_in(self):
        self.teleport_step += 0.15
        if self.teleport_step >= 1.0:
            self.teleport_step = 1.0
            self.window.attributes('-alpha', 1.0)
            self.current_state = 'idle'
        else:
            self.window.attributes('-alpha', self.teleport_step)
            
        self.update_position()
        self.window.after(30, self.physics_loop)

    def _fsm_walking_away(self):
        self.x += self.speed
        if self.x > self.v_x + self.v_width:
            self.on_remove(self)
            self.window.destroy()
            return
            
        if self.is_flying:
            self.fly_amplitude += 0.2
            self.y = self.floor_y + math.sin(self.fly_amplitude) * 10
        else:
            current_env, _ = self.get_window_environment()
            physical_floor = current_env['y'] if self.y <= current_env['y'] + 15 else self.default_floor_y
            
            # Efecto Lemming: Si pierden el suelo (ej: caen de una ventana mientras huyen), activan la caída libre
            if self.y < physical_floor - 15:
                self.current_state = 'falling'
                self.v_y_velocity = 0.0
                
        self.update_position()
        self.window.after(50, self.physics_loop)

    def _fsm_falling(self):
        # Aislamos la velocidad pesada solo al cuerpo del Pokémon
        fall_speed = 12
        if self.current_state == 'falling' and getattr(self, 'heavy_fall', False):
            fall_speed = 25
        elif self.current_state == 'falling_legendary': 
            fall_speed = 20

        self.y += fall_speed
        self.x += getattr(self, 'v_x_velocity', 0.0)
        
        if getattr(self, 'can_screen_wrap', False):
            if self.x <= self.v_x - self.size_w: self.x = self.v_x + self.v_width
            elif self.x >= self.v_x + self.v_width: self.x = self.v_x - self.size_w
        else:
            self.x = max(self.v_x, min(self.x, (self.v_x + self.v_width) - self.size_w))

        current_env, _ = self.get_window_environment()
        
        fall_tolerance = max(15, fall_speed + 15)
        target_y = current_env['y'] if self.y <= current_env['y'] + fall_tolerance else self.default_floor_y

        if self.is_flying and self.current_state == 'falling_legendary':
            target_y = getattr(self, 'target_floor_y', target_y)

        if self.y >= target_y:
            self.y = target_y
            if self.is_flying and self.current_state == 'falling_legendary': 
                self.floor_y = target_y

            if self.current_state == 'falling_egg':
                self.current_state = 'egg_idle'
                self.canvas.delete("spawn_egg")
                self.canvas.itemconfig(self.canvas_image_id, state='normal')
            elif self.current_state == 'falling_pokeball':
                self.current_state = 'idle'
                self.canvas.delete("spawn_pb")
                self.canvas.itemconfig(self.canvas_image_id, state='normal')
                self.play_shiny_sound()
                try:
                    snd_path = os.path.join(self.base_dir, "game_env", "sounds", "return.wav")
                    if os.path.exists(snd_path):
                        import pygame
                        if not hasattr(self, 'return_sound'):
                            self.return_sound = pygame.mixer.Sound(snd_path)
                            self.return_sound.set_volume(0.01)
                        self.return_sound.play()
                except: pass
                
                if getattr(self, 'is_flying', False):
                    self.floor_y = self.y 
                    self.current_state = 'ascending'
            elif self.current_state == 'falling_legendary':
                self.play_shiny_sound()
                if getattr(self, 'is_flying', False): 
                    self.current_state = 'idle'
                else:
                    self.v_y_velocity = -8.0
                    self.current_state = 'legendary_bounce'
            # (El resto de _fsm_falling queda igual, cambia solo este último bloque tras los IF de legendarios)
            else:
                if getattr(self, 'is_flying', False) and getattr(self, 'target_floor_y', self.y) != self.y:
                    self.floor_y = self.y
                    self.current_state = 'ascending'
                else:
                    # FIX: En estado de caída directa, la velocidad está bloqueada matemáticamente, 
                    # por lo que no es necesario evaluar self.v_y_velocity.
                    if getattr(self, 'heavy_fall', False):
                        self.trigger_landing_shake()
                    else:
                        if getattr(self, 'is_overflow', False):
                            self.current_state = 'walking_away'
                            self.is_facing_right = True
                        else:
                            self.current_state = 'idle'
        self.update_position()
        self.window.after(20, self.physics_loop)

    def _fsm_socializing(self):
        self.social_timer -= 1
        if self.social_timer <= 0:
            self.current_state = 'idle'
        else:
            if self.is_flying:
                self.fly_amplitude += 0.2
                self.y = self.floor_y + math.sin(self.fly_amplitude) * 10
            else:
                if self.y < self.floor_y:
                    self.v_y_velocity += 1.5 
                    self.y += self.v_y_velocity
                    if self.y >= self.floor_y:
                        self.y = self.floor_y
                        self.v_y_velocity = 0.0
                else:
                    phase = (self.social_timer // 8) % 2
                    my_turn = (phase == 0) if self.is_facing_right else (phase == 1)
                    if my_turn and self.social_timer % 8 == 0:
                        self.v_y_velocity = -5.0
                        self.y += self.v_y_velocity
        self.update_position()
        self.window.after(50, self.physics_loop)

    def _fsm_attacking(self):
        if not getattr(self, 'attack_target', None) or not self.attack_target.window.winfo_exists() or self.attack_target.current_state not in ['attacking', 'thrown']:
            self.current_state = 'idle'
            self.attack_target = None
            self.update_position()
            self.window.after(30, self.physics_loop)
            return

        current_time = time.time()
        if not hasattr(self, 'attack_phase_wait_until'):
            self.attack_phase_wait_until = 0.0

        if current_time < self.attack_phase_wait_until:
            self.update_position()
            self.window.after(30, self.physics_loop)
            return

        target = self.attack_target
        dist = abs(self.x - target.x)
        push_dir = 1 if self.is_facing_right else -1

        if not hasattr(self, 'attack_phase'):
            self.attack_phase = 0

        def advance_phase(next_phase, pause=True):
            self.attack_phase = next_phase
            if pause:
                self.attack_phase_wait_until = time.time() + 0.5 
            else:
                self.attack_phase_wait_until = 0.0

        self.is_facing_right = (target.x > self.x)

        if self.attack_phase == 0:
            if dist < 50: 
                self.x -= 3.0 * push_dir 
            elif dist > 55:
                self.x += 3.0 * push_dir 
            else: 
                advance_phase(1, pause=True)

        elif self.attack_phase == 1:
            self.x += 10.0 * push_dir
            if dist <= self.size_w * 0.4: 
                advance_phase(2, pause=False)
                self.v_x_velocity = -1.5 * push_dir
                self.v_y_velocity = -5.0

        elif self.attack_phase == 2:
            target_y = getattr(self, 'target_floor_y', self.floor_y) if self.is_flying else self.floor_y
            
            if self.y < target_y or self.v_y_velocity != 0:
                self.v_y_velocity += 1.0
                self.y += self.v_y_velocity
                self.x += self.v_x_velocity
                
                if self.y >= target_y and self.v_y_velocity > 0:
                    self.y = target_y
                    self.v_y_velocity = 0
                    self.v_x_velocity = 0
            else:
                if dist < 75:
                    self.x -= 3.0 * push_dir 
                else:
                    advance_phase(3, pause=True)

        elif self.attack_phase == 3:
            self.x += 12.0 * push_dir
            if dist <= self.size_w * 0.4: 
                advance_phase(4, pause=False)
                self.v_x_velocity = -2.0 * push_dir
                self.v_y_velocity = -6.0

        elif self.attack_phase == 4:
            target_y = getattr(self, 'target_floor_y', self.floor_y) if self.is_flying else self.floor_y
            
            if self.y < target_y or self.v_y_velocity != 0:
                self.v_y_velocity += 1.0
                self.y += self.v_y_velocity
                self.x += self.v_x_velocity
                
                if self.y >= target_y and self.v_y_velocity > 0:
                    self.y = target_y
                    self.v_y_velocity = 0
                    self.v_x_velocity = 0
            else:
                if dist < 100:
                    self.x -= 4.0 * push_dir 
                else:
                    advance_phase(5, pause=True)

        elif self.attack_phase == 5:
            self.x += 20.0 * push_dir
            
            has_crossed = (push_dir == 1 and self.x >= target.x) or (push_dir == -1 and self.x <= target.x)
            
            if dist <= self.size_w * 0.5 or has_crossed: 
                self.attack_phase = 6
                
                # --- SISTEMA DE MASA Y POTENCIA RELATIVA ---
                # Poder = Nivel + (Mitad del tamaño geométrico)
                my_power = self.pet_data['level'] + (self.size_w * 0.5)
                target_power = target.pet_data['level'] + (target.size_w * 0.5)
                
                # Ratio de impacto = Fuerza del enemigo / Mi propia masa
                # Limitado matemáticamente entre 0.4x y 2.0x para evitar colapsar la pantalla
                my_knockback_ratio = max(0.4, min(4.0, target_power / max(1, my_power)))
                target_knockback_ratio = max(0.4, min(4.0, my_power / max(1, target_power)))
                
                target_is_soft = not getattr(target, 'heavy_fall', False) or not getattr(target, 'aggressive', False)
                self_is_soft = not getattr(self, 'heavy_fall', False) or not getattr(self, 'aggressive', False)
                
                # Qué le ocurre al ATACANTE (self)
                if getattr(self, 'heavy_fall', False) and target_is_soft:
                    self.current_state = 'landing_shake'
                    self.shake_timer = 25 
                    self.v_x_velocity = 0.0
                    self.v_y_velocity = 0.0
                else:
                    self.current_state = 'thrown' 
                    self.v_x_velocity = -(25.0 * my_knockback_ratio) * push_dir 
                    # El eje Y se limita a 1.5 máximo para evitar que el salto rompa el radar de techo
                    self.v_y_velocity = -(15.0 * min(1.5, my_knockback_ratio))            
                
                # Qué le ocurre al RECEPTOR (target)
                if target and getattr(target, 'current_state', '') == 'attacking':
                    if getattr(target, 'heavy_fall', False) and self_is_soft:
                        target.current_state = 'landing_shake'
                        target.shake_timer = 25 
                        target.v_x_velocity = 0.0
                        target.v_y_velocity = 0.0
                    else:
                        target.current_state = 'thrown'
                        target.v_x_velocity = (25.0 * target_knockback_ratio) * push_dir 
                        target.v_y_velocity = -(15.0 * min(1.5, target_knockback_ratio))
                        
                    target.attack_target = None
                    target.attack_phase = 0
                    
                self.attack_target = None

        if not self.is_flying and self.current_state != 'thrown':
            self.x = max(self.v_x, min(self.x, (self.v_x + self.v_width) - self.size_w))

        if self.is_flying and getattr(self, 'attack_phase', 0) in [0, 1, 3, 5]:
            self.fly_amplitude += 0.2
            self.y = self.floor_y + math.sin(self.fly_amplitude) * 10
            
        self.update_position()
        self.window.after(30, self.physics_loop)

    def _fsm_eating(self):
        self.eating_timer -= 1
        if self.eating_timer <= 0:
            self.current_state = 'idle'
            if self.interaction_target:
                self.interaction_target.destroy()
                self.interaction_target = None
                self.pet_data["xp_boost_expiry"] = time.time() + 1800 
                if self.game_controller: self.game_controller.sync_save_state()
        else:
            if self.is_flying:
                self.fly_amplitude += 0.2
                self.y = self.floor_y + math.sin(self.fly_amplitude) * 10
            else:
                if self.y < self.floor_y:
                    self.v_y_velocity += 1.5 
                    self.y += self.v_y_velocity
                    if self.y >= self.floor_y:
                        self.y = self.floor_y
                        self.v_y_velocity = 0.0
                else:
                    if self.eating_timer in [20, 10]:
                        self.v_y_velocity = -4.0
                        self.y += self.v_y_velocity
        self.update_position()
        self.window.after(50, self.physics_loop)

    def _fsm_active(self):
        self.jump_cooldown = max(0, getattr(self, 'jump_cooldown', 0) - 1)
        self.social_cooldown = max(0, getattr(self, 'social_cooldown', 0) - 1)
        self.attack_cooldown = max(0, getattr(self, 'attack_cooldown', 0) - 1)
        self.teleport_cooldown = max(0, getattr(self, 'teleport_cooldown', 0) - 1)

        self.tk_cooldown = max(0, getattr(self, 'tk_cooldown', 0) - 1)
        
        if getattr(self, 'telekinetic', False) and self.tk_cooldown == 0 and self.current_state in ['idle', 'walking']:
            if random.randint(1, 1000) <= 8: # Probabilidad de activar poderes
                target = None
                if self.game_controller:
                    # 1. Prioriza atraer Bayas (Alcance de 400 -> 800)
                    for b in getattr(self.game_controller, 'active_berries', []):
                        if b.current_state not in ['exiting', 'tk_controlled'] and abs(b.x - self.x) < 800:
                            target = b; break
                    # 2. Si no hay bayas, busca el Juguete (Alcance de 400 -> 800)
                    if not target and getattr(self.game_controller, 'active_toy', None):
                        t = self.game_controller.active_toy
                        if t.current_state not in ['exiting', 'tk_controlled'] and abs(t.x - self.x) < 800:
                            target = t
                # 3. Si no hay objetos, levanta a otro Pokémon cercano (Alcance de 250 -> 500)
                if not target and getattr(self, 'get_all_pets', None):
                    valid_pets = [p for p in self.get_all_pets() if p != self and p.current_state in ['idle', 'walking'] and not getattr(p, 'is_egg', False) and abs(p.x - self.x) < 500]
                    if valid_pets: target = random.choice(valid_pets)
                    
                if target:
                    self.current_state = 'tk_channeling'
                    self.tk_target = target
                    self.tk_timer = 150 # Levitar durante 5 segundos
                    
                    self.tk_orbit_started = False # FIX: Fuerza el reseteo de la fase orbital
                    
                    target.tk_master = self
                    target.current_state = 'tk_controlled' if target.__class__.__name__ != 'DesktopPet' else 'tk_lifted'
                    if target.__class__.__name__ == 'DesktopPet':
                        target.anchored_hwnd = None
                        
                    self.window.after(50, self.physics_loop) 
                    return
        
        if self.can_teleport and self.teleport_cooldown == 0 and self.current_state in ['idle', 'walking']:
            if random.randint(1, 100) <= 1:
                self.current_state = 'teleporting_out'
                self.teleport_step = 1.0
                self.teleport_cooldown = 3000
                self.window.after(50, self.physics_loop)
                return

        current_env, ahead_env = self.get_window_environment()
        ahead_physical_floor = ahead_env['y'] if type(ahead_env) is dict else ahead_env
        
        is_climber = getattr(self, 'is_climbing', False) or self.config.get("physics", {}).get("is_climbing", False)
        if is_climber:
            self.is_climbing = True

        if not getattr(self, 'is_flying', False):
            if self.current_state in ['idle', 'walking'] and current_env['hwnd']:
                if getattr(self, 'climbing_surface', 'floor') == 'floor':
                    if getattr(self, 'anchored_hwnd', None) != current_env['hwnd']:
                        self.anchored_hwnd = current_env['hwnd']
                        self.anchored_rect = current_env['rect']
            else:
                if not is_climber:
                    self.anchored_hwnd = None

            if getattr(self, 'anchored_hwnd', None) and getattr(self, 'anchored_rect', None) and getattr(self, 'climbing_surface', 'floor') == 'floor':
                current_physical_floor = self.anchored_rect[1] - self.size_h - self.offset_y
            elif self.y <= current_env['y'] + 15:
                current_physical_floor = current_env['y']
            else:
                current_physical_floor = self.default_floor_y

            self.floor_y = current_physical_floor

            if not is_climber:
                if self.current_state in ['idle', 'walking'] and self.y < self.floor_y - 15:
                    self.current_state = 'jumping_arc'
                    self.jump_target_y = self.floor_y
                    self.v_y_velocity = 0.0 if self.heavy_fall else -3.0  
                    
                elif self.current_state == 'walking' and ahead_physical_floor is not None:
                    h = self.y - ahead_physical_floor
                    if 30 < h < 750 and self.jump_cooldown == 0: 
                        if random.randint(1, 1000) <= 30: 
                            self.current_state = 'jumping_arc'
                            self.jump_target_y = ahead_physical_floor
                            self.v_y_velocity = -math.sqrt(2 * 1.5 * (h + 30))
                            self.jump_cooldown = 400

                elif self.current_state == 'walking' and getattr(self, 'anchored_hwnd', None) and self.jump_cooldown == 0:
                    if random.randint(1, 1000) <= 5: 
                        self.current_state = 'jumping_arc'
                        self.jump_target_y = self.default_floor_y
                        self.v_y_velocity = 0.0 if self.heavy_fall else -3.0 
                        self.jump_cooldown = 400
                        self.anchored_hwnd = None
                        self.anchored_rect = None

            else:
                win_offset = 6 
                wall_offset = getattr(self, 'climb_offset_x', 0)
                ceil_offset = getattr(self, 'climb_offset_y', 0)

                if getattr(self, 'climbing_surface', 'floor') in ['wall_l', 'wall_r', 'ceiling']:
                    if not getattr(self, 'anchored_hwnd', None):
                        self.current_state = 'jumping_arc'
                        self.jump_target_y = self.default_floor_y
                        self.v_y_velocity = 0.0
                        self.climbing_surface = 'floor'
                        self.surface_angle = 0
                        self.jump_cooldown = 60
                elif getattr(self, 'climbing_surface', 'floor') == 'floor':
                    if not getattr(self, 'anchored_hwnd', None) and self.y < self.floor_y - 15:
                        self.current_state = 'jumping_arc'
                        self.jump_target_y = self.floor_y
                        self.v_y_velocity = 0.0
                        self.jump_cooldown = 60

                if not getattr(self, 'anchored_hwnd', None):
                    if self.climbing_surface == 'screen_l':
                        self.x = self.v_x + wall_offset
                        self.surface_angle = 270
                    elif self.climbing_surface == 'screen_r':
                        self.x = self.v_x + self.v_width - self.size_w - wall_offset
                        self.surface_angle = 90
                    elif self.climbing_surface == 'screen_ceiling':
                        self.y = self.v_y + ceil_offset
                        self.surface_angle = 180

                if self.current_state == 'walking':
                    if getattr(self, 'anchored_rect', None) and getattr(self, 'anchored_hwnd', None):
                        rect = self.anchored_rect
                        if getattr(self, 'climbing_surface', 'floor') == 'floor':
                            self.y = rect[1] - self.size_h - self.offset_y
                            self.x += self.speed if self.is_facing_right else -self.speed
                            
                            if self.x > rect[2] - self.size_w / 2 and self.is_facing_right:
                                self.climbing_surface = 'wall_r'
                                self.surface_angle = 270
                                self.x = rect[2] - win_offset
                                self.y = rect[1] - self.size_h / 2
                            elif self.x < rect[0] - self.size_w / 2 and not self.is_facing_right:
                                self.climbing_surface = 'wall_l'
                                self.surface_angle = 90
                                self.x = rect[0] - self.size_w + win_offset
                                self.y = rect[1] - self.size_h / 2

                        elif getattr(self, 'climbing_surface', 'floor') == 'wall_r':
                            self.x = rect[2] - win_offset
                            self.y += self.speed if self.is_facing_right else -self.speed 
                            if self.y > rect[3] - self.size_h / 2 and self.is_facing_right:
                                self.climbing_surface = 'ceiling'
                                self.surface_angle = 180
                                self.y = rect[3] - win_offset
                                self.x = rect[2] - self.size_w / 2
                            elif self.y < rect[1] - self.size_h / 2 and not self.is_facing_right:
                                self.climbing_surface = 'floor'
                                self.surface_angle = 0
                                self.y = rect[1] - self.size_h + win_offset
                                self.x = rect[2] - self.size_w / 2
                                
                        elif getattr(self, 'climbing_surface', 'floor') == 'wall_l':
                            self.x = rect[0] - self.size_w + win_offset
                            self.y -= self.speed if self.is_facing_right else -self.speed 
                            if self.y < rect[1] - self.size_h / 2 and self.is_facing_right:
                                self.climbing_surface = 'floor'
                                self.surface_angle = 0
                                self.y = rect[1] - self.size_h + win_offset
                                self.x = rect[0] - self.size_w / 2
                            elif self.y > rect[3] - self.size_h / 2 and not self.is_facing_right:
                                self.climbing_surface = 'ceiling'
                                self.surface_angle = 180
                                self.y = rect[3] - win_offset
                                self.x = rect[0] - self.size_w / 2
                                
                        elif getattr(self, 'climbing_surface', 'floor') == 'ceiling':
                            self.y = rect[3] - win_offset
                            self.x -= self.speed if self.is_facing_right else -self.speed 
                            if self.x < rect[0] - self.size_w / 2 and self.is_facing_right:
                                self.climbing_surface = 'wall_l'
                                self.surface_angle = 90
                                self.x = rect[0] - self.size_w + win_offset
                                self.y = rect[3] - self.size_h / 2
                            elif self.x > rect[2] - self.size_w / 2 and not self.is_facing_right:
                                self.climbing_surface = 'wall_r'
                                self.surface_angle = 270
                                self.x = rect[2] - win_offset
                                self.y = rect[3] - self.size_h / 2

                    else: 
                        if getattr(self, 'climbing_surface', 'floor') == 'floor':
                            self.y = self.default_floor_y
                            self.x += self.speed if self.is_facing_right else -self.speed
                            if self.x >= self.v_x + self.v_width - self.size_w and self.is_facing_right:
                                self.climbing_surface = 'screen_r'
                                self.surface_angle = 90
                                self.x = self.v_x + self.v_width - self.size_w - wall_offset
                                self.is_facing_right = False 
                            elif self.x <= self.v_x and not self.is_facing_right:
                                self.climbing_surface = 'screen_l'
                                self.surface_angle = 270
                                self.x = self.v_x + wall_offset
                                self.is_facing_right = True 
                            elif ahead_physical_floor is not None and ahead_env['hwnd']:
                                self.anchored_hwnd = ahead_env['hwnd']
                                self.anchored_rect = ahead_env['rect']
                                if self.is_facing_right:
                                    self.climbing_surface = 'wall_l'
                                    self.surface_angle = 90
                                    self.x = self.anchored_rect[0] - self.size_w + win_offset
                                else:
                                    self.climbing_surface = 'wall_r'
                                    self.surface_angle = 270
                                    self.x = self.anchored_rect[2] - win_offset
                                    
                        elif getattr(self, 'climbing_surface', 'floor') == 'screen_r':
                            self.x = self.v_x + self.v_width - self.size_w - wall_offset
                            self.y += self.speed if self.is_facing_right else -self.speed
                            if self.y <= self.v_y and not self.is_facing_right:
                                self.climbing_surface = 'screen_ceiling'
                                self.surface_angle = 180
                                self.y = self.v_y + ceil_offset
                                self.is_facing_right = True 
                            elif self.y >= self.default_floor_y and self.is_facing_right:
                                self.climbing_surface = 'floor'
                                self.surface_angle = 0
                                self.y = self.default_floor_y
                                self.is_facing_right = False 
                                
                        elif getattr(self, 'climbing_surface', 'floor') == 'screen_l':
                            self.x = self.v_x + wall_offset
                            self.y -= self.speed if self.is_facing_right else -self.speed
                            if self.y <= self.v_y and self.is_facing_right:
                                self.climbing_surface = 'screen_ceiling'
                                self.surface_angle = 180
                                self.y = self.v_y + ceil_offset
                                self.is_facing_right = False 
                            elif self.y >= self.default_floor_y and not self.is_facing_right:
                                self.climbing_surface = 'floor'
                                self.surface_angle = 0
                                self.y = self.default_floor_y
                                self.is_facing_right = True 
                                
                        elif getattr(self, 'climbing_surface', 'floor') == 'screen_ceiling':
                            self.y = self.v_y + ceil_offset
                            self.x -= self.speed if self.is_facing_right else -self.speed
                            if self.x <= self.v_x and self.is_facing_right:
                                self.climbing_surface = 'screen_l'
                                self.surface_angle = 270
                                self.x = self.v_x + wall_offset
                                self.is_facing_right = False 
                            elif self.x >= self.v_x + self.v_width - self.size_w and not self.is_facing_right:
                                self.climbing_surface = 'screen_r'
                                self.surface_angle = 90
                                self.x = self.v_x + self.v_width - self.size_w - wall_offset
                                self.is_facing_right = True 

        else:
            self.anchored_hwnd = None
            self.climbing_surface = 'floor'
            self.surface_angle = 0
            
            target = getattr(self, 'target_floor_y', self.floor_y)
            if self.floor_y > target:
                self.floor_y -= 5
                if self.floor_y < target: self.floor_y = target
            elif self.floor_y < target:
                self.floor_y += 5
                if self.floor_y > target: self.floor_y = target
                
            self.y = self.floor_y

        if self.current_state == 'idle':
            if is_climber and getattr(self, 'anchored_hwnd', None) and getattr(self, 'anchored_rect', None) and getattr(self, 'climbing_surface', 'floor') == 'floor':
                self.y = self.anchored_rect[1] - self.size_h - self.offset_y
                
            action_chance = random.randint(1, 100)
            if action_chance <= 5: 
                self.current_state = 'walking'
                self.is_facing_right = random.choice([True, False])
        
        elif self.current_state == 'walking':
            action_chance = random.randint(1, 100)
            if action_chance <= 5: 
                self.current_state = 'idle'
            else:
                if not is_climber:
                    self.x += self.speed if self.is_facing_right else -self.speed
                    
                    if getattr(self, 'climbing_surface', 'floor') == 'floor':
                        if getattr(self, 'can_screen_wrap', False):
                            # MÁRGEN DE DESBORDAMIENTO (El Pokémon sale por completo antes de teletransportarse)
                            if self.x <= self.v_x - self.size_w:
                                self.x = self.v_x + self.v_width
                                if random.randint(1, 100) <= 25: self.is_facing_right = True 
                            elif self.x >= self.v_x + self.v_width:
                                self.x = self.v_x - self.size_w
                                if random.randint(1, 100) <= 25: self.is_facing_right = False
                        else:
                            # LÍMITE SÓLIDO NORMAL
                            if self.x <= self.v_x:
                                self.x = self.v_x
                                self.is_facing_right = True
                            elif self.x >= (self.v_x + self.v_width) - self.size_w:
                                self.x = (self.v_x + self.v_width) - self.size_w
                                self.is_facing_right = False

        if self.current_state in ['idle', 'walking'] and getattr(self, 'get_all_pets', None) and not getattr(self, 'is_egg', False) and getattr(self, 'climbing_surface', 'floor') == 'floor':
            if self.social_cooldown == 0 or self.attack_cooldown == 0:
                for other in self.get_all_pets():
                    if other != self and other.current_state in ['idle', 'walking'] and not getattr(other, 'is_egg', False) and getattr(other, 'climbing_surface', 'floor') == 'floor' and self.is_flying == other.is_flying:
                        my_true_floor = getattr(self, 'target_floor_y', self.floor_y) if self.is_flying else (self.floor_y + self.size_h + self.offset_y)
                        other_true_floor = getattr(other, 'target_floor_y', other.floor_y) if other.is_flying else (other.floor_y + other.size_h + other.offset_y)
                        if abs(my_true_floor - other_true_floor) < 15 and 80 < abs(self.x - other.x) < 150:
                            roll = random.randint(1, 100)
                            
                            atk_chance = 5 if getattr(self, 'aggressive', False) else 1
                            atk_cd = 3600 if getattr(self, 'aggressive', False) else 12000
                            
                            if roll <= atk_chance and self.attack_cooldown == 0 and other.attack_cooldown == 0:
                                self.current_state = 'attacking'
                                other.current_state = 'attacking'
                                self.attack_phase = 0
                                other.attack_phase = 0
                                self.attack_phase_wait_until = 0.0
                                other.attack_phase_wait_until = 0.0
                                self.attack_target = other
                                other.attack_target = self
                                self.attack_cooldown = atk_cd 
                                other.attack_cooldown = 12000 
                                self.is_facing_right = (other.x > self.x)
                                other.is_facing_right = (self.x > other.x)
                                break
                            elif roll <= 3 and self.social_cooldown == 0 and other.social_cooldown == 0:
                                self.current_state = 'socializing'
                                other.current_state = 'socializing'
                                self.social_timer = 90
                                other.social_timer = 90
                                self.social_cooldown = 2400
                                other.social_cooldown = 2400
                                self.is_facing_right = (other.x > self.x)
                                other.is_facing_right = (self.x > other.x)
                                break

        # === INTERACCIÓN CON BAYAS (RADIAL Y DINÁMICA) ===
        if self.current_state in ['idle', 'walking'] and not self.is_wild and not getattr(self, 'is_egg', False) and self.game_controller:
            for berry in getattr(self.game_controller, 'active_berries', []):
                # Quitamos la restricción de 'dragged'. Si la baya existe, es comestible.
                if berry.current_state != 'exiting':
                    # Calculamos los centros geométricos reales de ambos objetos
                    my_cx = self.x + self.size_w / 2
                    my_cy = self.y + self.size_h / 2
                    berry_cx = berry.x + berry.size / 2
                    berry_cy = berry.y + berry.size / 2
                    
                    # Distancia Euclidiana
                    dist = math.sqrt((my_cx - berry_cx)**2 + (my_cy - berry_cy)**2)
                    
                    # Hitbox generosa (60% del tamaño del Pokémon)
                    if dist < max(self.size_w, self.size_h) * 0.6:
                        self.current_state = 'eating'
                        self.eating_timer = 30
                        self.interaction_target = berry
                        berry.destroy() # Destruye la baya visualmente
                        self.show_heart_vfx() # Dispara el corazón pixelado
                        break

        if self.is_flying and self.current_state not in ['socializing', 'attacking', 'eating']:
            self.fly_amplitude += 0.2
            self.y = self.floor_y + math.sin(self.fly_amplitude) * 10
            
        self.update_position()
        self.window.after(50, self.physics_loop)

    def _fsm_legendary_bounce(self):
        self.v_y_velocity += 1.5 
        self.y += self.v_y_velocity
        self.x += (self.speed * 0.5) if self.is_facing_right else -(self.speed * 0.5)

        target_y = getattr(self, 'floor_y', self.default_floor_y)
        if self.v_y_velocity > 0 and self.y >= target_y:
            self.y = target_y
            self.floor_y = target_y
            # FIX: Aseguramos el escape tras rebotar
            if getattr(self, 'is_overflow', False):
                self.current_state = 'walking_away'
                self.is_facing_right = True
            else:
                self.current_state = 'idle' 
            
        self.update_position()
        self.window.after(30, self.physics_loop)

    def _fsm_landing_shake(self):
        self.shake_timer -= 1
        if self.shake_timer <= 0:
            # Restaurar el sprite a su centro original y perfecto
            self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
            if getattr(self, 'is_overflow', False):
                self.current_state = 'walking_away'
                self.is_facing_right = True
            else:
                self.current_state = 'idle'
        else:
            # Desplazar la imagen un par de píxeles al azar para simular el temblor
            offset_x = random.choice([-3, 0, 3])
            offset_y = random.choice([-2, 0, 2])
            self.canvas.coords(self.canvas_image_id, (self.size_w//2) + offset_x, (self.size_h//2) + offset_y)
            
        self.update_position()
        self.window.after(30, self.physics_loop)

# --- POKÉBALL INTERACTIVA ---
class InteractivePokeball:
    def __init__(self, parent_root, base_dir, get_pets_callback, on_destroy_callback):
        self.window = tk.Toplevel(parent_root)
        self.window.title("Toy Pokeball")
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        
        CHROMA_KEY = '#00FF00'
        self.window.config(bg=CHROMA_KEY)
        try: self.window.wm_attributes('-transparentcolor', CHROMA_KEY)
        except tk.TclError: pass
        
        self.get_pets = get_pets_callback
        self.on_destroy = on_destroy_callback
        self.base_dir = base_dir
        
        self.size = 40
        self.offset_y = -6
        
        user32 = ctypes.windll.user32
        self.v_x = user32.GetSystemMetrics(76) 
        self.v_y = user32.GetSystemMetrics(77)
        self.v_width = user32.GetSystemMetrics(78)
        self.v_height = user32.GetSystemMetrics(79)
        
        self.default_floor_y = (self.v_y + self.v_height) - self.size - self.offset_y
        self.floor_y = self.default_floor_y
        
        self.x = random.randint(self.v_x, self.v_x + self.v_width - self.size)
        self.y = self.v_y - self.size
        self.v_x_velocity = 0.0
        self.v_y_velocity = 0.0
        
        self.current_state = 'falling'
        self.angle = 0
        
        self.canvas = tk.Canvas(self.window, width=self.size, height=self.size, bg=CHROMA_KEY, highlightthickness=0)
        self.canvas.pack()
        self.canvas_image_id = self.canvas.create_image(self.size//2, self.size//2, anchor=tk.CENTER)
        
        pb_dir = os.path.join(self.base_dir, "game_env", "ui")
        available_pbs = [f for f in os.listdir(pb_dir) if f.startswith("pokeball") and f.endswith(".png")]
        pb_file = random.choice(available_pbs) if available_pbs else "pokeball.png"
        
        try:
            raw_img = Image.open(os.path.join(pb_dir, pb_file)).convert("RGBA")
            r, g, b, a = raw_img.split()
            a = a.point(lambda p: 255 if p > 127 else 0)
            self.base_img = Image.merge("RGBA", (r, g, b, a)).resize((self.size, self.size), Image.Resampling.NEAREST)
            self.tk_image = ImageTk.PhotoImage(self.base_img)
            self.canvas.itemconfig(self.canvas_image_id, image=self.tk_image)
        except Exception as e:
            self.window.after(100, self.destroy)
            return
            
        self.window.geometry(f"{self.size}x{self.size}+{int(self.x)}+{int(self.y)}")
        
        self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self.on_drag_release)
        self.canvas.bind("<ButtonRelease-3>", lambda e: self.destroy())
        
        self.keep_on_top()
        self.animate_loop()
        self.physics_loop()

    def keep_on_top(self):
        if self.current_state != 'exiting':
            try: self.window.attributes('-topmost', True)
            except: pass
            self.window.after(2000, self.keep_on_top)

    def manage_tk_aura(self, canvas, w, h, is_active):
        if is_active:
            canvas.delete("tk_aura") 
            t = time.time()
            cx, cy = w / 2, h / 2
            base_radius = max(w, h) * 0.6
            
            # Enjambre de 24 partículas psíquicas generadas matemáticamente en tiempo real
            for i in range(24):
                # 1. Velocidad asimétrica (Algunas partículas van rápido, otras lento, otras al revés)
                speed = 1.5 + (math.sin(i * 7.1) * 2.0)
                angle = (t * speed) + (i * 0.8)
                
                # 2. Dispersión del radio (Rompe la circunferencia para crear una nube caótica)
                scatter = math.cos(i * 13.3) * (base_radius * 0.5)
                r = base_radius + scatter
                
                px = cx + math.cos(angle) * r
                py = cy + math.sin(angle) * r
                
                # 3. Fase de parpadeo individual basada en el tiempo
                blink_phase = math.sin(t * 12.0 + i * 3.14)
                
                if blink_phase > 0.5:
                    color = "#FFFFFF" # Destello blanco intenso
                    size = 2
                elif blink_phase > -0.3:
                    color = "#D24DFF" # Morado de energía base
                    size = 1
                else:
                    continue # Partícula invisible (simula que se apaga del todo)
                
                canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color, tags="tk_aura")
                
            canvas.tag_lower("tk_aura") # Forzar la nube por detrás del sprite
        else:
            canvas.delete("tk_aura")

    def destroy(self):
        self.current_state = 'exiting'
        if self.on_destroy:
            self.on_destroy()
        self.window.destroy()

    def update_position(self):
        self.window.geometry(f"+{int(self.x)}+{int(self.y)}")
        
    def on_drag_start(self, event):
        if self.current_state == 'exiting': return
        
        # FIX: Liberar el objeto de la telequinesis y avisar al Maestro para que pare
        if self.current_state == 'tk_controlled':
            self.current_state = 'falling'
            self.manage_tk_aura(self.canvas, self.size, self.size, False)
            master = getattr(self, 'tk_master', None)
            if master and master.current_state == 'tk_channeling':
                master.current_state = 'idle'
                master.manage_tk_aura(master.canvas, master.size_w, master.size_h, False)
                master.tk_target = None
            self.tk_master = None
            
        self.drag_offset_x = event.x
        self.drag_offset_y = event.y
        self.drag_start_x = self.window.winfo_pointerx()
        self.drag_start_y = self.window.winfo_pointery()
        self.is_dragging = False

    def on_drag_motion(self, event):
        if self.current_state == 'exiting': return
        pointer_x = self.window.winfo_pointerx()
        pointer_y = self.window.winfo_pointery()

        if not getattr(self, 'is_dragging', False):
            if abs(pointer_x - getattr(self, 'drag_start_x', pointer_x)) > 5 or \
               abs(pointer_y - getattr(self, 'drag_start_y', pointer_y)) > 5:
                self.is_dragging = True
                self.current_state = 'dragged'
                self.v_x_velocity = 0.0
                self.v_y_velocity = 0.0
                self.last_drag_time = time.time()
                self.last_mouse_x = pointer_x
                self.last_mouse_y = pointer_y
            else:
                return

        self.x = pointer_x - self.drag_offset_x
        self.y = pointer_y - self.drag_offset_y
        self.update_position()

        current_time = time.time()
        dt = current_time - getattr(self, 'last_drag_time', current_time)
        if dt > 0:
            self.v_x_velocity = (pointer_x - self.last_mouse_x) / (dt * 150.0) 
            self.v_y_velocity = (pointer_y - self.last_mouse_y) / (dt * 150.0)
        
        self.last_mouse_x = pointer_x
        self.last_mouse_y = pointer_y
        self.last_drag_time = current_time

    def on_drag_release(self, event):
        if getattr(self, 'is_dragging', False):
            self.is_dragging = False
            self.anchored_hwnd = None
            
            v_x = getattr(self, 'v_x_velocity', 0.0)
            v_y = getattr(self, 'v_y_velocity', 0.0)
            
            if math.isnan(v_x) or math.isinf(v_x): v_x = 0.0
            if math.isnan(v_y) or math.isinf(v_y): v_y = 0.0

            self.v_x_velocity = max(-40.0, min(40.0, v_x))
            self.v_y_velocity = max(-40.0, min(40.0, v_y))
            
            self.current_state = 'thrown'

    def get_window_environment(self):
        current_env = {'y': self.default_floor_y, 'hwnd': None, 'rect': None}
        if not HAS_WIN32: return current_env
        
        center_x = self.x + self.size // 2
        bottom_y = self.y
        CURRENT_PID = os.getpid()
        valid_windows = []
        
        def win_enum_handler(hwnd, ctx):
            if not win32gui.IsWindowVisible(hwnd): return
            if win32gui.IsIconic(hwnd): return 
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pid == CURRENT_PID:
                    # FIX EXCEPCIÓN: Permitir colisión con Bill's PC
                    title = win32gui.GetWindowText(hwnd)
                    if title != "Bill's PC":
                        return
            except: pass
            try:
                is_cloaked = ctypes.c_int(0)
                ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(is_cloaked), ctypes.sizeof(is_cloaked))
                if is_cloaked.value != 0: return
            except: pass
            try:
                ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                if ex_style & win32con.WS_EX_TRANSPARENT: return
            except: pass
            class_name = win32gui.GetClassName(hwnd)
            if class_name in ("Progman", "WorkerW", "Shell_TrayWnd", "EdgeUiInputTopWndClass", "DummyDWMWindow", "PopupHost"): return
            title = win32gui.GetWindowText(hwnd)
            if not title: return 
            rect = win32gui.GetWindowRect(hwnd)
            w_width = rect[2] - rect[0]
            w_height = rect[3] - rect[1]
            if w_width < 100 or w_height < 100: return
            
            placement = win32gui.GetWindowPlacement(hwnd) 
            is_fullscreen = False
            if placement[1] == win32con.SW_SHOWMAXIMIZED:
                is_fullscreen = True
            else:
                try:
                    monitor = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
                    mon_info = win32api.GetMonitorInfo(monitor)
                    mon_w = mon_info['Monitor'][2] - mon_info['Monitor'][0]
                    mon_h = mon_info['Monitor'][3] - mon_info['Monitor'][1]
                    if w_width >= mon_w - 10 and w_height >= mon_h - 10:
                        is_fullscreen = True
                except:
                    if w_width >= self.v_width and w_height >= (self.v_height - 10):
                        is_fullscreen = True
                        
            win_floor = rect[1] - self.size - self.offset_y
            valid_windows.append({'hwnd': hwnd, 'rect': rect, 'floor': win_floor, 'z': len(valid_windows), 'walkable': not is_fullscreen})
            
        win32gui.EnumWindows(win_enum_handler, None)
        
        under_windows = [w for w in valid_windows if w['walkable'] and w['rect'][0] <= center_x <= w['rect'][2] and w['floor'] >= bottom_y - 15]
        if under_windows:
            under_windows.sort(key=lambda w: w['floor'])
            for uw in under_windows:
                is_occluded = False
                check_y = uw['rect'][1] + 5
                for ow in valid_windows:
                    if ow['z'] < uw['z'] and ow['rect'][0] <= center_x <= ow['rect'][2] and ow['rect'][1] <= check_y <= ow['rect'][3]:
                        is_occluded = True
                        break
                if not is_occluded:
                    current_env['y'] = uw['floor']
                    current_env['hwnd'] = uw['hwnd']
                    current_env['rect'] = uw['rect']
                    break
        return current_env

    def animate_loop(self):
        if self.current_state == 'exiting': return
        
        if getattr(self, 'anchored_hwnd', None) and self.current_state == 'idle':
            try:
                if HAS_WIN32 and win32gui.IsWindowVisible(self.anchored_hwnd) and not win32gui.IsIconic(self.anchored_hwnd):
                    new_rect = win32gui.GetWindowRect(self.anchored_hwnd)
                    old_rect = getattr(self, 'anchored_rect', new_rect)
                    delta_x = new_rect[0] - old_rect[0]
                    delta_y = new_rect[1] - old_rect[1]
                    if delta_x != 0 or delta_y != 0:
                        self.x += delta_x
                        self.y += delta_y
                        self.floor_y += delta_y
                        self.x = max(self.v_x, min(self.x, (self.v_x + self.v_width) - self.size))
                        self.update_position()
                    self.anchored_rect = new_rect
                else:
                    self.anchored_hwnd = None
            except:
                self.anchored_hwnd = None

        if abs(self.v_x_velocity) > 0.5:
            self.angle = (self.angle - self.v_x_velocity * 4) % 360
            self.tk_image = ImageTk.PhotoImage(self.base_img.rotate(self.angle, resample=Image.NEAREST, expand=False))
            self.canvas.itemconfig(self.canvas_image_id, image=self.tk_image)
            
        self.window.after(16, self.animate_loop)

    def physics_loop(self):
        if self.current_state == 'exiting': return
        if self.current_state == 'dragged':
            self.window.after(30, self.physics_loop)
            return
        
        # FIX: Control Telequinético para el Juguete
        if self.current_state == 'tk_controlled':
            if not hasattr(self, 'tk_master') or not self.tk_master.window.winfo_exists() or self.tk_master.current_state != 'tk_channeling':
                self.current_state = 'falling'
                self.manage_tk_aura(self.canvas, self.size, self.size, False)
            self.window.after(30, self.physics_loop)
            return

        self.v_y_velocity += 0.99 
        self.v_x_velocity *= 0.99 
        
        self.y += self.v_y_velocity
        self.x += self.v_x_velocity

        if self.x <= self.v_x:
            self.x = self.v_x
            self.v_x_velocity *= -0.5 
        elif self.x >= (self.v_x + self.v_width) - self.size:
            self.x = (self.v_x + self.v_width) - self.size
            self.v_x_velocity *= -0.5

        if self.y <= self.v_y:
            self.y = self.v_y
            self.v_y_velocity *= -0.5 

        current_env = self.get_window_environment()
        if self.y <= current_env['y'] + 15:
            physical_floor = current_env['y']
            if current_env['hwnd']:
                if getattr(self, 'anchored_hwnd', None) != current_env['hwnd']:
                    self.anchored_hwnd = current_env['hwnd']
                    self.anchored_rect = current_env['rect']
        else:
            physical_floor = self.default_floor_y
            self.anchored_hwnd = None

        if self.y >= physical_floor and self.v_y_velocity > 0:
            self.y = physical_floor
            self.floor_y = physical_floor
            
            if self.v_y_velocity > 2.0:
                self.v_y_velocity *= -0.75 
                self.v_x_velocity *= 0.85 
            else:
                self.v_y_velocity = 0.0
                self.v_x_velocity *= 0.6
            
            if abs(self.v_x_velocity) < 0.5 and abs(self.v_y_velocity) < 0.5:
                self.current_state = 'idle'
                self.v_x_velocity = 0
                self.v_y_velocity = 0
        else:
            self.current_state = 'falling'

        if self.current_state != 'dragged':
            ball_cx = self.x + self.size/2
            ball_cy = self.y + self.size/2
            
            for p in self.get_pets():
                if p.current_state in ['falling_egg', 'falling_pokeball', 'exiting', 'dragged']: continue
                
                p_cx = p.x + p.size_w/2
                p_cy = p.y + p.size_h/2
                
                dx = ball_cx - p_cx
                dy = ball_cy - p_cy
                dist = math.sqrt(dx**2 + dy**2)
                
                min_dist = (self.size/2) + (p.size_w/2.5) 
                
                if dist < min_dist:
                    force_multiplier = (p.size_w / 64.0) * (p.speed * 1.5 if p.current_state == 'walking' else 1.0)
                    
                    if p.current_state == 'walking':
                        push_dir = 1 if p.is_facing_right else -1
                        self.v_x_velocity = push_dir * force_multiplier * 2.7
                    else:
                        if dx != 0:
                            self.v_x_velocity = (dx/dist) * force_multiplier * 2.7
                        else:
                            self.v_x_velocity = random.choice([-1, 1]) * force_multiplier * 2.7
                            
                    self.v_y_velocity = -force_multiplier * 2.7 - 2.7
                    self.y -= 5 
                    self.current_state = 'thrown'
                    self.anchored_hwnd = None
                    break 
        
        self.update_position()
        self.window.after(30, self.physics_loop)


# --- INYECCIÓN: BAYA CONSUMIBLE ---
class InteractiveBerry(InteractivePokeball):
    def __init__(self, parent_root, base_dir, get_pets_callback, on_destroy_callback):
        self.window = tk.Toplevel(parent_root)
        self.window.title("Consumable Berry")
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        CHROMA_KEY = '#00FF00'
        self.window.config(bg=CHROMA_KEY)
        try: self.window.wm_attributes('-transparentcolor', CHROMA_KEY)
        except tk.TclError: pass
        self.get_pets = get_pets_callback
        self.on_destroy = on_destroy_callback
        self.base_dir = base_dir
        
        self.size_baya = 40 
        self.size = self.size_baya
        self.offset_y = -6
        user32 = ctypes.windll.user32
        self.v_x = user32.GetSystemMetrics(76) 
        self.v_y = user32.GetSystemMetrics(77)
        self.v_width = user32.GetSystemMetrics(78)
        self.v_height = user32.GetSystemMetrics(79)
        self.default_floor_y = (self.v_y + self.v_height) - self.size - self.offset_y
        self.floor_y = self.default_floor_y
        
        spawn_edge = random.choice(['left', 'right', 'top'])
        if spawn_edge == 'left':
            self.x = self.v_x - self.size
            self.y = random.randint(self.v_y, self.v_y + self.v_height // 2)
            self.v_x_velocity = random.uniform(40.0, 60.0) 
            self.v_y_velocity = random.uniform(-10.0, -5.0)
        elif spawn_edge == 'right':
            self.x = self.v_x + self.v_width + self.size
            self.y = random.randint(self.v_y, self.v_y + self.v_height // 2)
            self.v_x_velocity = random.uniform(-60.0, -40.0) 
            self.v_y_velocity = random.uniform(-10.0, -5.0)
        else:
            self.x = random.randint(self.v_x, self.v_x + self.v_width - self.size)
            self.y = self.v_y - self.size
            self.v_x_velocity = random.uniform(-15.0, 15.0)
            self.v_y_velocity = 5.0
            
        self.current_state = 'thrown'
        self.angle = 0
        self.canvas = tk.Canvas(self.window, width=self.size, height=self.size, bg=CHROMA_KEY, highlightthickness=0)
        self.canvas.pack()
        self.canvas_image_id = self.canvas.create_image(self.size//2, self.size//2, anchor=tk.CENTER)
        
        pb_dir = os.path.join(self.base_dir, "game_env", "ui")
        available_berries = [f for f in os.listdir(pb_dir) if f.lower().endswith("berry.png")]
        if not available_berries: available_berries = [f for f in os.listdir(pb_dir) if f.startswith("pokeball") and f.endswith(".png")]
        pb_file = random.choice(available_berries) if available_berries else "pokeball.png"
        
        try:
            raw_img = Image.open(os.path.join(pb_dir, pb_file)).convert("RGBA")
            r, g, b, a = raw_img.split()
            a = a.point(lambda p: 255 if p > 127 else 0)
            self.base_img = Image.merge("RGBA", (r, g, b, a)).resize((self.size, self.size), Image.Resampling.NEAREST)
            self.tk_image = ImageTk.PhotoImage(self.base_img)
            self.canvas.itemconfig(self.canvas_image_id, image=self.tk_image)
        except:
            self.window.after(100, self.destroy)
            return
            
        self.window.geometry(f"{self.size}x{self.size}+{int(self.x)}+{int(self.y)}")
        self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self.on_drag_release)
        self.canvas.bind("<ButtonRelease-3>", lambda e: self.destroy())
        self.keep_on_top()
        self.animate_loop()
        self.physics_loop()

    def physics_loop(self):
        if self.current_state == 'exiting': return
        if self.current_state == 'dragged':
            self.window.after(30, self.physics_loop)
            return

        # FIX: Control Telequinético para la Baya
        if self.current_state == 'tk_controlled':
            if not hasattr(self, 'tk_master') or not self.tk_master.window.winfo_exists() or self.tk_master.current_state != 'tk_channeling':
                self.current_state = 'falling'
                self.manage_tk_aura(self.canvas, self.size, self.size, False)
            self.window.after(30, self.physics_loop)
            return

        self.v_y_velocity += 0.8 
        self.v_x_velocity *= 0.99 
        self.y += self.v_y_velocity
        self.x += self.v_x_velocity

        if self.x <= self.v_x:
            self.x = self.v_x
            self.v_x_velocity *= -0.5 
        elif self.x >= (self.v_x + self.v_width) - self.size:
            self.x = (self.v_x + self.v_width) - self.size
            self.v_x_velocity *= -0.5

        if self.y <= self.v_y:
            self.y = self.v_y
            self.v_y_velocity *= -0.75 

        current_env = self.get_window_environment()
        if self.y <= current_env['y'] + 15:
            physical_floor = current_env['y']
            if current_env['hwnd']:
                if getattr(self, 'anchored_hwnd', None) != current_env['hwnd']:
                    self.anchored_hwnd = current_env['hwnd']
                    self.anchored_rect = current_env['rect']
        else:
            physical_floor = self.default_floor_y
            self.anchored_hwnd = None

        if self.y >= physical_floor and self.v_y_velocity > 0:
            self.y = physical_floor
            self.floor_y = physical_floor
            if self.v_y_velocity > 2.0:
                self.v_y_velocity *= -0.05 
                self.v_x_velocity *= 0.6 
            else:
                self.v_y_velocity = 0.0
                self.v_x_velocity *= 0.3
            if abs(self.v_x_velocity) < 0.5 and abs(self.v_y_velocity) < 0.5:
                self.current_state = 'idle'
                self.v_x_velocity = 0
                self.v_y_velocity = 0
        else: self.current_state = 'falling'
        self.update_position()
        self.window.after(30, self.physics_loop)

# --- VENTANA DE SELECCIÓN DE INICIAL ---
class StarterSelectionWindow:
    def __init__(self, parent, pets_dir, on_select_callback):
        self.window = tk.Toplevel(parent)
        self.window.title("Selector Inicial")
        self.window.geometry("450x550")
        self.window.attributes('-topmost', True)
        self.window.grab_set() 

        self.pets_dir = pets_dir
        self.on_select = on_select_callback
        self.images_cache = [] # CRÍTICO: Previene que el Garbage Collector borre las imágenes
        
        tk.Label(self.window, text="Prepare for your new adventure.\nSelect your starting pokémon:", font=("Segoe UI", 12, "bold")).pack(pady=(15, 10))
        
        # 1. Crear el contenedor con Scroll (Lógica obligatoria en Tkinter para listas largas)
        container = tk.Frame(self.window)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=400)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 2. Bind para usar la rueda del ratón en el scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.window.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # 3. Matriz Canónica (9 Generaciones + Pikachu/Eevee)
        starter_grid = [
            ["pikachu", "eevee"],
            ["bulbasaur", "charmander", "squirtle"],
            ["chikorita", "cyndaquil", "totodile"],
            ["treecko", "torchic", "mudkip"],
            ["turtwig", "chimchar", "piplup"],
            ["snivy", "tepig", "oshawott"],
            ["chespin", "fennekin", "froakie"],
            ["rowlet", "litten", "popplio"],
            ["grookey", "scorbunny", "sobble"],
            ["sprigatito", "fuecoco", "quaxly"]
        ]
        
        # 4. Construcción del Grid Visual
        for row_idx, row_species in enumerate(starter_grid):
            row_frame = tk.Frame(self.scrollable_frame)
            row_frame.pack(fill=tk.X, pady=8)
            
            # Forzar el centrado distribuyendo el peso en columnas vacías a los lados
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(len(row_species)+1, weight=1)
            
            for col_idx, species in enumerate(row_species):
                btn = self.create_pet_button(row_frame, species)
                if btn:
                    btn.grid(row=0, column=col_idx+1, padx=8)
                    
    def create_pet_button(self, parent_frame, species):
        pet_path = os.path.join(self.pets_dir, species)
        if not os.path.exists(pet_path):
            return None # Si el usuario no tiene la carpeta descargada, se omite
            
        img_tk = None
        try:
            config_path = os.path.join(pet_path, "config.json")
            idle_file = "idle_0.png"
            
            # Buscar inteligentemente cómo se llama su sprite idle en el json
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    img_cfg = cfg.get("images", {})
                    pref = img_cfg.get("idle_prefix", "idle_")
                    suf = img_cfg.get("idle_suffix", ".png")
                    idle_file = f"{pref}0{suf}"
                    
            img_path = os.path.join(pet_path, idle_file)
            if os.path.exists(img_path):
                raw_img = Image.open(img_path).convert("RGBA")
                # Limpiar canales alpha sucios que rompen los fondos en Tkinter
                r, g, b, a = raw_img.split()
                a = a.point(lambda p: 255 if p > 127 else 0)
                raw_img = Image.merge("RGBA", (r, g, b, a))
                
                raw_img = raw_img.resize((64, 64), Image.Resampling.NEAREST)
                img_tk = ImageTk.PhotoImage(raw_img)
                self.images_cache.append(img_tk) 
        except Exception as e:
            print(f"Error procesando sprite de {species}: {e}")
            
        btn = tk.Button(
            parent_frame, 
            text=species.capitalize(), 
            image=img_tk, 
            compound=tk.TOP, 
            font=("Segoe UI", 9, "bold"),
            bg="#ECF0F1",
            activebackground="#D5D8DC",
            bd=1,
            relief=tk.RAISED,
            cursor="hand2",
            width=100,
            command=lambda s=species: self.confirm(s)
        )
        return btn
        
    def confirm(self, species):
        import tkinter.messagebox as mb
        if mb.askyesno("Confirmar", f"¿Recibir a {species.capitalize()} como tu Pokémon inicial?"):
            self.on_select(species)
            self.window.destroy()

# --- CONTROLADOR CENTRAL DEL JUEGO ---
class GameController:
    def __init__(self):
        self.save_mgr = SaveManager()
        self.active_instances = [] 
        self.wild_instances = []
        self.overflow_instances = [] 
        self.active_berries = [] 
        
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        self.pets_directory = os.path.join(base_dir, "game_env", "pets")
        
        self.root = tk.Tk()
        self.root.title("Bill's PC")
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        
        # Aumentamos la altura de 205 a 250 para acomodar el buscador sin aplastar
        w, h = 280, 250 
        screen_w = self.root.winfo_screenwidth()
        self.root.geometry(f"{w}x{h}+{screen_w - w - 20}+20")

        bg_main = "#ECF0F1"       
        bg_header = "#2C3E50"     
        fg_header = "#FFFFFF"     
        
        self.root.config(bg=bg_header)

        header_frame = tk.Frame(self.root, bg=bg_header, height=25)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False) 
        
        # --- LÓGICA DE ARRASTRE DE VENTANA ---
        self._drag_data = {"x": 0, "y": 0}
        def drag_start(event):
            self._drag_data["x"] = event.x
            self._drag_data["y"] = event.y
        def drag_motion(event):
            delta_x = event.x - self._drag_data["x"]
            delta_y = event.y - self._drag_data["y"]
            x = self.root.winfo_x() + delta_x
            y = self.root.winfo_y() + delta_y
            self.root.geometry(f"+{x}+{y}")
            
        header_frame.bind("<ButtonPress-1>", drag_start)
        header_frame.bind("<B1-Motion>", drag_motion)
        
        lbl_title = tk.Label(header_frame, text="Bill's PC", font=("Segoe UI", 9, "bold"), bg=bg_header, fg=fg_header)
        lbl_title.pack(side=tk.LEFT, padx=10)
        lbl_title.bind("<ButtonPress-1>", drag_start)
        lbl_title.bind("<B1-Motion>", drag_motion)
        
        btn_power = tk.Button(header_frame, text="X", font=("Segoe UI", 8, "bold"), bg="#C0392B", fg="white", bd=0, width=3, command=self.exit_game)
        btn_power.pack(side=tk.RIGHT, padx=(0,0))
        
        btn_hide = tk.Button(header_frame, text="—", font=("Segoe UI", 8, "bold"), bg="#7F8C8D", fg="white", bd=0, width=3, command=self.hide_pc_ui)
        btn_hide.pack(side=tk.RIGHT, padx=(0,2))

        content_frame = tk.Frame(self.root, bg=bg_main)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Barra de búsqueda
        search_row = tk.Frame(content_frame, bg=bg_main)
        search_row.pack(fill=tk.X, padx=10, pady=(8, 0))
        
        tk.Label(search_row, text="🔍", bg=bg_main, fg="#7F8C8D").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_pc_list)
        self.entry_search = tk.Entry(search_row, textvariable=self.search_var, relief=tk.FLAT)
        self.entry_search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        top_row = tk.Frame(content_frame, bg=bg_main)
        top_row.pack(fill=tk.X, padx=10, pady=(4, 4))
        
        self.combo_var = tk.StringVar()
        self.combo = ttk.Combobox(top_row, textvariable=self.combo_var, state="readonly", justify="center")
        self.combo.pack(fill=tk.X, expand=True)

        mid_row = tk.Frame(content_frame, bg=bg_main)
        mid_row.pack(fill=tk.X, padx=10, pady=(0, 2))
        
        self.everstone_var = tk.BooleanVar()
        self.chk_everstone = tk.Checkbutton(mid_row, text="Everstone", font=("Segoe UI", 8), variable=self.everstone_var, bg=bg_main, command=self.on_everstone_toggle)
        self.chk_everstone.pack(anchor=tk.CENTER)

        settings_row = tk.Frame(content_frame, bg=bg_main)
        settings_row.pack(fill=tk.X, padx=10, pady=(0, 4))
        
        self.allow_wild_var = tk.BooleanVar(value=self.save_mgr.data["settings"]["allow_wild"])
        self.allow_breed_var = tk.BooleanVar(value=self.save_mgr.data["settings"]["allow_breeding"])
        
        chk_wild = tk.Checkbutton(settings_row, text="Salvajes", font=("Segoe UI", 8), variable=self.allow_wild_var, bg=bg_main, command=self.sync_settings)
        chk_wild.pack(side=tk.LEFT, expand=True)
        
        chk_breed = tk.Checkbutton(settings_row, text="Crianza", font=("Segoe UI", 8), variable=self.allow_breed_var, bg=bg_main, command=self.sync_settings)
        chk_breed.pack(side=tk.RIGHT, expand=True)

        self.fly_wrapper = tk.Frame(content_frame, bg=bg_main)
        self.fly_wrapper.pack(fill=tk.X, padx=10, pady=(0, 4))
        
        self.fly_row = tk.Frame(self.fly_wrapper, bg=bg_main)
        tk.Label(self.fly_row, text="Alt. Vuelo", font=("Segoe UI", 8), bg=bg_main).pack(side=tk.LEFT)
        
        self.fly_height_var = tk.DoubleVar(value=3.0)
        self.slider_fly = ttk.Scale(self.fly_row, from_=0, to=100, variable=self.fly_height_var, orient=tk.HORIZONTAL, command=self.sync_fly_height)
        self.slider_fly.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        
        btn_reset_fly = tk.Button(self.fly_row, text="R", font=("Segoe UI", 7, "bold"), bg="#95A5A6", fg="white", bd=0, width=2, command=self.reset_fly_height)
        btn_reset_fly.pack(side=tk.RIGHT)

        toy_row = tk.Frame(content_frame, bg=bg_main)
        toy_row.pack(fill=tk.X, padx=10, pady=(0, 5))
        self.btn_toy = tk.Button(toy_row, text="Juguete (Pokéball)", font=("Segoe UI", 8, "bold"), bg="#E67E22", fg="white", bd=0, pady=2, command=self.toggle_toy_ball)
        self.btn_toy.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 0))

        bottom_row = tk.Frame(content_frame, bg=bg_main)
        bottom_row.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        btn_spawn = tk.Button(bottom_row, text="Spawn", font=("Segoe UI", 8, "bold"), bg="#27AE60", fg="white", bd=0, pady=2, command=self.spawn_from_pc)
        btn_spawn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        btn_release = tk.Button(bottom_row, text="Release", font=("Segoe UI", 8, "bold"), bg="#8E44AD", fg="white", bd=0, pady=2, command=self.release_from_pc)
        btn_release.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 2))

        btn_reset = tk.Button(bottom_row, text="New Adventure", font=("Segoe UI", 8), bg="#E74C3C", fg="white", bd=0, pady=2, command=self.confirm_reset)
        btn_reset.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))

        # --- INYECCIÓN DISCORD RPC ---
        self.discord_rpc = DiscordRPC("1517136709039685685") 
        self.discord_rpc.update_loop(self.root)

        self.build_spawn_pool()
        self.combo.bind("<<ComboboxSelected>>", self.on_combo_select)
        self.update_pc_ui()
        self.restore_active_pets()
        
        self.root.after(15000, self.wild_spawner_loop)
        self.root.after(10000, self.xp_tick_loop)
        self.root.after(600000, self.egg_laying_loop) 
        self.root.after(120000, self.berry_spawner_loop) 
        self.root.mainloop()

    def berry_spawner_loop(self):
        self.active_berries = [b for b in self.active_berries if b.current_state != 'exiting']
        if random.randint(1, 100) <= 25: 
            base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
            def remove_berry(b):
                if b in self.active_berries: self.active_berries.remove(b)
            berry = InteractiveBerry(self.root, base_dir, self.get_all_pets, None)
            berry.on_destroy = lambda: remove_berry(berry)
            self.active_berries.append(berry)
        self.root.after(random.randint(120000, 240000), self.berry_spawner_loop)

    def toggle_toy_ball(self):
        if hasattr(self, 'active_toy') and self.active_toy:
            self.active_toy.destroy()
        else:
            base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
            self.active_toy = InteractivePokeball(self.root, base_dir, self.get_all_pets, self.clear_toy)
            self.btn_toy.config(text="Eliminar Juguete", bg="#E74C3C")
            
    def clear_toy(self):
        self.active_toy = None
        if hasattr(self, 'btn_toy') and self.btn_toy.winfo_exists():
            self.btn_toy.config(text="Juguete (Pokéball)", bg="#E67E22")

    def get_all_pets(self):
        return self.active_instances + self.wild_instances + self.overflow_instances

    def sync_settings(self):
        self.save_mgr.data["settings"]["allow_wild"] = self.allow_wild_var.get()
        self.save_mgr.data["settings"]["allow_breeding"] = self.allow_breed_var.get()
        self.save_mgr.save_data()

    def sync_fly_height(self, event=None):
        pet = self.get_selected_pet()
        if not pet: return
        
        pct = self.fly_height_var.get()
        
        pet["flying_height_pct"] = pct
        for p in self.save_mgr.data["inventory"]:
            if p["id"] == pet["id"]:
                p["flying_height_pct"] = pct
                break
        self.save_mgr.save_data()
        
        for instance in self.active_instances + getattr(self, 'overflow_instances', []):
            if instance.pet_data["id"] == pet["id"]:
                instance.recalculate_floor(pct)
                break

    def reset_fly_height(self):
        self.fly_height_var.set(3.0)
        self.sync_fly_height()

    def build_spawn_pool(self):
        self.spawn_pool_species = []
        self.spawn_pool_weights = []
        self.evo_parents = {}
        self.species_flying_status = {}
        
        all_available = [d for d in os.listdir(self.pets_directory) if os.path.isdir(os.path.join(self.pets_directory, d))]
        
        for species in all_available:
            config_path = os.path.join(self.pets_directory, species, "config.json")
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                
                physics = cfg.get("physics", {})
                self.species_flying_status[species] = physics.get("is_flying", False)
                
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
            
            is_fly = self.species_flying_status.get(pet["species"], False)
            if is_fly:
                self.fly_row.pack(fill=tk.X)
                self.fly_height_var.set(pet.get("flying_height_pct", 3.0))
            else:
                self.fly_row.pack_forget()
        else:
            self.everstone_var.set(False)
            self.fly_row.pack_forget()

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
            self.save_mgr.data = self.save_mgr.load_save()
            
            if not new_state:
                for active_pet in self.active_instances:
                    if active_pet.pet_data["species"] == target_species and active_pet.pet_data["level"] == target_level and active_pet.pet_data.get("is_shiny", False) == is_shiny_spawn:
                        active_pet.check_evolution()

    def confirm_reset(self):
        if messagebox.askyesno("Restart", "WARNING: This action will delete all your pokémon and reset the game data.\n\nProceed?"):
            StarterSelectionWindow(self.root, self.pets_directory, self.execute_reset)

    def execute_reset(self, chosen_species):
        if hasattr(self, 'active_toy') and self.active_toy:
            self.active_toy.destroy()
            
        for pet in self.active_instances + self.wild_instances:
            pet.window.destroy()
        self.active_instances.clear()
        self.wild_instances.clear()
        
        self.save_mgr.reset_save(chosen_species)
        
        self.update_pc_ui()
        self.restore_active_pets() 
        self.show_pc_ui()

    def update_pc_ui(self):
        # Esta función ahora solo construye la lista maestra (sin filtrar)
        if not self.save_mgr.data["inventory"]:
            self.full_display_list = ["(Vacio)"]
        else:
            formatted_list = []
            for p in self.save_mgr.data["inventory"]:
                if p.get("is_egg", False): continue
                
                shiny_tag = " ★" if p.get("is_shiny", False) else ""
                formatted_list.append(f"{p['species'].capitalize()}{shiny_tag} - lvl.{p['level']}")
            
            if not formatted_list:
                self.full_display_list = ["(Vacio)"]
            else:
                unique_owned = sorted(list(set(formatted_list)))
                display_list = []
                for p_str in unique_owned:
                    count = formatted_list.count(p_str)
                    if count > 1: 
                        display_list.append(f"{p_str} (x{count})")
                    else: 
                        display_list.append(p_str)
                self.full_display_list = display_list
                
        # Llama al filtro para aplicar la búsqueda (o mostrar todos si está en blanco)
        self.filter_pc_list()

    def filter_pc_list(self, *args):
        search_query = self.search_var.get().lower().strip()
        current_selection = self.combo_var.get()
        
        if not hasattr(self, 'full_display_list'):
            return

        if not search_query:
            filtered = self.full_display_list
        else:
            # Filtra ignorando mayúsculas y acentos
            filtered = [item for item in self.full_display_list if search_query in item.lower()]
            
        if not filtered:
            filtered = ["(No hay resultados)"]
            
        self.combo['values'] = filtered
        
        if current_selection in filtered:
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
        
        active_ids = [pet.pet_data["id"] for pet in self.active_instances]
        if pet_to_release["id"] in active_ids:
            import tkinter.messagebox as mb
            mb.showwarning("Operación Denegada", "Debes guardar a este Pokémon en el PC antes de liberarlo.")
            return

        species_name = pet_to_release['species'].capitalize()
        if messagebox.askyesno("Liberar Entidad", f"¿Estás seguro de que quieres liberar a este {species_name}?\nEsta acción destruirá sus datos para siempre."):
            self.save_mgr.data["inventory"] = [p for p in self.save_mgr.data["inventory"] if p["id"] != pet_to_release["id"]]
            self.save_mgr.save_data()
            self.update_pc_ui()
            print(f"[+] Entidad {species_name} eliminada de la base de datos local.")

    def restore_active_pets(self):
        active_ids = self.save_mgr.data.get("active_pets", [])
        active_pets_data = []
        
        for pid in active_ids:
            pet_data = next((p for p in self.save_mgr.data["inventory"] if p["id"] == pid), None)
            if pet_data:
                active_pets_data.append(pet_data)
                
        active_pets_data.sort(key=lambda x: x.get("is_egg", False))
        self._chain_spawn(active_pets_data, 0)

    def _chain_spawn(self, pet_list, current_index):
        if current_index >= len(pet_list):
            return
            
        self.spawn_entity(pet_list[current_index], is_wild=False)
        self.root.after(500, lambda: self._chain_spawn(pet_list, current_index + 1))

    def spawn_entity(self, pet_data, is_wild, coords=None, is_mid_evo=False, evo_channel=None, is_overflow=False):
        pet_dir = os.path.join(self.pets_directory, pet_data["species"])
        if not os.path.exists(os.path.join(pet_dir, "config.json")):
            print(f"Error: No existen assets para {pet_data['species']}")
            return
            
        pet = DesktopPet(
            self.root, pet_data, is_wild, self.on_pet_removed, self.on_pet_caught, 
            self.show_pc_ui, self.on_pet_evolve, coords, is_mid_evo, evo_channel, 
            is_overflow=is_overflow, get_all_pets_callback=self.get_all_pets, game_controller_ref=self
        )
        
        if is_wild: 
            self.wild_instances.append(pet)
        elif is_overflow: 
            self.overflow_instances.append(pet)
        else: 
            self.active_instances.append(pet)
            self.sync_save_state()
            # FIX: El último Pokémon del PC captura la atención de Discord
            if hasattr(self, 'discord_rpc'):
                self.discord_rpc.set_target(pet)

    def wild_spawner_loop(self):
        if self.save_mgr.data.get("settings", {}).get("allow_wild", True):
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
                        
                        wild_data = {
                            "id": str(uuid.uuid4()), "species": target, "level": lvl, 
                            "xp": 0, "is_shiny": is_shiny_roll, "last_evolution_level": lvl,
                            "flying_height_pct": 3.0, "xp_boost_expiry": 0
                        }
                        self.spawn_entity(wild_data, is_wild=True)
                        
        next_interval = random.randint(45000, 75000)
        self.root.after(next_interval, self.wild_spawner_loop)

    def xp_tick_loop(self):
        for pet in self.active_instances:
            if not pet.is_wild:
                if getattr(pet, 'is_egg', False):
                    rem = pet.pet_data.get("hatch_time_remaining", random.randint(900000, 1800000))
                    rem -= 10000 
                    pet.pet_data["hatch_time_remaining"] = rem
                    
                    if rem <= 0 and pet.current_state not in ['evolving_start', 'evolving_finish', 'exiting']:
                        pet.pet_data["hatch_time_remaining"] = 0
                        pet.hatch_egg()
                else:
                    pet.gain_xp(20) 
                
        self.save_mgr.save_data()
        self.update_pc_ui() 
        self.root.after(10000, self.xp_tick_loop)

    def egg_laying_loop(self):
        if self.save_mgr.data.get("settings", {}).get("allow_breeding", True):
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
                            "everstone": False,
                            "flying_height_pct": 3.0,
                            "hatch_time_remaining": random.randint(900000, 1800000), "xp_boost_expiry": 0
                        }
                        self.save_mgr.data["inventory"].append(egg_data)
                        self.save_mgr.save_data()
                        
                        self.spawn_entity(egg_data, is_wild=False, coords=(pet.x, pet.y))
                        break

        self.root.after(600000, self.egg_laying_loop)

    def on_pet_evolve(self, pet_instance, new_species, is_mid_evo=False, evo_channel=None):
        if getattr(pet_instance, 'is_egg', False):
            # 1. Quitarle el estado de huevo y asegurar sus datos en el Inventario (PC)
            pet_instance.pet_data["is_egg"] = False
            self.save_mgr.save_data()
            
            # 2. Contar cuántos Pokémon patrullando hay (excluyendo el huevo que acaba de romperse)
            active_count = len([p for p in self.active_instances if not getattr(p, 'is_egg', False) and p != pet_instance])
            
            # 3. Extraer coordenadas y destruir la instancia del huevo
            target_coords = (pet_instance.x, pet_instance.y)
            if pet_instance in self.active_instances:
                self.active_instances.remove(pet_instance)
                # CRÍTICO: Sincronizar aquí borra temporalmente al Pokémon de la lista de "Activos" en el JSON
                self.sync_save_state()
            pet_instance.window.destroy()

            # 4. Decisión de Spawn basada en el límite de campo (6)
            if active_count >= 6:
                # OVERFLOW (Caminar hacia la derecha y guardarse):
                # Al pasar is_overflow=True, el FSM lo obligará a caminar e irse.
                # Como NO se añade a active_instances, se queda guardado de forma segura únicamente en el PC.
                self.spawn_entity(pet_instance.pet_data, is_wild=False, coords=target_coords, is_mid_evo=is_mid_evo, evo_channel=evo_channel, is_overflow=True)
            else:
                # ESPACIO DISPONIBLE:
                # Nace normal, entra en active_instances y se vuelve a sincronizar como Activo en el JSON.
                self.spawn_entity(pet_instance.pet_data, is_wild=False, coords=target_coords, is_mid_evo=is_mid_evo, evo_channel=evo_channel)
            
            self.update_pc_ui()
            return

        # === LÓGICA PARA EVOLUCIONES DE POKÉMON NORMALES (NO HUEVOS) ===
        pet_instance.pet_data["species"] = new_species
        pet_instance.pet_data["last_evolution_level"] = pet_instance.pet_data["level"]
        self.save_mgr.save_data()

        target_coords = (pet_instance.x, pet_instance.y)
        if pet_instance in self.active_instances:
            self.active_instances.remove(pet_instance)
            self.sync_save_state()
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
        elif pet_instance in getattr(self, 'overflow_instances', []):
            self.overflow_instances.remove(pet_instance)

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
        if hasattr(self, 'active_toy') and self.active_toy:
            self.active_toy.destroy()
        self.sync_save_state()
        sys.exit()

if __name__ == '__main__':
    try:
        import pygame
        pygame.mixer.init()
    except: pass
    
    GameController()