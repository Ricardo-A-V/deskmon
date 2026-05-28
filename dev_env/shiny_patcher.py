import os
from PIL import Image

# Configuración de rutas relativas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_SHINY_DIR = os.path.join(BASE_DIR, "raw_shinys")
PETS_DIR = os.path.join(BASE_DIR, "game_env", "pets")

def process_shiny_sprites():
    if not os.path.exists(RAW_SHINY_DIR):
        print(f"[!] Error crítico: El directorio de entrada '{RAW_SHINY_DIR}' no existe.")
        print("Crea la carpeta e introduce los spritesheets descargados.")
        return

    if not os.path.exists(PETS_DIR):
        print(f"[!] Error crítico: No se encuentra la base de datos principal '{PETS_DIR}'.")
        return

    processed_count = 0
    skipped_count = 0

    for filename in os.listdir(RAW_SHINY_DIR):
        if not filename.endswith(".png"):
            continue
            
        # Normalización de la cadena de texto para evitar fallos de Case-Sensitivity
        species_name = filename.replace(".png", "").lower()
        base_pet_dir = os.path.join(PETS_DIR, species_name)
        
        # Validación Estructural: Evita inyectar shinys de Pokémon no instalados
        if not os.path.exists(base_pet_dir):
            print(f"[-] Omitiendo '{species_name}': La especie base no existe en el sistema.")
            skipped_count += 1
            continue
            
        shiny_out_dir = os.path.join(base_pet_dir, "shiny")
        os.makedirs(shiny_out_dir, exist_ok=True)
        
        raw_path = os.path.join(RAW_SHINY_DIR, filename)
        try:
            # Renderizado en memoria y cálculo matemático de la cuadrícula
            sheet = Image.open(raw_path).convert("RGBA")
            w, h = sheet.size
            frame_w = w // 4
            frame_h = h // 4
            
            for col in range(4):
                # Extracción Fila 0 (Idle)
                box_idle = (col * frame_w, 0, (col + 1) * frame_w, frame_h)
                sheet.crop(box_idle).save(os.path.join(shiny_out_dir, f"idle_{col}.png"))
                
                # Extracción Fila 1 (Walk Left)
                box_left = (col * frame_w, frame_h, (col + 1) * frame_w, frame_h * 2)
                sheet.crop(box_left).save(os.path.join(shiny_out_dir, f"walk_l_{col}.png"))
                
                # Extracción Fila 2 (Walk Right)
                box_right = (col * frame_w, frame_h * 2, (col + 1) * frame_w, frame_h * 3)
                sheet.crop(box_right).save(os.path.join(shiny_out_dir, f"walk_r_{col}.png"))
                
            print(f"[+] Procesado con éxito: {species_name.capitalize()} (Genotipo Shiny inyectado)")
            processed_count += 1
        except Exception as e:
            print(f"[!] Error procesando la matriz gráfica de {species_name}: {e}")

    print("-" * 40)
    print(f"OPERACIÓN FINALIZADA. Procesados: {processed_count} | Omitidos: {skipped_count}")

if __name__ == "__main__":
    process_shiny_sprites()