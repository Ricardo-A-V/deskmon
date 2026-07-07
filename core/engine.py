import os
import sys
import json
import uuid
import random
import tkinter as tk
from tkinter import ttk, messagebox
from core.save_system import SaveManager
from core.discord_rpc import DiscordRPC
from entities.pet import DesktopPet
from entities.interactables import InteractiveBerry, InteractivePokeball
from ui.menus import StarterSelectionWindow

# --- CONTROLADOR CENTRAL DEL JUEGO ---
class GameController:
    def __init__(self):
        self.save_mgr = SaveManager()
        self.active_instances = [] 
        self.wild_instances = []
        self.overflow_instances = [] 
        self.active_berries = [] 
        
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
            base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
            base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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