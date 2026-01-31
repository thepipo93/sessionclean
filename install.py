"""Install SessionClean: creates Start Menu shortcut and pins to taskbar."""

import os
import sys
from pathlib import Path


def get_python_path() -> str:
    """Get the path to pythonw.exe (no console window)."""
    python_dir = Path(sys.executable).parent
    pythonw = python_dir / "pythonw.exe"
    if pythonw.exists():
        return str(pythonw)
    return sys.executable


def create_shortcut(
    shortcut_path: str,
    target: str,
    arguments: str,
    working_dir: str,
    description: str,
    icon_path: str | None = None,
) -> None:
    """Create a Windows shortcut (.lnk) file."""
    import subprocess
    # Use PowerShell to create the shortcut
    ps_script = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{target}"
$Shortcut.Arguments = "{arguments}"
$Shortcut.WorkingDirectory = "{working_dir}"
$Shortcut.Description = "{description}"
"""
    if icon_path:
        ps_script += f'$Shortcut.IconLocation = "{icon_path}"\n'
    ps_script += "$Shortcut.Save()\n"

    subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
        check=True, capture_output=True,
    )


def main():
    project_dir = Path(__file__).parent.resolve()
    python_path = get_python_path()
    main_script = str(project_dir / "src" / "sessionclean" / "__main__.py")

    print("=" * 50)
    print("  SessionClean Installer")
    print("=" * 50)
    print()

    # 1. Start Menu shortcut
    start_menu = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    start_shortcut = str(start_menu / "SessionClean.lnk")

    print(f"[1/3] Creating Start Menu shortcut...")
    try:
        create_shortcut(
            shortcut_path=start_shortcut,
            target=python_path,
            arguments=f'-m sessionclean',
            working_dir=str(project_dir),
            description="Review and clean files created during your session",
        )
        print(f"  ✅ Start Menu: {start_shortcut}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")

    # 2. Desktop shortcut
    desktop = Path.home() / "Desktop"
    desktop_shortcut = str(desktop / "SessionClean.lnk")

    print(f"[2/3] Creating Desktop shortcut...")
    try:
        create_shortcut(
            shortcut_path=desktop_shortcut,
            target=python_path,
            arguments=f'-m sessionclean',
            working_dir=str(project_dir),
            description="Review and clean files created during your session",
        )
        print(f"  ✅ Desktop: {desktop_shortcut}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")

    # 3. Taskbar pin (copy to taskbar folder)
    taskbar_dir = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Internet Explorer" / "Quick Launch" / "User Pinned" / "TaskBar"

    print(f"[3/3] Creating Taskbar shortcut...")
    if taskbar_dir.exists():
        taskbar_shortcut = str(taskbar_dir / "SessionClean.lnk")
        try:
            create_shortcut(
                shortcut_path=taskbar_shortcut,
                target=python_path,
                arguments=f'-m sessionclean',
                working_dir=str(project_dir),
                description="Review and clean files created during your session",
            )
            print(f"  ✅ Taskbar: {taskbar_shortcut}")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
    else:
        print("  ⚠️  Taskbar folder not found. Right-click the Desktop shortcut")
        print("      and select 'Pin to taskbar' manually.")

    # 4. Add to Windows Startup (auto-start on boot)
    startup_dir = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    startup_shortcut = str(startup_dir / "SessionClean.lnk")

    print()
    print("Optional: Start SessionClean automatically when Windows boots?")
    answer = input("  [Y/n]: ").strip().lower()
    if answer in ("", "y", "yes", "s", "si"):
        try:
            create_shortcut(
                shortcut_path=startup_shortcut,
                target=python_path,
                arguments=f'-m sessionclean',
                working_dir=str(project_dir),
                description="SessionClean auto-start",
            )
            print(f"  ✅ Startup: SessionClean will start automatically on boot")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
    else:
        print("  Skipped. You can add it later from Settings.")

    print()
    print("=" * 50)
    print("  ✅ Installation complete!")
    print()
    print("  How to use:")
    print("  • Search 'SessionClean' in Start Menu")
    print("  • Or double-click the Desktop shortcut")
    print("  • The app runs in the system tray (bottom-right)")
    print("  • Right-click tray icon → 'Review Files Now'")
    print("=" * 50)


if __name__ == "__main__":
    main()
