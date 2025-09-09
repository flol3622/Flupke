import flet as ft
import subprocess
import threading
from install_dialog import request_install

# config defaults
APP_NAME = "UVX Splash"
REPO_URL = "https://github.com/httpie/cli"
UVX_CMD = "uvx --from git+https://github.com/httpie/cli httpie"
UVX_CMD_NOCACHE = "uvx --from git+https://github.com/httpie/cli httpie"
SHOW_CONSOLE = True
CONTACT = "Philippe Soubrier"
CONTACT_EMAIL = "philippe@example.com"


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
    page.window.height = 450
    page.bgcolor = ft.Colors.WHITE
    # allow serving local SVG icons (git.svg, uv.svg)
    page.assets_dir = "icons"

    steps = []  # (name, status_text, ring_container)

    def make_step(name):
        t = ft.Text(name + " ...", size=14, color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.W_500)
        ring = ft.ProgressRing(
            width=16, height=16, visible=False, color=ft.Colors.BLUE_600, stroke_width=2
        )
        status_icon = ft.Icon(
            ft.Icons.RADIO_BUTTON_UNCHECKED, size=16, color=ft.Colors.GREY_400, visible=True
        )

        icon_stack = ft.Stack([status_icon, ring], width=16, height=16)

        row = ft.Container(
            content=ft.Row(
                [icon_stack, t], alignment=ft.MainAxisAlignment.START, spacing=12
            ),
            padding=ft.padding.symmetric(vertical=8, horizontal=16),
            border_radius=10,
            bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.PRIMARY),
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.GREY)),
        )
        steps.append((name, t, ring, status_icon))
        return row

    install_note = ft.Text("", size=12, color=ft.Colors.BLUE_GREY_600, italic=True)
    contact = ft.TextButton(
        text=f"{CONTACT} <{CONTACT_EMAIL}>",
        style=ft.ButtonStyle(
            color=ft.Colors.GREY_600,
            text_style=ft.TextStyle(size=10, italic=True)
        ),
        on_click=lambda e: page.launch_url(f"mailto:{CONTACT_EMAIL}")
    )

    # Header with app icon
    header = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.ROCKET_LAUNCH, size=24, color=ft.Colors.PRIMARY),
                ft.Text(
                    APP_NAME,
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.PRIMARY,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=12,
        ),
        padding=ft.padding.all(16),
        bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.PRIMARY),
        border_radius=ft.border_radius.only(top_left=16, top_right=16),
        margin=ft.margin.only(bottom=8),
    )

    col = ft.Column(
        [
            header,
            make_step("1. Check uv"),
            make_step("2. Check git"),
            make_step("3. Check repository"),
            make_step("4. Launch app"),
            ft.Divider(opacity=0.3, height=20),
            install_note,
            contact,
        ],
        spacing=8,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )

    # Center the container
    page.add(
        ft.Container(
            content=col,        
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
            t.color = ft.Colors.GREEN_700
            status_icon.name = ft.Icons.CHECK_CIRCLE
            status_icon.color = ft.Colors.GREEN_600
        elif error:
            t.value = t.value.split(" - ")[0] + " - ✗ ERROR"
            t.color = ft.Colors.RED_700
            status_icon.name = ft.Icons.ERROR
            status_icon.color = ft.Colors.RED_600
        elif spinning:
            t.color = ft.Colors.BLUE_700
            status_icon.name = ft.Icons.RADIO_BUTTON_UNCHECKED

        page.update()

    def ask_install(what):
        cmd = request_install(page, what)
        if cmd:
            install_note.value = f"⏳ Installing {what}..."
            install_note.color = ft.Colors.BLUE_700
            page.update()
            run(cmd)
            install_note.value = f"✅ {what} installation completed."
            install_note.color = ft.Colors.GREEN_700
            page.update()

    def flow():
        # uv
        update_step(0, spinning=True)
        if have("uv"):
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
            update_step(2, text="3. Check repository ... unreachable", spinning=False)
        # launch (prefer nocache if repo ok for freshness)
        update_step(3, spinning=True)
        cmd = UVX_CMD_NOCACHE if repo_ok else UVX_CMD
        launch(cmd)
        if repo_ok:
            update_step(3, done=True)
        else:
            update_step(
                3,
                text="4. Launch app ... attempted cached (see terminal)",
                spinning=False,
                done=True,
            )
            install_note.value = f"⚠️ If the app didn't start, please contact: {CONTACT} <{CONTACT_EMAIL}>"
            install_note.color = ft.Colors.ORANGE_700
            page.update()
        if install_note.value == "":
            success_msg = (
                "🚀 App launched in terminal window. You can close this launcher."
                if SHOW_CONSOLE
                else "🚀 App launched successfully. You can close this launcher."
            )
            install_note.value = success_msg
            install_note.color = ft.Colors.GREEN_700
            page.update()

    threading.Thread(target=flow, daemon=True).start()


ft.app(main)
