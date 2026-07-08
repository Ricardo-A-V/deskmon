import os
import sys
import json
import uuid
import random
from tkinter import messagebox

class SaveManager:
    def __init__(self, save_file="save_data.json"):
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
                        p.setdefault("last_evolution_level", p.get("level", 1))
                        p.setdefault("flying_height_pct", 3.0)
                        p.setdefault("xp_boost_expiry", 0)
                            
                    data.setdefault("active_pets", [])
                    data.setdefault("settings", {"allow_wild": True, "allow_breeding": True})
                    
                    if "flying_height_pct" in data.get("settings", {}):
                        del data["settings"]["flying_height_pct"]
                        
                    return data
            except json.JSONDecodeError:
                messagebox.showerror("Critical Error", "save_data.json is corrupted. Creating a new save file.")
        
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
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass