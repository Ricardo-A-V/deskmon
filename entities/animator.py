import time
import os
import sys
import random
from PIL import Image, ImageOps, ImageTk

# --- MOTOR DE ANIMACIÓN ---
class DesktopPetAnimator:
    def __init__(self, canvas_widget, config_img, size_idle, size_walk, pet_dir):
        self.canvas = canvas_widget
        self.current_frame_index = 0
        self.last_state = None
        self.tk_image_ref = None
        self.last_frame_time = time.time()

        self.invert_x_axis = config_img.get("invert_x_axis", False)
        self.idle_is_animated = config_img.get("idle_is_animated", True)
        self.directional_walk = config_img.get("directional_walk", True)
        self.fix_idle_direction = config_img.get("fix_idle_direction", True)

        scaling_filter = Image.Resampling.NEAREST 

        def clean_alpha(image):
            img = image.convert("RGBA")
            r, g, b, a = img.split()
            a = a.point(lambda p: 255 if p > 127 else 0) 
            return Image.merge("RGBA", (r, g, b, a))

        def load_frame(filename, size):
            path = os.path.join(pet_dir, filename)
            return clean_alpha(Image.open(path)).resize(size, scaling_filter)

        try:
            self.frames_idle = []
            if self.idle_is_animated:
                pref = config_img.get("idle_prefix", "idle_")
                suf = config_img.get("idle_suffix", ".png")
                for i in range(config_img.get("idle_frames", 4)):
                    self.frames_idle.append(load_frame(f"{pref}{i}{suf}", size_idle))
            
            suf = config_img.get("walk_suffix", ".png")
            if self.directional_walk:
                self.frames_walk_right = []
                pref_r = config_img.get("walk_right_prefix", "walk_r_")
                for i in range(config_img.get("walk_right_frames", 4)):
                    self.frames_walk_right.append(load_frame(f"{pref_r}{i}{suf}", size_walk))

                self.frames_walk_left = []
                pref_l = config_img.get("walk_left_prefix", "walk_l_")
                for i in range(config_img.get("walk_left_frames", 4)):
                    self.frames_walk_left.append(load_frame(f"{pref_l}{i}{suf}", size_walk))
                
        except FileNotFoundError as e:
            print(f"Error cargando assets: {e}")
            sys.exit(1)

    def update_animation(self, state, facing_right, canvas_image_id, animate_idle, fps_ms, blend_factor=0.0, rotation_angle=0, is_glitching=False, is_darkened=False):
        # FIX: Congelar el motor visual durante eventos estáticos
        if state in ['exiting', 'landing_shake', 'dark_victim_frozen', 'dark_victim_hidden']: return
        
        current_time = time.time()
        elapsed_time_ms = (current_time - self.last_frame_time) * 1000
        state_changed = state != self.last_state

        if not state_changed and elapsed_time_ms < fps_ms:
            return 

        if state_changed:
            self.current_frame_index = 0
            self.last_state = state

        self.last_frame_time = current_time
        disable_mirror = False
        raw_image = None  

        render_state = state
        # FIX: deluge_float movido aquí para forzar la animación de caída/flote
        # FIX VISUAL: groudon_channeling movido a 'idle' para forzar sprite frontal
        if render_state in ['falling', 'evolving_start', 'evolving_finish', 'ascending', 'falling_pokeball', 'falling_egg', 'dragged', 'thrown', 'falling_legendary', 'legendary_bounce', 'climbing', 'eating', 'tk_channeling', 'tk_lifted', 'tk_controlled', 'bubbled', 'deluge_float', 'groudon_channeling']:
            render_state = 'idle'
            
        elif render_state in ['walking_away', 'jumping_arc', 'socializing', 'attacking', 'hooh_channeling', 'panic_run', 'kyogre_channeling', 'groudon_channeling', 'lugia_channeling', 'lugia_dash', 'rayquaza_channeling', 'rayquaza_cyclone_victim']:
            render_state = 'walking'

        if render_state == 'walking':
            if self.directional_walk:
                disable_mirror = True
                active_matrix = self.frames_walk_right if facing_right else self.frames_walk_left
                if self.current_frame_index >= len(active_matrix): self.current_frame_index = 0
                
                raw_image = active_matrix[self.current_frame_index]
                self.current_frame_index = (self.current_frame_index + 1) % len(active_matrix)
            
        elif render_state == 'idle':
            if self.idle_is_animated:
                if self.current_frame_index >= len(self.frames_idle): self.current_frame_index = 0
                
                raw_image = self.frames_idle[self.current_frame_index]
                self.current_frame_index = (self.current_frame_index + 1) % len(self.frames_idle)

        if raw_image is None: raw_image = self.frames_idle[0]

        if disable_mirror:
            processed_image = raw_image
        else:
            effective_dir = True if (render_state == 'idle' and self.fix_idle_direction and state not in ['socializing', 'attacking', 'eating']) else facing_right
            should_mirror = effective_dir if self.invert_x_axis else (not effective_dir)
            processed_image = ImageOps.mirror(raw_image) if should_mirror else raw_image

        if rotation_angle != 0:
            processed_image = processed_image.rotate(rotation_angle, expand=False, resample=Image.NEAREST)

        if blend_factor > 0.0:
            white_layer = Image.new("RGBA", processed_image.size, (255, 255, 255, 255))
            white_layer.putalpha(processed_image.split()[3]) 
            processed_image = Image.blend(processed_image, white_layer, blend_factor)

        # --- NUEVO: EFECTO DE INTERFERENCIA (GLITCH VECTORIAL) ---
        # Alterna entre el sprite normal y el roto basándose en los milisegundos del reloj
        if is_glitching and int(time.time() * 15) % 2 == 0:
            w, h = processed_image.size
            glitched = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            strip_h = max(1, h // 5) # Corta el sprite en 5 láminas horizontales
            
            for i in range(5):
                box = (0, i * strip_h, w, min(h, (i + 1) * strip_h))
                strip = processed_image.crop(box)
                offset_x = random.choice([-12, -6, 6, 12]) # Las desplaza aleatoriamente
                glitched.paste(strip, (offset_x, i * strip_h))
                
            processed_image = glitched

        # --- NUEVO: MODO SINIESTRO (Silueta) ---
        if is_darkened:
            black_layer = Image.new("RGBA", processed_image.size, (0, 0, 0, 255))
            black_layer.putalpha(processed_image.split()[3])
            # Se mezcla al 85% para mantener ligeros matices del cuerpo
            processed_image = Image.blend(processed_image, black_layer, 0.85)

        self.tk_image_ref = ImageTk.PhotoImage(processed_image)
        self.canvas.itemconfig(canvas_image_id, image=self.tk_image_ref)
