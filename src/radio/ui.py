import time
import random
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from src.radio.models import RadioStation
from src.radio.services.localization_service import L

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
    "default": Theme("bold cyan", "blue", "bold magenta", "bright_green", "bold red"),
    "hacker": Theme("bold bright_green", "green", "bright_green", "bright_green", "bright_red"),
    "ocean": Theme("bright_blue", "cyan", "bold white", "bright_cyan", "bright_red"),
    "sunset": Theme("bold yellow", "bright_red", "bold magenta", "bright_yellow", "bright_red"),
    "midnight": Theme("bold magenta", "blue", "bright_cyan", "bright_green", "bright_red"),
    "sakura": Theme("bright_magenta", "magenta", "bright_white", "bright_green", "bright_red"),
    "winamp-classic": Theme("#00ff66", "#2f5dff", "#ffb000", "#00ff66", "#ff4048"),
    "besiktas": Theme("#ffffff", "#888888", "#e30513", "#00cc44", "#e30513"),
}

current_theme = THEMES["default"]
current_theme_name = "default"


def _get_theme_file_path() -> Path:
    return Path.home() / ".radio-shell" / "theme"


def load_theme():
    global current_theme, current_theme_name
    theme_file = _get_theme_file_path()
    if theme_file.exists():
        try:
            saved_theme = theme_file.read_text(encoding="utf-8").strip()
            if saved_theme in THEMES:
                current_theme = THEMES[saved_theme]
                current_theme_name = saved_theme
        except Exception:
            pass


def set_theme(theme_name: str) -> bool:
    global current_theme, current_theme_name
    if theme_name in THEMES:
        current_theme = THEMES[theme_name]
        current_theme_name = theme_name
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


def is_current_theme(theme_name: str) -> bool:
    return current_theme_name == theme_name


def _print_besiktas_banner():
    width = 66
    app_title = L.get("app_title")
    app_line = app_title[:60]
    version = "v2.0.0 | Python 3.14 + Rich"

    t = Text()

    # Top border
    t.append("\n  ╔", style=current_theme.secondary)
    t.append("═" * width, style=current_theme.secondary)
    t.append("╗\n", style=current_theme.secondary)

    # Jersey stripe row (3 white + 3 dark × 11 = 66 chars)
    t.append("  ║", style=current_theme.secondary)
    for _ in range(11):
        t.append("███", style=f"bold {current_theme.primary}")
        t.append("   ", style="")
    t.append("║\n", style=current_theme.secondary)

    # Title row: [BJK]   RADIO SHELL   [BJK]  — centered
    inner = "[BJK]   RADIO SHELL   [BJK]"
    left_pad = (width - len(inner)) // 2
    right_pad = width - len(inner) - left_pad
    t.append(f"  ║{' ' * left_pad}", style=current_theme.secondary)
    t.append("[BJK]", style=f"bold {current_theme.highlight}")
    t.append("   RADIO SHELL   ", style=f"bold {current_theme.primary}")
    t.append("[BJK]", style=f"bold {current_theme.highlight}")
    t.append(f"{' ' * right_pad}║\n", style=current_theme.secondary)

    # App title row — centered
    app_pad_l = (width - len(app_line)) // 2
    app_pad_r = width - len(app_line) - app_pad_l
    t.append(f"  ║{' ' * app_pad_l}", style=current_theme.secondary)
    t.append(app_line, style=f"bold {current_theme.primary}")
    t.append(f"{' ' * app_pad_r}║\n", style=current_theme.secondary)

    # Version row — centered
    ver_pad_l = (width - len(version)) // 2
    ver_pad_r = width - len(version) - ver_pad_l
    t.append(f"  ║{' ' * ver_pad_l}", style=current_theme.secondary)
    t.append(version, style="dim")
    t.append(f"{' ' * ver_pad_r}║\n", style=current_theme.secondary)

    # Jersey stripe row (bottom)
    t.append("  ║", style=current_theme.secondary)
    for _ in range(11):
        t.append("███", style=f"bold {current_theme.primary}")
        t.append("   ", style="")
    t.append("║\n", style=current_theme.secondary)

    # Bottom border
    t.append("  ╚", style=current_theme.secondary)
    t.append("═" * width, style=current_theme.secondary)
    t.append("╝\n", style=current_theme.secondary)

    console.print(t)


