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
            print(f"[-] Error connecting to Discord: {e}")
            self.connected = False

    def set_target(self, pet):
        # Ignore eggs so as not to ruin the surprise
        if getattr(pet, 'is_egg', False): return
        self.target_pet = pet

    def update_loop(self, root):
        if self.connected and self.target_pet and self.target_pet.window.winfo_exists():
            pet = self.target_pet
            
            # 1. Parse Name and Level
            name = pet.pet_data['species'].capitalize()
            if getattr(pet, 'is_shiny', False):
                name += " ★"
            level = pet.pet_data['level']

            # 2. Parse Activity and Environment (OS Awareness)
            window_title = ""
            if getattr(pet, 'anchored_hwnd', None):
                try:
                    raw_title = win32gui.GetWindowText(pet.anchored_hwnd)
                    if raw_title:
                        # Extract main program name
                        parts = raw_title.split('-')
                        window_title = parts[-1].strip()
                        if len(window_title) > 20:
                            window_title = window_title[:17] + "..."
                except Exception:
                    pass

            is_climbing = getattr(pet, 'is_climbing', False) and getattr(pet, 'climbing_surface', 'floor') != 'floor'
            
            if getattr(pet, 'is_flying', False):
                activity = f"Floating above {window_title}" if window_title else "Floating around the screen"
            elif is_climbing:
                activity = f"Climbing {window_title}" if window_title else "Climbing the edges"
            elif window_title:
                if pet.current_state == 'idle':
                    activity = f"Resting on {window_title}"
                else:
                    activity = f"Exploring {window_title}"
            else:
                if pet.current_state == 'idle': activity = "Resting on desktop"
                elif pet.current_state == 'jumping_arc': activity = "Jumping around"
                elif pet.current_state == 'falling': activity = "Falling into the void"
                elif pet.current_state == 'attacking': activity = "Fighting another pokemon"
                elif pet.current_state == 'socializing': activity = "Chatting with another pokemon"
                elif pet.current_state == 'eating': activity = "Eating a berry"
                else: activity = "Strolling the desktop"

            # 3. Asynchronous Payload Sending
            def send_payload():
                try:
                    self.RPC.update(
                        state=activity,
                        details=f"Lv. {level} | {name}",
                        large_image="app_logo", 
                        large_text="Deskmon",
                        small_image="shiny_star" if getattr(pet, 'is_shiny', False) else None,
                        small_text=name if getattr(pet, 'is_shiny', False) else None
                    )
                except Exception:
                    self.connected = False 
            
            # Fire in a background thread to prevent network wait from freezing animation at 60FPS
            threading.Thread(target=send_payload, daemon=True).start()
        
        # Refresh every 15 seconds (Strict Discord API Limit)
        root.after(15000, lambda: self.update_loop(root))