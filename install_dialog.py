import flet as ft
import subprocess
import threading

"""Simple install dialog for tools like git and uv."""

# Tool configurations - easy to maintain
TOOLS = {
	"git": {
		"name": "Git",
		"icon": "icons/git.svg",
		"description": "Tool for version control, enabling downloading and updating code.",
		"homepage": "https://git-scm.com/",
		"command": lambda: "winget install --id Git.Git -e --source winget" if _has_winget() else 
			"echo Install git manually from https://git-scm.com/download/win"
	},
	"uv": {
		"name": "uv", 
		"icon": "icons/uv.svg",
		"description": "Tool for managing Python code, installing and running Python, executing scripts, and more.",
		"homepage": "https://docs.astral.sh/uv/",
		"command": lambda: 'powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"'
	}
}

def _has_winget():
	"""Check if winget is available."""
	try:
		subprocess.run("winget --version", shell=True, capture_output=True, check=True)
		return True
	except Exception:
		return False

def _copy_command(page, command):
	"""Copy command to clipboard with feedback."""
	page.set_clipboard(command)
	page.snack_bar = ft.SnackBar(ft.Text("Command copied"), open=True)
	page.update()

def _build_dialog(page, tool_name):
	"""Build install dialog for a tool."""
	tool = TOOLS.get(tool_name.lower())
	
	# Get actual command
	command = tool["command"]()
	# Icon
	icon = ft.Image(src=tool["icon"], width=40, height=40) if tool["icon"] else \
		   ft.Icon(ft.Icons.INFO_OUTLINED, size=32, color=ft.Colors.PRIMARY)
	
	# Command box with copy button
	cmd_box = ft.Container(
		content=ft.Row([
			ft.Text(command, selectable=True, expand=True, size=12, color=ft.Colors.ON_SURFACE),
			ft.IconButton(
				icon=ft.Icons.CONTENT_COPY, 
				tooltip="Copy to clipboard",
				on_click=lambda e: _copy_command(page, command),
				icon_size=18,
				icon_color=ft.Colors.PRIMARY
			),
		]),
		padding=12,
		bgcolor=ft.Colors.BLUE_GREY_50,
		border=ft.border.all(1, ft.Colors.BLUE_GREY_200),
		border_radius=8,
	)
	
	# Actions
	actions = [
		ft.ElevatedButton(
			"Install now", 
			icon=ft.Icons.DOWNLOAD,
			bgcolor=ft.Colors.PRIMARY,
			color=ft.Colors.WHITE
		)
	]
	if tool.get("homepage"):
		actions.append(
			ft.TextButton(
				"Open website", 
				icon=ft.Icons.OPEN_IN_NEW,
				on_click=lambda e: page.launch_url(tool["homepage"])
			)
		)
	
	# Content
	content = ft.Column([
		ft.Row([
			icon, 
			ft.Column([
				ft.Text(f"{tool['name']} not found", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
				ft.Text("Required for this application", size=12, color=ft.Colors.GREY_600)
			], spacing=2, expand=True)
		], spacing=16, alignment=ft.CrossAxisAlignment.START),
		ft.Divider(opacity=0.3, height=1),
		ft.Text(tool["description"], size=13, color=ft.Colors.ON_SURFACE),
		ft.Container(height=8),
		ft.Text("Install command:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
		cmd_box,
	], tight=True, spacing=12)
	
	return ft.AlertDialog(
		modal=True,
		content=content,
		actions=actions,
		actions_alignment=ft.MainAxisAlignment.END,
		shape=ft.RoundedRectangleBorder(radius=16),
		bgcolor=ft.Colors.WHITE,
		elevation=15,
		surface_tint_color=ft.Colors.TRANSPARENT,
	), command

def request_install(page, tool_name):
	"""Show install dialog; return command if user chooses install, else None."""
	dialog, actual_command = _build_dialog(page, tool_name)
	
	user_choice = {"install": False}
	done = threading.Event()
	
	def on_install(e):
		user_choice["install"] = True
		page.close(dialog)
		done.set()
	
	# Wire up the callbacks
	dialog.actions[0].on_click = on_install  # Install button
	
	page.open(dialog)
	done.wait()
	
	return actual_command if user_choice["install"] else None
