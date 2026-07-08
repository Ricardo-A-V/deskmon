import os
import shutil
import subprocess
import sys

# Structural Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT = os.path.join(BASE_DIR, "main.py")
SPEC_FILE = os.path.join(BASE_DIR, "Deskmon.spec")
BUILD_DIR = os.path.join(BASE_DIR, "build")
DIST_DIR = os.path.join(BASE_DIR, "dist")

EXE_SOURCE = os.path.join(DIST_DIR, "Deskmon.exe")
EXE_DESTINATION = os.path.join(BASE_DIR, "Deskmon.exe")

ICON_PATH = os.path.join(BASE_DIR, "game_env", "ui", "icon.ico")

def create_desktop_shortcut(exe_path, icon_path):
    """Generates a native shortcut using the Windows WScript subsystem."""
    print("[+] Phase 5: Generating desktop shortcut...")
    
    # Embedded Visual Basic script to avoid external library dependencies
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
        subprocess.check_call(["cscript", "//nologo", vbs_path])
    except Exception as e:
        print(f"[!] Failed to create shortcut: {e}")
    finally:
        if os.path.exists(vbs_path):
            os.remove(vbs_path)

def compile_and_clean():
    if not os.path.exists(MAIN_SCRIPT):
        print(f"[!] Critical Error: '{MAIN_SCRIPT}' not found in the base directory.")
        sys.exit(1)

    print("[+] Phase 1: Starting strict compilation (PyInstaller)...")
    
    command = [sys.executable, "-m", "PyInstaller", "--windowed", "--onefile", "--clean", "--name=Deskmon"]
    
    if os.path.exists(ICON_PATH):
        command.append(f"--icon={ICON_PATH}")
        print(f"    - Icon detected and injected into the compilation contract.")
    else:
        print(f"    [!] Warning: '{ICON_PATH}' not found. Compiling without custom icon.")
        
    command.append("main.py")
    
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Critical compilation failure. Error: {e}")
        sys.exit(1)

    print("\n[+] Phase 2: Verifying artifact integrity...")
    if not os.path.exists(EXE_SOURCE):
        print("[!] Error: Compilation finished, but 'Deskmon.exe' binary was not generated.")
        sys.exit(1)

    print("[+] Phase 3: Extracting executable to the root directory...")
    if os.path.exists(EXE_DESTINATION):
        os.remove(EXE_DESTINATION)
    shutil.move(EXE_SOURCE, BASE_DIR)

    print("[+] Phase 4: Purging cache and compiler residues...")
    if os.path.exists(BUILD_DIR): shutil.rmtree(BUILD_DIR)
    if os.path.exists(DIST_DIR): shutil.rmtree(DIST_DIR)
    if os.path.exists(SPEC_FILE): os.remove(SPEC_FILE)

    if os.path.exists(ICON_PATH):
        create_desktop_shortcut(EXE_DESTINATION, ICON_PATH)

    print("-" * 50)
    print("[+] SUCCESSFUL OPERATION: 'Deskmon.exe' generated and environment purged.")

if __name__ == "__main__":
    compile_and_clean()