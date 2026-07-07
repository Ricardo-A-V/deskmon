import os
import json
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

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