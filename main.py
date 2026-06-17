import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import sys
import random
import math
import time
import uuid 

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

        render_state = state
        if render_state in ['falling', 'evolving_start', 'evolving_finish', 'ascending', 'falling_pokeball', 'falling_egg', 'dragged', 'thrown', 'falling_legendary', 'legendary_bounce', 'climbing']:
            render_state = 'idle'
        elif render_state in ['walking_away', 'jumping_arc', 'socializing', 'attacking', 'eating']:
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
                if self.is_legendary and not self.is_flying:
                    self.y = self.v_y - self.size_h
                    self.current_state = 'falling_legendary'
                elif self.is_legendary and self.is_flying:
                    self.y = self.v_y - self.size_h
                    self.floor_y = self.y 
                    self.current_state = 'ascending' 
                    self.play_shiny_sound() 
                else:
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
            'falling_egg': self._fsm_falling,
            'falling_pokeball': self._fsm_falling,
            'falling_legendary': self._fsm_falling,
            'socializing': self._fsm_socializing,
            'attacking': self._fsm_attacking,
            'eating': self._fsm_eating,
            'idle': self._fsm_active,
            'walking': self._fsm_active,
            'climbing': self._fsm_active
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
        
        def win_enum_handler(hwnd, ctx):
            if not win32gui.IsWindowVisible(hwnd): return
            if win32gui.IsIconic(hwnd): return 
            try: _, pid = win32process.GetWindowThreadProcessId(hwnd)
            except: return
            if pid == CURRENT_PID: return
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
        
        under_windows = [w for w in valid_windows if w['walkable'] and w['rect'][0] <= pet_center_x <= w['rect'][2] and w['floor'] >= pet_feet_y - 15]
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
        txt = self.canvas.create_text(self.size_w//2, 15, text="LEVEL UP!", fill="#F1C40F", font=("Segoe UI", 10, "bold"), tags="vfx_lvl")
        def float_up(step):
            if step < 20 and self.current_state != 'exiting':
                self.canvas.move(txt, 0, -1)
                self.window.after(50, lambda: float_up(step+1))
            else: self.canvas.delete(txt)
        float_up(0)

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
            if getattr(self, 'is_egg', False): self.on_open_pc(None) 
            else: self.on_open_pc(self.pet_data)

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
        handler = self.fsm.get(self.current_state, self._fsm_active)
        handler()

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

            if self.x <= self.v_x:
                self.x = self.v_x
                self.v_x_velocity *= -0.7 
                self.is_facing_right = True
            elif self.x >= (self.v_x + self.v_width) - self.size_w:
                self.x = (self.v_x + self.v_width) - self.size_w
                self.v_x_velocity *= -0.7
                self.is_facing_right = False
                
            current_env, _ = self.get_window_environment()
            physical_floor = current_env['y'] if self.y <= current_env['y'] + 15 else self.default_floor_y

            if self.y >= physical_floor and self.v_y_velocity > 0:
                self.y = physical_floor
                self.v_y_velocity *= -0.5
                
            if self.y < self.v_y:
                self.y = self.v_y
                self.v_y_velocity *= -0.5

            if abs(self.v_x_velocity) < 1.0 and abs(self.v_y_velocity) < 1.0:
                self.current_state = 'ascending'
                self.v_x_velocity = 0
                self.v_y_velocity = 0
                self.floor_y = self.y 
        elif getattr(self, 'is_climbing', False) or self.config.get("physics", {}).get("is_climbing", False):
            # Forzar la persistencia del atributo de escalada si el JSON lo dictamina
            self.is_climbing = True
            self.v_y_velocity += 1.5 
            self.v_x_velocity *= 0.95 
            self.y += self.v_y_velocity
            self.x += self.v_x_velocity
            
            wall_offset = getattr(self, 'climb_offset_x', 0)
            ceil_offset = getattr(self, 'climb_offset_y', 0)
            
            current_env, _ = self.get_window_environment()
            
            # ANCLAJE DETECTADO: Captura el impacto en el techo del monitor de forma efectiva con tolerancia
            if self.y <= self.v_y + 15:
                self.y = self.v_y + ceil_offset
                self.v_x_velocity = 0; self.v_y_velocity = 0
                self.climbing_surface = 'screen_ceiling'
                self.surface_angle = 180
                self.current_state = 'idle'
            elif self.x <= self.v_x:
                self.x = self.v_x + wall_offset
                self.v_x_velocity = 0; self.v_y_velocity = 0
                self.climbing_surface = 'screen_l'
                self.surface_angle = 270
                self.current_state = 'idle'
            elif self.x >= (self.v_x + self.v_width) - self.size_w:
                self.x = self.v_x + self.v_width - self.size_w - wall_offset
                self.v_x_velocity = 0; self.v_y_velocity = 0
                self.climbing_surface = 'screen_r'
                self.surface_angle = 90
                self.current_state = 'idle'
            else:
                physical_floor = current_env['y'] if self.y <= current_env['y'] + 15 else self.default_floor_y
                if self.v_y_velocity > 0 and self.y >= physical_floor:
                    self.y = physical_floor
                    self.floor_y = physical_floor
                    self.v_x_velocity = 0; self.v_y_velocity = 0
                    self.climbing_surface = 'floor'
                    self.surface_angle = 0
                    self.current_state = 'idle'
                    if current_env['hwnd']:
                        self.anchored_hwnd = current_env['hwnd']
                        self.anchored_rect = current_env['rect']
        else:
            self.v_y_velocity += 1.5 
            self.v_x_velocity *= 0.95 
            self.y += self.v_y_velocity
            self.x += self.v_x_velocity

            if self.x <= self.v_x:
                self.x = self.v_x
                self.v_x_velocity *= -0.7 
                self.is_facing_right = True
            elif self.x >= (self.v_x + self.v_width) - self.size_w:
                self.x = (self.v_x + self.v_width) - self.size_w
                self.v_x_velocity *= -0.7
                self.is_facing_right = False

            current_env, _ = self.get_window_environment()
            physical_floor = current_env['y'] if self.y <= current_env['y'] + 15 else self.default_floor_y

            if self.v_y_velocity > 0 and self.y >= physical_floor:
                self.y = physical_floor
                self.floor_y = physical_floor
                self.v_x_velocity = 0
                self.current_state = 'egg_idle' if getattr(self, 'is_egg', False) else 'idle'
            
        self.update_position()
        self.window.after(20, self.physics_loop)

    def _fsm_jumping_arc(self):
        self.v_y_velocity += 1.5 
        self.y += self.v_y_velocity
        self.x += (self.speed * 1.5) if self.is_facing_right else -(self.speed * 1.5)
        self.x = max(self.v_x, min(self.x, (self.v_x + self.v_width) - self.size_w))

        target_y = getattr(self, 'jump_target_y', getattr(self, 'floor_y', self.default_floor_y))
        
        if self.v_y_velocity > 0 and self.y >= target_y:
            self.y = target_y
            self.floor_y = target_y
            self.current_state = 'walking' 
            
            # --- ANCLAJE INSTANTÁNEO ---
            # Bloquea la condición de carrera asegurando la ventana físicamente en el frame exacto de aterrizaje.
            current_env, _ = self.get_window_environment()
            if current_env['hwnd']:
                self.anchored_hwnd = current_env['hwnd']
                self.anchored_rect = current_env['rect']
            else:
                self.anchored_hwnd = None
            # ---------------------------
                
            if hasattr(self, 'jump_target_y'): delattr(self, 'jump_target_y')
            
        self.update_position()
        self.window.after(30, self.physics_loop)
    def _fsm_ascending(self):
        if self.floor_y > getattr(self, 'target_floor_y', self.floor_y):
            self.floor_y -= 5
            if self.floor_y <= getattr(self, 'target_floor_y', self.floor_y):
                self.floor_y = self.target_floor_y
                self.current_state = 'idle'
        elif self.floor_y < getattr(self, 'target_floor_y', self.floor_y):
            self.floor_y += 5
            if self.floor_y >= getattr(self, 'target_floor_y', self.floor_y):
                self.floor_y = self.target_floor_y
                self.current_state = 'idle'
        else:
            self.current_state = 'idle'
            
        self.fly_amplitude += 0.2
        self.y = self.floor_y + math.sin(self.fly_amplitude) * 10
        self.update_position()
        self.window.after(50, self.physics_loop)

    def _fsm_walking_away(self):
        self.x += self.speed
        if self.x > self.v_x + self.v_width:
            self.on_remove(self)
            self.window.destroy()
            return
        if self.is_flying:
            self.fly_amplitude += 0.2
            self.y = self.floor_y + math.sin(self.fly_amplitude) * 10
        self.update_position()
        self.window.after(50, self.physics_loop)

    def _fsm_falling(self):
        self.y += 20 if self.current_state == 'falling_legendary' else 12
        self.x += getattr(self, 'v_x_velocity', 0.0)
        self.x = max(self.v_x, min(self.x, (self.v_x + self.v_width) - self.size_w))
        current_env, _ = self.get_window_environment()
        
        target_y = current_env['y'] if self.y <= current_env['y'] + 15 else self.default_floor_y

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
            else:
                if getattr(self, 'is_flying', False) and getattr(self, 'target_floor_y', self.y) != self.y:
                    self.floor_y = self.y
                    self.current_state = 'ascending'
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
        # Chequeo de seguridad: Si el objetivo ya no existe o aborta, salimos
        if not getattr(self, 'attack_target', None) or not self.attack_target.window.winfo_exists() or self.attack_target.current_state not in ['attacking', 'thrown']:
            self.current_state = 'idle'
            self.attack_target = None
            self.update_position()
            self.window.after(30, self.physics_loop)
            return

        current_time = time.time()
        if not hasattr(self, 'attack_phase_wait_until'):
            self.attack_phase_wait_until = 0.0

        # Pausas coreográficas de medio segundo justo antes de arrancar a correr
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
            # Fase previa: Se colocan EXACTAMENTE a 50 px de distancia
            if dist < 50: 
                self.x -= 3.0 * push_dir 
            elif dist > 55:
                self.x += 3.0 * push_dir 
            else: 
                advance_phase(1, pause=True)

        elif self.attack_phase == 1:
            # Primera carrera
            self.x += 10.0 * push_dir
            if dist <= self.size_w * 0.4: 
                advance_phase(2, pause=False)
                self.v_x_velocity = -1.5 * push_dir
                self.v_y_velocity = -5.0

        elif self.attack_phase == 2:
            # Primer rebote con corrección a 75 px
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
            # Segunda carrera
            self.x += 12.0 * push_dir
            if dist <= self.size_w * 0.4: 
                advance_phase(4, pause=False)
                self.v_x_velocity = -2.0 * push_dir
                self.v_y_velocity = -6.0

        elif self.attack_phase == 4:
            # Segundo rebote con corrección a 100 px
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
            # Tercera carrera extremadamente rápida
            self.x += 20.0 * push_dir
            if dist <= self.size_w * 0.4: 
                self.attack_phase = 6
                self.v_x_velocity = -25.0 * push_dir 
                self.v_y_velocity = -15.0            
                self.current_state = 'thrown' 
                
                # Inyección física al rival para que caigan y boten juntos
                if self.attack_target and getattr(self.attack_target, 'current_state', '') == 'attacking':
                    self.attack_target.v_x_velocity = 25.0 * push_dir 
                    self.attack_target.v_y_velocity = -15.0
                    self.attack_target.current_state = 'thrown'
                    self.attack_target.attack_target = None
                    self.attack_target.attack_phase = 0
                    
                self.attack_target = None
                # Se purga el 'return' que paralizaba el hilo FSM de este Pokémon

        # Seguridad de bordes de pantalla para los que no vuelan
        if not self.is_flying and self.current_state != 'thrown':
            self.x = max(self.v_x, min(self.x, (self.v_x + self.v_width) - self.size_w))

        # Flotación para los voladores durante el combate
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

        current_env, ahead_env = self.get_window_environment()
        ahead_physical_floor = ahead_env['y'] if type(ahead_env) is dict else ahead_env
        
        is_climber = getattr(self, 'is_climbing', False) or self.config.get("physics", {}).get("is_climbing", False)
        if is_climber:
            self.is_climbing = True

        if not getattr(self, 'is_flying', False):
            
            # --- ANCLAJE EN MODO TERRESTRE ---
            if self.current_state in ['idle', 'walking'] and current_env['hwnd']:
                if getattr(self, 'climbing_surface', 'floor') == 'floor':
                    if getattr(self, 'anchored_hwnd', None) != current_env['hwnd']:
                        self.anchored_hwnd = current_env['hwnd']
                        self.anchored_rect = current_env['rect']
            else:
                if not is_climber:
                    self.anchored_hwnd = None

            # Calcular suelo físico dinámico
            if getattr(self, 'anchored_hwnd', None) and getattr(self, 'anchored_rect', None) and getattr(self, 'climbing_surface', 'floor') == 'floor':
                current_physical_floor = self.anchored_rect[1] - self.size_h - self.offset_y
            elif self.y <= current_env['y'] + 15:
                current_physical_floor = current_env['y']
            else:
                current_physical_floor = self.default_floor_y

            self.floor_y = current_physical_floor

            # ====================================================================
            # LÓGICA DE FÍSICA PARA TERRESTRES NO ESCALADORES 
            # ====================================================================
            if not is_climber:
                if self.current_state in ['idle', 'walking'] and self.y < self.floor_y - 15:
                    self.current_state = 'jumping_arc'
                    self.jump_target_y = self.floor_y
                    self.v_y_velocity = -3.0  
                    
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
                        self.v_y_velocity = -3.0
                        self.jump_cooldown = 400
                        self.anchored_hwnd = None
                        self.anchored_rect = None

            # ====================================================================
            # LÓGICA DE FÍSICA Y SUPERFICIES PARA ESCALADORES
            # ====================================================================
            else:
                win_offset = 6 
                wall_offset = getattr(self, 'climb_offset_x', 0)
                ceil_offset = getattr(self, 'climb_offset_y', 0)

                # Caídas desde paredes, techos o suelo flotante (Si se minimiza/cierra la ventana)
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

                # Reposo en marcos del monitor
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

                # Lógica de caminata en superficies
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

                    else: # Comportamiento en escritorio (Monitor)
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
            # === LÓGICA PARA VOLADORES ===
            self.anchored_hwnd = None
            self.climbing_surface = 'floor'
            self.surface_angle = 0
            if self.floor_y > getattr(self, 'target_floor_y', self.floor_y):
                self.floor_y -= 5
            elif self.floor_y < getattr(self, 'target_floor_y', self.floor_y):
                self.floor_y += 5
            self.y = self.floor_y

        # ==== GESTIÓN FINAL DE ESTADOS GENÉRICOS ====
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
                        if self.x <= self.v_x:
                            self.x = self.v_x
                            self.is_facing_right = True
                        elif self.x >= (self.v_x + self.v_width) - self.size_w:
                            self.x = (self.v_x + self.v_width) - self.size_w
                            self.is_facing_right = False

        # === INTERACCIONES SOCIALES Y DE COMBATE ===
        if self.current_state in ['idle', 'walking'] and getattr(self, 'get_all_pets', None) and not getattr(self, 'is_egg', False) and getattr(self, 'climbing_surface', 'floor') == 'floor':
            if self.social_cooldown == 0 or self.attack_cooldown == 0:
                for other in self.get_all_pets():
                    if other != self and other.current_state in ['idle', 'walking'] and not getattr(other, 'is_egg', False) and getattr(other, 'climbing_surface', 'floor') == 'floor' and self.is_flying == other.is_flying:
                        my_true_floor = getattr(self, 'target_floor_y', self.floor_y) if self.is_flying else (self.floor_y + self.size_h + self.offset_y)
                        other_true_floor = getattr(other, 'target_floor_y', other.floor_y) if other.is_flying else (other.floor_y + other.size_h + other.offset_y)
                        if abs(my_true_floor - other_true_floor) < 15 and 80 < abs(self.x - other.x) < 150:
                            roll = random.randint(1, 100)
                            if roll <= 1 and self.attack_cooldown == 0 and other.attack_cooldown == 0:
                                self.current_state = 'attacking'
                                other.current_state = 'attacking'
                                self.attack_phase = 0
                                other.attack_phase = 0
                                self.attack_phase_wait_until = 0.0
                                other.attack_phase_wait_until = 0.0
                                self.attack_target = other
                                other.attack_target = self
                                self.attack_cooldown = 12000
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

        if self.current_state in ['idle', 'walking'] and not self.is_wild and not self.is_egg and getattr(self, 'climbing_surface', 'floor') == 'floor' and self.game_controller:
            for berry in getattr(self.game_controller, 'active_berries', []):
                if berry.current_state not in ['exiting', 'dragged']:
                    my_true_floor = getattr(self, 'target_floor_y', self.floor_y) if self.is_flying else (self.floor_y + self.size_h + self.offset_y)
                    berry_true_floor = berry.floor_y + berry.size - 6
                    if abs(my_true_floor - berry_true_floor) < 15 and abs(self.x - berry.x) < 20:
                        self.current_state = 'eating'
                        self.eating_timer = 30
                        self.is_facing_right = (berry.x > self.x)
                        self.interaction_target = berry
                        berry.destroy()
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
            self.current_state = 'idle' 
            
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

    def destroy(self):
        self.current_state = 'exiting'
        if self.on_destroy:
            self.on_destroy()
        self.window.destroy()

    def update_position(self):
        self.window.geometry(f"+{int(self.x)}+{int(self.y)}")
        
    def on_drag_start(self, event):
        if self.current_state == 'exiting': return
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
                if pid == CURRENT_PID: return
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
        
        w, h = 280, 205 
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

        btn_reset = tk.Button(bottom_row, text="Format PC", font=("Segoe UI", 8), bg="#E74C3C", fg="white", bd=0, pady=2, command=self.confirm_reset)
        btn_reset.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))

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
        if random.randint(1, 100) <= 20: 
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
        if messagebox.askyesno("Reinicio", "ALERTA: Esto borrará todos tus Pokémon y restablecerá los datos de fábrica.\n\n¿Proceder?"):
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
            pet_instance.pet_data["is_egg"] = False
            self.save_mgr.save_data()
            
            active_count = len([p for p in self.active_instances if not getattr(p, 'is_egg', False) and p != pet_instance])
            
            target_coords = (pet_instance.x, pet_instance.y)
            if pet_instance in self.active_instances:
                self.active_instances.remove(pet_instance)
            pet_instance.window.destroy()

            if active_count >= 6:
                self.spawn_entity(pet_instance.pet_data, is_wild=False, coords=target_coords, is_mid_evo=is_mid_evo, evo_channel=evo_channel, is_overflow=True)
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