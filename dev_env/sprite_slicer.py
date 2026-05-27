import os
import json
import requests
from PIL import Image
import time

def fetch_pokemon_data(pokemon_name):
    """
    Queries /pokemon-species/ to get RPG data, then dynamically extracts
    the exact /pokemon/ URL for the default form to avoid 404 errors on variants.
    """
    print(f"Fetching biological and RPG data for {pokemon_name}...")
    url_species = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_name}/"
    
    try:
        # --- 1. RPG Data (Species Endpoint) ---
        response_species = requests.get(url_species, timeout=10)
        if response_species.status_code != 200:
            raise ValueError(f"Species data not found for {pokemon_name}")
            
        data_species = response_species.json()
        
        capture_rate = data_species.get("capture_rate", 45)
        spawn_rate = round(capture_rate / 255.0, 3)
        
        chain_url = data_species["evolution_chain"]["url"]
        chain_data = requests.get(chain_url, timeout=10).json()["chain"]
        
        def find_evolution(node, target_name, depth=0):
            if node["species"]["name"] == target_name:
                if node["evolves_to"]:
                    evolutions_list = []
                    fallback_level = 20 if depth == 0 else 35
                    determined_level = fallback_level
                    
                    for next_evo in node["evolves_to"]:
                        evolutions_list.append(next_evo["species"]["name"])
                        if determined_level == fallback_level:
                            evo_details = next_evo["evolution_details"][0] if next_evo.get("evolution_details") else {}
                            min_level = evo_details.get("min_level")
                            if min_level:
                                determined_level = min_level
                                
                    return evolutions_list, determined_level
                return ["none"], 99
            
            for next_node in node["evolves_to"]:
                res_names, res_lvl = find_evolution(next_node, target_name, depth + 1)
                if res_names != ["none"]: 
                    return res_names, res_lvl
            return ["none"], 99
            
        evolves_to_list, evolution_level = find_evolution(chain_data, pokemon_name)

        # --- 2. Dynamic Biology Endpoint Resolution ---
        # Instead of guessing the URL, we ask the API for the default variety's exact URL
        varieties = data_species.get("varieties", [])
        default_variety = next((v for v in varieties if v.get("is_default")), None)
        
        if default_variety:
            url_biology = default_variety["pokemon"]["url"]
        else:
            url_biology = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}/"

        response_bio = requests.get(url_biology, timeout=10)
        data_bio = response_bio.json()

        # --- 3. Physical Traits Calculation ---
        height_dm = data_bio.get("height", 10)
        if height_dm < 5: size = 48
        elif height_dm < 15: size = 64
        elif height_dm < 25: size = 80
        else: size = 96

        base_speed = next((s['base_stat'] for s in data_bio['stats'] if s['stat']['name'] == 'speed'), 50)
        movement_speed = max(1, min(4, round(base_speed / 30)))

        return {
            "rpg_data": {
                "evolves_to": evolves_to_list,
                "evolution_level": evolution_level,
                "spawn_rate": spawn_rate,
                "spawn_conditions": ["day"] 
            },
            "physics": {
                "size": size,
                "movement_speed": movement_speed
            }
        }

    except Exception as e:
        print(f"[!] API Error for {pokemon_name}: {e}. Applying balanced failsafe limits.")
        return {
            "rpg_data": {
                "evolves_to": ["none"],
                "evolution_level": 36, 
                "spawn_rate": 0.05, 
                "spawn_conditions": ["day"]
            },
            "physics": {"size": 64, "movement_speed": 2}
        }


def process_sprite_batch():
    input_dir = "raw_sprites"
    output_dir = "../game_env/pets"

    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    files = [f for f in os.listdir(input_dir) if f.endswith(".png")]

    for file in files:
        raw_name = os.path.splitext(file)[0]
        folder_name = raw_name.lower()
        display_name = raw_name.replace("_", " ").title() 
        api_query_name = folder_name.split('_')[0]
        
        img_path = os.path.join(input_dir, file)
        output_folder = os.path.join(output_dir, folder_name)

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        try:
            img = Image.open(img_path).convert("RGBA")
        except Exception:
            continue

        frame_width = img.width // 4
        frame_height = img.height // 4

        def save_frame(col, row, file_name):
            x1, y1 = col * frame_width, row * frame_height
            x2, y2 = x1 + frame_width, y1 + frame_height
            img.crop((x1, y1, x2, y2)).save(os.path.join(output_folder, file_name))

        for i in range(4): save_frame(i, 0, f"idle_{i}.png")
        for i in range(4): save_frame(i, 1, f"walk_l_{i}.png")
        for i in range(4): save_frame(i, 2, f"walk_r_{i}.png")
            
        # --- HARD-LIMIT OPTICAL SCANNING ---
        idle_0_path = os.path.join(output_folder, "idle_0.png")
        try:
            alpha_channel = Image.open(idle_0_path).split()[3]
            bbox = alpha_channel.getbbox() 
            
            if bbox:
                lowest_pixel_y = bbox[3]
                gap = frame_height - lowest_pixel_y
                
                # Strict evaluation based on observed pixel gaps
                # Ground <= 5 pixels | Flying >= 6 pixels
                if gap >= 6:
                    is_flying = True
                    offset_y = 40
                else:
                    is_flying = False
                    offset_y = 5
            else:
                is_flying = False
                offset_y = 5
        except Exception as e:
            print(f"Optical scan failed for {display_name}, defaulting to ground. {e}")
            is_flying = False
            offset_y = 5

        time.sleep(1) # Espera 1 segundo para no saturar la API
        fetched_data = fetch_pokemon_data(api_query_name)
        
        physics_data = fetched_data["physics"]
        physics_data["is_flying"] = is_flying
        physics_data["offset_y"] = offset_y
            
        config_data = {
            "display_name": display_name,
            "physics": physics_data,
            "images": {
                "idle_is_animated": True,
                "idle_prefix": "idle_",
                "idle_frames": 4,
                "idle_suffix": ".png",
                "directional_walk": True,
                "walk_right_prefix": "walk_r_",
                "walk_right_frames": 4,
                "walk_left_prefix": "walk_l_",
                "walk_left_frames": 4,
                "walk_suffix": ".png",
                "frame_rate_active": 120,
                "frame_rate_idle": 200,
                "fix_idle_direction": True,
                "invert_x_axis": False
            },
            "rpg_data": fetched_data["rpg_data"]
        }

        with open(os.path.join(output_folder, "config.json"), "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)

        print(f"[*] Successfully processed: {display_name} (Flying: {is_flying})\n")

if __name__ == "__main__":
    process_sprite_batch()