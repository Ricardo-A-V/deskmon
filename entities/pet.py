
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

# --- PHYSICAL ENTITY (REFACTORED TO STATE MACHINE) ---
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
from mechanics.giratina import GiratinaMechanics
from mechanics.zekrom import ZekromMechanics
from mechanics.reshiram import ReshiramMechanics
from mechanics.heatran import HeatranMechanics
from mechanics.kyurem import KyuremMechanics
from mechanics.xerneas import XerneasMechanics
from mechanics.yveltal import YveltalMechanics
from mechanics.zygarde import ZygardeMechanics
from mechanics.lunala import LunalaMechanics
from mechanics.solgaleo import SolgaleoMechanics
from mechanics.necrozma import NecrozmaMechanics
from mechanics.zacian import ZacianMechanics
from mechanics.zamazenta import ZamazentaMechanics
from mechanics.eternatus import EternatusMechanics
from mechanics.koraidon import KoraidonMechanics
from mechanics.miraidon import MiraidonMechanics
from mechanics.legendary_birds import LegendaryBirdsMechanics
from mechanics.mew import MewMechanics
from mechanics.legendary_beasts import LegendaryBeastsMechanics
from mechanics.celebi import CelebiMechanics
from mechanics.legendary_regis import LegendaryRegisMechanics
from mechanics.jirachi import JirachiMechanics
from mechanics.darkrai import DarkraiMechanics
from mechanics.cresselia import CresseliaMechanics
from mechanics.lati_twins import LatiTwinsMechanics
from mechanics.deoxys import DeoxysMechanics
from mechanics.lake_trio import LakeTrioMechanics
from mechanics.shaymin import ShayminMechanics
from mechanics.tapus import TapusMechanics
from mechanics.sea_guardians import SeaGuardiansMechanics
from mechanics.victini import VictiniMechanics
from mechanics.genesect import GenesectMechanics
from mechanics.meloetta import MeloettaMechanics
from mechanics.legendary_genies import LegendaryGeniesMechanics
from mechanics.hoopa import HoopaMechanics

