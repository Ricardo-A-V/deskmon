import os
import shutil
import subprocess
import sys

# --- RUTAS ESTRUCTURALES ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT = os.path.join(BASE_DIR, "main.py")
SPEC_FILE = os.path.join(BASE_DIR, "Deskmon.spec")
BUILD_DIR = os.path.join(BASE_DIR, "build")
DIST_DIR = os.path.join(BASE_DIR, "dist")

EXE_SOURCE = os.path.join(DIST_DIR, "Deskmon.exe")
EXE_DESTINATION = os.path.join(BASE_DIR, "Deskmon.exe")

# [NUEVO] RUTA ESTRICTA DEL ICONO
ICON_PATH = os.path.join(BASE_DIR, "game_env", "ui", "icon.ico")

def create_desktop_shortcut(exe_path, icon_path):
    """Genera un acceso directo nativo usando el subsistema WScript de Windows."""
    print("[+] Fase 5: Generando acceso directo en el Escritorio...")
    
    # Script visual basic incrustado para evitar dependencias de librerías externas
    vbs_script = f"""
    Set ws = CreateObject("WScript.Shell")
    desktopPath = ws.SpecialFolders("Desktop")
    Set shortcut = ws.CreateShortcut(desktopPath & "\\Deskmon.lnk")
    shortcut.TargetPath = "{exe_path}"
    shortcut.WorkingDirectory = "{os.path.dirname(exe_path)}"
    shortcut.IconLocation = "{icon_path}"
    shortcut.Save
    """
    
    vbs_path = os.path.join(BASE_DIR, "temp_shortcut.vbs")
    with open(vbs_path, "w", encoding="utf-8") as f:
        f.write(vbs_script)
        
    try:
        # Ejecuta el script de Windows de forma silenciosa
        subprocess.check_call(["cscript", "//nologo", vbs_path])
    except Exception as e:
        print(f"[!] Fallo al crear el acceso directo: {e}")
    finally:
        # Purga el script temporal
        if os.path.exists(vbs_path):
            os.remove(vbs_path)

def compile_and_clean():
    if not os.path.exists(MAIN_SCRIPT):
        print(f"[!] Error Crítico: No se encuentra '{MAIN_SCRIPT}' en el directorio base.")
        sys.exit(1)

    print("[+] Fase 1: Iniciando compilación estricta (PyInstaller)...")
    
    # Forzamos el nombre de salida a 'Deskmon'
    command = [sys.executable, "-m", "PyInstaller", "--windowed", "--onefile", "--clean", "--name=Deskmon"]
    
    # Inyección estructural del icono en el binario
    if os.path.exists(ICON_PATH):
        command.append(f"--icon={ICON_PATH}")
        print(f"    - Icono detectado e inyectado en el contrato de compilación.")
    else:
        print(f"    [!] Advertencia: No se encontró '{ICON_PATH}'. Compilando sin icono personalizado.")
        
    command.append("main.py")
    
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Fallo crítico en la compilación. Error: {e}")
        sys.exit(1)

    print("\n[+] Fase 2: Verificando integridad del artefacto...")
    if not os.path.exists(EXE_SOURCE):
        print("[!] Error: Compilación finalizada, pero no se generó el binario 'Deskmon.exe'.")
        sys.exit(1)

    print("[+] Fase 3: Extrayendo ejecutable al directorio raíz...")
    if os.path.exists(EXE_DESTINATION):
        os.remove(EXE_DESTINATION)
    shutil.move(EXE_SOURCE, BASE_DIR)

    print("[+] Fase 4: Purgando caché y residuos del compilador...")
    if os.path.exists(BUILD_DIR): shutil.rmtree(BUILD_DIR)
    if os.path.exists(DIST_DIR): shutil.rmtree(DIST_DIR)
    if os.path.exists(SPEC_FILE): os.remove(SPEC_FILE)

    # Invocación de la creación del acceso directo (solo si el icono existe)
    if os.path.exists(ICON_PATH):
        create_desktop_shortcut(EXE_DESTINATION, ICON_PATH)

    print("-" * 50)
    print("[+] OPERACIÓN EXITOSA: 'Deskmon.exe' generado y entorno purgado.")

if __name__ == "__main__":
    compile_and_clean()