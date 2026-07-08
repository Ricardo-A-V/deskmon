import os

# --- STRICT SUPPRESSION OF PYGAME TERMINAL ---
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

try:
    import win32gui
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    print("[!] Warning: Missing 'pywin32' library. Run 'pip install pywin32'.")

try:
    from pypresence import Presence
    HAS_DISCORD = True
except ImportError:
    HAS_DISCORD = False
    print("[!] Warning: Missing 'pypresence' library. Run 'pip install pypresence' to enable Discord RPC.")

from core.engine import GameController

if __name__ == '__main__':
    try:
        import pygame
        pygame.mixer.init()
    except ImportError:
        pass
    
    GameController()