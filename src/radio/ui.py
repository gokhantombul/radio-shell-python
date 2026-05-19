import os
import sys
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from src.radio.models import RadioStation

# Use global console
console = Console()

class Theme:
    def __init__(self, primary: str, secondary: str, highlight: str, success: str, error: str):
        self.primary = primary
        self.secondary = secondary
        self.highlight = highlight
        self.success = success
        self.error = error

THEMES = {
    "default": Theme("cyan", "blue", "magenta", "green", "red"),
    "hacker": Theme("green", "green", "bold green", "green", "red"),
    "ocean": Theme("blue", "cyan", "white", "bright_blue", "red"),
    "sunset": Theme("yellow", "red", "magenta", "yellow", "red")
}

current_theme = THEMES["default"]

def _get_theme_file_path() -> Path:
    return Path.home() / ".radio-shell" / "theme"

def load_theme():
    global current_theme
    theme_file = _get_theme_file_path()
    if theme_file.exists():
        try:
            saved_theme = theme_file.read_text(encoding="utf-8").strip()
            if saved_theme in THEMES:
                current_theme = THEMES[saved_theme]
        except Exception:
            pass

def set_theme(theme_name: str) -> bool:
    global current_theme
    if theme_name in THEMES:
        current_theme = THEMES[theme_name]
        try:
            theme_file = _get_theme_file_path()
            theme_file.parent.mkdir(parents=True, exist_ok=True)
            theme_file.write_text(theme_name, encoding="utf-8")
        except Exception:
            pass
        return True
    return False

def get_themes() -> List[str]:
    return list(THEMES.keys())

def print_banner():
    width = 66
    banner = f"""
  ╔{"═" * width}╗
  ║{" " * 18} ♬  ░░░ RADIO SHELL ░░░  ♬ {" " * (width - 45)}║
  ║{" " * 12} Terminal FM Radio Player - Türkiye & Dünya {" " * (width - 56)}║
  ║{" " * 20} v2.0.0 | Python 3.14 + Rich {" " * (width - 41)}║
  ╚{"═" * width}╝
"""
    console.print(Text(banner, style=current_theme.primary))

def print_header(title: str):
    ui_text = Text()
    ui_text.append(" ❯❯ ", style=f"bold {current_theme.highlight}")
    ui_text.append(title, style=f"bold {current_theme.primary}")
    ui_text.append(" ❮❮ ", style=f"bold {current_theme.highlight}")
    
    panel = Panel(
        ui_text,
        box=box.HORIZONTALS,
        border_style=current_theme.secondary,
        padding=(0, 2),
        expand=False
    )
    console.print(panel)

def print_error(msg: str):
    console.print(f"[{current_theme.error}]  ✘ {msg}[/]")

def print_success(msg: str):
    console.print(f"[{current_theme.success}]  ✔ {msg}[/]")

def print_info(msg: str):
    console.print(f"[{current_theme.highlight}]  ℹ {msg}[/]")

def print_station_table(title: str, stations: List[RadioStation]):
    if not stations:
        print_info("Gösterilecek istasyon bulunamadı.")
        return

    # Unified header style with uppercase title
    # Simple Turkish i -> İ conversion for better appearance
    title_upper = title.replace('i', 'İ').upper()
    print_header(title_upper)

    # Modern and elegant table design
    table = Table(
        box=box.SIMPLE_HEAVY,
        border_style=current_theme.secondary,
        header_style=f"bold {current_theme.highlight}",
        row_styles=["none", "dim"],
        show_lines=False,
        pad_edge=True,
        collapse_padding=True
    )

    table.add_column("No", style="dim", justify="center", width=4)
    table.add_column("ID", style="bold yellow", justify="right", width=20)
    table.add_column("İstasyon İsmi", style="bold white", min_width=25)
    table.add_column("Ülke", style=current_theme.primary, justify="left")
    table.add_column("Müzik Türü", style=current_theme.secondary, justify="left")
    table.add_column("Fav", justify="center")

    for idx, s in enumerate(stations, 1):
        fav_icon = f"[{current_theme.highlight}]★[/]" if s.favorite else "[dim]☆[/]"
        # Add a small radio icon before name for aesthetics
        name_with_icon = f"📻 {s.name}"
        
        table.add_row(
            str(idx),
            s.id,
            name_with_icon,
            s.country or "-",
            s.genre or "-",
            fav_icon
        )
    
    console.print(table)
    console.print(f"  [dim]Toplam {len(stations)} istasyon listelendi.[/]\n")

def print_now_playing(station: RadioStation, song: Optional[str], volume: int, is_recording: bool):
    content = f"[{current_theme.primary}]Radyo:[/] {station.name}\n"
    content += f"[{current_theme.primary}]Ülke:[/] {station.country or '-'}\n"
    content += f"[{current_theme.primary}]Tür:[/] {station.genre or '-'}\n"

    if song:
        content += f"[{current_theme.highlight}]Şarkı:[/] {song}\n"

    content += f"[{current_theme.secondary}]Ses:[/] %{volume}"
    if is_recording:
        content += f" | [{current_theme.error}]● KAYIT YAPILIYOR[/]"

    panel = Panel(
        content,
        title=f"[{current_theme.highlight}]♬ Çalıyor[/]",
        border_style=current_theme.primary,
        box=box.ROUNDED,
        padding=(1, 2)
    )
    console.print(panel)
