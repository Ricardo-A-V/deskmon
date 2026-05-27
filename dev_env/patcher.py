import os
import json
import requests
import time

# Mapa de corrección exhaustivo y validado contra la PokeAPI oficial
NAME_ALIASES = {
    # Correcciones manuales base
    "hakamoo": "hakamo-o",
    "jangmoo": "jangmo-o", 
    "kommoo": "kommo-o",
    "hooh": "ho-oh",
    "porygonz": "porygon-z",
    "typenull": "type-null", # <--- Corregido a la nomenclatura de tu sistema de archivos
    "tapukoko": "tapu-koko",
    "tapulele": "tapu-lele",
    "tapubulu": "tapu-bulu",
    "tapufini": "tapu-fini",
    "mrmime": "mr-mime",
    "mrrime": "mr-rime",
    "mimejr": "mime-jr",
    "nidoranfe": "nidoran-f",
    "nidoranma": "nidoran-m",
    "mabostiff": "mabosstiff", 
    "orthworms": "orthworm",
    "bombirdiers": "bombirdier",
    "polthcageist": "poltchageist",
    
    # Paradojas (Generación IX)
    "greattusk": "great-tusk",
    "screamtail": "scream-tail",
    "brutebonnet": "brute-bonnet",
    "fluttermane": "flutter-mane",
    "slitherwing": "slither-wing",
    "sandyshocks": "sandy-shocks",
    "roaringmoon": "roaring-moon",
    "irontreads": "iron-treads",
    "ironbundle": "iron-bundle",
    "ironhands": "iron-hands",
    "ironjugulis": "iron-jugulis",
    "ironmoth": "iron-moth",
    "ironthorns": "iron-thorns",
    "ironvaliant": "iron-valiant",
    "walkingwake": "walking-wake",
    "ironleaves": "iron-leaves",
    "gougingfire": "gouging-fire",
    "ragingbolt": "raging-bolt",
    "ironboulder": "iron-boulder",
    "ironcrown": "iron-crown",
    
    # Leyendas de la Ruina y excepciones de puntuación
    "tinglu": "ting-lu",
    "chienpao": "chien-pao",
    "wochien": "wo-chien",
    "chiyu": "chi-yu",
    "farfetchd": "farfetchd",
    "sirfetchd": "sirfetchd"
}

def patch_pokemon(folder_name):
    print(f"[*] Evaluando: {folder_name}...")
    
    # Segmentación lógica: Aísla el nombre biológico de variantes visuales (ej. unown_1 -> unown)
    base_name = folder_name.lower().split('_')[0]
    api_name = NAME_ALIASES.get(base_name, base_name)
    
    url_species = f"https://pokeapi.co/api/v2/pokemon-species/{api_name}/"
    
    try:
        # Mitigación de bloqueos (Rate Limiting) de PokeAPI
        time.sleep(1.2)
        response = requests.get(url_species, timeout=15)
        
        if response.status_code != 200:
            print(f"    [!] Error de API: {api_name} no encontrado en la base de datos (HTTP {response.status_code}).")
            return

        data_species = response.json()
        
        # Lógica de cálculo de evolución
        chain_url = data_species["evolution_chain"]["url"]
        chain_data = requests.get(chain_url, timeout=10).json()["chain"]
        
        def find_evolution(node, target_name, depth=0):
            if node["species"]["name"] == target_name:
                if node["evolves_to"]:
                    evolutions_list = [n["species"]["name"] for n in node["evolves_to"]]
                    return evolutions_list, 35 # Nivel estandarizado para ramas reparadas
                return ["none"], 99
            for next_node in node["evolves_to"]:
                res_names, res_lvl = find_evolution(next_node, target_name, depth + 1)
                if res_names != ["none"]: 
                    return res_names, res_lvl
            return ["none"], 99

        evolves_to_list, evolution_level = find_evolution(chain_data, api_name)

        # Resolución dinámica de la URL de biología (evita errores 404 en variantes)
        varieties = data_species.get("varieties", [])
        default_variety = next((v for v in varieties if v.get("is_default")), None)
        url_bio = default_variety["pokemon"]["url"] if default_variety else f"https://pokeapi.co/api/v2/pokemon/{api_name}/"
        
        # Extracción de físicas
        data_bio = requests.get(url_bio, timeout=10).json()
        height_dm = data_bio.get("height", 10)
        
        if height_dm < 5: size = 48
        elif height_dm < 15: size = 64
        elif height_dm < 25: size = 80
        else: size = 96
            
        base_speed = next((s['base_stat'] for s in data_bio['stats'] if s['stat']['name'] == 'speed'), 50)
        movement_speed = max(1, min(4, round(base_speed / 30)))

        # Inyección directa en el JSON existente
        config_path = f"../game_env/pets/{folder_name}/config.json"
        
        with open(config_path, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data["rpg_data"]["evolves_to"] = evolves_to_list
            data["rpg_data"]["evolution_level"] = evolution_level
            data["physics"]["size"] = size
            data["physics"]["movement_speed"] = movement_speed
            
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
            
        print(f"    [+] Reparación exitosa: {folder_name} procesado como {api_name}.")

    except requests.exceptions.RequestException as req_err:
        print(f"    [!] Fallo de red en {folder_name}: {req_err}")
    except Exception as e:
        print(f"    [!] Error de estructura procesando {folder_name}: {e}")

def run_patcher():
    pets_dir = "../game_env/pets"
    
    if not os.path.exists(pets_dir):
        print(f"Error crítico: El directorio de destino {pets_dir} no existe.")
        return
        
    for folder in sorted(os.listdir(pets_dir)):
        config_path = os.path.join(pets_dir, folder, "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                # Puerta lógica: solo interviene si los datos son los del failsafe
                if data.get("rpg_data", {}).get("evolution_level") == 36:
                    patch_pokemon(folder)
            except json.JSONDecodeError:
                print(f"[!] JSON corrupto detectado en la carpeta: {folder}")

if __name__ == "__main__":
    run_patcher()