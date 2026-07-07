
import ctypes
from entities.animator import DesktopPetAnimator
try:
    import win32process
    import win32con
    import win32api
except ImportError:
    pass

import os
import sys
import json
import time
import math
import random
import tkinter as tk
from PIL import Image, ImageTk
from entities.interactables import BubbleProjectile
try:
    import win32gui
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

# --- ENTIDAD FÍSICA (REFACCIONADA A MÁQUINA DE ESTADOS) ---
from mechanics.rayquaza import RayquazaMechanics
from mechanics.lugia import LugiaMechanics
from mechanics.mewtwo import MewtwoMechanics
from mechanics.hooh import HoOhMechanics
from mechanics.kyogre import KyogreMechanics
from mechanics.groudon import GroudonMechanics
from mechanics.telekinesis import TelekinesisMechanics
from mechanics.dark_arts import DarkArtsMechanics
from mechanics.shared_vfx import SharedVFX
from mechanics.dialga import DialgaMechanics
from mechanics.palkia import PalkiaMechanics

class DesktopPet(DialgaMechanics, PalkiaMechanics, RayquazaMechanics, LugiaMechanics, MewtwoMechanics, HoOhMechanics, KyogreMechanics, GroudonMechanics, TelekinesisMechanics, DarkArtsMechanics, SharedVFX):
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
        
        self.base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
        self.bubble_blower = physics.get("bubble_blower", False) 
        self.can_dig = physics.get("can_dig", False)
        self.fairy_aura = physics.get("fairy_aura", False)
        self.dark_arts = physics.get("dark_arts", False) # NUEVA
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
            
            # FIX: Anular mecánicas avanzadas para que el huevo no herede comportamientos de adulto
            self.heavy_fall = False
            self.can_screen_wrap = False
            self.can_teleport = False
            self.telekinetic = False
            self.bubble_blower = False
            self.can_dig = False
            self.fairy_aura = False
            self.dark_arts = False
            self.aggressive = False
            
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
            self.schedule_loop(random.randint(45000, 75000), self.egg_wiggle_loop)
        
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
            self.despawn_timer = self.schedule_loop(despawn_time, self.start_wild_despawn)
            
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
            'teleporting_in': self._fsm_teleporting_in,
            'bubbled': self._fsm_bubbled,
            'digging_in': self._fsm_digging_in,
            'digging': self._fsm_digging,
            'digging_out': self._fsm_digging_out,
            'mewtwo_channeling': self._fsm_mewtwo_channeling, 
            'mewtwo_victim': self._fsm_mewtwo_victim,
            'hooh_channeling': self._fsm_hooh_channeling, 
            'panic_run': self._fsm_panic_run,
            'kyogre_channeling': self._fsm_kyogre_channeling,
            'deluge_float': self._fsm_deluge_float,
            'groudon_channeling': self._fsm_groudon_channeling,
            'lugia_channeling': self._fsm_lugia_channeling,
            'lugia_dash': self._fsm_lugia_dash,
            'rayquaza_channeling': self._fsm_rayquaza_channeling, # NUEVO
            'rayquaza_cyclone_victim': self._fsm_rayquaza_cyclone_victim, # NUEVO
            'palkia_channeling': self._fsm_palkia_channeling,
            'palkia_invert_transition': self._fsm_palkia_invert_transition,
            'palkia_revert_transition': self._fsm_palkia_revert_transition
        }            
        self.keep_on_top()
        self.animate_loop()
        self.physics_loop()

    def keep_on_top(self):
        if self.current_state != 'exiting':
            try: self.window.attributes('-topmost', True)
            except: pass
            self.schedule_loop(2000, self.keep_on_top)

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
                
        # FIX: Explotar la burbuja manualmente si agarras al objetivo
        if self.current_state == 'bubbled':
            self.manage_bubble_vfx(False)
            self.show_bubble_burst_vfx()
            self.current_state = 'thrown' if getattr(self, 'is_flying', False) else 'falling'

        # FIX: Interrumpir la excavación manualmente restaurando las coordenadas internas
        if self.current_state in ['digging', 'digging_in', 'digging_out']:
            self.canvas.itemconfig(self.canvas_image_id, state='normal')
            # Reset estricto al centro geométrico del Canvas
            self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2) 
            self.current_state = 'falling'

        # FIX: Destruir interacción de las Sombras si intervienes
        if self.current_state.startswith('dark_'):
            self.cancel_dark_arts()

        # FIX: Interrumpir el Vórtice Psíquico de Mewtwo
        if self.current_state.startswith('mewtwo_'):
            self.cancel_mewtwo_arts()

        # FIX: Interrumpir Fuego Sagrado de Ho-Oh
        if self.current_state in ['hooh_channeling', 'panic_run']:
            self.cancel_hooh_arts()
        # FIX: Solo cancelar Kyogre si agarras al Maestro (Kyogre). 
        # Las víctimas pueden ser arrastradas y seguirán afectadas por la inundación al soltarlas.
        elif self.current_state == 'kyogre_channeling':
            self.cancel_kyogre_arts()

        elif self.current_state == 'groudon_channeling': self.cancel_groudon_arts()

        elif self.current_state in ['lugia_channeling', 'lugia_dash']: self.cancel_lugia_arts()

        elif self.current_state == 'rayquaza_channeling': self.cancel_rayquaza_arts()

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
                self.climbing_surface = 'floor'
                self.surface_angle = 180 if getattr(self, 'gravity_inverted', False) else 0
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

        # FIX: Destrucción del vínculo si se hace clic en la víctima de telequinesis
        if self.current_state == 'tk_lifted':
            self.current_state = 'falling'
            self.manage_tk_aura(self.canvas, self.size_w, self.size_h, False)
            master = getattr(self, 'tk_master', None)
            if master and master.current_state == 'tk_channeling':
                master.current_state = 'idle'
                master.manage_tk_aura(master.canvas, master.size_w, master.size_h, False)
                master.tk_target = None
            self.tk_master = None
            
        # FIX: Explotar la burbuja manualmente si agarras al objetivo
        if self.current_state == 'bubbled':
            self.manage_bubble_vfx(False)
            self.show_bubble_burst_vfx()
            self.current_state = 'falling'

        # FIX: Interrumpir la excavación manualmente si agarras al objetivo
        if self.current_state == 'digging':
            self.canvas.itemconfig(self.canvas_image_id, state='normal')
            self.current_state = 'falling'

        # FIX: Destruir interacción de las Sombras si intervienes
        if self.current_state.startswith('dark_'):
            self.cancel_dark_arts()

        # FIX: Interrumpir Fuego Sagrado de Ho-Oh
        if self.current_state in ['hooh_channeling', 'panic_run']:
            self.cancel_hooh_arts()
        # FIX: Solo cancelar Kyogre si agarras al Maestro (Kyogre). 
        # Las víctimas pueden ser arrastradas y seguirán afectadas por la inundación al soltarlas.
        elif self.current_state == 'kyogre_channeling':
            self.cancel_kyogre_arts()

        elif self.current_state == 'groudon_channeling': self.cancel_groudon_arts()

        elif self.current_state in ['lugia_channeling', 'lugia_dash']: self.cancel_lugia_arts()

        elif self.current_state == 'rayquaza_channeling': self.cancel_rayquaza_arts()
        
        # ACTUALIZACIÓN DE VARIABLES PARA FÍSICAS (Sin alterar el offset del ratón)
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
            
            # FIX: Si está siendo inundado, vuelve al estado flotante en lugar de estrellarse contra el suelo
            if getattr(self, 'kyogre_master', None) and getattr(self.kyogre_master, 'current_state', '') == 'kyogre_channeling':
                self.current_state = 'deluge_float'
            else:
                self.current_state = 'thrown'

    def get_window_environment(self):
        is_inverted = getattr(self, 'gravity_inverted', False)
        current_env = {'y': self.v_y if is_inverted else self.default_floor_y, 'hwnd': None, 'rect': None}
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
        elif self.current_state in ['thrown', 'jumping_arc'] and getattr(self, 'v_y_velocity', 0) != 0:
            fall_tolerance = max(15, abs(int(self.v_y_velocity)) + 15)
        
        def win_enum_handler(hwnd, ctx):
            if not win32gui.IsWindowVisible(hwnd): return
            if win32gui.IsIconic(hwnd): return 
            try: _, pid = win32process.GetWindowThreadProcessId(hwnd)
            except: return
            
            if pid == CURRENT_PID:
                title = win32gui.GetWindowText(hwnd)
                if title != "Bill's PC": return

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
            
            if is_inverted:
                win_floor = rect[3] + getattr(self, 'offset_y', 0)
            else:
                win_floor = rect[1] - self.size_h - getattr(self, 'offset_y', 0)
                
            valid_windows.append({'hwnd': hwnd, 'rect': rect, 'floor': win_floor, 'z': len(valid_windows), 'walkable': not is_fullscreen})
            
        win32gui.EnumWindows(win_enum_handler, None)
        
        if is_inverted:
            under_windows = [w for w in valid_windows if w['walkable'] and w['rect'][0] <= pet_center_x <= w['rect'][2] and w['floor'] <= pet_feet_y + fall_tolerance]
        else:
            under_windows = [w for w in valid_windows if w['walkable'] and w['rect'][0] <= pet_center_x <= w['rect'][2] and w['floor'] >= pet_feet_y - fall_tolerance]
            
        if under_windows:
            under_windows.sort(key=lambda w: w['floor'], reverse=is_inverted)
            for uw in under_windows:
                is_occluded = False
                check_y = uw['rect'][3] - 5 if is_inverted else uw['rect'][1] + 5
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
                check_y = sw['rect'][3] - 5 if is_inverted else sw['rect'][1] + 5
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
            self.schedule_loop(random.randint(45000, 75000), self.egg_wiggle_loop)

    def animate_egg_wiggle(self, step=0):
        if self.current_state != 'egg_wiggle': return
        frames = [15, -15, 10, -10, 5, -5, 0]
        if step >= len(frames):
            self.current_state = 'egg_idle'
            if getattr(self, 'egg_tk', None): self.canvas.itemconfig(self.canvas_image_id, image=self.egg_tk)
            self.schedule_loop(random.randint(45000, 75000), self.egg_wiggle_loop)
            return
        rotated = self.egg_base_img.rotate(frames[step], expand=True, resample=Image.NEAREST)
        self.egg_tk_wiggle = ImageTk.PhotoImage(rotated)
        self.canvas.itemconfig(self.canvas_image_id, image=self.egg_tk_wiggle)
        self.schedule_loop(80, lambda: self.animate_egg_wiggle(step + 1))

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
        self.schedule_loop(50, lambda: self.start_evolution_vfx(target_species, step+1))

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
        self.schedule_loop(50, lambda: self.finish_evolution_vfx(step+1))

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
                    
                self.schedule_loop(50, lambda: float_up(step+1))
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
                self.schedule_loop(50, lambda: float_up(step+1))
            else: 
                self.canvas.delete("vfx_heart")
        float_up(0)











        






        





        












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
        self.schedule_loop(30, lambda: self.animate_egg_spawn(step + 1))

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
            self.schedule_loop(300, self.window.destroy)
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
            self.schedule_loop(30, lambda: self.animate_vfx(action_type, step + 1))
        else:
            self.schedule_loop(100, self.window.destroy)

    def start_wild_despawn(self):
        if self.current_state in ['exiting', 'evolving_start', 'evolving_finish', 'despawning_wild']: return
        
        # FIX ESTRUCTURAL: Liberar víctima antes de desaparecer en la hierba/nube
        if self.current_state.startswith('dark_'):
            self.cancel_dark_arts()
        elif self.current_state.startswith('mewtwo_'):
            self.cancel_mewtwo_arts()
        elif self.current_state in ['hooh_channeling', 'panic_run']:
            self.cancel_hooh_arts()
        elif self.current_state == 'groudon_channeling': self.cancel_groudon_arts()
        elif self.current_state == 'kyogre_channeling': self.cancel_kyogre_arts()
        elif self.current_state in ['lugia_channeling', 'lugia_dash']: self.cancel_lugia_arts()
        elif self.current_state == 'rayquaza_channeling': self.cancel_rayquaza_arts()
            
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
        self.schedule_loop(30, lambda: self.animate_wild_despawn(step + 1))

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
        self.schedule_loop(30, lambda: self.animate_wild_spawn(step + 1))

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
        self.schedule_loop(30, lambda: self.animate_owned_spawn(step + 1))

    def handle_right_click(self, event):
        if self.is_egg: return
        if self.current_state not in ['exiting', 'evolving_start', 'evolving_finish', 'despawning_wild']:
            
            # FIX ESTRUCTURAL: Liberar conexiones Siniestras si se guarda en la Pokéball
            if self.current_state.startswith('dark_'):
                self.cancel_dark_arts()
            elif self.current_state.startswith('mewtwo_'):
                self.cancel_mewtwo_arts()
            elif self.current_state in ['hooh_channeling', 'panic_run']:
                self.cancel_hooh_arts()
            elif self.current_state == 'groudon_channeling': self.cancel_groudon_arts()
            elif self.current_state == 'kyogre_channeling': self.cancel_kyogre_arts()
            elif self.current_state in ['lugia_channeling', 'lugia_dash']: self.cancel_lugia_arts()
            elif self.current_state == 'rayquaza_channeling': self.cancel_rayquaza_arts()
                
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
        if getattr(self, 'anchored_hwnd', None) and self.current_state in ['idle', 'walking', 'socializing', 'attacking', 'digging', 'digging_in', 'digging_out']:
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
                            # FIX: Seguir el borde inferior de la ventana si está invertido
                            if getattr(self, 'gravity_inverted', False):
                                self.y += delta_b
                                self.floor_y += delta_b
                            else:
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
                
        # --- FIX: ANULAR MOONWALK EN GRAVEDAD INVERTIDA ---
        if getattr(self, 'gravity_inverted', False):
            render_facing_right = not render_facing_right

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
            target_ms = self.frame_rate_active if self.current_state in ['walking', 'falling', 'walking_away', 'jumping_arc', 'climbing', 'attacking', 'eating', 'dark_dash', 'hooh_channeling', 'panic_run', 'kyogre_channeling', 'deluge_float', 'groudon_channeling', 'lugia_channeling', 'lugia_dash', 'rayquaza_channeling', 'rayquaza_cyclone_victim', 'dialga_channeling'] else self.frame_rate_idle
            if getattr(self, 'time_distorted', False):
                target_ms = int(target_ms * 4.0)
            
            anim_state = self.current_state
            if anim_state == 'hooh_channeling' and getattr(self, 'hooh_phase', 0) == 1:
                anim_state = 'idle'
            # FIX: Kyogre mira al frente mientras invoca la lluvia
            if anim_state == 'kyogre_channeling' and getattr(self, 'kyogre_phase', 0) == 1:
                anim_state = 'idle'
            if anim_state == 'dialga_channeling':
                anim_state = 'jump' if getattr(self, 'dialga_step', 0) < 2 else 'idle'
                
            self.animator.update_animation(anim_state, render_facing_right, self.canvas_image_id, True, target_ms, blend_factor=blend, rotation_angle=self.surface_angle, is_glitching=getattr(self, 'is_glitching', False), is_darkened=getattr(self, 'dark_mode', False))
                        
        self.schedule_loop(16, self.animate_loop)

    def physics_loop(self):
        if hasattr(self, 'check_time_distortion'):
            self.check_time_distortion()
        if hasattr(self, 'check_gravity_inversion'):
            self.check_gravity_inversion()
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
        self.schedule_loop(50, self.physics_loop)

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
            # --- PARCHE ESTRUCTURAL: GRAVEDAD NEGATIVA (HACIA ARRIBA) EN LANZAMIENTOS ---
            if getattr(self, 'gravity_inverted', False):
                # La gravedad ahora tira hacia los números negativos (arriba en Tkinter)
                gravity = -4.0 if getattr(self, 'heavy_fall', False) and self.v_y_velocity <= 0.5 else -1.5
                self.v_y_velocity += gravity
                self.v_x_velocity *= 0.95 
                self.y += self.v_y_velocity
                self.x += self.v_x_velocity

                # Límites laterales
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

                # FIX: Inyectar el Radar de Ventanas para lanzamientos
                current_env, _ = self.get_window_environment()
                fall_tolerance = max(15, abs(int(self.v_y_velocity)) + 15) if self.v_y_velocity < 0 else 15
                
                target_y = current_env['y'] if self.y <= current_env['y'] + fall_tolerance else self.v_y
                if getattr(self, 'is_flying', False): target_y += getattr(self, 'target_offset_y', 0)

                # Si su velocidad es negativa (subiendo) y choca contra el techo/ventana
                if self.v_y_velocity < 0 and self.y <= target_y:
                    self.y = target_y
                    self.floor_y = target_y
                    self.v_x_velocity = 0
                    
                    if current_env['hwnd']:
                        self.anchored_hwnd = current_env['hwnd']
                        self.anchored_rect = current_env['rect']
                    else:
                        self.anchored_hwnd = None
                        
                    if getattr(self, 'heavy_fall', False) and self.v_y_velocity < -15:
                        self.trigger_landing_shake()
                    else:
                        if getattr(self, 'is_overflow', False):
                            self.current_state = 'walking_away'
                            self.is_facing_right = True
                        else:
                            self.current_state = 'egg_idle' if getattr(self, 'is_egg', False) else 'idle'
                
                self.update_position()
                self.schedule_loop(20, self.physics_loop)
                return
            # -------------------------------------------------------------
            
            gravity = 4.0 if getattr(self, 'heavy_fall', False) and self.v_y_velocity >= -0.5 else 1.5
            self.v_y_velocity += gravity
            
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
        self.schedule_loop(20, self.physics_loop)

    def _fsm_jumping_arc(self):
        is_inverted = getattr(self, 'gravity_inverted', False)
        gravity = -1.5 if is_inverted else 1.5
        
        if getattr(self, 'heavy_fall', False):
            if is_inverted and self.v_y_velocity <= 0.5: gravity = -4.0
            elif not is_inverted and self.v_y_velocity >= -0.5: gravity = 4.0

        self.v_y_velocity += gravity
        self.y += self.v_y_velocity
        self.x += (self.speed * 1.5) if self.is_facing_right else -(self.speed * 1.5)
        
        if getattr(self, 'can_screen_wrap', False):
            if self.x <= self.v_x - self.size_w: self.x = self.v_x + self.v_width
            elif self.x >= self.v_x + self.v_width: self.x = self.v_x - self.size_w
        else:
            self.x = max(self.v_x, min(self.x, (self.v_x + self.v_width) - self.size_w))

        target_y = getattr(self, 'jump_target_y', getattr(self, 'floor_y', self.v_y if is_inverted else self.default_floor_y))
        
        condition = (self.v_y_velocity < 0 and self.y <= target_y) if is_inverted else (self.v_y_velocity > 0 and self.y >= target_y)
        
        if condition:
            self.y = target_y
            self.floor_y = target_y
            
            if getattr(self, 'heavy_fall', False) and abs(self.v_y_velocity) > 15:
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
        self.schedule_loop(30, self.physics_loop)

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
        self.schedule_loop(50, self.physics_loop)

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
        self.schedule_loop(50, self.physics_loop)

    def _fsm_falling(self):
        fall_speed = 12
        if self.current_state == 'falling' and getattr(self, 'heavy_fall', False):
            fall_speed = 25
        elif self.current_state == 'falling_legendary': 
            fall_speed = 20

        # --- PARCHE ESTRUCTURAL: GRAVEDAD NEGATIVA (HACIA ARRIBA) ---
        if getattr(self, 'gravity_inverted', False):
            self.y -= fall_speed
            self.x += getattr(self, 'v_x_velocity', 0.0)
            
            if getattr(self, 'can_screen_wrap', False):
                if self.x <= self.v_x - self.size_w: self.x = self.v_x + self.v_width
                elif self.x >= self.v_x + self.v_width: self.x = self.v_x - self.size_w
            else:
                self.x = max(self.v_x, min(self.x, (self.v_x + self.v_width) - self.size_w))

            # FIX: Inyectar el Radar de Ventanas para caída libre invertida
            current_env, _ = self.get_window_environment()
            fall_tolerance = max(15, fall_speed + 15)
            
            target_y = current_env['y'] if self.y <= current_env['y'] + fall_tolerance else self.v_y
            if getattr(self, 'is_flying', False): target_y += getattr(self, 'target_offset_y', 0)

            if self.y <= target_y:
                self.y = target_y
                self.floor_y = target_y
                self.v_x_velocity = 0
                
                if current_env['hwnd']:
                    self.anchored_hwnd = current_env['hwnd']
                    self.anchored_rect = current_env['rect']
                else:
                    self.anchored_hwnd = None

                if getattr(self, 'heavy_fall', False):
                    self.trigger_landing_shake()
                else:
                    self.current_state = 'idle'
                    
            self.update_position()
            self.schedule_loop(20, self.physics_loop)
            return
        # -------------------------------------------------------------

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
        self.schedule_loop(20, self.physics_loop)

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
        self.schedule_loop(50, self.physics_loop)

    def _fsm_attacking(self):
        if not getattr(self, 'attack_target', None) or not self.attack_target.window.winfo_exists() or self.attack_target.current_state not in ['attacking', 'thrown']:
            self.current_state = 'idle'
            self.attack_target = None
            self.update_position()
            self.schedule_loop(30, self.physics_loop)
            return

        current_time = time.time()
        if not hasattr(self, 'attack_phase_wait_until'):
            self.attack_phase_wait_until = 0.0

        if current_time < self.attack_phase_wait_until:
            self.update_position()
            self.schedule_loop(30, self.physics_loop)
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
        self.schedule_loop(30, self.physics_loop)

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
        self.schedule_loop(50, self.physics_loop)

    def schedule_glitch_teleport(self):
        if not getattr(self, 'is_glitching', False) or self.current_state == 'exiting':
            return
            
        # Si el usuario lo agarra o está involucrado en telequinesis, pausamos los saltos
        if self.current_state in ['dragged', 'tk_controlled', 'tk_lifted']:
            self.schedule_loop(500, self.schedule_glitch_teleport)
            return
            
        if getattr(self, 'glitch_teleports_left', 0) > 0:
            self.glitch_teleports_left -= 1
            
            # Teletransporte caótico: Nueva coordenada X
            self.x = random.randint(self.v_x, self.v_x + self.v_width - self.size_w)
            
            if getattr(self, 'is_flying', False):
                self.y = random.randint(self.v_y, self.default_floor_y)
                self.floor_y = self.y
            else:
                self.y = self.default_floor_y if getattr(self, 'gravity_inverted', False) else self.v_y 
                current_env, _ = self.get_window_environment()
                
                if current_env['hwnd']:
                    self.anchored_hwnd = current_env['hwnd']
                    self.anchored_rect = current_env['rect']
                    self.floor_y = current_env['y']
                    self.y = self.floor_y
                else:
                    self.anchored_hwnd = None
                    self.anchored_rect = None
                    self.floor_y = self.v_y if getattr(self, 'gravity_inverted', False) else self.default_floor_y
                    self.y = self.floor_y
                
            self.update_position()
            
            # Programar la siguiente interferencia entre 1.5 y 3 segundos
            self.schedule_loop(random.randint(1500, 3000), self.schedule_glitch_teleport)
        else:
            # Fin de la fase
            self.is_glitching = False
            self.glitch_cooldown = 12000
            try: self.window.attributes('-alpha', 1.0)
            except: pass

    def _fsm_digging_in(self):
        self.dig_step += 1
        desplazamiento = self.dig_step * 3
        if getattr(self, 'gravity_inverted', False):
            self.canvas.coords(self.canvas_image_id, self.size_w//2, (self.size_h//2) - desplazamiento)
        else:
            self.canvas.coords(self.canvas_image_id, self.size_w//2, (self.size_h//2) + desplazamiento)
        
        if self.dig_step % 2 == 0:
            self.show_dirt_vfx()
            
        if desplazamiento >= self.size_h // 2 + 10: 
            # Totalmente oculto bajo el límite del Canvas
            self.current_state = 'digging'
            self.canvas.itemconfig(self.canvas_image_id, state='hidden')
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_digging(self):
        self.dig_timer -= 1
        
        # --- NAVEGACIÓN ORGÁNICA ---
        if random.randint(1, 1000) <= 20:
            self.is_facing_right = not self.is_facing_right
        
        velocidad_excavacion = self.speed * 2

        # FIX: Clampeo estricto y predictivo contra redimensionados de ventana bruscos
        if getattr(self, 'anchored_rect', None):
            rect = self.anchored_rect
            
            # 1. Clampeo de emergencia: Si la ventana lo ha dejado fuera, lo forzamos adentro
            if self.x > rect[2] - self.size_w:
                self.x = rect[2] - self.size_w
                self.is_facing_right = False
            elif self.x < rect[0]:
                self.x = rect[0]
                self.is_facing_right = True
            # 2. Comprobación predictiva estándar: Rebotar antes de salir
            else:
                if self.is_facing_right and self.x + velocidad_excavacion > rect[2] - self.size_w:
                    self.is_facing_right = False
                elif not self.is_facing_right and self.x - velocidad_excavacion < rect[0]:
                    self.is_facing_right = True

        self.x += velocidad_excavacion if self.is_facing_right else -velocidad_excavacion
        
        if getattr(self, 'can_screen_wrap', False):
            if self.x <= self.v_x - self.size_w: self.x = self.v_x + self.v_width
            elif self.x >= self.v_x + self.v_width: self.x = self.v_x - self.size_w
        else:
            if self.x <= self.v_x:
                self.x = self.v_x
                self.is_facing_right = True
            elif self.x >= (self.v_x + self.v_width) - self.size_w:
                self.x = (self.v_x + self.v_width) - self.size_w
                self.is_facing_right = False
        
        current_env, _ = self.get_window_environment()
        if getattr(self, 'anchored_hwnd', None):
            if not current_env['hwnd'] or current_env['hwnd'] != self.anchored_hwnd:
                self.anchored_hwnd = None
                self.canvas.itemconfig(self.canvas_image_id, state='normal')
                self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
                self.current_state = 'falling'
                self.v_y_velocity = 0.0
                self.update_position()
                self.schedule_loop(30, self.physics_loop)
                return
        
        if getattr(self, 'anchored_hwnd', None):
            self.y = getattr(self, 'anchored_rect', [0, 0, 0, 0])[3] + getattr(self, 'offset_y', 0) if getattr(self, 'gravity_inverted', False) else getattr(self, 'anchored_rect', [0, 0, 0, 0])[1] - self.size_h - getattr(self, 'offset_y', 0)
        else:
            self.y = self.v_y if getattr(self, 'gravity_inverted', False) else self.default_floor_y
        self.floor_y = self.y
        
        if self.dig_timer % 4 == 0:
            self.show_dirt_vfx()
            
        if self.dig_timer <= 0:
            self.current_state = 'digging_out'
            self.canvas.itemconfig(self.canvas_image_id, state='normal')
            
        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def _fsm_digging_out(self):
        self.dig_step -= 1
        desplazamiento = self.dig_step * 3
        if getattr(self, 'gravity_inverted', False):
            self.canvas.coords(self.canvas_image_id, self.size_w//2, (self.size_h//2) - desplazamiento)
        else:
            self.canvas.coords(self.canvas_image_id, self.size_w//2, (self.size_h//2) + desplazamiento)
        
        if self.dig_step % 2 == 0:
            self.show_dirt_vfx()
            
        if self.dig_step <= 0:
            self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
            self.current_state = 'idle'
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)



    def _fsm_active(self):
        self.jump_cooldown = max(0, getattr(self, 'jump_cooldown', 0) - 1)
        self.social_cooldown = max(0, getattr(self, 'social_cooldown', 0) - 1)
        self.attack_cooldown = max(0, getattr(self, 'attack_cooldown', 0) - 1)
        self.teleport_cooldown = max(0, getattr(self, 'teleport_cooldown', 0) - 1)

        self.tk_cooldown = max(0, getattr(self, 'tk_cooldown', 0) - 1)
        self.glitch_cooldown = max(0, getattr(self, 'glitch_cooldown', 0) - 1)
        self.bubble_cooldown = max(0, getattr(self, 'bubble_cooldown', 0) - 1)
        self.dig_cooldown = max(0, getattr(self, 'dig_cooldown', 0) - 1)
        
        # FIX: Inicialización y decaimiento del contador Siniestro por fotograma
        self.dark_cooldown = max(0, getattr(self, 'dark_cooldown', 0) - 1) 
        self.mewtwo_cooldown = max(0, getattr(self, 'mewtwo_cooldown', 0) - 1) 
        self.dialga_cooldown = max(0, getattr(self, 'dialga_cooldown', 0) - 1)
        self.hooh_cooldown = max(0, getattr(self, 'hooh_cooldown', 0) - 1) 
        self.kyogre_cooldown = max(0, getattr(self, 'kyogre_cooldown', 0) - 1)
        self.groudon_cooldown = max(0, getattr(self, 'groudon_cooldown', 0) - 1)
        self.lugia_cooldown = max(0, getattr(self, 'lugia_cooldown', 0) - 1)
        self.rayquaza_cooldown = max(0, getattr(self, 'rayquaza_cooldown', 0) - 1) # NUEVO
        self.palkia_cooldown = max(0, getattr(self, 'palkia_cooldown', 0) - 1)

        # --- MECÁNICA EXCLUSIVA: INVERSIÓN ESPACIAL DE PALKIA ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "palkia" and getattr(self, 'palkia_cooldown', 0) == 0 and self.current_state in ['idle', 'walking']:
            if random.randint(1, 1000) <= 8:
                self.current_state = 'palkia_channeling'
                self.schedule_loop(50, self.physics_loop)
                return

        # --- MECÁNICA EXCLUSIVA: CICLÓN ESMERALDA DE RAYQUAZA ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "rayquaza" and self.rayquaza_cooldown == 0 and self.current_state in ['idle', 'walking']:
            if random.randint(1, 1000) <= 8: 
                if getattr(self, 'get_all_pets', None):
                    excluded_states = ['exiting', 'dragged', 'mewtwo_victim', 'panic_run', 'deluge_float', 'rayquaza_cyclone_victim', 'evolving_start', 'evolving_finish', 'spawning_wild', 'despawning_wild', 'falling_pokeball', 'falling_egg']
                    valid_targets = [p for p in self.get_all_pets() if p != self and p.current_state not in excluded_states and not getattr(p, 'is_egg', False)]
                    
                    if valid_targets:
                        self.rayquaza_cooldown = 108000 # 1.5 horas
                        self.current_state = 'rayquaza_channeling'
                        self.rayquaza_phase = 0
                        
                        # FIX: Definir número de idas y vueltas y la duración inicial del barrido
                        self.rayquaza_sweeps_total = random.randint(8, 10)
                        self.rayquaza_sweeps_done = 0
                        self.rayquaza_sweep_duration = 120 # Arranca lento (~3.6s el primer cruce)
                        
                        self.rayquaza_targets = valid_targets 
                        self.schedule_loop(50, self.physics_loop)
                        return

        # --- MECÁNICA EXCLUSIVA: VENDAVAL AEROBLÁSICO DE LUGIA ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "lugia" and self.lugia_cooldown == 0 and self.current_state in ['idle', 'walking']:
            if random.randint(1, 1000) <= 8: 
                self.lugia_cooldown = 108000 # 1.5 horas
                self.current_state = 'lugia_channeling'
                self.is_facing_right = random.choice([True, False]) # Decide hacia dónde va a barrer la pantalla
                self.schedule_loop(50, self.physics_loop)
                return

        # --- MECÁNICA EXCLUSIVA: TERREMOTO DE GROUDON ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "groudon" and self.groudon_cooldown == 0 and self.current_state in ['idle', 'walking']:
            if random.randint(1, 1000) <= 8: 
                self.groudon_cooldown = 108000 # 1.5 horas
                self.current_state = 'groudon_channeling'
                # FIX LÓGICO: Definimos aleatoriedad de repeticiones (5 a 10) y la primera propulsión
                self.groudon_jumps_left = random.randint(5, 10) 
                self.groudon_phase = 'jumping'
                self.v_y_velocity = -28.0 
                self.schedule_loop(50, self.physics_loop)
                return

        # --- MECÁNICA EXCLUSIVA: DILUVIO DE KYOGRE ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "kyogre" and self.kyogre_cooldown == 0 and self.current_state in ['idle', 'walking']:
            if random.randint(1, 1000) <= 8: 
                if getattr(self, 'get_all_pets', None):
                    excluded_states = ['exiting', 'dragged', 'mewtwo_victim', 'panic_run', 'deluge_float', 'evolving_start', 'evolving_finish', 'spawning_wild', 'despawning_wild', 'falling_pokeball', 'falling_egg']
                    valid_targets = [p for p in self.get_all_pets() if p != self and p.current_state not in excluded_states and not getattr(p, 'is_egg', False)]
                    
                    if valid_targets:
                        self.kyogre_cooldown = 108000 # 1.5 horas
                        self.current_state = 'kyogre_channeling'
                        self.kyogre_phase = 0
                        self.kyogre_timer = 666 # 20 segundos exactos
                        self.kyogre_targets = valid_targets 
                        self.schedule_loop(50, self.physics_loop)
                        return


        # --- MECÁNICA EXCLUSIVA: DISTORSIÓN TEMPORAL DE DIALGA ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "dialga" and getattr(self, 'dialga_cooldown', 0) == 0 and self.current_state in ['idle', 'walking']:
            if random.randint(1, 1000) <= 8:
                self.current_state = 'dialga_channeling'
                self.schedule_loop(50, self.physics_loop)
                return
        # --- MECÁNICA EXCLUSIVA: FUEGO SAGRADO DE HO-OH ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "hooh" and self.hooh_cooldown == 0 and self.current_state in ['idle', 'walking']:
            if random.randint(1, 1000) <= 8: 
                if getattr(self, 'get_all_pets', None):
                    excluded_states = ['exiting', 'dragged', 'mewtwo_victim', 'panic_run', 'evolving_start', 'evolving_finish', 'spawning_wild', 'despawning_wild', 'falling_pokeball', 'falling_egg']
                    valid_targets = [p for p in self.get_all_pets() if p != self and p.current_state not in excluded_states and not getattr(p, 'is_egg', False)]
                    
                    if valid_targets:
                        self.hooh_cooldown = 108000 
                        self.current_state = 'hooh_channeling'
                        self.hooh_phase = 0
                        self.hooh_timer = 666 
                        
                        # FIX: Solo guardamos los objetivos en memoria, pero NO los interrumpimos aún.
                        # Seguirán haciendo su vida normal durante el vuelo de preparación.
                        self.hooh_targets = valid_targets 
                        
                        self.schedule_loop(50, self.physics_loop)
                        return

        # --- MECÁNICA EXCLUSIVA: VÓRTICE PSÍQUICO DE MEWTWO ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "mewtwo" and self.mewtwo_cooldown == 0 and self.current_state in ['idle', 'walking']:
            if random.randint(1, 1000) <= 8: 
                if getattr(self, 'get_all_pets', None):
                    
                    # FIX: Excluir estados de transición crítica (spawns y evoluciones) para evitar bucles paralelos
                    excluded_states = ['exiting', 'dragged', 'mewtwo_victim', 'evolving_start', 'evolving_finish', 'spawning_wild', 'despawning_wild', 'falling_pokeball', 'falling_egg']
                    valid_targets = [p for p in self.get_all_pets() if p != self and p.current_state not in excluded_states and not getattr(p, 'is_egg', False)]
                    
                    if valid_targets:
                        self.mewtwo_cooldown = 108000 # 1 hora y media
                        self.current_state = 'mewtwo_channeling'
                        self.mewtwo_timer = 0
                        self.mewtwo_targets = valid_targets
                        self.manage_tk_aura(self.canvas, self.size_w, self.size_h, True)
                        
                        for i, target in enumerate(valid_targets):
                            
                            # FIX ESTRUCTURAL: Limpieza exhaustiva de vínculos de otras mecánicas para evitar escape de víctimas
                            if target.current_state.startswith('dark_'):
                                target.cancel_dark_arts()
                                
                            elif target.current_state == 'tk_channeling':
                                target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
                                if getattr(target, 'tk_target', None):
                                    if getattr(target.tk_target, 'current_state', '') in ['tk_controlled', 'tk_lifted']:
                                        
                                        # FIX: Forzar la limpieza de partículas del objeto/víctima flotante
                                        t_targ = target.tk_target
                                        t_w = t_targ.size_w if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size
                                        t_h = t_targ.size_h if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size
                                        target.manage_tk_aura(t_targ.canvas, t_w, t_h, False)
                                        
                                        t_targ.current_state = 'falling'
                                        if hasattr(t_targ, 'tk_master'):
                                            t_targ.tk_master = None
                                target.tk_target = None
                                
                            elif target.current_state == 'tk_lifted':
                                target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
                                if getattr(target, 'tk_master', None):
                                    target.tk_master.tk_target = None
                                    target.tk_master.manage_tk_aura(target.tk_master.canvas, target.tk_master.size_w, target.tk_master.size_h, False)
                                    target.tk_master.current_state = 'falling'
                                target.tk_master = None
                                
                            elif target.current_state == 'bubbled':
                                target.manage_bubble_vfx(False)
                                target.show_bubble_burst_vfx()
                                
                            # FIX: Cancelar el Glitch de los Fantasmas
                            if getattr(target, 'is_glitching', False):
                                target.is_glitching = False
                                target.glitch_teleports_left = 0
                                target.glitch_cooldown = 12000
                                
                            # Limpieza del renderizado visual
                            target.canvas.itemconfig(target.canvas_image_id, state='normal')
                            target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
                            try: target.window.attributes('-alpha', 1.0)
                            except: pass
                            
                            # Finalmente, el secuestro orbital
                            target.current_state = 'mewtwo_victim'
                            target.mewtwo_master = self
                            target.mewtwo_orbit_offset = (i * (2 * math.pi / len(valid_targets))) 
                            target.mewtwo_activation_tick = i * 33 
                            target.anchored_hwnd = None 
                            
                        self.schedule_loop(50, self.physics_loop)
                        return
                    
        # --- MECÁNICA: PACIFICACIÓN TIPO HADA ---
        if getattr(self, 'fairy_aura', False) and self.current_state in ['idle', 'walking']:
            if getattr(self, 'get_all_pets', None):
                for other in self.get_all_pets():
                    # Si detecta a un Pokémon peleando y entra en su Hitbox (distancia menor al ancho del sprite)
                    if other != self and other.current_state == 'attacking' and abs(self.x - other.x) < self.size_w and abs(self.y - other.y) < self.size_h:
                        
                        # Pacificar a su oponente de forma remota y aplicar gravedad
                        opponent = getattr(other, 'attack_target', None)
                        if opponent:
                            opponent.current_state = 'thrown' if getattr(opponent, 'is_flying', False) else 'falling'
                            opponent.v_y_velocity = 0.0
                            opponent.v_x_velocity = 0.0
                            opponent.attack_cooldown = 12000
                            opponent.attack_target = None
                            opponent.show_fairy_sparkles_vfx()
                            
                        # Pacificar al objetivo primario y aplicar gravedad
                        other.current_state = 'thrown' if getattr(other, 'is_flying', False) else 'falling'
                        other.v_y_velocity = 0.0
                        other.v_x_velocity = 0.0
                        other.attack_cooldown = 12000
                        other.attack_target = None
                        other.show_fairy_sparkles_vfx()
                        
                        self.show_fairy_sparkles_vfx()
                        
                        # El hada da un pequeño salto de felicidad al detener la pelea
                        self.current_state = 'jumping_arc'
                        self.jump_target_y = self.floor_y
                        self.v_y_velocity = -3.0
                        self.schedule_loop(50, self.physics_loop)
                        return
        
        # --- MECÁNICA: EMBOSCADA TIPO SINIESTRO ---
        if getattr(self, 'dark_arts', False) and self.dark_cooldown == 0 and self.current_state in ['idle', 'walking'] and getattr(self, 'climbing_surface', 'floor') == 'floor':
            if random.randint(1, 1000) <= 10: 
                if getattr(self, 'get_all_pets', None):
                    # FIX: Se inyecta la restricción de altura estricta "abs(p.y - self.y) < 80"
                    valid_targets = [p for p in self.get_all_pets() if p != self and p.current_state in ['idle', 'walking'] and getattr(p, 'climbing_surface', 'floor') == 'floor' and not getattr(p, 'is_egg', False) and abs(p.x - self.x) < 500 and abs(p.y - self.y) < 80]
                    if valid_targets:
                        target = random.choice(valid_targets)
                        self.dark_cooldown = 12000 
                        self.current_state = 'dark_dash'
                        self.dark_target = target
                        self.dark_mode = True
                        try: self.window.attributes('-alpha', 0.7)
                        except: pass
                        
                        target.current_state = 'dark_victim_frozen'
                        target.dark_master = self
                        
                        self.schedule_loop(50, self.physics_loop)
                        return

        # --- MECÁNICA: EXCAVACIÓN TIPO TIERRA ---
        if getattr(self, 'can_dig', False) and self.dig_cooldown == 0 and self.current_state in ['idle', 'walking'] and getattr(self, 'climbing_surface', 'floor') == 'floor':
            if random.randint(1, 1000) <= 10: 
                self.current_state = 'digging_in'
                self.dig_step = 0
                self.dig_timer = random.randint(200, 400) # Tiempo bajo tierra
                self.dig_cooldown = 12000 # 10 minutos reales
                self.schedule_loop(50, self.physics_loop)
                return
        
        # --- MECÁNICA: BURBUJA DE AGUA ---
        if getattr(self, 'bubble_blower', False) and self.bubble_cooldown == 0 and self.current_state in ['idle', 'walking']:
            if random.randint(1, 1000) <= 8: 
                if getattr(self, 'get_all_pets', None):
                    # FIX: Alcance muy reducido (150px horizontal, 60px vertical)
                    valid_targets = [p for p in self.get_all_pets() if p != self and p.current_state in ['idle', 'walking'] and not getattr(p, 'is_egg', False) and abs(p.x - self.x) < 150 and abs(p.y - self.y) < 60]
                    if valid_targets:
                        target = random.choice(valid_targets)
                        self.bubble_cooldown = 12000 
                        
                        # Disparamos el proyectil animado desde nuestro centro geométrico
                        def on_bubble_hit(hit_target):
                            # FIX ESTRUCTURAL: Prevenir corrupción FSM si la burbuja impacta a un Siniestro
                            if getattr(hit_target, 'current_state', '').startswith('dark_'):
                                hit_target.cancel_dark_arts()
                            elif getattr(hit_target, 'current_state', '').startswith('mewtwo_'):
                                hit_target.cancel_mewtwo_arts()
                            elif getattr(hit_target, 'current_state', '') in ['hooh_channeling', 'panic_run']:
                                hit_target.cancel_hooh_arts()
                            elif getattr(hit_target, 'current_state', '') in ['lugia_channeling', 'lugia_dash']: hit_target.cancel_lugia_arts()
                                
                            hit_target.current_state = 'bubbled'
                            hit_target.bubble_max_time = random.randint(130, 200) 
                            hit_target.bubble_timer = hit_target.bubble_max_time
                            hit_target.anchored_hwnd = None
                        
                        BubbleProjectile(self.window.master, self.base_dir, self.x + self.size_w/2, self.y + self.size_h/2, target, on_bubble_hit)
                        
                        # El Pokémon que lanza la burbuja hace un pequeño salto de invocación
                        self.current_state = 'jumping_arc'
                        self.jump_target_y = self.floor_y
                        self.v_y_velocity = -4.0
                        self.schedule_loop(50, self.physics_loop)
                        return

        # --- FASE DE INTERFERENCIA PARA FANTASMAS (SCREEN WRAP) ---
        if getattr(self, 'can_screen_wrap', False) and self.glitch_cooldown == 0 and not getattr(self, 'is_glitching', False):
            if random.randint(1, 1000) <= 10: # Aprox 1% de probabilidad
                self.is_glitching = True
                self.glitch_teleports_left = random.randint(4, 10) # Número de teletransportes caóticos
                try: self.window.attributes('-alpha', 0.5) # Baja la opacidad al 50%
                except: pass
                self.schedule_glitch_teleport()
        
        if getattr(self, 'telekinetic', False) and self.tk_cooldown == 0 and self.current_state in ['idle', 'walking']:
            if random.randint(1, 1000) <= 10: # Probabilidad de activar poderes
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
                        
                    self.schedule_loop(50, self.physics_loop) 
                    return
        
        if self.can_teleport and self.teleport_cooldown == 0 and self.current_state in ['idle', 'walking']:
            if random.randint(1, 100) <= 1:
                self.current_state = 'teleporting_out'
                self.teleport_step = 1.0
                self.teleport_cooldown = 3000
                self.schedule_loop(50, self.physics_loop)
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
                if getattr(self, 'gravity_inverted', False):
                    # Suelo invertido = Borde inferior de la ventana
                    current_physical_floor = self.anchored_rect[3] + getattr(self, 'offset_y', 0)
                else:
                    current_physical_floor = self.anchored_rect[1] - self.size_h - getattr(self, 'offset_y', 0)
            elif (self.y >= current_env['y'] - 15) if getattr(self, 'gravity_inverted', False) else (self.y <= current_env['y'] + 15):
                current_physical_floor = current_env['y']
            else:
                current_physical_floor = self.v_y if getattr(self, 'gravity_inverted', False) else self.default_floor_y

            self.floor_y = current_physical_floor

            if not is_climber:
                if getattr(self, 'gravity_inverted', False):
                    if self.current_state in ['idle', 'walking'] and self.y > self.floor_y + 15:
                        self.current_state = 'jumping_arc'
                        self.jump_target_y = self.floor_y
                        self.v_y_velocity = 0.0 if self.heavy_fall else 3.0  
                        
                    elif self.current_state == 'walking' and ahead_physical_floor is not None:
                        h = ahead_physical_floor - self.y
                        if 30 < h < 750 and self.jump_cooldown == 0: 
                            if random.randint(1, 1000) <= 30: 
                                self.current_state = 'jumping_arc'
                                self.jump_target_y = ahead_physical_floor
                                self.v_y_velocity = math.sqrt(2 * 1.5 * (h + 30))
                                self.jump_cooldown = 400

                    elif self.current_state == 'walking' and getattr(self, 'anchored_hwnd', None) and self.jump_cooldown == 0:
                        if random.randint(1, 1000) <= 5: 
                            self.current_state = 'jumping_arc'
                            self.jump_target_y = self.v_y
                            self.v_y_velocity = 0.0 if self.heavy_fall else 3.0 
                            self.jump_cooldown = 400
                            self.anchored_hwnd = None
                            self.anchored_rect = None
                else:
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
            
            # FIX VOLADORES: Mantener la rotación de 180 grados si la gravedad está invertida
            self.surface_angle = 180 if getattr(self, 'gravity_inverted', False) else 0
            
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
        self.schedule_loop(50, self.physics_loop)

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
        self.schedule_loop(30, self.physics_loop)

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
        self.schedule_loop(30, self.physics_loop)

    def schedule_loop(self, delay, func, *args):
        multiplier = 4.0 if getattr(self, 'time_distorted', False) and getattr(func, '__name__', '') != 'animate_loop' else 1.0
        def wrapper():
            func(*args)
        return self.window.after(int(delay * multiplier), wrapper)