def _print_winamp_banner():
    width = 66
    title = "RADIO SHELL"
    app_title = L.get("app_title")
    app_line = app_title[:52]

    t = Text()

    def append_row(segments):
        used_width = 1
        t.append("  | ", style=current_theme.secondary)
        for value, style in segments:
            if style:
                t.append(value, style=style)
            else:
                t.append(value)
            used_width += len(value)
        t.append(" " * max(0, width - used_width))
        t.append("|\n", style=current_theme.secondary)

    t.append("\n  +", style=current_theme.secondary)
    t.append("-" * width, style=current_theme.secondary)
    t.append("+\n", style=current_theme.secondary)
    append_row([
        ("[WINAMP]", f"bold {current_theme.highlight}"),
        (f"  {title}", "bold white on #17235e"),
    ])
    append_row([
        ("00:00", f"bold {current_theme.primary}"),
        ("  ", ""),
        ("▁▂▄▇▆▄▂▁▃▅▇▅▃▂▁▃", current_theme.primary),
        ("  ", ""),
        ("STEREO", f"bold {current_theme.highlight}"),
        ("  128 KBPS  44 KHZ", "dim"),
    ])
    append_row([
        (app_line, f"bold {current_theme.primary}"),
    ])
    t.append("  +", style=current_theme.secondary)
    t.append("-" * width, style=current_theme.secondary)
    t.append("+\n", style=current_theme.secondary)

    console.print(t)


def print_banner():
    if is_current_theme("besiktas"):
        _print_besiktas_banner()
        return
    if is_current_theme("winamp-classic"):
        _print_winamp_banner()
        return

    width = 66
    app_title = L.get("app_title")
    padding_title = (width - len(app_title) - 10) // 2

    border = current_theme.secondary
    title_style = f"bold {current_theme.highlight}"
    name_style = f"bold {current_theme.primary}"
    dim_style = "dim"

    t = Text()
    t.append(f"\n  ╔{'═' * width}╗\n", style=border)
    t.append(f"  ║{' ' * 18} ♬  ", style=border)
    t.append("░░░ RADIO SHELL ░░░", style=title_style)
    t.append(f"  ♬ {' ' * (width - 45)}║\n", style=border)
    t.append(f"  ║{' ' * max(0, padding_title)} ", style=border)
    t.append(app_title, style=name_style)
    t.append(f" {' ' * max(0, width - len(app_title) - padding_title - 2)}║\n", style=border)
    t.append(f"  ║{' ' * 20} ", style=border)
    t.append("v2.0.0 | Python 3.14 + Rich", style=dim_style)
    t.append(f" {' ' * (width - 49)}║\n", style=border)
    t.append(f"  ╚{'═' * width}╝\n", style=border)

    console.print(t)


