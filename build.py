import os
import platform
import shutil
import subprocess

def get_choice(prompt, options):
    while True:
        print(prompt)
        for i, opt in enumerate(options, 1):
            print(f"  [{i}] {opt}")
        choice = input("Select an option (number): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print("Invalid choice.\n")

def get_checkboxes(prompt, options):
    while True:
        print(prompt + " (e.g., type '1,2' for multiple, or '1' for one)")
        for i, opt in enumerate(options, 1):
            print(f"  [{i}] {opt}")
        selection = input("Select (comma-separated numbers): ").strip()
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(",") if x.strip().isdigit()]
            valid_selections = [options[i] for i in indices if 0 <= i < len(options)]
            if valid_selections:
                return valid_selections
        except Exception:
            pass
        print("Invalid selection.\n")

def build_wizard():
    project_name = os.path.basename(os.getcwd()).lower().replace(" ", "-")
    
    version = input("Enter the release version (e.g., 1.0.6): v").strip()
    version_str = f"v{version}" if not version.startswith('v') else version

    platforms = get_checkboxes("Choose a platform for release", ["Windows", "Linux", "MacOS"])
    
    formats = get_checkboxes("Enter formats to generate?", ["Standalone Binary (.exe / raw binary)", "Compressed Archive (.zip / .tar.gz)"])

    is_complex = os.path.exists("src") or os.path.exists("app_assets")
    if is_complex:
        print("Found multi-folder project structure. Extra asset folders will be bundled.")
    else:
        print("Found single-file script layout.")

    # Base build requirements
    current_os = platform.system().lower()
    os.makedirs("downloads", exist_ok=True)
    arch = "x64" 

    for target in platforms:
        target_lower = "macos" if target == "MacOS" else target.lower()
        
        if target_lower == "windows" and current_os != "windows" and "Standalone Binary (.exe / raw binary)" in formats:
            print(f"Skipping native Windows .exe compiler because you are currently running on {platform.system()}.")
            continue
        if target_lower == "linux" and current_os != "linux" and "Standalone Binary (.exe / raw binary)" in formats:
            print(f"Skipping native Linux binary compiler because you are currently running on {platform.system()}.")
            continue

        print(f"\nProcessing builds for {target}...")

        dist_dir = f"temp_dist_{target_lower}"
        app_dir = os.path.join(dist_dir, project_name)
        os.makedirs(app_dir, exist_ok=True)

        if "Standalone Binary (.exe / raw binary)" in formats or is_complex:
            print(f"🔨 Compiling binary files via PyInstaller...")
            build_type = "--onedir" if is_complex else "--onefile"
            subprocess.run(["pyinstaller", build_type, "main.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if is_complex:
            extra_folders = ["src", "app_assets"]
            for folder in extra_folders:
                if os.path.exists(folder):
                    shutil.copytree(folder, os.path.join(app_dir, folder), dirs_exist_ok=True)
            if os.path.exists("dist/main"):
                shutil.copytree("dist/main", app_dir, dirs_exist_ok=True)

        if "Standalone Binary (.exe / raw binary)" in formats and not is_complex:
            ext = ".exe" if target_lower == "windows" else ""
            final_bin_name = f"{project_name}_{version_str}_{target_lower}_{arch}{ext}"
            src_file = "dist/main.exe" if current_os == "windows" else "dist/main"
            
            if os.path.exists(src_file):
                shutil.copy(src_file, os.path.join("downloads", final_bin_name))
                print(f"Generated Standalone: downloads/{final_bin_name}")

        if "Compressed Archive (.zip / .tar.gz)" in formats:
            ext = ".tar.gz" if target_lower == "linux" else ".zip"
            archive_format = "gztar" if target_lower == "linux" else "zip"
            final_archive_name = f"{project_name}_{version_str}_{target_lower}_{arch}"
            
            if not is_complex:
                ext_bin = ".exe" if target_lower == "windows" else ""
                src_file = "dist/main.exe" if current_os == "windows" else "dist/main"
                if os.path.exists(src_file):
                    shutil.copy(src_file, os.path.join(app_dir, f"{project_name}{ext_bin}"))

            shutil.make_archive(
                base_name=os.path.join("downloads", final_archive_name),
                format=archive_format,
                root_dir=dist_dir,
                base_dir=project_name
            )
            print(f"Generated Archive: downloads/{final_archive_name}{ext}")

        shutil.rmtree("build", ignore_errors=True)
        shutil.rmtree("dist", ignore_errors=True)
        shutil.rmtree(dist_dir, ignore_errors=True)

    # Final sweep cleanup
    if os.path.exists("main.spec"): os.remove("main.spec")
    print("\nWizard completed, files generated in the /downloads folder.")

if __name__ == "__main__":
    build_wizard()