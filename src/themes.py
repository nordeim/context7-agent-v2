from rich.style import Style
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.theme import Theme

THEMES = {
    "cyberpunk": Theme({
        "primary": "bold magenta",
        "accent": "bright_cyan",
        "header": "bold magenta on black",
        "background": "black",
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        "ascii": "bright_magenta",
        "glow": "bold magenta blink",
        "gradient": "magenta on black",
    }),
    "ocean": Theme({
        "primary": "bold blue",
        "accent": "cyan",
        "header": "bold white on blue",
        "background": "blue",
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        "ascii": "cyan",
        "glow": "bold blue blink",
        "gradient": "cyan on blue",
    }),
    "forest": Theme({
        "primary": "bold green",
        "accent": "bright_green",
        "header": "bold green on black",
        "background": "black",
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        "ascii": "green",
        "glow": "bold green blink",
        "gradient": "green on black",
    }),
    "sunset": Theme({
        "primary": "bold yellow",
        "accent": "bright_red",
        "header": "bold white on red",
        "background": "red",
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        "ascii": "yellow",
        "glow": "bold yellow blink",
        "gradient": "yellow on red",
    }),
}

ASCII_ART = {
    "cyberpunk": r"""
     ____            _               _     _     _           
    / ___| ___ _ __ | |_ _   _ _ __ | |__ (_)___| | __       
   | |   / _ \ '_ \| __| | | | '_ \| '_ \| / __| |/ /       
   | |__|  __/ | | | |_| |_| | |_) | | | | \__ \   <        
    \____\___|_| |_|\__|\__,_| .__/|_| |_|_|___/_|\_\       
                             |_|                             
    """,
    "ocean": r"""
     ~~~~~  OCEAN THEME  ~~~~~
    ~~~  ~~~   ~~~   ~~~   ~~~
    """,
    "forest": r"""
      🌲🌳 FOREST THEME 🌳🌲
     ////\\\\////\\\\////\\\\
    """,
    "sunset": r"""
      🌅 SUNSET THEME 🌅
    ~~~~~~~~~~~~~~~~~~~~~~
    """,
}

ANIMATION_FRAMES = {
    "cyberpunk": [
        "[magenta]*[/magenta]    ",
        " [magenta]*[/magenta]   ",
        "  [magenta]*[/magenta]  ",
        "   [magenta]*[/magenta] ",
        "    [magenta]*[/magenta]",
        "   [magenta]*[/magenta] ",
        "  [magenta]*[/magenta]  ",
        " [magenta]*[/magenta]   ",
    ],
    "ocean": [
        "[cyan]~[/cyan]    ",
        " [cyan]~[/cyan]   ",
        "  [cyan]~[/cyan]  ",
        "   [cyan]~[/cyan] ",
        "    [cyan]~[/cyan]",
        "   [cyan]~[/cyan] ",
        "  [cyan]~[/cyan]  ",
        " [cyan]~[/cyan]   ",
    ],
    "forest": [
        "[green]🌲[/green]    ",
        " [green]🌲[/green]   ",
        "  [green]🌲[/green]  ",
        "   [green]🌲[/green] ",
        "    [green]🌲[/green]",
        "   [green]🌲[/green] ",
        "  [green]🌲[/green]  ",
        " [green]🌲[/green]   ",
    ],
    "sunset": [
        "[yellow]🌅[/yellow]    ",
        " [yellow]🌅[/yellow]   ",
        "  [yellow]🌅[/yellow]  ",
        "   [yellow]🌅[/yellow] ",
        "    [yellow]🌅[/yellow]",
        "   [yellow]🌅[/yellow] ",
        "  [yellow]🌅[/yellow]  ",
        " [yellow]🌅[/yellow]   ",
    ],
}

def get_theme(theme_name: str):
    return THEMES.get(theme_name, THEMES["cyberpunk"])

def get_ascii_art(theme_name: str):
    return ASCII_ART.get(theme_name, ASCII_ART["cyberpunk"])

def get_animation_frames(theme_name: str):
    return ANIMATION_FRAMES.get(theme_name, ANIMATION_FRAMES["cyberpunk"])