def print_header(title: str):
    ui_text = Text()
    if is_current_theme("winamp-classic"):
        ui_text.append(" WINAMP ", style=f"bold {current_theme.highlight}")
        ui_text.append("▌▌ ", style=f"bold {current_theme.primary}")
        ui_text.append(title.upper(), style=f"bold {current_theme.primary}")
    elif is_current_theme("besiktas"):
        ui_text.append(" [BJK] ", style=f"bold {current_theme.highlight}")
        ui_text.append("█ ", style=f"bold {current_theme.primary}")
        ui_text.append(title.upper(), style=f"bold {current_theme.primary}")
        ui_text.append(" █ ", style=f"bold {current_theme.primary}")
        ui_text.append("[BJK] ", style=f"bold {current_theme.highlight}")
    else:
        ui_text.append(" ❯❯ ", style=f"bold {current_theme.highlight}")
        ui_text.append(title, style=f"bold {current_theme.primary}")
        ui_text.append(" ❮❮ ", style=f"bold {current_theme.highlight}")

    panel = Panel(
        ui_text,
        box=box.SQUARE if is_current_theme("winamp-classic") or is_current_theme("besiktas") else box.HORIZONTALS,
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


def show_connecting_progress(station_name: str):
    """Displays a modern connecting progress bar animation."""
    with Progress(
        SpinnerColumn(),
        TextColumn(f"[bold {current_theme.primary}]{L.get('connecting')}[/] [white]{{task.fields[name]}}[/]"),
        BarColumn(bar_width=40, complete_style=current_theme.primary, finished_style=current_theme.success),
        TaskProgressColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("connecting", name=station_name, total=100)
        while not progress.finished:
            # Random advance for a more realistic feel (approx 2 seconds total)
            progress.update(task, advance=random.randint(1, 4))
            time.sleep(0.05)


def print_station_table(title: str, stations: List[RadioStation], subtitle: Optional[str] = None):
    if not stations:
        print_info(L.get("no_stations"))
        return

    # Unified header style with uppercase title
    print_header(title.upper())

    # Modern and elegant table design with thin row separators
    winamp = is_current_theme("winamp-classic")
    table = Table(
        box=box.SQUARE if winamp else box.HORIZONTALS,
        border_style=current_theme.secondary,
        header_style=f"bold {current_theme.highlight}",
        row_styles=[current_theme.primary, "#a8ffbd"] if winamp else ["none", "dim"],
        show_lines=not winamp,
        pad_edge=True,
        collapse_padding=True
    )

    table.add_column(L.get("no"), style="dim", justify="center", width=4)
    table.add_column(L.get("id"), style=current_theme.highlight if winamp else "bold yellow", justify="right", width=20)
    table.add_column(L.get("name"), style=f"bold {current_theme.primary}" if winamp else "bold white", min_width=25)
    table.add_column(L.get("country"), style=current_theme.primary, justify="left")
    table.add_column(L.get("genre"), style=current_theme.secondary, justify="left")
    table.add_column(L.get("fav"), justify="center")

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
    console.print(f"  [dim]{L.get('total_stations', count=len(stations))}[/]")
    if subtitle:
        console.print(f"  [{current_theme.highlight}]ℹ  {subtitle}[/]")
    console.print()


def print_now_playing(station: RadioStation, song: Optional[str], volume: int, is_recording: bool):
    if is_current_theme("winamp-classic"):
        content = f"[{current_theme.highlight}]STATION[/]  [{current_theme.primary}]{station.name}[/]\n"
        content += f"[{current_theme.highlight}]COUNTRY[/]  [{current_theme.primary}]{station.country or '-'}[/]\n"
        content += f"[{current_theme.highlight}]GENRE[/]    [{current_theme.primary}]{station.genre or '-'}[/]\n"

        if song:
            content += f"[{current_theme.highlight}]TITLE[/]    [{current_theme.primary}]{song}[/]\n"

        content += f"[{current_theme.highlight}]VOLUME[/]   [{current_theme.primary}]%{volume}[/]"
        if is_recording:
            content += f"  [{current_theme.error}]REC[/]"

        panel = Panel(
            content,
            title=f"[bold {current_theme.highlight}]▶ WINAMP CLASSIC[/]",
            border_style=current_theme.secondary,
            box=box.SQUARE,
            padding=(1, 2)
        )
        console.print(panel)
        return

    content = f"[{current_theme.primary}]{L.get('station')}:[/] {station.name}\n"
    content += f"[{current_theme.primary}]{L.get('country')}:[/] {station.country or '-'}\n"
    content += f"[{current_theme.primary}]{L.get('genre')}:[/] {station.genre or '-'}\n"

    if song:
        content += f"[{current_theme.highlight}]{L.get('song')}:[/] {song}\n"

    content += f"[{current_theme.secondary}]{L.get('volume')}:[/] %{volume}"
    if is_recording:
        content += f" | [{current_theme.error}]● {L.get('recording')}[/]"

    panel = Panel(
        content,
        title=f"[{current_theme.highlight}]♬ {L.get('now_playing')}[/]",
        border_style=current_theme.primary,
        box=box.ROUNDED,
        padding=(1, 2)
    )
    console.print(panel)
