# Deskmon 💻🐾

Deskmon is an interactive desktop Pokémon engine (Desktop Pets) developed in Python using the native `Tkinter` interface. The program generates autonomous Pokémon that interact with your screen's boundaries, simulating a living ecosystem over your Windows applications.

## Structural Features of the Pokémon Ecosystem

- **Physics & Locomotion Engine:** Dynamic collisions with the Windows taskbar. Pokémon can walk, remain in idle states, or fly with mathematical oscillation depending on their biology.
- **Bill's PC (State Manager):** Centralized interface to store your captures, spawn up to 6 simultaneous Pokémon onto the desktop, and manage your team.
- **RPG Progression & Evolution Trees:** Asynchronous experience (XP) gain based on active screen time (Strict Lv.100 cap). If the Pokémon reaches the required level, it will execute a visual metamorphosis into its next evolutionary stage.
- **Genetics & Nature Mechanics:**
  - **Wild Encounters:** Procedural generation of wild Pokémon that spawn from tall grass or clouds and despawn if not caught in time.
  - **Shiny Genotype:** Strict 1% mathematical probability calculated at the exact moment of entity generation, featuring exclusive sound effects.
  - **Breeding:** Pokémon that have reached their final evolutionary stage have a chance to lay Eggs. These will hatch into the base stage of the species after a randomized timer, with an increased probability (20%) of inheriting the Shiny gene.
- **Item Management:** Support for equipping an _Everstone_ from the PC, mathematically locking the evolution of any species.

## Environment Requirements

To run or compile the source code, a configured Python environment is required:

- Python 3.10 or higher.
- `Pillow` (PIL) library for Alpha-channel sprite rendering: `pip install Pillow`
- `pygame` library for the audio subsystem and sound effects: `pip install pygame`
- _(Optional)_ `PyInstaller` if you wish to compile the binary executable: `pip install pyinstaller`

## Directory Architecture

The graphical and audio database is the core of the engine. Any new Pokémon species or resource must strictly follow this immutable structure:

    /game_env
      ├── /pets
      │    └── /pikachu
      │         ├── config.json       # Mathematical logic (XP, evolution, speed)
      │         ├── idle_0.png        # Spritesheets (Standard frames)
      │         └── /shiny            # (Optional) Shiny variant spritesheets
      ├── /sounds                     # Global sound effects (.wav)
      └── /ui                         # Static UI (Grass, Clouds, Egg, and Pokéballs)

## Build Pipeline

The project includes an autonomous script to generate the distribution binary. You must never upload the `.exe` file directly to the source code repository.

To generate a clean Windows executable:

1.  Open the terminal in the root directory.
2.  Run: `python build_game.py`
3.  The engine will audit the code, inject the native icon, package the environment into a single `main.exe` in the root directory, and purge residual caches automatically.

## Trainer Controls

- **Right Click (Wild Pokémon):** Throws a Pokéball to attempt capturing the wild Pokémon. If successful, it will be registered in your PC.
- **Right Click (Owned Pokémon):** Recalls your Pokémon from the desktop and returns it to the PC box.
- **Double Left Click:** Opens the PC and auto-selects the clicked Pokémon to manage its options (e.g., giving/taking the _Everstone_).
