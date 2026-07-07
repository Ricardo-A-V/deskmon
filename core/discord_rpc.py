import threading
try:
    from pypresence import Presence
    HAS_DISCORD = True
except ImportError:
    HAS_DISCORD = False
try:
    import win32gui
except ImportError:
    pass

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