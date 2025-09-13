import flet as ft
import subprocess
import threading
from flauncher.install_dialog import request_install
import time

# config defaults
APP_NAME = "UVX Splash"
REPO_URL = "https://github.com/flol3622/Flupke-launcher"
UVX_cmd = "uvx --from flauncher test"
UVX_install_update = "uv tool install git+https://github.com/flol3622/Flupke-launcher"
UVX_remove = "uv tool uninstall flauncher"
SHOW_CONSOLE = True
CONTACT = "Flol3622"
CONTACT_EMAIL = "flupke@example.com"

Csuccess      = "#3300ff"  
Cerror        = "#ff4910"  
Cmain         = "#FFBC42"  ##FFBC42
Cdarkaccent   = "#000000"  
Clightshades  = "#F5F5F5"  

# helper to run a command, returning (code, output)
def run(cmd):
    p = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, text=True
    )
    out = p.communicate()[0]
    return p.returncode, out


# non-UI helpers
def have(cmd):
    code, _ = run(cmd + " --version")
    return code == 0


def check_repo():
    code, _ = run("git ls-remote " + REPO_URL)
    return code == 0


def launch(cmd):
    if SHOW_CONSOLE:
        subprocess.Popen(f'start "" cmd /k {cmd}', shell=True)
    else:
        subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
    return 0


