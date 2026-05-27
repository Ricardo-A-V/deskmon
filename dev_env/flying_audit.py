import os
import json
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

class FlightTinder(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Auditoría de Vuelo (Solo Voladores)")
        self.geometry("450x550")
        self.configure(bg="#2c3e50")
        self.pets_dir = "../game_env/pets"
        self.queue = []
        self.current_pet = None

        # UI Elements
        self.lbl_title = tk.Label(self, text="Cargando base de datos...", font=("Arial", 16, "bold"), bg="#2c3e50", fg="white")
        self.lbl_title.pack(pady=20)

        self.canvas = tk.Canvas(self, width=192, height=192, bg="#34495e", highlightthickness=0)
        self.canvas.pack(pady=10)
        self.img_on_canvas = self.canvas.create_image(96, 96, anchor=tk.CENTER)

        self.lbl_status = tk.Label(self, text="", font=("Arial", 12), bg="#2c3e50", fg="#bdc3c7")
        self.lbl_status.pack(pady=5)

        self.lbl_counter = tk.Label(self, text="", font=("Arial", 10), bg="#2c3e50", fg="#7f8c8d")
        self.lbl_counter.pack(pady=5)

        self.btn_frame = tk.Frame(self, bg="#2c3e50")
        self.btn_frame.pack(pady=20)

        self.btn_no = tk.Button(self.btn_frame, text="NO VUELA\n(Bajar al suelo)", bg="#e74c3c", fg="white", 
                                font=("Arial", 12, "bold"), width=15, height=3, 
                                command=lambda: self.process_swipe(False))
        self.btn_no.pack(side=tk.LEFT, padx=15)

        self.btn_yes = tk.Button(self.btn_frame, text="VUELA\n(Mantener)", bg="#2ecc71", fg="white", 
                                 font=("Arial", 12, "bold"), width=15, height=3, 
                                 command=lambda: self.process_swipe(True))
        self.btn_yes.pack(side=tk.LEFT, padx=15)

        # Iniciar carga
        self.after(100, self.build_queue)

    def build_queue(self):
        if not os.path.exists(self.pets_dir):
            messagebox.showerror("Error", f"No se encuentra el directorio: {self.pets_dir}")
            self.destroy()
            return

        for folder in sorted(os.listdir(self.pets_dir)):
            config_path = os.path.join(self.pets_dir, folder, "config.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        continue
                        
                # Filtro estricto: Añadir solo si el JSON dice que vuela
                if data.get("physics", {}).get("is_flying", False):
                    self.queue.append({
                        "folder": folder,
                        "config_path": config_path,
                        "data": data
                    })

        self.load_next()

    def load_next(self):
        if not self.queue:
            self.lbl_title.config(text="Auditoría Completada")
            self.lbl_status.config(text="No quedan más Pokémon por revisar.")
            self.lbl_counter.config(text="0 restantes")
            self.canvas.delete("all")
            self.btn_yes.config(state=tk.DISABLED)
            self.btn_no.config(state=tk.DISABLED)
            return

        self.current_pet = self.queue.pop(0)
        data = self.current_pet["data"]
        
        display_name = data.get("display_name", self.current_pet["folder"].title())
        self.lbl_title.config(text=display_name)
        self.lbl_status.config(text="Actualmente: VOLANDO")
        self.lbl_counter.config(text=f"{len(self.queue) + 1} restantes")

        # Cargar el sprite original para que juzgues visualmente
        idle_img_path = os.path.join(self.pets_dir, self.current_pet["folder"], "idle_0.png")
        if os.path.exists(idle_img_path):
            try:
                img = Image.open(idle_img_path).convert("RGBA")
                # Escalar x3 con Nearest Neighbor para no difuminar el pixel art
                img = img.resize((img.width * 3, img.height * 3), Image.NEAREST)
                self.tk_img = ImageTk.PhotoImage(img)
                self.canvas.itemconfig(self.img_on_canvas, image=self.tk_img)
            except Exception:
                self.canvas.delete("all")
                self.canvas.create_text(96, 96, text="Error al cargar\nla imagen", fill="white")
        else:
            self.canvas.delete("all")
            self.canvas.create_text(96, 96, text="Imagen\nno encontrada", fill="white")

    def process_swipe(self, set_flying):
        if not self.current_pet: return

        data = self.current_pet["data"]
        
        # Reescribimos el JSON solo si decides cambiar su estado al suelo
        if data["physics"].get("is_flying") != set_flying:
            data["physics"]["is_flying"] = set_flying
            data["physics"]["offset_y"] = 40 if set_flying else 5

            try:
                with open(self.current_pet["config_path"], "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
            except Exception as e:
                print(f"Error crítico al guardar {self.current_pet['folder']}: {e}")

        self.load_next()

if __name__ == "__main__":
    app = FlightTinder()
    app.mainloop()