class DesktopPet(HoopaMechanics, LegendaryGeniesMechanics, MeloettaMechanics, GenesectMechanics, VictiniMechanics, SeaGuardiansMechanics, TapusMechanics, ShayminMechanics, LakeTrioMechanics, DeoxysMechanics, LatiTwinsMechanics, CresseliaMechanics, DarkraiMechanics, JirachiMechanics, LegendaryRegisMechanics, CelebiMechanics, LegendaryBeastsMechanics, MewMechanics, LegendaryBirdsMechanics, MiraidonMechanics, KoraidonMechanics, EternatusMechanics, MewtwoMechanics, HoOhMechanics, LugiaMechanics, KyogreMechanics, GroudonMechanics, RayquazaMechanics, DialgaMechanics, PalkiaMechanics, GiratinaMechanics, ReshiramMechanics, ZekromMechanics, KyuremMechanics, XerneasMechanics, YveltalMechanics, ZygardeMechanics, SolgaleoMechanics, LunalaMechanics, NecrozmaMechanics, ZacianMechanics, ZamazentaMechanics, HeatranMechanics, TelekinesisMechanics, DarkArtsMechanics, SharedVFX):
    def __init__(self, parent_root, pet_data, is_wild, on_remove_callback, on_catch_callback, on_open_pc_callback, on_evolve_callback, spawn_coords=None, is_mid_evo=False, evo_channel=None, is_overflow=False, get_all_pets_callback=None, game_controller_ref=None):
        self.pet_data = pet_data
        self.pet_name = pet_data["species"]
        self.is_wild = is_wild
        self.is_egg = self.pet_data.get("is_egg", False)
        self.is_overflow = is_overflow
        self.game_controller = game_controller_ref
        
        # CLIMBING CONFIGURATOR
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
            "articuno", "articuni1", "zapdos", "zapdos1", "moltres", "moltres1", "mewtwo", "mew", "raikou", "entei", "suicune", "lugia", "hooh", "celebi",
            "regirock", "regice", "registeel", "latias", "latios", "kyogre", "groudon", "rayquaza", "jirachi", "deoxys",
            "uxie", "mesprit", "azelf", "dialga", "palkia", "heatran", "regigigas", "giratina", "giratina1", "cresselia", "manaphy", "phione", "darkrai", "shaymin", "shaymin1", "arceus",
            "victini", "cobalion", "terrakion", "virizion", "tornadus", "tornadus1", "thundurus", "thundurus1", "reshiram", "zekrom", "landorus", "landorus1", "kyurem", "kyurem1", "kyurem2", "keldeo", "meloetta", "meloetta1", "genesect",
            "xerneas", "yveltal", "zygarde", "diancie", "hoopa", "hoopa1", "volcanion",
            "tapukoko", "tapulele", "tapubulu", "tapufini", "cosmog", "cosmoem", "solgaleo", "lunala", "nihilego", "buzzwole", "pheromosa", "xurkillree", "celesteela", "kartana", "guzzlord", "necrozma", "necrozma1", "necrozma2", "magearna", "marshadow", "poipole", "naganadel", "stakataka", "blacephalon", "zeraora", "melmetal",
            "zacian", "zacian1", "zamazenta", "zamazenta1", "eternatus", "kubfu", "urshifu", "zarude", "regieleki", "regidrago", "glastrier", "spectrier", "calyrex", "enamorus", "enamorus1",
            "tinglu", "chienpao", "wochien", "chiyu", "koraidon", "miraidon", "walkingwake", "ironleaves", "okidogi", "munkidori", "fezandipiti", "ogerpon", "terapagos", "pecharunt", "ragingbolt", "gougingfire", "ironboulder", "ironcrown"
        }
        
        rpg_data = self.config.get("rpg_data", {})
        rarity_str = rpg_data.get("rarity", "").lower()
        self.is_legendary = (normalized_name in LEGENDARY_MATRIX) or rpg_data.get("is_legendary", False) or (rarity_str in ["legendary", "mythical", "legendario", "singular"])

        self.window = tk.Toplevel(parent_root)
        wild_tag = "(WILD)" if is_wild else f"Lv.{self.pet_data['level']}"
        if self.is_egg: wild_tag = "(EGG)"
        self.window.title(f"{self.config.get('display_name', 'Pokemon')} {wild_tag}")
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)

        CHROMA_KEY = '#00FF00'
        self.window.config(bg=CHROMA_KEY)
        try: self.window.wm_attributes('-transparentcolor', CHROMA_KEY)
        except tk.TclError: pass 

        size_multiplier = 1.55
        if self.is_legendary:
            size_multiplier *= 1.2 
            
        # Forces a strictly larger AABB for physical collision detection
        if normalized_name == "regigigas":
            size_multiplier *= 1.5
        elif normalized_name == "hoopa1":
            size_multiplier *= 2.0

        speed_multiplier = 2
        physics = self.config.get("physics", {})
        
        self.size_w = int(physics.get("size", 64) * size_multiplier)
        self.size_h = int(physics.get("size", 64) * size_multiplier)
        
        base_speed = physics.get("movement_speed", 2)
        self.speed = max(1, int(base_speed * speed_multiplier))
        
        # Enforces the Slow Start biological trait physically
        if normalized_name == "regigigas":
            self.speed = max(1, self.speed // 2)

        self.is_flying = physics.get("is_flying", False)
        self.is_climbing = physics.get("is_climbing", False) and not self.is_flying 
        
        # --- HARDCODED BEHAVIOR MECHANICS ---
        self.can_screen_wrap = physics.get("can_screen_wrap", False)
        self.can_teleport = physics.get("can_teleport", False)
        self.heavy_fall = physics.get("heavy_fall", False)
        self.telekinetic = physics.get("telekinetic", False)
        self.bubble_blower = physics.get("bubble_blower", False) 
        self.can_dig = physics.get("can_dig", False)
        self.fairy_aura = physics.get("fairy_aura", False)
        self.dark_arts = physics.get("dark_arts", False)
        self.aggressive = physics.get("aggressive", False)
        self.teleport_cooldown = 0
        self.sg_cooldown = 0
        self.victini_cooldown = 0
        self.genesect_cooldown = 0
        self.meloetta_cooldown = 0

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
            
            # FIX: Nullify advanced mechanics so the egg doesn't inherit adult behaviors
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
            if spawn_coords[1] == "floor":
                self.y = self.default_floor_y
                self.floor_y = self.y
            else:
                self.y = spawn_coords[1]
                if self.is_egg:
                    self.floor_y = self.default_floor_y
                else:
                    self.floor_y = spawn_coords[1]

            if is_mid_evo:
                self.evo_channel = evo_channel
                self.current_state = 'evolving_finish'
                self.finish_evolution_vfx(step=0)
            else:
                if self.is_egg:
                    # FIX: Inject the egg into the 'thrown' state so it has real gravity and bounces
                    self.current_state = 'thrown'
                    self.v_x_velocity = random.choice([-2.0, 2.0])
                    self.v_y_velocity = -4.0 # Small parabolic jump when laid by the mother
                else:
                    if self.is_flying and spawn_coords[1] == "floor":
                        self.current_state = 'ascending'
                    else:
                        self.current_state = 'idle'
                    self.spawn_particles = []
                    self.animate_spawn_glow()
        else:
            self.x = random.randint(self.v_x, self.v_x + self.v_width - self.size_w)
            if self.is_egg:
                self.y = self.v_y - self.size_h
                self.current_state = 'thrown' # Falls bouncing when starting the app
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
                    # FIX: Wild flyers now spawn in the sky (target_floor_y), not on the ground
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
            
        # Maps multi-purpose or alias states to their shared mathematical physics handler.
        # Bypasses the 'else' fallback overhead for core loops like 'idle'.
        self.state_aliases = {
            'egg_idle': 'wait',
            'egg_wiggle': 'wait',
            'dragged': 'wait',
            'evolving_start': 'wait',
            'evolving_finish': 'wait',
            'despawning_wild': 'wait',
            'spawning_wild': 'wait',
            'falling_egg': 'falling',
            'falling_pokeball': 'falling',
            'falling_legendary': 'falling',
            'idle': 'active', 
            'walking': 'active',
            'climbing': 'active',
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
        if self.current_state in ['exiting', 'falling_pokeball', 'falling_egg', 'spawning_wild', 'despawning_wild', 'celebi_frozen', 'cresselia_blessing', 'lake_rotating']: return

        normalized_name = self.pet_name.lower().replace("_", "").replace("-", "")
        shakeable_forms = [
            "meloetta", "meloetta1", "giratina1", "zacian1", "zamazenta1", "shaymin1",
            "thundurus", "thundurus1", "tornadus", "tornadus1", "landorus", "landorus1",
            "enamorus", "enamorus1", "dialga", "dialga1", "palkia", "palkia1",
            "keldeo1", "hoopa", "hoopa1", "urshifu", "urshifu1", "terapagos1"
        ]
        if normalized_name in shakeable_forms:
            self.meloetta_angle_sum = 0
            self.last_meloetta_angle = None
        if self.current_state == 'regirock_embedded':
            self.current_state = 'dragged'
            self.surface_angle = 0
            self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)

        # Restores the alpha channel explicitly if the user interrupts a phase-shift sequence via mouse interaction.
        if self.current_state in ['teleporting_out', 'teleporting_in']:
            try: self.window.attributes('-alpha', 1.0)
            except: pass

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
                
        # FIX: Destruction of the link if the victim (Pokemon) is clicked
        if self.current_state == 'tk_lifted':
            self.current_state = 'falling'
            self.manage_tk_aura(self.canvas, self.size_w, self.size_h, False)
            master = getattr(self, 'tk_master', None)
            if master and master.current_state == 'tk_channeling':
                master.current_state = 'idle'
                master.manage_tk_aura(master.canvas, master.size_w, master.size_h, False)
                master.tk_target = None
            self.tk_master = None
                
        # FIX: Pop the bubble manually if you grab the target
        if self.current_state == 'bubbled':
            self.manage_bubble_vfx(False)
            self.show_bubble_burst_vfx()
            self.current_state = 'thrown' if getattr(self, 'is_flying', False) else 'falling'

        # FIX: Interrupt digging manually by restoring internal coordinates
        if self.current_state in ['digging', 'digging_in', 'digging_out']:
            self.canvas.itemconfig(self.canvas_image_id, state='normal')
            # Strict reset to the geometric center of the Canvas
            self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2) 
            self.current_state = 'falling'

        # FIX: Destroy Shadows interaction if you intervene
        if self.current_state.startswith('dark_'):
            self.cancel_dark_arts()

        # Interrupt Mewtwo's Psychic Vortex
        if self.current_state.startswith('mewtwo_'):
            self.cancel_mewtwo_arts()
            
        elif self.current_state.startswith('meloetta_'):
            if hasattr(self, 'cancel_meloetta_arts'):
                self.cancel_meloetta_arts()

        # Interrupt Ho-Oh's Sacred Fire
        elif self.current_state in ['hooh_channeling', 'panic_run']:
            self.cancel_hooh_arts()

        elif self.current_state in ['lugia_channeling', 'lugia_dash']:
            self.cancel_lugia_arts()

        # Only cancel Kyogre if you grab the Master (Kyogre). 
        # Victims can be dragged and will still be affected by the flood when released.
        elif self.current_state == 'kyogre_channeling':
            self.cancel_kyogre_arts()

        elif self.current_state == 'groudon_channeling':
            self.cancel_groudon_arts()

        elif self.current_state == 'rayquaza_channeling':
            self.cancel_rayquaza_arts()

        # Cancel vortex and restore opacity if you grab Giratina
        elif self.current_state.startswith('giratina_') and hasattr(self, 'cancel_giratina_arts'):
            self.cancel_giratina_arts()

        elif self.current_state.startswith('reshiram_') and hasattr(self, 'cancel_reshiram_arts'):
            self.cancel_reshiram_arts()
        elif self.current_state.startswith('heatran_') and hasattr(self, 'cancel_heatran_arts'):
            self.cancel_heatran_arts()

        elif self.current_state.startswith('zekrom_') and hasattr(self, 'cancel_zekrom_arts'):
            self.cancel_zekrom_arts()

        elif self.current_state.startswith('sea_guardian_') and hasattr(self, 'cancel_sea_guardian_arts'):
            self.cancel_sea_guardian_arts()
            
        elif self.current_state.startswith('victini_') and hasattr(self, 'cancel_victini_arts'):
            self.cancel_victini_arts()

        elif self.current_state.startswith('genesect_') and hasattr(self, 'cancel_genesect_arts'):
            self.cancel_genesect_arts()

        elif self.current_state == 'kyurem_channeling' and hasattr(self, 'cancel_kyurem_arts'):
            self.cancel_kyurem_arts()

        elif self.current_state == 'xerneas_channeling' and hasattr(self, 'cancel_xerneas_arts'): 
            self.cancel_xerneas_arts()

        elif self.current_state == 'yveltal_channeling' and hasattr(self, 'cancel_yveltal_arts'):
            self.cancel_yveltal_arts()

        elif self.current_state in ['zygarde_channeling', 'zygarde50_channeling'] and hasattr(self, 'cancel_zygarde_arts'):
            self.cancel_zygarde_arts()

        elif self.current_state == 'solgaleo_channeling' and hasattr(self, 'cancel_solgaleo_arts'):
            self.cancel_solgaleo_arts()

        elif self.current_state == 'lunala_channeling' and hasattr(self, 'cancel_lunala_arts'):
            self.cancel_lunala_arts()

        elif self.current_state == 'necrozma_channeling' and hasattr(self, 'cancel_necrozma_arts'):
            self.cancel_necrozma_arts()

        elif self.current_state == 'zacian_channeling' and hasattr(self, 'cancel_zacian_arts'): 
            self.cancel_zacian_arts()

        elif self.current_state == 'zamazenta_channeling' and hasattr(self, 'cancel_zamazenta_arts'):
            self.cancel_zamazenta_arts()

        elif self.current_state == 'eternatus_channeling' and hasattr(self, 'cancel_eternatus_arts'):
            self.cancel_eternatus_arts()

        elif self.current_state.startswith('koraidon_') and hasattr(self, 'cancel_koraidon_arts'):
            self.cancel_koraidon_arts()

        elif self.current_state.startswith('miraidon_') and self.current_state != 'miraidon_paralyzed' and hasattr(self, 'cancel_miraidon_arts'):
            self.cancel_miraidon_arts()
            
        elif self.current_state == 'miraidon_paralyzed':
            self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
            self.current_state = 'falling'

        elif self.current_state == 'bird_channeling' and hasattr(self, 'cancel_bird_arts'):
            self.cancel_bird_arts()

        elif self.current_state in ['mew_channeling', 'mew_bounce'] and hasattr(self, 'cancel_mew_arts'):
            self.cancel_mew_arts()

        elif self.current_state.startswith('beast_') and hasattr(self, 'cancel_beast_arts'):
            self.cancel_beast_arts()

        elif self.current_state.startswith('genie_') and hasattr(self, 'cancel_genie_arts'):
            self.cancel_genie_arts()

        elif self.current_state in ['celebi_channeling', 'celebi_wait', 'celebi_freeze', 'celebi_revert_flight'] and hasattr(self, 'cancel_celebi_arts'):
            self.cancel_celebi_arts()

        elif self.current_state in ['regi_approach', 'regi_strike'] and hasattr(self, 'cancel_regi_arts'):
            self.cancel_regi_arts()

        elif self.current_state in ['jirachi_channeling', 'jirachi_vanished', 'jirachi_flyby'] and hasattr(self, 'cancel_jirachi_arts'):
            self.cancel_jirachi_arts()

        elif self.current_state.startswith('darkrai_') and hasattr(self, 'cancel_darkrai_arts'):
            self.cancel_darkrai_arts()

        elif self.current_state.startswith('cresselia_') and self.current_state != 'cresselia_blessing' and hasattr(self, 'cancel_cresselia_arts'):
            self.cancel_cresselia_arts()
            
        elif self.current_state.startswith('lati_') and hasattr(self, 'cancel_lati_arts'):
            self.cancel_lati_arts()
            
        elif self.current_state.startswith('deoxys_') and hasattr(self, 'cancel_deoxys_arts'):
            self.cancel_deoxys_arts()
            
        elif self.current_state.startswith('lake_') and hasattr(self, 'cancel_lake_arts'):
            self.cancel_lake_arts()
            
        elif self.current_state.startswith('shaymin_') and hasattr(self, 'cancel_shaymin_arts'):
            self.cancel_shaymin_arts()

        elif self.current_state.startswith('tapu_') and hasattr(self, 'cancel_tapu_mechanic'):
            self.cancel_tapu_mechanic()

        elif self.current_state.startswith('sea_guardian_') and hasattr(self, 'cancel_sea_guardian_arts'):
            self.cancel_sea_guardian_arts()
            
        elif self.current_state.startswith('victini_') and hasattr(self, 'cancel_victini_arts'):
            self.cancel_victini_arts()

        elif self.current_state.startswith('genesect_') and hasattr(self, 'cancel_genesect_arts'):
            self.cancel_genesect_arts()

        elif hasattr(self, 'cancel_hoopa_arts') and self.current_state.startswith('hoopa_'):
            self.cancel_hoopa_arts()
        elif hasattr(self, 'cancel_volcanion_arts') and self.current_state.startswith('volcanion_'):
            self.cancel_volcanion_arts()

        # Inyección Víctima (El Pokémon anclado)
        elif self.current_state == 'mew_tethered':
            self.current_state = 'falling'
            self.canvas.delete("vfx_mew_bubble")
            master = getattr(self, 'mew_master', None)
            if master and hasattr(master, 'mew_victims') and self in master.mew_victims:
                master.mew_victims.remove(self)
            self.mew_master = None

        if self.current_state in ['giratina_victim_pulled', 'giratina_victim_fade', 'giratina_victim_absorbed']:
            self.canvas.itemconfig(self.canvas_image_id, state='normal')
            try: self.window.attributes('-alpha', 1.0)
            except: pass
            self.current_state = 'falling'

        self.drag_offset_x = event.x
        self.drag_offset_y = event.y
        self.drag_start_x = self.window.winfo_pointerx()
        self.drag_start_y = self.window.winfo_pointery()
        self.is_dragging = False

    def on_drag_motion(self, event):
        if self.current_state in ['exiting', 'falling_pokeball', 'falling_egg', 'spawning_wild', 'despawning_wild', 'celebi_frozen']: return
        pointer_x = self.window.winfo_pointerx()
        pointer_y = self.window.winfo_pointery()

        if not getattr(self, 'is_dragging', False):
            if abs(pointer_x - getattr(self, 'drag_start_x', pointer_x)) > 5 or \
               abs(pointer_y - getattr(self, 'drag_start_y', pointer_y)) > 5:
                self.is_dragging = True
                
                if hasattr(self, 'cancel_dialga_arts') and self.current_state == 'dialga_channeling': self.cancel_dialga_arts()
                elif hasattr(self, 'cancel_palkia_arts') and self.current_state == 'palkia_channeling': self.cancel_palkia_arts()
                elif hasattr(self, 'cancel_groudon_arts') and self.current_state == 'groudon_channeling': self.cancel_groudon_arts()
                elif hasattr(self, 'cancel_kyogre_arts') and self.current_state == 'kyogre_channeling': self.cancel_kyogre_arts()
                elif hasattr(self, 'cancel_lugia_arts') and self.current_state == 'lugia_channeling': self.cancel_lugia_arts()
                elif hasattr(self, 'cancel_hooh_arts') and self.current_state == 'hooh_channeling': self.cancel_hooh_arts()
                elif hasattr(self, 'cancel_hoopa_arts') and self.current_state.startswith('hoopa_'): self.cancel_hoopa_arts()
                elif hasattr(self, 'cancel_volcanion_arts') and self.current_state.startswith('volcanion_'): self.cancel_volcanion_arts()
                
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

        normalized_name = self.pet_name.lower().replace("_", "").replace("-", "")
        shakeable_forms = [
            "meloetta", "meloetta1", "giratina1", "zacian1", "zamazenta1", "shaymin1",
            "thundurus", "thundurus1", "tornadus", "tornadus1", "landorus", "landorus1",
            "enamorus", "enamorus1", "dialga", "dialga1", "palkia", "palkia1",
            "keldeo1", "hoopa", "hoopa1", "urshifu", "urshifu1", "terapagos1",
            "deoxys", "deoxys1", "deoxys2", "deoxys3"
        ]
        if normalized_name in shakeable_forms:
            dx = pointer_x - getattr(self, 'last_mouse_x', pointer_x)
            dy = pointer_y - getattr(self, 'last_mouse_y', pointer_y)
            if math.hypot(dx, dy) > 2:
                angle = math.atan2(dy, dx)
                if getattr(self, 'last_meloetta_angle', None) is None:
                    self.last_meloetta_angle = angle
                else:
                    diff = angle - self.last_meloetta_angle
                    if diff > math.pi: diff -= 2 * math.pi
                    elif diff < -math.pi: diff += 2 * math.pi
                    self.meloetta_angle_sum = getattr(self, 'meloetta_angle_sum', 0) + diff
                    self.last_meloetta_angle = angle
                    
                    if abs(self.meloetta_angle_sum) >= 8 * math.pi:
                        self.meloetta_angle_sum = 0
                        self.manual_alter_form()

        # FIX: Destruction of the link if the telekinesis victim is clicked
        if self.current_state == 'tk_lifted':
            self.current_state = 'falling'
            self.manage_tk_aura(self.canvas, self.size_w, self.size_h, False)
            master = getattr(self, 'tk_master', None)
            if master and master.current_state == 'tk_channeling':
                master.current_state = 'idle'
                master.manage_tk_aura(master.canvas, master.size_w, master.size_h, False)
                master.tk_target = None
            self.tk_master = None
            
        # FIX: Pop the bubble manually if you grab the target
        if self.current_state == 'bubbled':
            self.manage_bubble_vfx(False)
            self.show_bubble_burst_vfx()
            self.current_state = 'falling'

        # FIX: Interrupt digging manually if you grab the target
        if self.current_state == 'digging':
            self.canvas.itemconfig(self.canvas_image_id, state='normal')
            self.current_state = 'falling'

        # FIX: Destroy Shadows interaction if you intervene
        if self.current_state.startswith('dark_'):
            self.cancel_dark_arts()

        # Interrupt Mewtwo's Psychic Vortex
        if self.current_state.startswith('mewtwo_'):
            self.cancel_mewtwo_arts()

        elif self.current_state.startswith('meloetta_'):
            if hasattr(self, 'cancel_meloetta_arts'):
                self.cancel_meloetta_arts()

        # Interrupt Ho-Oh's Sacred Fire
        elif self.current_state in ['hooh_channeling', 'panic_run']:
            self.cancel_hooh_arts()

        elif self.current_state in ['lugia_channeling', 'lugia_dash']:
            self.cancel_lugia_arts()

        # Only cancel Kyogre if you grab the Master (Kyogre). 
        # Victims can be dragged and will still be affected by the flood when released.
        elif self.current_state == 'kyogre_channeling':
            self.cancel_kyogre_arts()

        elif self.current_state == 'groudon_channeling':
            self.cancel_groudon_arts()

        elif self.current_state == 'rayquaza_channeling':
            self.cancel_rayquaza_arts()

        # Cancel vortex and restore opacity if you grab Giratina
        elif self.current_state.startswith('giratina_') and hasattr(self, 'cancel_giratina_arts'):
            self.cancel_giratina_arts()

        elif self.current_state.startswith('reshiram_') and hasattr(self, 'cancel_reshiram_arts'):
            self.cancel_reshiram_arts()
        elif self.current_state.startswith('heatran_') and hasattr(self, 'cancel_heatran_arts'):
            self.cancel_heatran_arts()

        elif self.current_state.startswith('zekrom_') and hasattr(self, 'cancel_zekrom_arts'):
            self.cancel_zekrom_arts()
            
        elif self.current_state.startswith('victini_') and hasattr(self, 'cancel_victini_arts'):
            self.cancel_victini_arts()

        elif self.current_state.startswith('genesect_') and hasattr(self, 'cancel_genesect_arts'):
            self.cancel_genesect_arts()

        elif self.current_state == 'kyurem_channeling' and hasattr(self, 'cancel_kyurem_arts'):
            self.cancel_kyurem_arts()

        elif self.current_state == 'xerneas_channeling' and hasattr(self, 'cancel_xerneas_arts'): 
            self.cancel_xerneas_arts()

        elif self.current_state == 'yveltal_channeling' and hasattr(self, 'cancel_yveltal_arts'):
            self.cancel_yveltal_arts()

        elif self.current_state in ['zygarde_channeling', 'zygarde50_channeling'] and hasattr(self, 'cancel_zygarde_arts'):
            self.cancel_zygarde_arts()

        elif self.current_state == 'solgaleo_channeling' and hasattr(self, 'cancel_solgaleo_arts'):
            self.cancel_solgaleo_arts()

        elif self.current_state == 'lunala_channeling' and hasattr(self, 'cancel_lunala_arts'):
            self.cancel_lunala_arts()

        elif self.current_state == 'necrozma_channeling' and hasattr(self, 'cancel_necrozma_arts'):
            self.cancel_necrozma_arts()

        elif self.current_state == 'zacian_channeling' and hasattr(self, 'cancel_zacian_arts'): 
            self.cancel_zacian_arts()

        elif self.current_state == 'zamazenta_channeling' and hasattr(self, 'cancel_zamazenta_arts'): 
            self.cancel_zamazenta_arts()

        elif self.current_state == 'eternatus_channeling' and hasattr(self, 'cancel_eternatus_arts'):
            self.cancel_eternatus_arts()

        elif self.current_state.startswith('koraidon_') and hasattr(self, 'cancel_koraidon_arts'):
            self.cancel_koraidon_arts()

        elif self.current_state.startswith('miraidon_') and self.current_state != 'miraidon_paralyzed' and hasattr(self, 'cancel_miraidon_arts'):
            self.cancel_miraidon_arts()
            
        elif self.current_state == 'miraidon_paralyzed':
            self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
            self.current_state = 'falling'

        elif self.current_state == 'bird_channeling' and hasattr(self, 'cancel_bird_arts'):
                    self.cancel_bird_arts()

        elif self.current_state in ['mew_channeling', 'mew_bounce'] and hasattr(self, 'cancel_mew_arts'):
            self.cancel_mew_arts()

        elif self.current_state.startswith('beast_') and hasattr(self, 'cancel_beast_arts'):
            self.cancel_beast_arts()

        elif self.current_state.startswith('genie_') and hasattr(self, 'cancel_genie_arts'):
            self.cancel_genie_arts()

        elif self.current_state in ['celebi_channeling', 'celebi_wait', 'celebi_freeze', 'celebi_revert_flight'] and hasattr(self, 'cancel_celebi_arts'):
            self.cancel_celebi_arts()

        elif self.current_state in ['regi_approach', 'regi_strike'] and hasattr(self, 'cancel_regi_arts'):
            self.cancel_regi_arts()

        elif self.current_state in ['jirachi_channeling', 'jirachi_vanished', 'jirachi_flyby'] and hasattr(self, 'cancel_jirachi_arts'):
            self.cancel_jirachi_arts()

        elif self.current_state.startswith('darkrai_') and hasattr(self, 'cancel_darkrai_arts'):
            self.cancel_darkrai_arts()

        elif self.current_state.startswith('cresselia_') and self.current_state != 'cresselia_blessing' and hasattr(self, 'cancel_cresselia_arts'):
            self.cancel_cresselia_arts()
            
        elif self.current_state.startswith('lati_') and hasattr(self, 'cancel_lati_arts'):
            self.cancel_lati_arts()
            
        elif self.current_state.startswith('deoxys_') and hasattr(self, 'cancel_deoxys_arts'):
            self.cancel_deoxys_arts()

        elif self.current_state.startswith('lake_') and hasattr(self, 'cancel_lake_arts'):
                    self.cancel_lake_arts()
                    
        elif self.current_state.startswith('shaymin_') and hasattr(self, 'cancel_shaymin_arts'):
            self.cancel_shaymin_arts()

        elif self.current_state.startswith('tapu_') and hasattr(self, 'cancel_tapu_mechanic'):
            self.cancel_tapu_mechanic()

        # Inyección Víctima (El Pokémon anclado)
        elif self.current_state == 'mew_tethered':
            self.current_state = 'falling'
            self.canvas.delete("vfx_mew_bubble")
            master = getattr(self, 'mew_master', None)
            if master and hasattr(master, 'mew_victims') and self in master.mew_victims:
                master.mew_victims.remove(self)
            self.mew_master = None

        if self.current_state in ['giratina_victim_pulled', 'giratina_victim_fade', 'giratina_victim_absorbed']:
            self.canvas.itemconfig(self.canvas_image_id, state='normal')
            try: self.window.attributes('-alpha', 1.0)
            except: pass
            self.current_state = 'falling'
        
        # VARIABLE UPDATE FOR PHYSICS (Without altering mouse offset)
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
            
            # --- STRUCTURAL FIX: STATE ROUTING WITH ABSOLUTE PRIORITY ---
            # Evaluates persisting debuffs to prevent clearing them when the user drops the entity
            if self.current_state in ['celebi_frozen']: return
            if getattr(self, 'kyurem_frozen_timer', 0) > 0:
                self.current_state = 'kyurem_frozen'
            elif getattr(self, 'zekrom_para_timer', 0) > 0:
                self.current_state = 'zekrom_paralyzed'
            elif getattr(self, 'mrd_para_timer', 0) > 0:
                self.current_state = 'miraidon_paralyzed'
            elif getattr(self, 'reshiram_burn_timer', 0) > 0:
                self.current_state = 'reshiram_burn'
            elif getattr(self, 'kyogre_master', None) and getattr(self.kyogre_master, 'current_state', '') == 'kyogre_channeling':
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
                # FIX EXCEPTION: Allow collision with Bill's PC ignoring the rest of the pets
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

    def animate_spawn_glow(self, step=0):
        if not hasattr(self, 'spawn_particles'):
            self.spawn_particles = []
        if step == 0:
            for _ in range(12):
                px = self.size_w / 2
                py = self.size_h / 2
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(4, 10)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                p_id = self.canvas.create_rectangle(px-2, py-2, px+2, py+2, fill="white", outline="")
                self.spawn_particles.append({'id': p_id, 'x': px, 'y': py, 'vx': vx, 'vy': vy, 'life': 15})
        
        active_p = []
        for p in self.spawn_particles:
            p['life'] -= 1
            if p['life'] <= 0:
                self.canvas.delete(p['id'])
            else:
                p['x'] += p['vx']
                p['y'] += p['vy']
                p['vx'] *= 0.85
                p['vy'] *= 0.85
                self.canvas.coords(p['id'], p['x']-2, p['y']-2, p['x']+2, p['y']+2)
                active_p.append(p)
        self.spawn_particles = active_p
        
        frames = 30
        if step <= frames:
            self.spawn_blend = 1.0 - (step / frames)
            self.schedule_loop(33, lambda: self.animate_spawn_glow(step + 1))
        else:
            self.spawn_blend = 0.0

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
            else: 
                # Forces a physical drop to recalculate the bounding box collision against the real floor.
                self.current_state = 'falling'
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
        
        # Group the border and the center under the same tag ("vfx_lvl_group")
        offsets = [(-1, -1), (1, -1), (-1, 1), (1, 1)]
        for ox, oy in offsets:
            self.canvas.create_text(x + ox, y + oy, text="LEVEL UP!", fill="#000000", font=font_config, tags="vfx_lvl_group")
            
        self.canvas.create_text(x, y, text="LEVEL UP!", fill="#F10F0F", font=font_config, tags="vfx_lvl_group")
        
        def float_up(step):
            if step < 20 and self.current_state != 'exiting':
                self.canvas.move("vfx_lvl_group", 0, -1)
                
                # MATHEMATICAL SOLUTION: Entire block blinking.
                # By hiding and showing both elements at the same time, red never interacts with green.
                blink_state = 'hidden' if (step // 2) % 2 == 0 else 'normal'
                self.canvas.itemconfig("vfx_lvl_group", state=blink_state)
                    
                self.schedule_loop(50, lambda: float_up(step+1))
            else:
                self.canvas.delete("vfx_lvl_group")
        float_up(0)

    def show_heart_vfx(self):
        # Structured matrix: 0 = Empty, 1 = Red (Fill), 2 = Black (Border)
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
        
        # SEISMIC SHOCKWAVE
        if getattr(self, 'get_all_pets', None):
            my_cx = self.x + self.size_w / 2
            my_cy = self.y + self.size_h / 2
            
            for other in self.get_all_pets():
                if other != self and other.current_state in ['idle', 'walking', 'socializing', 'attacking'] and not getattr(other, 'is_flying', False) and not getattr(other, 'is_egg', False):
                    
                    other_cx = other.x + other.size_w / 2
                    other_cy = other.y + other.size_h / 2
                    
                    # STRUCTURAL FIX: Trigonometric Euclidean distance to create a true circular blast radius.
                    dist = math.hypot(my_cx - other_cx, my_cy - other_cy)
                    
                    if dist <= 400:
                        # KINETIC RESET: Forcibly detach climbers and reset their rotation matrix before launching them.
                        other.climbing_surface = 'floor'
                        other.surface_angle = 180 if getattr(other, 'gravity_inverted', False) else 0
                        other.anchored_hwnd = None
                        
                        other.current_state = 'jumping_arc'
                        # Send them to the absolute physical floor, not the surface they were climbing
                        other.jump_target_y = other.default_floor_y
                        other.v_y_velocity = -5.0 
                        other.v_x_velocity = 0.0


    def check_evolution(self):
        if self.pet_data.get("everstone", False): return
        rpg = self.config.get("rpg_data", {})
        evo_level = rpg.get("evolution_level", 99)
        evolves_to = rpg.get("evolves_to", [])
        last_evo = self.pet_data.get("last_evolution_level", 1)
        if self.pet_data["level"] >= evo_level and (self.pet_data["level"] - last_evo) >= 5 and evolves_to and evolves_to[0] != "none":
            self.start_evolution_vfx(random.choice(evolves_to), step=0)

    def load_config(self):
        config_path = os.path.join(self.pet_dir, "config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"\n[!] CRITICAL ERROR: The engine has stopped.")
            print(f"[!] Failed to read the file: {config_path}")
            print(f"[!] Technical reason: {e}\n")
            import sys
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

    def animate_vfx(self, action_type, step=0, pb_file=None):
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
                if not pb_file:
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
            self.schedule_loop(30, lambda: self.animate_vfx(action_type, step + 1, pb_file))
        else:
            self.schedule_loop(100, self.window.destroy)

    def start_wild_despawn(self):
        if self.current_state in ['exiting', 'evolving_start', 'evolving_finish', 'despawning_wild']: return
        
        # STRUCTURAL FIX: Release victim before disappearing into the grass/cloud
        if self.current_state.startswith('dark_'):
            self.cancel_dark_arts()
        elif self.current_state.startswith('mewtwo_'):
            self.cancel_mewtwo_arts()
        elif self.current_state in ['hooh_channeling', 'panic_run']:
            self.cancel_hooh_arts()
        elif self.current_state in ['lugia_channeling', 'lugia_dash']:
            self.cancel_lugia_arts()
        elif self.current_state == 'kyogre_channeling':
            self.cancel_kyogre_arts()
        elif self.current_state == 'groudon_channeling':
            self.cancel_groudon_arts()
        elif self.current_state == 'rayquaza_channeling':
            self.cancel_rayquaza_arts()
        elif hasattr(self, 'cancel_hoopa_arts') and self.pet_name.lower().replace("_", "").replace("-", "") in ["hoopa", "hoopa1"]:
            self.cancel_hoopa_arts()
        elif hasattr(self, 'cancel_volcanion_arts') and self.pet_name.lower().replace("_", "").replace("-", "") == "volcanion":
            self.cancel_volcanion_arts()
            
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
            self.animate_spawn_glow()
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
            
            # STRUCTURAL FIX: Release Sinister connections if stored in the Pokeball
            if self.current_state.startswith('dark_'):
                self.cancel_dark_arts()
            elif self.current_state.startswith('mewtwo_'):
                self.cancel_mewtwo_arts()
            elif self.current_state in ['hooh_channeling', 'panic_run']:
                self.cancel_hooh_arts()
            elif self.current_state in ['lugia_channeling', 'lugia_dash']:
                self.cancel_lugia_arts()
            elif self.current_state == 'kyogre_channeling':
                self.cancel_kyogre_arts()
            elif self.current_state == 'groudon_channeling':
                self.cancel_groudon_arts()
            elif self.current_state == 'rayquaza_channeling':
                self.cancel_rayquaza_arts()
            elif self.current_state.startswith('giratina_'):
                self.cancel_giratina_arts()
            elif self.current_state.startswith('reshiram_') and hasattr(self, 'cancel_reshiram_arts'):
                self.cancel_reshiram_arts()
            elif self.current_state.startswith('heatran_') and hasattr(self, 'cancel_heatran_arts'):
                self.cancel_heatran_arts()
            elif self.current_state.startswith('zekrom_') and hasattr(self, 'cancel_zekrom_arts'):
                self.cancel_zekrom_arts()
            elif self.current_state.startswith('sea_guardian_') and hasattr(self, 'cancel_sea_guardian_arts'):
                self.cancel_sea_guardian_arts()
            elif self.current_state.startswith('victini_') and hasattr(self, 'cancel_victini_arts'):
                self.cancel_victini_arts()
            elif self.current_state.startswith('genesect_') and hasattr(self, 'cancel_genesect_arts'):
                self.cancel_genesect_arts()
            elif hasattr(self, 'cancel_hoopa_arts') and self.pet_name.lower().replace("_", "").replace("-", "") in ["hoopa", "hoopa1"]:
                self.cancel_hoopa_arts()
            elif hasattr(self, 'cancel_volcanion_arts') and self.pet_name.lower().replace("_", "").replace("-", "") == "volcanion":
                self.cancel_volcanion_arts()
            elif self.current_state == 'kyurem_channeling' and hasattr(self, 'cancel_kyurem_arts'):
                self.cancel_kyurem_arts()
            elif self.current_state == 'xerneas_channeling' and hasattr(self, 'cancel_xerneas_arts'):
                self.cancel_xerneas_arts()
            elif self.current_state == 'yveltal_channeling' and hasattr(self, 'cancel_yveltal_arts'):
                self.cancel_yveltal_arts()
            elif self.current_state in ['zygarde_channeling', 'zygarde50_channeling'] and hasattr(self, 'cancel_zygarde_arts'):
                self.cancel_zygarde_arts()
            elif self.current_state == 'solgaleo_channeling' and hasattr(self, 'cancel_solgaleo_arts'):
                self.cancel_solgaleo_arts()
            elif self.current_state == 'lunala_channeling' and hasattr(self, 'cancel_lunala_arts'):
                self.cancel_lunala_arts()
            elif self.current_state == 'zamazenta_channeling' and hasattr(self, 'cancel_zamazenta_arts'):
                self.cancel_zamazenta_arts()
            elif self.current_state == 'eternatus_channeling' and hasattr(self, 'cancel_eternatus_arts'):
                self.cancel_eternatus_arts()
            elif self.current_state.startswith('koraidon_') and hasattr(self, 'cancel_koraidon_arts'):
                self.cancel_koraidon_arts()
            elif self.current_state.startswith('koraidon_') and hasattr(self, 'cancel_koraidon_arts'):
                self.cancel_koraidon_arts()
            elif self.current_state.startswith('miraidon_') and self.current_state != 'miraidon_paralyzed' and hasattr(self, 'cancel_miraidon_arts'):
                self.cancel_miraidon_arts()            
            elif self.current_state == 'miraidon_paralyzed':
                self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
                self.current_state = 'falling'
            elif self.current_state == 'bird_channeling' and hasattr(self, 'cancel_bird_arts'):
                self.cancel_bird_arts()
            elif self.current_state in ['mew_channeling', 'mew_bounce'] and hasattr(self, 'cancel_mew_arts'):
                self.cancel_mew_arts()
            elif self.current_state.startswith('beast_') and hasattr(self, 'cancel_beast_arts'):
                self.cancel_beast_arts()
            elif self.current_state.startswith('genie_') and hasattr(self, 'cancel_genie_arts'):
                self.cancel_genie_arts()
            elif self.current_state in ['celebi_channeling', 'celebi_wait', 'celebi_freeze', 'celebi_revert_flight'] and hasattr(self, 'cancel_celebi_arts'):
                self.cancel_celebi_arts()
            elif self.current_state in ['regi_approach', 'regi_strike'] and hasattr(self, 'cancel_regi_arts'):
                self.cancel_regi_arts()
            elif self.current_state in ['jirachi_channeling', 'jirachi_vanished', 'jirachi_flyby'] and hasattr(self, 'cancel_jirachi_arts'):
                self.cancel_jirachi_arts()
            elif self.current_state.startswith('darkrai_') and hasattr(self, 'cancel_darkrai_arts'):
                self.cancel_darkrai_arts()
            elif self.current_state.startswith('cresselia_') and self.current_state != 'cresselia_blessing' and hasattr(self, 'cancel_cresselia_arts'):
                self.cancel_cresselia_arts()
            elif self.current_state.startswith('lati_') and hasattr(self, 'cancel_lati_arts'):
                self.cancel_lati_arts()
            elif self.current_state.startswith('deoxys_') and hasattr(self, 'cancel_deoxys_arts'):
                self.cancel_deoxys_arts()
            elif self.current_state.startswith('lake_') and hasattr(self, 'cancel_lake_arts'):
                self.cancel_lake_arts()        
            elif self.current_state.startswith('shaymin_') and hasattr(self, 'cancel_shaymin_arts'):
                self.cancel_shaymin_arts()

            elif self.current_state.startswith('tapu_') and hasattr(self, 'cancel_tapu_mechanic'):
                self.cancel_tapu_mechanic()

            # Inyección Víctima (El Pokémon anclado)
            elif self.current_state == 'mew_tethered':
                self.current_state = 'falling'
                self.canvas.delete("vfx_mew_bubble")
                master = getattr(self, 'mew_master', None)
                if master and hasattr(master, 'mew_victims') and self in master.mew_victims:
                    master.mew_victims.remove(self)
                self.mew_master = None
                
            if self.is_wild:
                if getattr(self, 'game_controller', None) and getattr(self.game_controller, 'trainer', None):
                    self.current_state = 'idle'
                    def on_hit(pb_file=None):
                        self.on_catch(self)
                        self.animate_vfx("catch", pb_file=pb_file)
                    self.game_controller.trainer.spawn_pokeball_to(self.x + self.size_w/2, self.y + self.size_h/2, on_hit)
                else:
                    self.on_catch(self)
                    self.animate_vfx("catch")
            else:
                if getattr(self, 'game_controller', None) and getattr(self.game_controller, 'trainer', None):
                    self.current_state = 'idle'
                    def on_hit_return(pb_file=None):
                        self.on_remove(self)
                        self.animate_vfx("return", pb_file=pb_file)
                    self.game_controller.trainer.spawn_pokeball_to(self.x + self.size_w/2, self.y + self.size_h/2, on_hit_return)
                else:
                    self.on_remove(self)
                    self.animate_vfx("return")

    def handle_double_click(self, event):
        if self.current_state not in ['exiting', 'evolving_start', 'evolving_finish', 'despawning_wild']:
            if getattr(self, 'is_egg', False): 
                self.on_open_pc(None) 
            else: 
                self.on_open_pc(self.pet_data)
                # FIX: Double-clicking makes it the Discord star
                if self.game_controller and hasattr(self.game_controller, 'discord_rpc'):
                    self.game_controller.discord_rpc.set_target(self)

    def update_position(self):
        self.window.geometry(f"+{int(self.x)}+{int(self.y)}")

    def animate_loop(self):
        if self.current_state == 'exiting': return 
        
        # 60 FPS Anchor Synchronization (Window Drag Physics)
        if getattr(self, 'anchored_hwnd', None) and self.current_state in ['idle', 'walking', 'socializing', 'attacking', 'digging', 'digging_in', 'digging_out']:
            try:
                if HAS_WIN32 and win32gui.IsWindowVisible(self.anchored_hwnd) and not win32gui.IsIconic(self.anchored_hwnd):
                    new_rect = win32gui.GetWindowRect(self.anchored_hwnd)
                    old_rect = getattr(self, 'anchored_rect', new_rect)
                    
                    delta_l = new_rect[0] - old_rect[0]
                    delta_t = new_rect[1] - old_rect[1]
                    delta_r = new_rect[2] - old_rect[2]
                    delta_b = new_rect[3] - old_rect[3]

                    # ANTI-TELEPORT FILTER (If the window is minimized or changes virtual desktop)
                    if abs(delta_l) > 2000 or abs(delta_t) > 2000:
                        self.anchored_hwnd = None
                        self.anchored_rect = None
                    elif delta_l != 0 or delta_t != 0 or delta_r != 0 or delta_b != 0:
                        surface = getattr(self, 'climbing_surface', 'floor')

                        if surface == 'floor':
                            self.x += delta_l
                            # FIX: Follow the bottom edge of the window if inverted
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

        blend = max(getattr(self, 'evo_blend', 0.0), getattr(self, 'spawn_blend', 0.0))
        
        # --- GEOMETRIC FIX: VISUAL INVERSION FOR OPPOSITE EDGES ---
        render_facing_right = self.is_facing_right
        surface = getattr(self, 'climbing_surface', 'floor')
        
        # Monitor borders (screen_r: 90°, screen_l: 270°) are the inverse of window borders 
        # (wall_r: 270°, wall_l: 90°). They require prior mirror inversion.
        if surface in ['screen_l', 'screen_r']:
            render_facing_right = not self.is_facing_right
            
        # Palkia's inverted gravity on a standard floor also requires inversion
        if getattr(self, 'gravity_inverted', False) and surface == 'floor':
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
            # --- FRAME RATE EVALUATION ---
            target_ms = self.frame_rate_active if self.current_state in ['walking', 'falling', 'walking_away', 'jumping_arc', 'climbing', 'attacking', 'eating', 'dark_dash', 'hooh_channeling', 'panic_run', 'kyogre_channeling', 'deluge_float', 'groudon_channeling', 'lugia_channeling', 'lugia_dash', 'rayquaza_channeling', 'rayquaza_cyclone_victim', 'dialga_channeling', 'lati_channeling', 'deoxys_channeling', 'lake_rotating', 'shaymin_sky_jump', 'joy_jump'] else self.frame_rate_idle
            if getattr(self, 'time_distorted', False):
                target_ms = int(target_ms * 4.0)
            
            # --- VISUAL STATE OVERRIDE ---
            anim_state = self.current_state
            freeze_animation = False
            
            # 1. Absolute Priority: Freezing, Paralysis, and Petrification
            # Enforces sprite freezing across all paralysis types, overriding native FSM requests
            if getattr(self, 'kyurem_frozen_timer', 0) > 0 or getattr(self, 'zekrom_para_timer', 0) > 0 or getattr(self, 'mrd_para_timer', 0) > 0 or anim_state in ['zekrom_paralyzed', 'miraidon_paralyzed', 'kyurem_frozen', 'yveltal_petrified']:
                anim_state = 'idle'
                freeze_animation = True
                if hasattr(self, 'animator'):
                    self.animator.current_frame = getattr(self.animator, 'current_frame', 0) 
                target_ms = 999999
                
            elif anim_state == 'dragged':
                # Overrides the dragged sprite if the entity is currently burning or frozen
                if getattr(self, 'reshiram_burn_timer', 0) > 0:
                    anim_state = 'walking' 
                    target_ms = max(10, self.frame_rate_active // 2)
                elif getattr(self, 'kyurem_frozen_timer', 0) > 0 or getattr(self, 'zekrom_para_timer', 0) > 0 or getattr(self, 'mrd_para_timer', 0) > 0:
                    anim_state = 'idle'
                    freeze_animation = True
                    target_ms = 999999
                    if hasattr(self, 'animator'):
                        self.animator.current_frame = getattr(self.animator, 'current_frame', 0)
                
            # 2. Channeling Readjustments
            elif anim_state == 'hooh_channeling':
                anim_state = 'walking' if getattr(self, 'hooh_phase', 0) == 0 else 'idle'
            elif anim_state in ['kyogre_channeling', 'dialga_channeling', 'palkia_channeling', 'groudon_channeling']:
                anim_state = 'idle'
            elif anim_state == 'lugia_channeling':
                anim_state = 'walking'
            elif anim_state in ['giratina_dash_prep', 'giratina_dash']:
                anim_state = 'walking'
            elif anim_state in ['zekrom_channeling', 'reshiram_channeling', 'kyurem_channeling', 'xerneas_channeling', 'heatran_channeling', 'heatran_jump_down', 'heatran_storm', 'heatran_falling', 'lati_channeling']:
                anim_state = 'idle'
            elif anim_state in ['reshiram_burn', 'xerneas_pacified', 'yveltal_channeling', 'heatran_positioning', 'lati_spiral', 'lati_dash', 'lati_return']:
                anim_state = 'walking' 
            elif anim_state in ['zygarde_grounded']:
                anim_state = 'idle'
            elif anim_state == 'zygarde_channeling':
                if getattr(self, 'zygarde_phase', 0) in [0, 4]:
                    anim_state = 'idle' 
                else:
                    anim_state = 'walking'

            # ADD THIS FOR THE 50%
            elif anim_state == 'zygarde50_channeling':
                if getattr(self, 'zygarde50_phase', 0) in [0, 1]:
                    anim_state = 'idle' # Or 'digging' if you have the animation
                else:
                    anim_state = 'idle' # Stays in idle shooting while looking at the target

            # --- ADD THIS FOR LAND'S WRATH LAUNCH ---
            elif anim_state == 'zygarde_launched':
                anim_state = 'falling'

            elif anim_state == 'lunala_channeling':
                anim_state = 'idle' if getattr(self, 'lunala_phase', 0) > 0 else 'walking'

            elif anim_state == 'solgaleo_channeling':
                anim_state = 'walking'

            elif anim_state == 'zacian_channeling':
                anim_state = 'walking'

            elif anim_state == 'zamazenta_channeling':
                anim_state = 'walking'

            elif anim_state == 'eternatus_channeling':
                anim_state = 'idle'

            elif anim_state in ['koraidon_sprint', 'koraidon_climb', 'koraidon_dive', 'koraidon_dismount']:
                anim_state = 'walking' 
                # Bypasses the idle evaluation and forces exactly 2x active walking speed
                target_ms = max(10, self.frame_rate_active // 2)
            elif anim_state in ['koraidon_leap']:
                anim_state = 'falling'
            elif anim_state in ['koraidon_apex', 'koraidon_impact']:
                anim_state = 'idle'

            elif anim_state in ['miraidon_absorb', 'miraidon_impact']:
                anim_state = 'idle'
            elif anim_state in ['miraidon_descent', 'miraidon_dash']:
                anim_state = 'walking' 
                target_ms = max(10, self.frame_rate_active // 2)
            elif anim_state == 'miraidon_paralyzed':
                anim_state = 'idle'
                freeze_animation = True
                target_ms = 999999
                if hasattr(self, 'animator'):
                    self.animator.current_frame = getattr(self.animator, 'current_frame', 0)

            elif anim_state == 'bird_channeling':
                anim_state = 'idle'
                
            elif anim_state in ['mew_channeling', 'mew_bounce', 'mew_tethered']:
                anim_state = 'idle'

            elif anim_state in ['beast_channeling', 'beast_roar', 'beast_wait_clear']:
                anim_state = 'idle'
            elif anim_state in ['genie_channeling', 'genie_shoot', 'genie_wait_tornado', 'genie_finish']:
                anim_state = 'idle'
            elif anim_state in ['tornadus_victim', 'landorus_thrown', 'enamorus_joy']:
                anim_state = 'falling'
            elif anim_state == 'beast_dash':
                anim_state = 'walking'
                target_ms = max(10, self.frame_rate_active // 2)
            elif anim_state == 'beast_dismount':
                anim_state = 'falling'

            elif anim_state in ['celebi_channeling', 'celebi_wait', 'celebi_freeze', 'celebi_frozen']:
                anim_state = 'idle'
                if anim_state == 'celebi_frozen':
                    freeze_animation = True
                    target_ms = 999999
            elif anim_state == 'celebi_revert_flight':
                anim_state = 'walking'
                target_ms = max(10, self.frame_rate_active // 2)

            elif anim_state in ['regi_approach', 'regi_channeling', 'regigigas_approach', 'regigigas_grab']:
                regi_id = self.pet_name.lower().replace("_", "").replace("-", "")
                
                if anim_state == 'regi_channeling' and regi_id == "regigigas":
                    # Forces the forward-facing sprite while accumulating kinetic energy
                    anim_state = 'idle'
                elif regi_id == "regice" and anim_state == 'regi_approach':
                    anim_state = 'walking' 
                    freeze_animation = True
                    target_ms = 999999
                elif regi_id == "regieleki":
                    anim_state = 'walking' 
                    target_ms = max(10, self.frame_rate_active // 3) 
                elif regi_id == "regigigas":
                    anim_state = 'walking'
                    # Delays the visual refresh cycle to sync with the lethargic movement
                    target_ms = int(self.frame_rate_active * 2.0) 
                else:
                    anim_state = 'walking'
            elif anim_state == 'regi_strike':
                anim_state = 'idle'
            elif anim_state == 'regidrago_slowed':
                anim_state = 'walking'
                target_ms = int(self.frame_rate_active * 2.5) 
            elif anim_state == 'regirock_embedded':
                anim_state = 'idle'
                freeze_animation = True
                # Eliminado target_ms = 999999 para evitar la muerte del hilo visual

            # JIRACHI FSM RENDER
            elif anim_state == 'jirachi_channeling':
                anim_state = 'idle'
            elif anim_state == 'jirachi_flyby':
                anim_state = 'walking' 
                freeze_animation = True
                
            elif anim_state in ['sea_guardian_absorb', 'sea_guardian_wait', 'sea_guardian_braking', 'victini_channeling', 'victini_forming_v']:
                anim_state = 'idle'
            elif anim_state in ['sea_guardian_big_jump', 'sea_guardian_jump', 'sea_guardian_last_jump', 'victini_flying', 'victini_dash', 'genesect_walk']:
                anim_state = 'walking'
            elif anim_state in ['genesect_channeling', 'genesect_laser']:
                anim_state = 'walking'
                freeze_animation = True

            # JIRACHI BUFF TIMEOUT EVALUATION
            if getattr(self, 'jirachi_buff_timer', 0) > 0:
                self.jirachi_buff_timer -= 1
                if self.jirachi_buff_timer <= 0:
                    # Restores absolute original speed to prevent permanent acceleration logic
                    self.speed = getattr(self, 'base_buffered_speed', self.speed)

            # DARKRAI FSM RENDER
            elif anim_state in ['darkrai_channeling', 'darkrai_aoe']:
                anim_state = 'idle'
            elif anim_state == 'darkrai_shadow_walk':
                anim_state = 'walking' 
            elif anim_state == 'darkrai_nightmare':
                anim_state = 'idle'
                freeze_animation = True

            # CRESSELIA FSM RENDER
            elif anim_state in ['cresselia_channeling', 'cresselia_aurora']:
                anim_state = 'idle'
            elif anim_state in ['cresselia_ascension', 'cresselia_blessing']:
                anim_state = 'walking'
                
            # LATI TWINS FSM RENDER
            elif anim_state in ['lati_channeling', 'lati_spiral', 'lati_dash', 'lati_return']:
                anim_state = 'walking' if anim_state != 'lati_channeling' else 'idle'

            # DEOXYS FSM RENDER
            elif anim_state in ['deoxys_channeling', 'deoxys_ascend', 'deoxys_wait', 'deoxys_meteor', 'deoxys_emerge']:
                anim_state = 'idle'
                
            # LAKE TRIO FSM RENDER
            elif anim_state in ['lake_channeling', 'lake_rotating']:
                anim_state = 'walking' if anim_state == 'lake_rotating' else 'idle'
                
            # SHAYMIN FSM RENDER
            elif anim_state in ['shaymin_summon', 'shaymin_channeling']:
                anim_state = 'idle'
            elif anim_state in ['shaymin_sky_jump']:
                anim_state = 'walking'
            elif anim_state in ['joy_jump']:
                anim_state = 'falling'
                
            # TAPU FSM RENDER
            elif anim_state in ['tapu_channeling', 'tapu_active']:
                anim_state = 'idle'
            elif anim_state == 'tapu_positioning':
                anim_state = 'walking'

            # MELOETTA FSM RENDER
            elif anim_state in ['meloetta_aria_charge', 'meloetta_aria_wait', 'meloetta_aria_fire', 'meloetta_pirouette_fire']:
                anim_state = 'idle'
            elif anim_state in ['meloetta_aria_fly_up', 'meloetta_aria_fly_down', 'meloetta_aria_float', 'meloetta_pirouette_walk', 'meloetta_pirouette_jump_off', 'dancing', 'meloetta_pirouette_dance']:
                anim_state = 'walking'

            # --- PHYSICAL AND GEOMETRIC EXPANSION ENGINE ---
            if not hasattr(self, 'base_size_w'):
                self.base_size_w = self.size_w
                self.base_size_h = self.size_h
                
            enamorus_scale = 1.5 if self.pet_name.lower().replace("_", "").replace("-", "") in ["enamorus", "enamorus1"] else 1.0
            scale_mod = getattr(self, 'scale_mod', getattr(self, 'necrozma_scale_mod', enamorus_scale))
            if enamorus_scale > 1.0 and scale_mod < enamorus_scale:
                scale_mod = enamorus_scale
            target_w = max(1, int(self.base_size_w * scale_mod))
            target_h = max(1, int(self.base_size_h * scale_mod))
            
            if self.size_w != target_w or self.size_h != target_h:
                delta_w = target_w - self.size_w
                delta_h = target_h - self.size_h
                
                # 1. Updates absolute hitbox for collision engine scanner
                self.size_w = target_w
                self.size_h = target_h
                
                # 2. Shifts coordinates so it grows from center to sides and bottom to top
                self.x -= delta_w / 2
                self.y -= delta_h
                
                # 3. Recalculates gravity to not punch through Windows physical floor
                self.default_floor_y = (self.v_y + self.v_height) - self.size_h - getattr(self, 'offset_y', 0)
                
                # 4. Expands window and native Tkinter Canvas in real time
                self.window.geometry(f"{self.size_w}x{self.size_h}+{int(self.x)}+{int(self.y)}")
                self.canvas.config(width=self.size_w, height=self.size_h)
                
                # 5. Repositions the visual anchor of the sprite to the new calculated center
                if anim_state not in ['landing_shake', 'digging_in', 'digging_out']:
                    self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
                    
            # FIX: Passing the dynamically calculated render_facing_right instead of the raw physical direction
            self.animator.update_animation(
                anim_state, 
                render_facing_right, 
                self.canvas_image_id, 
                True, 
                target_ms, 
                blend, 
                getattr(self, 'surface_angle', 0), 
                getattr(self, 'is_glitching', False),
                getattr(self, 'dark_mode', False),
                scale_mod=scale_mod,
                bright_mod=getattr(self, 'necrozma_bright_mod', 1.0),
                darkness_mod=getattr(self, 'darkness_mod', 0.0),
                nightmare_filter=getattr(self, 'nightmare_filter', False),
                red_mod=getattr(self, 'volcanion_burn', 0) / 450.0
            )
        self.schedule_loop(16, self.animate_loop)

    def physics_loop(self):
        if getattr(self, 'is_glitching', False) and getattr(self, 'has_genesect_glitch', False) and hasattr(self, 'spawn_genesect_particle'):
            if random.random() < 0.4:
                cx = self.x - self.v_x + self.size_w/2 + random.uniform(-self.size_w*0.4, self.size_w*0.4)
                cy = self.y - self.v_y + self.size_h/2 + random.uniform(-self.size_h*0.4, self.size_h*0.4)
                self.spawn_genesect_particle(cx, cy, random.uniform(-1, 1), random.uniform(-3, -1), random.randint(15, 30), p_type="charge")

        if hasattr(self, 'check_time_distortion'):
            self.check_time_distortion()
        if hasattr(self, 'check_gravity_inversion'):
            self.check_gravity_inversion()
            
        if hasattr(self, 'tapu_field_timeout'):
            self.tapu_field_timeout -= 1
            if self.tapu_field_timeout <= 0:
                delattr(self, 'tapu_field_timeout')
                try: delattr(self, 'tapu_field_effect')
                except: pass
                if hasattr(self, 'original_speed'):
                    self.speed = self.original_speed
                if getattr(self, 'scale_mod', 1.0) != 1.0:
                    self.scale_mod = max(1.0, getattr(self, 'scale_mod', 1.0) - 0.05)
                    if self.scale_mod > 1.0:
                        self.tapu_field_timeout = 1

            
        # Resolves shared physics handlers by checking the alias map first. 
        # Falls back to the raw state name for dedicated 1:1 FSM handlers.
        target_fsm_name = self.state_aliases.get(self.current_state, self.current_state)
        handler_name = f"_fsm_{target_fsm_name}"
        
        # Executes the resolved function dynamically, avoiding bloated hardcoded dictionaries.
        if hasattr(self, handler_name):
            getattr(self, handler_name)()
        else:
            self._fsm_active()
            
        # FIX: Global Egg Safeguard
        # If an egg was forcefully transitioned to an adult state by a legendary mechanic, revert it.
        if getattr(self, 'is_egg', False):
            allowed_egg_states = ['egg_idle', 'egg_wiggle', 'falling_egg', 'dragged', 'falling', 'thrown', 'exiting', 'spawning_wild', 'despawning_wild']
            if self.current_state not in allowed_egg_states and not self.current_state.startswith('falling_'):
                self.current_state = 'egg_idle'

    def _fsm_exiting(self):
        pass 

    def _fsm_wait(self):
        if getattr(self, 'is_egg', False) and not getattr(self, 'is_dragging', False):
            current_env, _ = self.get_window_environment()
            if self.y < current_env['y'] - 15:
                self.current_state = 'falling_egg'
                self.v_y_velocity = 0.0
            else:
                self.y = current_env['y']
                self.floor_y = current_env['y']
                self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def _fsm_volcanion_channeling(self):
        import mechanics.volcanion
        mechanics.volcanion._fsm_volcanion_channeling(self)
        self.update_position()

    def _fsm_volcanion_shooting(self):
        import mechanics.volcanion
        mechanics.volcanion._fsm_volcanion_shooting(self)
        self.update_position()

    def _fsm_volcanion_victim(self):
        if not getattr(self, 'is_flying', False) and not getattr(self, 'is_climbing', False):
            self.v_y_velocity += 1.5
        self.v_x_velocity *= 0.85
        self.x += self.v_x_velocity
        self.y += self.v_y_velocity
        
        current_env, _ = self.get_window_environment()
        
        target_floor = self.default_floor_y
        if current_env['hwnd'] and self.y <= current_env['y'] + max(15, abs(int(self.v_y_velocity)) + 15):
            target_floor = current_env['y']
            
        if self.y >= target_floor and self.v_y_velocity >= 0:
            self.y = target_floor
            self.v_y_velocity = 0
            if target_floor == current_env.get('y'):
                self.anchored_hwnd = current_env['hwnd']
                self.anchored_rect = current_env['rect']
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

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
            # --- STRUCTURAL PATCH: NEGATIVE GRAVITY (UPWARDS) IN THROWS ---
            if getattr(self, 'gravity_inverted', False):
                if not getattr(self, 'hoopa_thrown', False):
                    gravity = -4.0 if getattr(self, 'heavy_fall', False) and self.v_y_velocity <= 0.5 else -1.5
                    self.v_y_velocity += gravity
                    self.v_x_velocity *= 0.95
                self.y += self.v_y_velocity
                self.x += self.v_x_velocity

                # Lateral limits
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

                # FIX: Inject the Window Radar for throws
                current_env, _ = self.get_window_environment()
                fall_tolerance = max(15, abs(int(self.v_y_velocity)) + 15) if self.v_y_velocity < 0 else 15
                
                target_y = current_env['y'] if self.y <= current_env['y'] + fall_tolerance else self.v_y
                if getattr(self, 'is_flying', False): target_y += getattr(self, 'target_offset_y', 0)

                # If its velocity is negative (going up) and hits the ceiling/window
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
            
            if not getattr(self, 'hoopa_thrown', False):
                gravity = 4.0 if getattr(self, 'heavy_fall', False) and self.v_y_velocity >= -0.5 else 1.5
                self.v_y_velocity += gravity
                
                gravity = 4.0 if getattr(self, 'heavy_fall', False) and self.v_y_velocity >= -0.5 else 1.5
                self.v_y_velocity += gravity
            if not getattr(self, 'hoopa_thrown', False):
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
                    self.hoopa_thrown = False
                elif self.x >= (self.v_x + self.v_width) - self.size_w:
                    self.x = (self.v_x + self.v_width) - self.size_w
                    self.v_x_velocity *= -0.7
                    self.is_facing_right = False
                    self.hoopa_thrown = False

            current_env, _ = self.get_window_environment()
            
            # ANTI-PASS-THROUGH FIX: Absorbs the tolerance calculated in get_window_environment
            fall_tolerance = max(15, int(self.v_y_velocity) + 15) if self.v_y_velocity > 0 else 15
            physical_floor = current_env['y'] if self.y <= current_env['y'] + fall_tolerance else self.default_floor_y

            # (The rest of _fsm_thrown remains the same, only this last block changes)
            if self.v_y_velocity > 0 and self.y >= physical_floor:
                self.y = physical_floor
                self.floor_y = physical_floor
                self.v_x_velocity = 0
                self.hoopa_thrown = False
                
                # INTERNAL VIBRATION TRIGGER OF THE POKEMON (Adjusted to 0.75s)
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
            
            # 1. We choose the new X coordinate at random
            self.x = random.randint(self.v_x, self.v_x + self.v_width - self.size_w)
            
            # 2. Y relocation logic
            if getattr(self, 'is_flying', False):
                self.y = getattr(self, 'target_floor_y', self.default_floor_y)
                self.floor_y = self.y
                self.anchored_hwnd = None
                self.anchored_rect = None
            else:
                # RADAR TRICK: We temporarily move the Pokemon to the upper limit of the monitor 
                # so that the scanner sweeps the entire screen downwards looking for windows.
                self.y = self.v_y 
                current_env, _ = self.get_window_environment()
                
                if current_env['hwnd']:
                    # It found a window at this X. It anchors and appears on top.
                    self.anchored_hwnd = current_env['hwnd']
                    self.anchored_rect = current_env['rect']
                    self.floor_y = self.anchored_rect[1] - self.size_h - getattr(self, 'offset_y', 0)
                    self.y = self.floor_y
                else:
                    # There is no window. It goes to the base floor.
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
            
            # Lemming Effect: If they lose the ground (e.g. they fall from a window while fleeing), they activate free fall
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

        # --- STRUCTURAL PATCH: NEGATIVE GRAVITY (UPWARDS) ---
        if getattr(self, 'gravity_inverted', False):
            self.y -= fall_speed
            self.x += getattr(self, 'v_x_velocity', 0.0)
            
            if getattr(self, 'can_screen_wrap', False):
                if self.x <= self.v_x - self.size_w: self.x = self.v_x + self.v_width
                elif self.x >= self.v_x + self.v_width: self.x = self.v_x - self.size_w
            else:
                self.x = max(self.v_x, min(self.x, (self.v_x + self.v_width) - self.size_w))

            # FIX: Inject the Window Radar for inverted free fall
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
                self.animate_spawn_glow()
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
            # (The rest of _fsm_falling remains the same, only this last block changes after the legendary IFs)
            else:
                if getattr(self, 'is_flying', False) and getattr(self, 'target_floor_y', self.y) != self.y:
                    self.floor_y = self.y
                    self.current_state = 'ascending'
                else:
                    # FIX: In direct fall state, velocity is mathematically locked, 
                    # so it is not necessary to evaluate self.v_y_velocity.
                    if getattr(self, 'heavy_fall', False):
                        self.trigger_landing_shake()
                    else:
                        if getattr(self, 'is_overflow', False):
                            self.current_state = 'walking_away'
                            self.is_facing_right = True
                        else:
                            if hasattr(self, 'meloetta_resume_state'):
                                self.current_state = self.meloetta_resume_state
                                delattr(self, 'meloetta_resume_state')
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
                        self.v_y_velocity = 5.0 if getattr(self, 'gravity_inverted', False) else -5.0
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
        is_inv = getattr(self, 'gravity_inverted', False)

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
                self.v_y_velocity = 5.0 if is_inv else -5.0

        elif self.attack_phase == 2:
            target_y = getattr(self, 'target_floor_y', self.floor_y) if self.is_flying else self.floor_y
            
            if (self.y > target_y if is_inv else self.y < target_y) or self.v_y_velocity != 0:
                self.v_y_velocity += -1.0 if is_inv else 1.0
                self.y += self.v_y_velocity
                self.x += self.v_x_velocity
                
                if (self.y <= target_y and self.v_y_velocity < 0) if is_inv else (self.y >= target_y and self.v_y_velocity > 0):
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
                self.v_y_velocity = 6.0 if is_inv else -6.0

        elif self.attack_phase == 4:
            target_y = getattr(self, 'target_floor_y', self.floor_y) if self.is_flying else self.floor_y
            
            if (self.y > target_y if is_inv else self.y < target_y) or self.v_y_velocity != 0:
                self.v_y_velocity += -1.0 if is_inv else 1.0
                self.y += self.v_y_velocity
                self.x += self.v_x_velocity
                
                if (self.y <= target_y and self.v_y_velocity < 0) if is_inv else (self.y >= target_y and self.v_y_velocity > 0):
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
                
                my_power = self.pet_data['level'] + (self.size_w * 0.5)
                target_power = target.pet_data['level'] + (target.size_w * 0.5)
                
                my_knockback_ratio = max(0.4, min(4.0, target_power / max(1, my_power)))
                target_knockback_ratio = max(0.4, min(4.0, my_power / max(1, target_power)))
                
                target_is_soft = not getattr(target, 'heavy_fall', False) or not getattr(target, 'aggressive', False)
                self_is_soft = not getattr(self, 'heavy_fall', False) or not getattr(self, 'aggressive', False)
                
                mult = 1 if not is_inv else -1
                
                # Retrieve dynamic force multipliers injected by Eternatus' Dynamax FSM
                my_force = getattr(self, 'push_force_mult', 1.0)
                target_force = getattr(target, 'push_force_mult', 1.0)
                
                if getattr(self, 'heavy_fall', False) and target_is_soft:
                    self.current_state = 'landing_shake'
                    self.shake_timer = 25 
                    self.v_x_velocity = 0.0
                    self.v_y_velocity = 0.0
                else:
                    self.current_state = 'thrown' 
                    # Apply target's force multiplier to self knockback
                    self.v_x_velocity = -(25.0 * my_knockback_ratio * target_force) * push_dir 
                    self.v_y_velocity = -(15.0 * min(1.5, my_knockback_ratio) * target_force) * mult            
                
                if target and getattr(target, 'current_state', '') == 'attacking':
                    if getattr(target, 'heavy_fall', False) and self_is_soft:
                        target.current_state = 'landing_shake'
                        target.shake_timer = 25 
                        target.v_x_velocity = 0.0
                        target.v_y_velocity = 0.0
                    else:
                        target.current_state = 'thrown'
                        # Apply self force multiplier to target knockback
                        target.v_x_velocity = (25.0 * target_knockback_ratio * my_force) * push_dir 
                        target.v_y_velocity = -(15.0 * min(1.5, target_knockback_ratio) * my_force) * mult
                        
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
                        self.v_y_velocity = 4.0 if getattr(self, 'gravity_inverted', False) else -4.0
                        self.y += self.v_y_velocity
        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def schedule_glitch_teleport(self):
        if not getattr(self, 'is_glitching', False) or self.current_state == 'exiting':
            return
            
        # If the user grabs it or it is involved in telekinesis, we pause the jumps
        if self.current_state in ['dragged', 'tk_controlled', 'tk_lifted']:
            self.schedule_loop(500, self.schedule_glitch_teleport)
            return
            
        if getattr(self, 'glitch_teleports_left', 0) > 0:
            self.glitch_teleports_left -= 1
            
            # Chaotic teleportation: New X coordinate
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
            
            # Schedule the next interference between 1.5 and 3 seconds
            self.schedule_loop(random.randint(1500, 3000), self.schedule_glitch_teleport)
        else:
            # End of phase
            self.is_glitching = False
            self.has_genesect_glitch = False
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
            # Totally hidden under the Canvas limit
            self.current_state = 'digging'
            self.canvas.itemconfig(self.canvas_image_id, state='hidden')
            
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

    def _fsm_digging(self):
        self.dig_timer -= 1
        
        # --- ORGANIC NAVIGATION ---
        if random.randint(1, 1000) <= 20:
            self.is_facing_right = not self.is_facing_right
        
        dig_speed = self.speed * 2

        # FIX: Strict and predictive clamping against sudden window resizing
        if getattr(self, 'anchored_rect', None):
            rect = self.anchored_rect
            
            # 1. Emergency clamping: If the window left it out, we force it inside
            if self.x > rect[2] - self.size_w:
                self.x = rect[2] - self.size_w
                self.is_facing_right = False
            elif self.x < rect[0]:
                self.x = rect[0]
                self.is_facing_right = True
            # 2. Standard predictive check: Bounce before exiting
            else:
                if self.is_facing_right and self.x + dig_speed > rect[2] - self.size_w:
                    self.is_facing_right = False
                elif not self.is_facing_right and self.x - dig_speed < rect[0]:
                    self.is_facing_right = True

        self.x += dig_speed if self.is_facing_right else -dig_speed
        
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
        self.sg_cooldown = max(0, getattr(self, 'sg_cooldown', 0) - 1)
        self.victini_cooldown = max(0, getattr(self, 'victini_cooldown', 0) - 1)
        self.genesect_cooldown = max(0, getattr(self, 'genesect_cooldown', 0) - 1)
        self.meloetta_cooldown = max(0, getattr(self, 'meloetta_cooldown', 0) - 1)
        self.social_cooldown = max(0, getattr(self, 'social_cooldown', 0) - 1)
        self.attack_cooldown = max(0, getattr(self, 'attack_cooldown', 0) - 1)

        self.teleport_cooldown = max(0, getattr(self, 'teleport_cooldown', 0) - 1)
        self.tk_cooldown = max(0, getattr(self, 'tk_cooldown', 0) - 1)
        self.glitch_cooldown = max(0, getattr(self, 'glitch_cooldown', 0) - 1)
        self.bubble_cooldown = max(0, getattr(self, 'bubble_cooldown', 0) - 1)
        self.dig_cooldown = max(0, getattr(self, 'dig_cooldown', 0) - 1)
        
        # FIX: Initialization and decay of the Sinister counter per frame
        self.dark_cooldown = max(0, getattr(self, 'dark_cooldown', 0) - 1) 
        self.mewtwo_cooldown = max(0, getattr(self, 'mewtwo_cooldown', 0) - 1) 
        self.dialga_cooldown = max(0, getattr(self, 'dialga_cooldown', 0) - 1)
        self.hooh_cooldown = max(0, getattr(self, 'hooh_cooldown', 0) - 1) 
        self.kyogre_cooldown = max(0, getattr(self, 'kyogre_cooldown', 0) - 1)
        self.groudon_cooldown = max(0, getattr(self, 'groudon_cooldown', 0) - 1)
        self.lugia_cooldown = max(0, getattr(self, 'lugia_cooldown', 0) - 1)
        self.rayquaza_cooldown = max(0, getattr(self, 'rayquaza_cooldown', 0) - 1)
        self.palkia_cooldown = max(0, getattr(self, 'palkia_cooldown', 0) - 1)
        self.giratina_cooldown = max(0, getattr(self, 'giratina_cooldown', 0) - 1)
        self.zekrom_cooldown = max(0, getattr(self, 'zekrom_cooldown', 0) - 1)
        self.reshiram_cooldown = max(0, getattr(self, 'reshiram_cooldown', 0) - 1)
        self.heatran_cooldown = max(0, getattr(self, 'heatran_cooldown', 0) - 1)
        self.kyurem_cooldown = max(0, getattr(self, 'kyurem_cooldown', 0) - 1)
        self.xerneas_cooldown = max(0, getattr(self, 'xerneas_cooldown', 0) - 1)
        self.yveltal_cooldown = max(0, getattr(self, 'yveltal_cooldown', 0) - 1)
        self.zygarde_cooldown = max(0, getattr(self, 'zygarde_cooldown', 0) - 1)
        self.lunala_cooldown = max(0, getattr(self, 'lunala_cooldown', 0) - 1)
        self.solgaleo_cooldown = max(0, getattr(self, 'solgaleo_cooldown', 0) - 1)
        self.necrozma_cooldown = max(0, getattr(self, 'necrozma_cooldown', 0) - 1)
        self.zacian_cooldown = max(0, getattr(self, 'zacian_cooldown', 0) - 1)
        self.zamazenta_cooldown = max(0, getattr(self, 'zamazenta_cooldown', 0) - 1)
        self.eternatus_cooldown = max(0, getattr(self, 'eternatus_cooldown', 0) - 1)
        self.koraidon_cooldown = max(0, getattr(self, 'koraidon_cooldown', 0) - 1)
        self.miraidon_cooldown = max(0, getattr(self, 'miraidon_cooldown', 0) - 1)
        self.bird_cooldown = max(0, getattr(self, 'bird_cooldown', 0) - 1)
        self.mew_cooldown = max(0, getattr(self, 'mew_cooldown', 0) - 1)
        self.beast_cooldown = max(0, getattr(self, 'beast_cooldown', 0) - 1)
        self.celebi_cooldown = max(0, getattr(self, 'celebi_cooldown', 0) - 1) 
        self.regi_cooldown = max(0, getattr(self, 'regi_cooldown', 0) - 1)
        self.jirachi_cooldown = max(0, getattr(self, 'jirachi_cooldown', 0) - 1)
        self.darkrai_cooldown = max(0, getattr(self, 'darkrai_cooldown', 0) - 1)
        self.cresselia_cooldown = max(0, getattr(self, 'cresselia_cooldown', 0) - 1)
        self.lati_cooldown = max(0, getattr(self, 'lati_cooldown', 0) - 1)
        self.deoxys_cooldown = max(0, getattr(self, 'deoxys_cooldown', 0) - 1)
        self.lake_cooldown = max(0, getattr(self, 'lake_cooldown', 0) - 1)
        self.shaymin_cooldown = max(0, getattr(self, 'shaymin_cooldown', 0) - 1)
        self.genie_cooldown = max(0, getattr(self, 'genie_cooldown', 0) - 1)
        self.hoopa_cooldown = max(0, getattr(self, 'hoopa_cooldown', 0) - 1)
        self.volcanion_cooldown = max(0, getattr(self, 'volcanion_cooldown', 0) - 1)
        self.volcanion_cooldown = max(0, getattr(self, 'volcanion_cooldown', 0) - 1)

        # CENTRALIZED ALLOCATION: Extracted and evaluated once per tick for all legendary mechanics.
        normalized_name = self.pet_name.lower().replace("_", "").replace("-", "")

        # --- EXCLUSIVE MECHANIC: CRESSELIA ---
        if normalized_name == "cresselia" and getattr(self, 'cresselia_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.cresselia_cooldown = 72000 
                self.trigger_cresselia_arts()
                return

        # --- EXCLUSIVE MECHANIC: HOOPA ---
        if normalized_name in ["hoopa", "hoopa1"] and getattr(self, 'hoopa_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.start_hoopa_mechanic()
                return

        # --- EXCLUSIVE MECHANIC: VOLCANION ---
        if normalized_name == "volcanion" and getattr(self, 'volcanion_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.start_volcanion_mechanic()
                return

        # --- EXCLUSIVE MECHANIC: DARKRAI ---
        if normalized_name == "darkrai" and getattr(self, 'darkrai_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.darkrai_cooldown = 72000 
                self.trigger_darkrai_arts()
                return

        # --- EXCLUSIVE MECHANIC: JIRACHI ---
        if normalized_name == "jirachi" and getattr(self, 'jirachi_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.jirachi_cooldown = 72000 
                self.trigger_jirachi_arts()
                return

        # --- EXCLUSIVE MECHANIC: LEGENDARY REGIS ---
        normalized_name = self.pet_name.lower().replace("_", "").replace("-", "")
        # The string "regigigas" must be explicitly present to grant FSM entry
        if normalized_name in ["regirock", "regice", "registeel", "regieleki", "regidrago", "regigigas"] and getattr(self, 'regi_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.regi_cooldown = 72000 
                self.trigger_regi_arts()
                return

        # --- EXCLUSIVE MECHANIC: TEMPORAL CHECKPOINT (CELEBI) ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "celebi" and getattr(self, 'celebi_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.celebi_cooldown = 72000 
                self.trigger_celebi_arts()
                return

        # --- EXCLUSIVE MECHANIC: LEGENDARY BEASTS (RAIKOU, ENTEI, SUICUNE) ---
        if self.pet_name.lower().replace("_", "").replace("-", "") in ["raikou", "entei", "suicune", "ragingbolt", "gougingfire", "walkingwake"] and getattr(self, 'beast_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.beast_cooldown = 72000 
                self.trigger_beast_arts()
                return

        # --- EXCLUSIVE MECHANIC: LEGENDARY GENIES (TORNADUS, THUNDURUS, LANDORUS, ENAMORUS) ---
        if self.pet_name.lower().replace("_", "").replace("-", "") in ["tornadus", "tornadus1", "thundurus", "thundurus1", "landorus", "landorus1", "enamorus", "enamorus1"] and getattr(self, 'genie_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.genie_cooldown = 72000
                self.trigger_genie_arts()
                return

        # --- EXCLUSIVE MECHANIC: GENESIS BUBBLE (MEW) ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "mew" and getattr(self, 'mew_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.mew_cooldown = 72000 
                self.trigger_mew_arts()
                return

        # --- EXCLUSIVE MECHANIC: LEGENDARY BIRDS ---
        if self.pet_name.lower().replace("_", "").replace("-", "") in ["articuno", "articuno1", "zapdos", "zapdos1", "moltres", "moltres1"] and getattr(self, 'bird_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.bird_cooldown = 72000 
                self.trigger_bird_arts()
                return

        # --- EXCLUSIVE MECHANIC: ELECTRO DRIFT (MIRAIDON) ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "miraidon" and getattr(self, 'miraidon_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.miraidon_cooldown = 72000 
                self.trigger_electro_drift()
                return

        # --- EXCLUSIVE MECHANIC: APEX CRASH (KORAIDON) ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "koraidon" and getattr(self, 'koraidon_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.koraidon_cooldown = 72000 
                self.trigger_apex_crash()
                return

        # --- EXCLUSIVE MECHANIC: ETERNABEAM (ETERNATUS) ---
        if self.pet_name.lower().replace("_", "").replace("-", "") in ["eternatus", "eternatus1"] and getattr(self, 'eternatus_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.eternatus_cooldown = 72000 
                self.current_state = 'eternatus_channeling'
                self.schedule_loop(50, self.physics_loop)
                return

        # --- EXCLUSIVE MECHANIC: DAUNTLESS SHIELD (ZAMAZENTA) ---
        if self.pet_name.lower().replace("_", "").replace("-", "") in ["zamazenta", "zamazenta1"] and getattr(self, 'zamazenta_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.zamazenta_cooldown = 72000 
                self.current_state = 'zamazenta_channeling'
                self.schedule_loop(50, self.physics_loop)
                return

        # --- EXCLUSIVE MECHANIC: CROSS SCREEN DASH (LATIOS/LATIAS) ---
        if self.pet_name.lower().replace("_", "").replace("-", "") in ["latios", "latias"] and getattr(self, 'lati_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active(ignore_lati=True):
            if random.randint(1, 1000) <= 8:
                self.lati_cooldown = 72000 
                self.current_state = 'lati_channeling'
                self.schedule_loop(50, self.physics_loop)
                return

        # --- EXCLUSIVE MECHANIC: METEOR STRIKE (DEOXYS) ---
        if self.pet_name.lower().replace("_", "").replace("-", "") in ["deoxys", "deoxys1", "deoxys2", "deoxys3"] and getattr(self, 'deoxys_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.deoxys_cooldown = 72000
                self.current_state = 'deoxys_channeling'
                self.schedule_loop(50, self.physics_loop)
                return

        # --- EXCLUSIVE MECHANIC: LAKE TRIO ROTATION (AZELF, MESPRIT, UXIE) ---
        if self.pet_name.lower().replace("_", "") in ["azelf", "mesprit", "uxie"] and getattr(self, 'lake_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active(ignore_lake=True):
            if random.randint(1, 1000) <= 8:
                self.lake_cooldown = 72000
                self.current_state = 'lake_channeling'
                self.schedule_loop(50, self.physics_loop)
                return
                
        # --- EXCLUSIVE MECHANIC: SHAYMIN (LAND / SKY) ---
        if self.pet_name.lower().replace("_", "") == "shaymin" and getattr(self, 'shaymin_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.shaymin_cooldown = 108000
                self.current_state = 'shaymin_summon'
                self.schedule_loop(50, self.physics_loop)
                return
                
        if self.pet_name.lower().replace("_", "") == "shaymin1" and getattr(self, 'shaymin_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.shaymin_cooldown = 108000
                if hasattr(self, 'start_shaymin_sky_jump'):
                    self.start_shaymin_sky_jump()
                self.schedule_loop(50, self.physics_loop)
                return

        # --- EXCLUSIVE MECHANIC: BEHEMOTH BLADE (ZACIAN) ---
        if self.pet_name.lower().replace("_", "").replace("-", "") in ["zacian", "zacian1"] and getattr(self, 'zacian_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.zacian_cooldown = 72000 
                self.current_state = 'zacian_channeling'
                self.schedule_loop(50, self.physics_loop)
                return

        # --- EXCLUSIVE MECHANIC: VICTINI ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "victini" and getattr(self, 'victini_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active(ignore_victini=True):
            if random.randint(1, 1000) <= 8:
                if hasattr(self, 'start_victini_mechanic'):
                    self.start_victini_mechanic()
                return

        # --- EXCLUSIVE MECHANIC: GENESECT ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "genesect" and getattr(self, 'genesect_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and getattr(self, 'climbing_surface', 'floor') == 'floor' and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active(ignore_genesect=True):
            if random.randint(1, 1000) <= 8:
                if hasattr(self, 'start_genesect_mechanic'):
                    self.start_genesect_mechanic()
                return

        # --- EXCLUSIVE MECHANIC: MELOETTA ---
        if self.pet_name.lower().replace("_", "").replace("-", "") in ["meloetta", "meloetta1"] and getattr(self, 'meloetta_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and getattr(self, 'climbing_surface', 'floor') == 'floor' and not self.is_global_mechanic_active(ignore_meloetta=True):
            if random.randint(1, 1000) <= 8:
                if hasattr(self, 'start_meloetta_mechanic'):
                    self.start_meloetta_mechanic()
                return

        # --- EXCLUSIVE MECHANIC: SEA GUARDIANS (MANAPHY, PHIONE) ---
        if self.pet_name.lower().replace("_", "").replace("-", "") in ["manaphy", "phione"] and getattr(self, 'sg_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active(ignore_sea_guardians=True):
            if random.randint(1, 1000) <= 8:
                if hasattr(self, 'start_sea_guardian_mechanic'):
                    self.start_sea_guardian_mechanic()
                self.schedule_loop(33, self.physics_loop)
                return

        # --- EXCLUSIVE MECHANIC: TAPUS (KOKO, LELE, BULU, FINI) ---
        if self.pet_name.lower().replace("_", "").replace("-", "") in ["tapukoko", "tapukoko1", "tapulele", "tapulele1", "tapubulu", "tapubulu1", "tapufini", "tapufini1"] and getattr(self, 'tapu_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.tapu_cooldown = 108000
                if hasattr(self, 'start_tapu_mechanic'):
                    self.start_tapu_mechanic()
                self.schedule_loop(33, self.physics_loop)
                return

        # --- EXCLUSIVE MECHANIC: PRISMATIC LASER (NECROZMA) ---
        # Base Necrozma, Dusk Mane (necrozma1) and Dawn Wings (necrozma2) share this core ability
        if self.pet_name.lower().replace("_", "").replace("-", "") in ["necrozma", "necrozma1", "necrozma2"] and getattr(self, 'necrozma_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.necrozma_cooldown = 72000 
                self.current_state = 'necrozma_channeling'
                self.schedule_loop(50, self.physics_loop)
                return

        # --- EXCLUSIVE MECHANIC: SUNSTEEL STRIKE (SOLGALEO) ---
        # Shared with Dusk Mane Necrozma (necrozma1) due to assimilation
        if self.pet_name.lower().replace("_", "").replace("-", "") in ["solgaleo", "necrozma1"] and getattr(self, 'solgaleo_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.solgaleo_cooldown = 72000 
                self.current_state = 'solgaleo_channeling'
                self.schedule_loop(50, self.physics_loop)
                return

        # --- EXCLUSIVE MECHANIC: MOONGEIST BEAM (LUNALA) ---
        # Shared with Dawn Wings Necrozma (necrozma2) due to assimilation
        if self.pet_name.lower().replace("_", "").replace("-", "") in ["lunala", "necrozma2"] and getattr(self, 'lunala_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.lunala_cooldown = 72000 
                self.current_state = 'lunala_channeling'
                self.schedule_loop(50, self.physics_loop)
                return
                
        # --- EXCLUSIVE MECHANIC: LAND'S WRATH / THOUSAND ARROWS (ZYGARDE 50%) ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "zygarde" and getattr(self, 'zygarde_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.zygarde_cooldown = 72000 # 1 hour
                self.current_state = 'zygarde50_channeling'
                self.schedule_loop(50, self.physics_loop)
                return

        # --- EXCLUSIVE MECHANIC: THOUSAND ARROWS (ZYGARDE 10%) ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "zygarde1" and getattr(self, 'zygarde_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.zygarde_cooldown = 72000 # 1 hour
                self.current_state = 'zygarde_channeling'
                self.schedule_loop(50, self.physics_loop)
                return

        # --- EXCLUSIVE MECHANIC: OBLIVION WING (YVELTAL) ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "yveltal" and getattr(self, 'yveltal_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.yveltal_cooldown = 72000 # 1 hour
                self.current_state = 'yveltal_channeling'
                self.schedule_loop(50, self.physics_loop)
                return

        # --- EXCLUSIVE MECHANIC: XERNEAS' GEOMANCY ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "xerneas" and getattr(self, 'xerneas_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.xerneas_cooldown = 72000 # 1 hour
                self.current_state = 'xerneas_channeling'
                self.schedule_loop(50, self.physics_loop)
                return

        # --- EXCLUSIVE MECHANIC: GLACIATE (KYUREM) ---
        # Base Kyurem, White Kyurem (kyurem1) and Black Kyurem (kyurem2) share this core ability
        if self.pet_name.lower().replace("_", "").replace("-", "") in ["kyurem", "kyurem1", "kyurem2"] and getattr(self, 'kyurem_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.kyurem_cooldown = 108000 
                self.current_state = 'kyurem_channeling'
                self.schedule_loop(50, self.physics_loop)
                return

        # --- EXCLUSIVE MECHANIC: MAGMA STORM (HEATRAN) ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "heatran" and getattr(self, 'heatran_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and getattr(self, 'climbing_surface', 'floor') == 'floor' and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.heatran_cooldown = 72000 
                if self.y < self.default_floor_y - 15:
                    self.current_state = 'heatran_jump_down'
                    self.v_y_velocity = -10.0
                else:
                    self.current_state = 'heatran_channeling'
                self.schedule_loop(50, self.physics_loop)
                return

        # --- EXCLUSIVE MECHANIC: BLUE FLARE (RESHIRAM) ---
        # Shared with White Kyurem (kyurem1) due to assimilation
        if self.pet_name.lower().replace("_", "").replace("-", "") in ["reshiram", "kyurem1"] and getattr(self, 'reshiram_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.reshiram_cooldown = 72000 
                self.current_state = 'reshiram_channeling'
                self.schedule_loop(50, self.physics_loop)
                return

        # --- EXCLUSIVE MECHANIC: BOLT STRIKE (ZEKROM) ---
        # Shared with Black Kyurem (kyurem2) due to assimilation
        if self.pet_name.lower().replace("_", "").replace("-", "") in ["zekrom", "kyurem2"] and getattr(self, 'zekrom_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.zekrom_cooldown = 72000 
                self.current_state = 'zekrom_channeling'
                self.schedule_loop(50, self.physics_loop)
                return

        # --- EXCLUSIVE MECHANIC: GIRATINA'S DISTORTION VORTEX ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "giratina" and getattr(self, 'giratina_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not getattr(self, 'is_glitching', False) and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                if getattr(self, 'get_all_pets', None):
                    excluded_states = ['exiting', 'dragged', 'mewtwo_victim', 'panic_run', 'deluge_float', 'rayquaza_cyclone_victim', 'evolving_start', 'evolving_finish', 'spawning_wild', 'despawning_wild', 'falling_pokeball', 'falling_egg', 'giratina_victim_pulled', 'giratina_victim_fade', 'giratina_victim_absorbed']
                    valid_targets = [p for p in self.get_all_pets() if p != self and p.current_state not in excluded_states and not getattr(p, 'is_egg', False)]
                    
                    if valid_targets:
                        self.giratina_cooldown = 108000 # 1.5 hours
                        self.current_state = 'giratina_channeling'
                        
                        # --- ABSOLUTE CLEANUP OF PREVIOUS MECHANICS ---
                        for target in valid_targets:
                            # 1. Dark Arts
                            if target.current_state.startswith('dark_'): 
                                target.cancel_dark_arts()
                                
                            # 2. Telekinesis (Auras and Master/Victim Links)
                            elif target.current_state == 'tk_channeling':
                                if hasattr(target, 'manage_tk_aura'): target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
                                if getattr(target, 'tk_target', None):
                                    t_targ = target.tk_target
                                    if hasattr(target, 'manage_tk_aura'):
                                        t_w = t_targ.size_w if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size
                                        t_h = t_targ.size_h if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size
                                        target.manage_tk_aura(t_targ.canvas, t_w, t_h, False)
                                    t_targ.current_state = 'falling'
                                    if hasattr(t_targ, 'tk_master'): t_targ.tk_master = None
                                target.tk_target = None
                            elif target.current_state == 'tk_lifted':
                                if hasattr(target, 'manage_tk_aura'): target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
                                if getattr(target, 'tk_master', None):
                                    target.tk_master.tk_target = None
                                    if hasattr(target.tk_master, 'manage_tk_aura'): target.tk_master.manage_tk_aura(target.tk_master.canvas, target.tk_master.size_w, target.tk_master.size_h, False)
                                    target.tk_master.current_state = 'falling'
                                target.tk_master = None
                                
                            # 3. Water Bubbles
                            elif target.current_state == 'bubbled':
                                if hasattr(target, 'manage_bubble_vfx'): target.manage_bubble_vfx(False)
                                if hasattr(target, 'show_bubble_burst_vfx'): target.show_bubble_burst_vfx()
                            
                            # 4. FIX: Restore Canvas Base Coordinates for Digging
                            elif target.current_state in ['digging_in', 'digging', 'digging_out']:
                                target.canvas.itemconfig(target.canvas_image_id, state='normal')
                                target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)

                            # 5. FIX: Stop Asynchronous Ghost Interference Thread (Glitch)
                            if getattr(target, 'is_glitching', False):
                                target.is_glitching = False
                                target.has_genesect_glitch = False
                                target.glitch_teleports_left = 0
                                target.glitch_cooldown = 12000

                            # 6. Disconnection of ongoing Legendary Channelers
                            if target.current_state.startswith('mewtwo_') and hasattr(target, 'cancel_mewtwo_arts'):
                                target.cancel_mewtwo_arts()
                            elif target.current_state in ['hooh_channeling', 'panic_run'] and hasattr(target, 'cancel_hooh_arts'):
                                target.cancel_hooh_arts()
                            elif target.current_state in ['lugia_channeling', 'lugia_dash'] and hasattr(target, 'cancel_lugia_arts'):
                                target.cancel_lugia_arts()
                            elif target.current_state == 'kyogre_channeling' and hasattr(target, 'cancel_kyogre_arts'):
                                target.cancel_kyogre_arts()
                            elif target.current_state == 'groudon_channeling' and hasattr(target, 'cancel_groudon_arts'):
                                target.cancel_groudon_arts()
                            elif target.current_state == 'rayquaza_channeling' and hasattr(target, 'cancel_rayquaza_arts'):
                                target.cancel_rayquaza_arts()
                            elif target.current_state == 'dialga_channeling' and hasattr(target, 'cancel_dialga_arts'):
                                target.cancel_dialga_arts()
                            elif target.current_state == 'palkia_channeling' and hasattr(target, 'cancel_palkia_arts'):
                                target.cancel_palkia_arts()

                            # 7. Final Visual Reset and Assignment
                            target.canvas.itemconfig(target.canvas_image_id, state='normal')
                            try: target.window.attributes('-alpha', 1.0)
                            except: pass
                                
                            target.current_state = 'giratina_victim_pulled'
                            target.giratina_master = self
                            target.anchored_hwnd = None
                        # ------------------------------------------------
                            
                        self.giratina_targets = valid_targets
                        self.schedule_loop(50, self.physics_loop)
                        return

       # --- EXCLUSIVE MECHANIC: PALKIA'S GRAVITY INVERSION ---
        if self.pet_name.lower() == "palkia" and getattr(self, 'palkia_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.current_state = 'palkia_channeling'
                self.schedule_loop(50, self.physics_loop)
                return

       # --- EXCLUSIVE MECHANIC: RAYQUAZA'S EMERALD CYCLONE ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "rayquaza" and self.rayquaza_cooldown == 0 and self.current_state in ['idle', 'walking'] and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8: 
                if getattr(self, 'get_all_pets', None):
                    excluded_states = ['exiting', 'dragged', 'mewtwo_victim', 'panic_run', 'deluge_float', 'rayquaza_cyclone_victim', 'evolving_start', 'evolving_finish', 'spawning_wild', 'despawning_wild', 'falling_pokeball', 'falling_egg']
                    valid_targets = [p for p in self.get_all_pets() if p != self and p.current_state not in excluded_states and not getattr(p, 'is_egg', False)]
                    
                    if valid_targets:
                        self.rayquaza_cooldown = 108000 # 1.5 hours
                        self.current_state = 'rayquaza_channeling'
                        self.rayquaza_phase = 0
                        
                        # FIX: Define number of back and forths and the initial sweep duration
                        self.rayquaza_sweeps_total = random.randint(8, 10)
                        self.rayquaza_sweeps_done = 0
                        self.rayquaza_sweep_duration = 120 # Starts slow (~3.6s the first crossing)
                        
                        self.rayquaza_targets = valid_targets 
                        self.schedule_loop(50, self.physics_loop)
                        return

        # --- EXCLUSIVE MECHANIC: LUGIA'S AEROBLAST GALE ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "lugia" and self.lugia_cooldown == 0 and self.current_state in ['idle', 'walking'] and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8: 
                self.lugia_cooldown = 108000 # 1.5 hours
                self.current_state = 'lugia_channeling'
                self.is_facing_right = random.choice([True, False]) # Decide where it's going to sweep the screen
                self.schedule_loop(50, self.physics_loop)
                return

        # --- EXCLUSIVE MECHANIC: GROUDON'S EARTHQUAKE ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "groudon" and self.groudon_cooldown == 0 and self.current_state in ['idle', 'walking'] and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8: 
                self.groudon_cooldown = 108000 # 1.5 hours
                self.current_state = 'groudon_channeling'
                # LOGICAL FIX: Define randomness of repetitions (5 to 10) and the first propulsion
                self.groudon_jumps_left = random.randint(5, 10) 
                self.groudon_phase = 'jumping'
                self.v_y_velocity = -28.0 
                self.schedule_loop(50, self.physics_loop)
                return

        # --- EXCLUSIVE MECHANIC: KYOGRE'S DELUGE ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "kyogre" and self.kyogre_cooldown == 0 and self.current_state in ['idle', 'walking'] and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8: 
                if getattr(self, 'get_all_pets', None):
                    excluded_states = ['exiting', 'dragged', 'mewtwo_victim', 'panic_run', 'deluge_float', 'evolving_start', 'evolving_finish', 'spawning_wild', 'despawning_wild', 'falling_pokeball', 'falling_egg']
                    valid_targets = [p for p in self.get_all_pets() if p != self and p.current_state not in excluded_states and not getattr(p, 'is_egg', False)]
                    
                    if valid_targets:
                        self.kyogre_cooldown = 108000 # 1.5 hours
                        self.current_state = 'kyogre_channeling'
                        self.kyogre_phase = 0
                        self.kyogre_timer = 666 # exactly 20 seconds
                        self.kyogre_targets = valid_targets 
                        self.schedule_loop(50, self.physics_loop)
                        return


        # --- EXCLUSIVE MECHANIC: DIALGA'S TIME DISTORTION ---
        if self.pet_name.lower() == "dialga" and getattr(self, 'dialga_cooldown', 0) == 0 and self.current_state in ['idle', 'walking'] and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8:
                self.current_state = 'dialga_channeling'
                self.schedule_loop(50, self.physics_loop)
                return
            
        # --- EXCLUSIVE MECHANIC: HO-OH'S SACRED FIRE ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "hooh" and self.hooh_cooldown == 0 and self.current_state in ['idle', 'walking'] and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8: 
                if getattr(self, 'get_all_pets', None):
                    excluded_states = ['exiting', 'dragged', 'mewtwo_victim', 'panic_run', 'evolving_start', 'evolving_finish', 'spawning_wild', 'despawning_wild', 'falling_pokeball', 'falling_egg']
                    valid_targets = [p for p in self.get_all_pets() if p != self and p.current_state not in excluded_states and not getattr(p, 'is_egg', False)]
                    
                    if valid_targets:
                        self.hooh_cooldown = 108000 
                        self.current_state = 'hooh_channeling'
                        self.hooh_phase = 0
                        self.hooh_timer = 666 
                        
                        # FIX: We only keep the targets in memory, but DO NOT interrupt them yet.
                        # They will continue their normal life during the preparation flight.
                        self.hooh_targets = valid_targets 
                        
                        self.schedule_loop(50, self.physics_loop)
                        return

        # --- EXCLUSIVE MECHANIC: MEWTWO'S PSYCHIC VORTEX ---
        if self.pet_name.lower().replace("_", "").replace("-", "") == "mewtwo" and self.mewtwo_cooldown == 0 and self.current_state in ['idle', 'walking'] and not self.is_global_mechanic_active():
            if random.randint(1, 1000) <= 8: 
                if getattr(self, 'get_all_pets', None):
                    
                    # FIX: Exclude critical transition states (spawns and evolutions) to avoid parallel loops
                    excluded_states = ['exiting', 'dragged', 'mewtwo_victim', 'evolving_start', 'evolving_finish', 'spawning_wild', 'despawning_wild', 'falling_pokeball', 'falling_egg']
                    valid_targets = [p for p in self.get_all_pets() if p != self and p.current_state not in excluded_states and not getattr(p, 'is_egg', False)]
                    
                    if valid_targets:
                        self.mewtwo_cooldown = 108000 # 1.5 hours
                        self.current_state = 'mewtwo_channeling'
                        self.mewtwo_timer = 0
                        self.mewtwo_targets = valid_targets
                        self.manage_tk_aura(self.canvas, self.size_w, self.size_h, True)
                        
                        for i, target in enumerate(valid_targets):
                            
                            # STRUCTURAL FIX: Exhaustive cleanup of links from other mechanics to prevent victims from escaping
                            if target.current_state.startswith('dark_'):
                                target.cancel_dark_arts()
                                
                            elif target.current_state == 'tk_channeling':
                                target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
                                if getattr(target, 'tk_target', None):
                                    if getattr(target.tk_target, 'current_state', '') in ['tk_controlled', 'tk_lifted']:
                                        
                                        # FIX: Force particle cleanup of the floating object/victim
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
                                
                            # FIX: Cancel Ghosts' Glitch
                            if getattr(target, 'is_glitching', False):
                                target.is_glitching = False
                                target.has_genesect_glitch = False
                                target.glitch_teleports_left = 0
                                target.glitch_cooldown = 12000
                                
                            # Visual render cleanup
                            target.canvas.itemconfig(target.canvas_image_id, state='normal')
                            target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
                            try: target.window.attributes('-alpha', 1.0)
                            except: pass
                            
                            # Finally, the orbital abduction
                            target.current_state = 'mewtwo_victim'
                            target.mewtwo_master = self
                            target.mewtwo_orbit_offset = (i * (2 * math.pi / len(valid_targets))) 
                            target.mewtwo_activation_tick = i * 33 
                            target.anchored_hwnd = None 
                            
                        self.schedule_loop(50, self.physics_loop)
                        return
                    
        # --- MECHANIC: FAIRY TYPE PACIFICATION ---
        if getattr(self, 'fairy_aura', False) and self.current_state in ['idle', 'walking']:
            if getattr(self, 'get_all_pets', None):
                for other in self.get_all_pets():
                    # If it detects a fighting Pokemon and enters its Hitbox (distance less than the sprite width)
                    if other != self and other.current_state == 'attacking' and abs(self.x - other.x) < self.size_w and abs(self.y - other.y) < self.size_h:
                        
                        # Remotely pacify its opponent and apply gravity
                        opponent = getattr(other, 'attack_target', None)
                        if opponent:
                            opponent.current_state = 'thrown' if getattr(opponent, 'is_flying', False) else 'falling'
                            opponent.v_y_velocity = 0.0
                            opponent.v_x_velocity = 0.0
                            opponent.attack_cooldown = 12000
                            opponent.attack_target = None
                            opponent.show_fairy_sparkles_vfx()
                            
                        # Pacify primary target and apply gravity
                        other.current_state = 'thrown' if getattr(other, 'is_flying', False) else 'falling'
                        other.v_y_velocity = 0.0
                        other.v_x_velocity = 0.0
                        other.attack_cooldown = 12000
                        other.attack_target = None
                        other.show_fairy_sparkles_vfx()
                        
                        self.show_fairy_sparkles_vfx()
                        
                        # The fairy does a small happy jump upon stopping the fight
                        self.current_state = 'jumping_arc'
                        self.jump_target_y = self.floor_y
                        self.v_y_velocity = 3.0 if getattr(self, 'gravity_inverted', False) else -3.0
                        self.schedule_loop(50, self.physics_loop)
                        return
        
        # --- MECHANIC: DARK TYPE AMBUSH ---
        if getattr(self, 'dark_arts', False) and self.dark_cooldown == 0 and self.current_state in ['idle', 'walking'] and getattr(self, 'climbing_surface', 'floor') == 'floor':
            if random.randint(1, 1000) <= 10: 
                if getattr(self, 'get_all_pets', None):
                    # FIX: Inject strict height restriction "abs(p.y - self.y) < 80"
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

        # --- MECHANIC: GROUND TYPE DIG ---
        if getattr(self, 'can_dig', False) and self.dig_cooldown == 0 and self.current_state in ['idle', 'walking'] and getattr(self, 'climbing_surface', 'floor') == 'floor':
            if random.randint(1, 1000) <= 10: 
                self.current_state = 'digging_in'
                self.dig_step = 0
                self.dig_timer = random.randint(200, 400) # Time underground
                self.dig_cooldown = 12000 # 10 real minutes
                self.schedule_loop(50, self.physics_loop)
                return
        
        # --- MECHANIC: WATER BUBBLE ---
        if getattr(self, 'bubble_blower', False) and self.bubble_cooldown == 0 and self.current_state in ['idle', 'walking']:
            if random.randint(1, 1000) <= 8: 
                if getattr(self, 'get_all_pets', None):
                    # FIX: Greatly reduced range (150px horizontal, 60px vertical)
                    valid_targets = [p for p in self.get_all_pets() if p != self and p.current_state in ['idle', 'walking'] and not getattr(p, 'is_egg', False) and abs(p.x - self.x) < 150 and abs(p.y - self.y) < 60]
                    if valid_targets:
                        target = random.choice(valid_targets)
                        self.bubble_cooldown = 12000 
                        
                        # We fire the animated projectile from our geometric center
                        def on_bubble_hit(hit_target):
                            # STRUCTURAL FIX: Prevent FSM corruption if the bubble hits a Dark type
                            if getattr(hit_target, 'current_state', '').startswith('dark_'):
                                hit_target.cancel_dark_arts()
                            elif getattr(hit_target, 'current_state', '').startswith('mewtwo_'):
                                hit_target.cancel_mewtwo_arts()
                            elif getattr(hit_target, 'current_state', '') in ['hooh_channeling', 'panic_run']:
                                hit_target.cancel_hooh_arts()
                            elif getattr(hit_target, 'current_state', '') in ['lugia_channeling', 'lugia_dash']:
                                hit_target.cancel_lugia_arts()
                                
                            hit_target.current_state = 'bubbled'
                            hit_target.bubble_max_time = random.randint(130, 200) 
                            hit_target.bubble_timer = hit_target.bubble_max_time
                            hit_target.anchored_hwnd = None
                        
                        BubbleProjectile(self.window.master, self.base_dir, self.x + self.size_w/2, self.y + self.size_h/2, target, on_bubble_hit)
                        
                        # The Pokemon throwing the bubble makes a small summoning jump
                        self.current_state = 'jumping_arc'
                        self.jump_target_y = self.floor_y
                        self.v_y_velocity = 4.0 if getattr(self, 'gravity_inverted', False) else -4.0
                        self.schedule_loop(50, self.physics_loop)
                        return

        # --- INTERFERENCE PHASE FOR GHOSTS (SCREEN WRAP) ---
        if getattr(self, 'can_screen_wrap', False) and self.glitch_cooldown == 0 and not getattr(self, 'is_glitching', False):
            if random.randint(1, 1000) <= 10: # Approx 1% probability
                self.is_glitching = True
                self.glitch_teleports_left = random.randint(4, 10) # Number of chaotic teleports
                try: self.window.attributes('-alpha', 0.5) # Lowers opacity to 50%
                except: pass
                self.schedule_glitch_teleport()
        
        if getattr(self, 'telekinetic', False) and self.tk_cooldown == 0 and self.current_state in ['idle', 'walking']:
            if random.randint(1, 1000) <= 10: # Probability of activating powers
                target = None
                if self.game_controller:
                    # 1. Prioritize attracting Berries (Range of 400 -> 800)
                    for b in getattr(self.game_controller, 'active_berries', []):
                        if b.current_state not in ['exiting', 'tk_controlled'] and abs(b.x - self.x) < 800:
                            target = b; break
                    # 2. If there are no berries, look for the Toy (Range of 400 -> 800)
                    if not target and getattr(self.game_controller, 'active_toy', None):
                        t = self.game_controller.active_toy
                        if t.current_state not in ['exiting', 'tk_controlled'] and abs(t.x - self.x) < 800:
                            target = t
                # 3. If there are no objects, lift another nearby Pokemon (Range of 250 -> 500)
                if not target and getattr(self, 'get_all_pets', None):
                    valid_pets = [p for p in self.get_all_pets() if p != self and p.current_state in ['idle', 'walking'] and not getattr(p, 'is_egg', False) and abs(p.x - self.x) < 500]
                    if valid_pets: target = random.choice(valid_pets)
                    
                if target:
                    self.current_state = 'tk_channeling'
                    self.tk_target = target
                    self.tk_timer = random.randint(100, 166) # Levitate for 3-5 seconds
                    
                    self.tk_orbit_started = False # FIX: Forces orbital phase reset
                    
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
                    # Inverted floor = Bottom edge of the window
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
            
            # FLYERS FIX: Maintain 180 degree rotation if gravity is inverted
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
                            # OVERFLOW MARGIN (The Pokemon exits completely before teleporting)
                            if self.x <= self.v_x - self.size_w:
                                self.x = self.v_x + self.v_width
                                if random.randint(1, 100) <= 25: self.is_facing_right = True 
                            elif self.x >= self.v_x + self.v_width:
                                self.x = self.v_x - self.size_w
                                if random.randint(1, 100) <= 25: self.is_facing_right = False
                        else:
                            # NORMAL SOLID LIMIT
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

        # === INTERACTION WITH BERRIES (RADIAL AND DYNAMIC) ===
        if self.current_state in ['idle', 'walking'] and not self.is_wild and not getattr(self, 'is_egg', False) and self.game_controller:
            for berry in getattr(self.game_controller, 'active_berries', []):
                # We remove the 'dragged' restriction. If the berry exists, it is edible.
                if berry.current_state != 'exiting':
                    # We calculate the real geometric centers of both objects
                    my_cx = self.x + self.size_w / 2
                    my_cy = self.y + self.size_h / 2
                    berry_cx = berry.x + berry.size / 2
                    berry_cy = berry.y + berry.size / 2
                    
                    # Euclidean distance
                    dist = math.sqrt((my_cx - berry_cx)**2 + (my_cy - berry_cy)**2)
                    
                    # Generous hitbox (60% of Pokemon size)
                    if dist < max(self.size_w, self.size_h) * 0.6:
                        self.current_state = 'eating'
                        self.eating_timer = 30
                        self.interaction_target = berry
                        berry.destroy() # Destroys the berry visually
                        self.show_heart_vfx() # Triggers the pixelated heart
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
            # FIX: Ensure escape after bouncing
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
            # Restore the sprite to its original and perfect center
            self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
            if getattr(self, 'is_overflow', False):
                self.current_state = 'walking_away'
                self.is_facing_right = True
            else:
                self.current_state = 'idle'
        else:
            # Shift the image a few random pixels to simulate the tremor
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
    
    def swap_form_generic(self, target_species, vfx_colors=None):
        self.pet_name = target_species
        self.pet_data["species"] = target_species
        from entities.animator import DesktopPetAnimator
        anim_dir = os.path.join(self.base_dir, "game_env", "pets", target_species)
        if self.is_shiny and os.path.exists(os.path.join(anim_dir, "shiny")):
            anim_dir = os.path.join(anim_dir, "shiny")
        
        config_path = os.path.join(self.base_dir, "game_env", "pets", target_species, "config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                new_config = json.load(f)
                self.config = new_config
                physics = new_config.get("physics", {})
                self.is_flying = physics.get("is_flying", False)
                self.can_screen_wrap = physics.get("can_screen_wrap", False)
                self.can_teleport = physics.get("can_teleport", False)
                self.heavy_fall = physics.get("heavy_fall", False)
                self.telekinetic = physics.get("telekinetic", False)
                self.bubble_blower = physics.get("bubble_blower", False) 
                self.can_dig = physics.get("can_dig", False)
                self.fairy_aura = physics.get("fairy_aura", False)
                self.dark_arts = physics.get("dark_arts", False)
                self.aggressive = physics.get("aggressive", False)
        except Exception:
            pass

        if getattr(self, 'is_flying', False):
            fly_height_pct = self.pet_data.get("flying_height_pct", 3.0)
            max_offset = self.v_height - self.size_h
            self.target_offset_y = int(max_offset * (fly_height_pct / 100.0))
            self.target_floor_y = (self.v_y + self.v_height) - self.size_h - self.target_offset_y
        
        self.default_floor_y = (self.v_y + self.v_height) - self.size_h - self.offset_y
        if not getattr(self, 'is_flying', False):
            self.target_floor_y = self.default_floor_y

        bw = getattr(self, 'base_size_w', self.size_w)
        bh = getattr(self, 'base_size_h', self.size_h)
        self.animator = DesktopPetAnimator(
            self.canvas, self.config.get("images", {}), 
            (bw, bh), (bw, bh), anim_dir
        )
        
        if self.current_state != 'dragged':
            self.current_state = 'falling'
        self.play_shiny_sound()
        if vfx_colors:
            self.show_alter_form_vfx(vfx_colors)
        else:
            self.show_alter_form_vfx()

    def manual_alter_form(self):
        name = self.pet_name.lower().replace("_", "").replace("-", "")
        
        form_mappings = {
            "giratina1": ("giratina", ["#FF0000", "#FFD700", "#555555"]),
            "giratina": ("giratina_1", ["#FF0000", "#FFD700", "#555555"]),
            "shaymin1": ("shaymin", ["#FFFFFF", "#00FF00", "#AAFF00"]),
            "zacian1": ("zacian", ["#1E90FF", "#00BFFF", "#FF69B4"]),
            "zamazenta1": ("zamazenta", ["#DC143C", "#4169E1", "#FFD700"]),
            "meloetta": ("meloetta_1", ["#FF0000", "#FF5555", "#FF8888"]),
            "meloetta1": ("meloetta", ["#00FF00", "#55FF55", "#88FF88"]),
            "thundurus": ("thundurus_1", ["#4169E1", "#800080", "#FFFFFF"]),
            "thundurus1": ("thundurus", ["#4169E1", "#800080", "#FFFFFF"]),
            "tornadus": ("tornadus_1", ["#228B22", "#800080", "#FFFFFF"]),
            "tornadus1": ("tornadus", ["#228B22", "#800080", "#FFFFFF"]),
            "landorus": ("landorus_1", ["#FF8C00", "#DC143C", "#FFFFFF"]),
            "landorus1": ("landorus", ["#FF8C00", "#DC143C", "#FFFFFF"]),
            "enamorus": ("enamorus_1", ["#FF69B4", "#DC143C", "#FFFFFF"]),
            "enamorus1": ("enamorus", ["#FF69B4", "#DC143C", "#FFFFFF"]),
            "dialga": ("dialga_1", ["#00008B", "#00BFFF", "#C0C0C0"]),
            "dialga1": ("dialga", ["#00008B", "#00BFFF", "#C0C0C0"]),
            "palkia": ("palkia_1", ["#F5F5F5", "#DA70D6", "#8B008B"]),
            "palkia1": ("palkia", ["#F5F5F5", "#DA70D6", "#8B008B"]),
            "keldeo1": ("keldeo", ["#FFFDD0", "#FFA500", "#87CEEB"]),
            "hoopa": ("hoopa_1", ["#800080", "#FFD700", "#FF1493"]),
            "hoopa1": ("hoopa", ["#800080", "#FFD700", "#FF1493"]),
            "urshifu": ("urshifu_1", ["#2F4F4F", "#F8F8FF", "#DC143C"]),
            "urshifu1": ("urshifu", ["#2F4F4F", "#F8F8FF", "#DC143C"]),
            "terapagos1": ("terapagos", ["#0000FF", "#00FFFF", "#FFFFFF"]),
            "deoxys": ("deoxys_1", ["#FF4500", "#00FFFF", "#FFA500"]),
            "deoxys1": ("deoxys_2", ["#FF4500", "#00FFFF", "#FFA500"]),
            "deoxys2": ("deoxys_3", ["#FF4500", "#00FFFF", "#FFA500"]),
            "deoxys3": ("deoxys", ["#FF4500", "#00FFFF", "#FFA500"])
        }
        
        if name in form_mappings:
            target_form, colors = form_mappings[name]
            
            # Special case for Giratina mechanics
            if name in ["giratina", "giratina1"]:
                self.swap_giratina_form(target_form)
                if self.current_state != 'dragged':
                    self.current_state = 'ascending' if name == "giratina" else 'falling'
                self.play_shiny_sound()
                self.show_alter_form_vfx(colors)
            
            # Special case for Shaymin mechanics (needs to cancel arts)
            elif name == "shaymin1":
                if hasattr(self, 'cancel_shaymin_arts'):
                    self.cancel_shaymin_arts()
                self.swap_form_generic(target_form, colors)
                
            elif name in ["hoopa", "hoopa1"]:
                if name == "hoopa":
                    self.size_w = int(self.size_w * 2.0)
                    self.size_h = int(self.size_h * 2.0)
                else:
                    self.size_w = int(self.size_w / 2.0)
                    self.size_h = int(self.size_h / 2.0)
                    
                self.base_size_w = self.size_w
                self.base_size_h = self.size_h
                try:
                    self.window.geometry(f"{self.size_w}x{self.size_h}+{int(self.x)}+{int(self.y)}")
                    self.canvas.config(width=self.size_w, height=self.size_h)
                    self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
                except: pass
                
                self.swap_form_generic(target_form, colors)
                
            else:
                self.swap_form_generic(target_form, colors)

    def show_alter_form_vfx(self, colors=None):
        if getattr(self, 'current_state', 'exiting') == 'exiting': return
        
        particles = []
        cx = self.size_w // 2
        cy = self.size_h // 2
        
        # Generate between 15 and 20 particles for the explosion
        for _ in range(random.randint(15, 20)):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(6.0, 12.0) # Strong initial explosion
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            size = random.choice([3, 4, 5])
            if not colors:
                colors = ["#000000", "#1A1A1A", "#4B0082", "#2C003E", "#8A2BE2"]
            color = random.choice(colors)
            
            pid = self.canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline=color, tags="vfx_alter")
            particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': random.randint(15, 25)})
            
        def animate_explosion():
            if getattr(self, 'current_state', 'exiting') == 'exiting': return
            alive = 0
            for p in particles:
                if p['life'] > 0:
                    self.canvas.move(p['id'], p['vx'], p['vy'])
                    # Air friction (0.85) for a fast and kinetic braking effect
                    p['vx'] *= 0.85 
                    p['vy'] *= 0.85
                    p['life'] -= 1
                    alive += 1
                elif p['life'] == 0:
                    self.canvas.delete(p['id'])
                    p['life'] = -1
                    
            if alive > 0:
                self.window.after(30, animate_explosion)
                
        animate_explosion()

    def is_global_mechanic_active(self, ignore_lati=False, ignore_lake=False, ignore_sea_guardians=False, ignore_victini=False, ignore_genesect=False, ignore_meloetta=False):
        # 1. If there is no pet system linked, there is no blocking
        if not getattr(self, 'get_all_pets', None):
            return False
            
        # 2. Strict list of "Master" states (excludes victim states to avoid false positives)
        blocking_states = [
            'mewtwo_channeling', 
            'hooh_channeling', 
            'kyogre_channeling',
            'groudon_channeling', 
            'lugia_channeling', 'lugia_dash',
            'rayquaza_channeling', 
            'dialga_channeling', 
            'palkia_channeling',
            'giratina_channeling', 'giratina_dash_prep', 'giratina_dash', 'giratina_wait_reappear',
            'zekrom_channeling',
            'reshiram_channeling',
            'heatran_jump_down',
            'heatran_channeling',
            'heatran_positioning',
            'heatran_storm',
            'heatran_falling',
            'kyurem_channeling',
            'xerneas_channeling',
            'yveltal_channeling',
            'yveltal_channeling',
            'zygarde_channeling',
            'zygarde50_channeling',
            'lunala_channeling',
            'solgaleo_channeling',
            'necrozma_channeling',
            'zacian_channeling',
            'zamazenta_channeling',
            'eternatus_channeling',
            'koraidon_sprint',
            'koraidon_climb',
            'koraidon_leap',
            'koraidon_apex',
            'koraidon_dive',
            'koraidon_impact',
            'miraidon_absorb',
            'miraidon_descent',
            'miraidon_dash',
            'miraidon_impact',
            'bird_channeling',
            'mew_channeling',
            'mew_bounce',
            'beast_dismount',
            'beast_channeling',
            'beast_roar',
            'beast_dash',
            'beast_wait_clear',
            'genie_channeling',
            'genie_shoot',
            'genie_wait_tornado',
            'genie_finish',
            'tapu_channeling',
            'tapu_positioning',
            'tapu_active',
            'celebi_channeling',
            'celebi_wait',
            'celebi_freeze',
            'celebi_revert_flight',
            'regi_approach',
            'regi_strike',
            'regigigas_approach',
            'regigigas_grab',
            'jirachi_channeling',
            'jirachi_vanished',
            'jirachi_flyby',
            'darkrai_shadow_walk',
            'darkrai_channeling',
            'darkrai_aoe',
            'cresselia_channeling',
            'cresselia_ascension',
            'cresselia_aurora',
            'lati_channeling',
            'lati_spiral',
            'lati_dash_wait',
            'lati_dash',
            'lati_return',
            'deoxys_channeling',
            'deoxys_ascend',
            'deoxys_wait',
            'deoxys_meteor',
            'deoxys_emerge',
            'lake_channeling',
            'lake_rotating',
            'shaymin_summon',
            'shaymin_sky_jump',
            'sea_guardian_absorb',
            'sea_guardian_big_jump',
            'sea_guardian_jump',
            'sea_guardian_wait',
            'victini_channeling',
            'victini_forming_v',
            'victini_flying',
            'victini_dash',
            'victini_impact',
            'genesect_walk',
            'genesect_channeling',
            'genesect_laser',
            'meloetta_aria_charge',
            'meloetta_aria_teleport',
            'meloetta_aria_float',
            'meloetta_aria_wait',
            'meloetta_aria_fire',
            'meloetta_pirouette_walk',
            'meloetta_pirouette_dance',
            'meloetta_pirouette_fire'
        ]
        
        if ignore_meloetta:
            blocking_states = [s for s in blocking_states if not s.startswith('meloetta_')]
            
        if ignore_genesect:
            blocking_states = [s for s in blocking_states if not s.startswith('genesect_')]

        if ignore_victini:
            blocking_states = [s for s in blocking_states if not s.startswith('victini_')]

        if ignore_sea_guardians:
            blocking_states = [s for s in blocking_states if not s.startswith('sea_guardian_')]

        if ignore_lati:
            blocking_states = [s for s in blocking_states if not s.startswith('lati_')]
            
        if ignore_lake:
            blocking_states = [s for s in blocking_states if not s.startswith('lake_')]
            
        if hasattr(self, 'krd_phase'):
            return True
        
        # 3. Structural scan
        for p in self.get_all_pets():
            if p != self and p.current_state in blocking_states:
                return True
        return False
        
    def get_random_valid_target(self):
        valid = [p for p in self.get_all_pets() if p != self and p.current_state not in ['exiting', 'despawning_wild', 'spawning_wild', 'falling_pokeball', 'falling_egg', 'celebi_frozen']]
        return random.choice(valid) if valid else None

    def start_hoopa_mechanic(self):
        self.hoopa_cooldown = 108000
        import mechanics.hoopa
        mechanics.hoopa.init_hoopa_arts(self)
        self.cancel_hoopa_arts = lambda: mechanics.hoopa.cancel_hoopa_arts(self)

    def start_volcanion_mechanic(self):
        self.volcanion_cooldown = 108000
        import mechanics.volcanion
        mechanics.volcanion.init_volcanion_arts(self)
        self.cancel_volcanion_arts = lambda: mechanics.volcanion.cancel_volcanion_arts(self)
        self.schedule_loop(50, self.physics_loop)
