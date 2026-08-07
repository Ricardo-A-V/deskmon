import os
import re
import json
import time
import urllib.request
import urllib.error

# Maps standard names to PokeAPI specific endpoint structures.
# Required because PokeAPI uses hyphenated suffixes for alternate forms,
# and direct queries for base names (like 'urshifu') will fail or return incorrect IDs.
API_OVERRIDES = {
    "type: null": "type-null",
    "tapu koko": "tapu-koko",
    "tapu lele": "tapu-lele",
    "tapu bulu": "tapu-bulu",
    "tapu fini": "tapu-fini",
    "walking wake": "walking-wake",
    "iron leaves": "iron-leaves",
    "gouging fire": "gouging-fire",
    "raging bolt": "raging-bolt",
    "iron boulder": "iron-boulder",
    "iron crown": "iron-crown",
    "deoxys": "deoxys-normal",
    "giratina": "giratina-altered",
    "shaymin": "shaymin-land",
    "tornadus": "tornadus-incarnate",
    "thundurus": "thundurus-incarnate",
    "landorus": "landorus-incarnate",
    "keldeo": "keldeo-ordinary",
    "meloetta": "meloetta-aria",
    "zygarde": "zygarde-50",
    "urshifu": "urshifu-single-strike",
    "enamorus": "enamorus-incarnate"
}

ROSTER = [
    "Articuno", "Zapdos", "Moltres", "Mewtwo", "Mew",
    "Raikou", "Entei", "Suicune", "Lugia", "Ho-Oh", "Celebi",
    "Regirock", "Regice", "Registeel", "Latias", "Latios", "Kyogre", "Groudon", "Rayquaza", "Jirachi", "Deoxys",
    "Uxie", "Mesprit", "Azelf", "Dialga", "Palkia", "Heatran", "Regigigas", "Giratina", "Cresselia", "Phione", "Manaphy", "Darkrai", "Shaymin", "Arceus",
    "Victini", "Cobalion", "Terrakion", "Virizion", "Tornadus", "Thundurus", "Reshiram", "Zekrom", "Landorus", "Kyurem", "Keldeo", "Meloetta", "Genesect",
    "Xerneas", "Yveltal", "Zygarde", "Diancie", "Hoopa", "Volcanion",
    "Type: Null", "Silvally", "Tapu Koko", "Tapu Lele", "Tapu Bulu", "Tapu Fini", "Cosmog", "Cosmoem", "Solgaleo", "Lunala", "Nihilego", "Buzzwole", "Pheromosa", "Xurkitree", "Celesteela", "Kartana", "Guzzlord", "Necrozma", "Magearna", "Marshadow", "Poipole", "Naganadel", "Stakataka", "Blacephalon", "Zeraora", "Meltan", "Melmetal",
    "Zacian", "Zamazenta", "Eternatus", "Kubfu", "Urshifu", "Zarude", "Regieleki", "Regidrago", "Glastrier", "Spectrier", "Calyrex", "Enamorus",
    "Wo-Chien", "Chien-Pao", "Ting-Lu", "Chi-Yu", "Koraidon", "Miraidon", "Walking Wake", "Iron Leaves", 
    "Okidogi", "Munkidori", "Fezandipiti", 
    "Ogerpon", "Gouging Fire", "Raging Bolt", "Iron Boulder", "Iron Crown", "Terapagos", "Pecharunt"
]

def format_filename(name):
    # Matches the exact Regex /[:\s]/g used in the React frontend
    # Ensures the downloaded file string aligns with the dynamic asset loader
    return re.sub(r'[:\s]', '', name.lower()) + '.png'

def get_pokemon_id(name):
    lower_name = name.lower()
    query_name = API_OVERRIDES.get(lower_name, lower_name)
    
    url = f"https://pokeapi.co/api/v2/pokemon/{query_name}"
    
    # User-Agent spoofing is necessary because standard urllib headers are often blacklisted by CDNs protecting public APIs
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            # Returns the National Dex integer for zero-padding logic later
            return data['id']
    except Exception as e:
        print(f"[-] Failed to fetch metadata for {name} ({query_name}): {e}")
        return None

def download_image(pokemon_id, filename):
    padded_id = str(pokemon_id).zfill(3)
    
    # Primary Source: Pokemon.com CMS. High resolution, transparent backgrounds.
    primary_url = f"https://assets.pokemon.com/assets/cms2/img/pokedex/full/{padded_id}.png"
    # Fallback Source: PokeAPI raw GitHub repository. 
    # Used when Pokemon.com's Cloudflare WAF blocks automated requests or for alternate forms that break the CMS numbering.
    fallback_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{pokemon_id}.png"
    
    req = urllib.request.Request(primary_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    
    try:
        with urllib.request.urlopen(req) as response:
            with open(filename, 'wb') as f:
                f.write(response.read())
        return True
    except urllib.error.HTTPError as e:
        print(f"    [!] Pokemon.com rejected request ({e.code}). Attempting GitHub fallback...")
        
        fallback_req = urllib.request.Request(fallback_url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(fallback_req) as response:
                with open(filename, 'wb') as f:
                    f.write(response.read())
            return True
        except Exception as fallback_e:
            print(f"    [-] Fallback failed: {fallback_e}")
            return False

def main():
    target_dir = os.path.join(os.getcwd(), 'public')
    
    # Guards against execution in the wrong directory context, preventing asset clutter in root folders
    if not os.path.exists(target_dir):
        print("[!] Target directory 'public' not found. Creating it.")
        os.makedirs(target_dir, exist_ok=True)
    
    print(f"[*] Starting sequential download of {len(ROSTER)} entities to '{target_dir}'...")
    
    for name in ROSTER:
        filename = format_filename(name)
        filepath = os.path.join(target_dir, filename)
        
        if os.path.exists(filepath):
            print(f"[~] Skipping {name} ({filename}) - File already exists.")
            continue
            
        print(f"[*] Fetching {name}...")
        
        poke_id = get_pokemon_id(name)
        if not poke_id:
            continue
            
        success = download_image(poke_id, filepath)
        
        if success:
            print(f"    [+] Saved as {filename}")
        
        # Artificial delay to avoid rate limiting and IP blacklisting from the REST API
        time.sleep(0.5)
        
    print("[*] Operation complete.")

if __name__ == '__main__':
    main()
