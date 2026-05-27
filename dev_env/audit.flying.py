import os
import json
import tkinter as tk
from tkinter import messagebox

class FlyingManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pokemon Flight Manager")
        self.geometry("400x600")
        self.pets_dir = "../game_env/pets"
        
        self.label = tk.Label(self, text="Click to Toggle Flight Status", font=("Arial", 12, "bold"))
        self.label.pack(pady=10)

        self.listbox = tk.Listbox(self, width=50)
        self.listbox.pack(pady=10, fill=tk.BOTH, expand=True)

        self.btn_frame = tk.Frame(self)
        self.btn_frame.pack(pady=10)

        self.btn_yes = tk.Button(self.btn_frame, text="Set Flying", bg="green", fg="white", command=lambda: self.toggle_flight(True))
        self.btn_yes.pack(side=tk.LEFT, padx=5)

        self.btn_no = tk.Button(self.btn_frame, text="Set Grounded", bg="red", fg="white", command=lambda: self.toggle_flight(False))
        self.btn_no.pack(side=tk.LEFT, padx=5)

        self.load_pets()

    def load_pets(self):
        self.pet_data = []
        for folder in sorted(os.listdir(self.pets_dir)):
            config_path = os.path.join(self.pets_dir, folder, "config.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    is_flying = data.get("physics", {}).get("is_flying", False)
                    self.pet_data.append({"folder": folder, "data": data, "config_path": config_path})
                    status = "[FLYING]" if is_flying else "[GROUND]"
                    self.listbox.insert(tk.END, f"{status} {data.get('display_name')}")

    def toggle_flight(self, state):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Select", "Please select a Pokemon first.")
            return
        
        idx = selection[0]
        pet = self.pet_data[idx]
        
        # Update JSON data
        pet["data"]["physics"]["is_flying"] = state
        pet["data"]["physics"]["offset_y"] = 40 if state else 5
        
        with open(pet["config_path"], "w", encoding="utf-8") as f:
            json.dump(pet["data"], f, indent=4)
            
        self.listbox.delete(idx)
        status = "[FLYING]" if state else "[GROUND]"
        self.listbox.insert(idx, f"{status} {pet['data'].get('display_name')}")
        self.listbox.select_set(idx)

if __name__ == "__main__":
    app = FlyingManager()
    app.mainloop()