from core.engine import GameController

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import sys
import random
import math
import time
import uuid
import threading 

try:
    import win32gui
    import win32con
    import win32process
    import win32api
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    print("[!] Advertencia: Falta la librería 'pywin32'. Ejecuta 'pip install pywin32'.")

# --- SUPRESIÓN ESTRICTA DE LA TERMINAL DE PYGAME ---
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

try:
    from pypresence import Presence
    HAS_DISCORD = True
except ImportError:
    HAS_DISCORD = False
    print("[!] Advertencia: Falta la librería 'pypresence'. Ejecuta 'pip install pypresence' para habilitar Discord RPC.")

import threading # Obligatorio para evitar micro-tirones en Tkinter



from PIL import Image, ImageTk, ImageOps

if __name__ == '__main__':
    try:
        import pygame
        pygame.mixer.init()
    except: pass
    
    GameController()