def main(page: ft.Page):
    page.title = "Flupke launcher"
    page.window.width = 450
    page.window.height = 500
    page.assets_dir = "icons"
    page.bgcolor = Clightshades

    steps = []  # (name, status_text, ring_container)

    def make_step(name):
        t = ft.Text(name + " ...", size=14, color=Cdarkaccent, weight=ft.FontWeight.W_500)
        ring = ft.ProgressRing(
            width=16, height=16, visible=False, color=Cmain, stroke_width=2
        )
        status_icon = ft.Icon(
            ft.Icons.RADIO_BUTTON_UNCHECKED, size=16, color=Cdarkaccent, visible=True
        )

        icon_stack = ft.Stack([status_icon, ring], width=16, height=16)

        row = ft.Container(
            content=ft.Row(
                [icon_stack, t], alignment=ft.MainAxisAlignment.START, spacing=12
            ),
            padding=ft.padding.symmetric(vertical=8, horizontal=16),
            bgcolor=Clightshades,
            border=ft.border.all(1, Cdarkaccent),
            shadow=ft.BoxShadow(color=Cdarkaccent, offset=ft.Offset(4, 4))
        )
        steps.append((name, t, ring, status_icon))
        return row

    install_note = ft.Text("", size=12, color=Cdarkaccent, italic=True)
    contact = ft.TextButton(
        text=f"{CONTACT} <{CONTACT_EMAIL}>",
        style=ft.ButtonStyle(
            color=Cdarkaccent,
            text_style=ft.TextStyle(size=10, italic=True)
        ),
        on_click=lambda e: page.launch_url(f"mailto:{CONTACT_EMAIL}")
    )

    # Header with app icon
    header = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.ROCKET_LAUNCH, size=24, color=Cdarkaccent),
                ft.Text(
                    APP_NAME,
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=Cdarkaccent,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=12,            
        ),
        padding=ft.padding.all(16),
        bgcolor=Cmain
    )

    def run_button_click(e):
        """Handle Run button click - execute the full flow"""
        def flow():
            # uv
            update_step(0, spinning=True)
            if not have("uv"):
                update_step(0, done=True)
            else:
                update_step(0, text="1. Check uv ... missing", spinning=False)
                ask_install("uv")
                if have("uv"):
                    update_step(0, done=True)
                else:
                    update_step(0, error=True)
                    return
            # git
            update_step(1, spinning=True)
            if have("git"):
                update_step(1, done=True)
            else:
                update_step(1, text="2. Check git ... missing", spinning=False)
                # prefer winget if present
                ask_install("git")
                if have("git"):
                    update_step(1, done=True)
                else:
                    update_step(1, error=True)
                    return
            # repo
            update_step(2, spinning=True)
            repo_ok = check_repo()
            if repo_ok:
                update_step(2, done=True)
            else:
                update_step(2, text="3. Check repository ... unreachable", error=True)
                
            # launch (prefer fresh install if repo ok, otherwise try cached version)
            update_step(3, spinning=True)
            if repo_ok:
                # Repository is accessible, run install/update command
                install_note.value = "🔄 Installing/updating from repository..."
                install_note.color = Cmain
                page.update()
                
                code, output = run(UVX_install_update)
                if code == 0:
                    install_note.value = "✅ Install/update completed successfully!"
                    install_note.color = Csuccess
                else:
                    install_note.value = f"⚠️ Install/update had issues: {output[:50]}..."
                    install_note.color = Cerror
                page.update()
                
                launch(UVX_cmd)
                update_step(3, done=True)                
            else:
                # No repository access, try to use offline/cached version
                update_step(3, text="4. Launch app ... trying cached version", spinning=True)
                install_note.value = "⚠️ No repository access - running cached version"
                install_note.color = Cerror
                page.update()
                
                launch(UVX_cmd)
                update_step(3, text="4. Launch app ... using cached version", done=True)
                
            if install_note.value.startswith("⚠️ No repository access"):
                pass  # Keep the warning message
            elif not install_note.value.startswith("⚠️"):
                success_msg = (
                    "🚀 App launched in terminal window. You can close this launcher."
                    if SHOW_CONSOLE
                    else "🚀 App launched successfully. You can close this launcher."
                )
                install_note.value = success_msg
                install_note.color = Csuccess
                page.update()
                time.sleep(1)
                page.window.close()
        
        # Run in separate thread to avoid blocking UI
        threading.Thread(target=flow, daemon=True).start()

    def clear_cache_click(e):
        """Handle Clear Cache button click - remove installed flauncher"""
        def clear_action():
            install_note.value = "🗑️ Clearing cache..."
            install_note.color = Cmain
            page.update()
            
            code, output = run(UVX_remove)
            if code == 0:
                install_note.value = "✅ Cache cleared successfully!"
                install_note.color = Csuccess
            else:
                install_note.value = f"⚠️ Cache clear had issues: {output[:50]}..."
                install_note.color = Cerror
            page.update()
        
        # Run in separate thread to avoid blocking UI
        threading.Thread(target=clear_action, daemon=True).start()

    # Action buttons
    action_buttons = ft.Container(
        content=ft.Row(
            [
                ft.FilledButton(
                    text="Run",
                    icon=ft.Icons.PLAY_ARROW,
                    bgcolor=Csuccess,
                    color=Clightshades,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=0),
                    ),
                    on_click=run_button_click,
                ),
                ft.FilledButton(
                    text="Clear Cache",
                    icon=ft.Icons.CLEAR_ALL,
                    bgcolor=Clightshades,
                    color=Cdarkaccent,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=0),
                        side=ft.BorderSide(1, Cdarkaccent),
                    ),
                    on_click=clear_cache_click,
                ),
            ],
            spacing=12,
            alignment=ft.MainAxisAlignment.CENTER
        ),
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
    )

    col = ft.Column(
        [
            header,
            action_buttons,
            make_step("1. Check uv"),
            make_step("2. Check git"),
            make_step("3. Check repository"),
            make_step("4. Launch app"),
            ft.Divider(opacity=0.3, height=20),
            install_note,
            contact,
        ],
        spacing=12,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )

    # Center the container
    page.add(
        ft.Container(
            content=col,
            padding=ft.padding.all(10),
        )
    )

    def update_step(idx, text=None, spinning=False, done=False, error=False):
        name, t, ring, status_icon = steps[idx]
        if text:
            t.value = text
        ring.visible = spinning
        status_icon.visible = not spinning

        if done:
            t.value = t.value.split(" - ")[0] + " - ✓ OK"
            t.color = Csuccess
            status_icon.name = ft.Icons.CHECK_CIRCLE
            status_icon.color = Csuccess
        elif error:
            t.value = t.value.split(" - ")[0] + " - ✗ ERROR"
            t.color = Cerror
            status_icon.name = ft.Icons.ERROR
            status_icon.color = Cerror
        elif spinning:
            t.color = Cmain
            status_icon.name = ft.Icons.RADIO_BUTTON_UNCHECKED

        page.update()

    def ask_install(what):
        cmd = request_install(page, what)
        if cmd:
            install_note.value = f"⏳ Installing {what}..."
            install_note.color = Cmain
            page.update()
            run(cmd)
            install_note.value = f"✅ {what} installation completed."
            install_note.color = Cdarkaccent
            page.update()


def run_launcher():
    ft.app(main)

if __name__ == "__main__":
    ft.app(main)