import shlex
from datetime import datetime
from typing import Dict, Callable, Iterable, Optional
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

from src.radio import ui
from src.radio.services.station_service import StationService
from src.radio.player import AudioPlayer
from src.radio.services.localization_service import L


class ShellCommand:
    def __init__(self, name: str, func: Callable, desc: str, category: Optional[str] = None, hint: str = ""):
        self.name = name
        self.func = func
        self.desc_key = desc
        self.category_key = category
        self.hint_key = hint

    @property
    def desc(self) -> str:
        if "_" in self.desc_key:
            return L.get(self.desc_key)
        return self.desc_key

    @property
    def category(self) -> str:
        if not self.category_key:
            return L.get("cat_other")
        if "_" in self.category_key:
            return L.get(self.category_key)
        return self.category_key

    @property
    def hint(self) -> str:
        if not self.hint_key:
            return ""
        if "_" in self.hint_key:
            return L.get(self.hint_key)
        return self.hint_key


class RadioCompleter(Completer):
    def __init__(self, shell: 'InteractiveShell', station_service: StationService):
        self.shell = shell
        self.station_service = station_service

    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        text = document.text_before_cursor
        words = text.split(' ')

        # If empty or first word, complete command names
        if len(words) <= 1:
            word = words[0].lower() if words else ''
            commands = list(self.shell.commands.keys()) + ["help", "exit", "q", "?"]
            for cmd in commands:
                if word in cmd.lower():
                    yield Completion(cmd, start_position=-len(word))
            return

        cmd = words[0].lower()
        last_word = words[-1].lower()

        # Context-aware completion based on command
        if cmd in ('cal', 'kontrol', 'favori', 'sil'):
            # These commands often take a station ID. We complete IDs if after -i or directly
            # For simplicity, if not completing a flag like -i, provide station IDs.
            if last_word.startswith('-'):
                yield Completion('-i', start_position=-len(last_word))
            else:
                for s in self.station_service.get_all_stations():
                    # Match by ID or Name
                    if last_word in s.id.lower() or last_word in s.name.lower():
                        yield Completion(s.id, start_position=-len(last_word), display_meta=s.name)

        elif cmd == 'ulke':
            if last_word.startswith('-'):
                yield Completion('-i', start_position=-len(last_word))
            else:
                for c in self.station_service.get_countries():
                    if last_word in c.lower():
                        yield Completion(c, start_position=-len(last_word))

        elif cmd == 'tur':
            if last_word.startswith('-'):
                yield Completion('-i', start_position=-len(last_word))
            else:
                for g in self.station_service.get_genres():
                    if last_word in g.lower():
                        yield Completion(g, start_position=-len(last_word))

        elif cmd == 'tema':
            for t in ui.get_themes():
                if last_word in t.lower():
                    yield Completion(t, start_position=-len(last_word))


class InteractiveShell:
    def __init__(self, station_service: StationService):
        self.commands: Dict[str, ShellCommand] = {}
        self.station_service = station_service
        self.completer = RadioCompleter(self, station_service)

        self.style = Style.from_dict({
            'bottom-toolbar':                         'noinherit bg:#1e2030 fg:#9aa5ce',
            'completion-menu':                        'bg:#0d1117 fg:#7ee787',
            'completion-menu.completion':             'bg:#0d1117 fg:#7ee787',
            'completion-menu.completion.current':     'bg:#1a2e1a fg:#b9f4b9 bold',
            'completion-menu.meta.completion':        'bg:#0d1117 fg:#4a8a4a',
            'completion-menu.meta.completion.current': 'bg:#1a2e1a fg:#7ee787',
            'scrollbar.background':                   'bg:#0d1117',
            'scrollbar.button':                       'bg:#2a4a2a',
        })

        self.session: PromptSession = PromptSession(
            history=InMemoryHistory(),
            completer=self.completer,
            style=self.style
        )
        self.running = True
        self.player: Optional[AudioPlayer] = None

    def register(self, name: str, func: Callable, desc: str, category: str = "DİĞER", hint: str = ""):
        self.commands[name] = ShellCommand(name, func, desc, category, hint)

    def print_help(self):
        ui.print_header(L.get("help_title"))

        category_order = [
            L.get("cat_listing"),
            L.get("cat_playback"),
            L.get("cat_recording"),
            L.get("cat_management"),
            L.get("cat_other")
        ]

        grouped: Dict[str, list] = {}
        for cmd in self.commands.values():
            grouped.setdefault(cmd.category, []).append(cmd)

        shown = set()
        for cat_name in category_order:
            if cat_name not in grouped:
                continue
            ui.console.print(f"\n  [bold {ui.current_theme.primary}]{cat_name}[/]")
            for cmd in sorted(grouped[cat_name], key=lambda c: c.name):
                ui.console.print(f"    [cyan]{cmd.name:<20}[/] - {cmd.desc}")
                if cmd.hint:
                    ui.console.print(f"    {'':20}   [{ui.current_theme.highlight}]ℹ  {cmd.hint}[/]")
            shown.add(cat_name)

        for cat_name, cmds in grouped.items():
            if cat_name in shown:
                continue
            ui.console.print(f"\n  [bold {ui.current_theme.primary}]{cat_name}[/]")
            for cmd in sorted(cmds, key=lambda c: c.name):
                ui.console.print(f"    [cyan]{cmd.name:<20}[/] - {cmd.desc}")
                if cmd.hint:
                    ui.console.print(f"    {'':20}   [{ui.current_theme.highlight}]ℹ  {cmd.hint}[/]")

        ui.console.print(f"\n  [bold {ui.current_theme.primary}]{L.get('cat_general')}[/]")
        ui.console.print(f"    [cyan]{L.get('help_general')}")
        ui.console.print(f"    [cyan]{L.get('exit_general')}")

    def _get_bottom_toolbar(self):
        SEP = '  <ansibrightblack>│</ansibrightblack>  '

        if not self.player or not self.player.is_playing():
            if ui.is_current_theme("winamp-classic"):
                return HTML('  <ansibrightgreen>▌▌ WINAMP CLASSIC</ansibrightgreen>  <ansiyellow>STOPPED</ansiyellow>  ')
            return HTML(f'  <ansibrightblack>⏹  {L.get("stopped")}</ansibrightblack>  ')

        p = self.player
        s = p.current_station

        station_name = (s.name[:30] + '…') if s and len(s.name) > 30 else (s.name if s else '—')
        country = s.country if s and s.country else '—'
        genre = s.genre if s and s.genre else ''

        codec_parts = [x for x in (p.codec, p.bitrate, p.sample_rate) if x]
        codec_str = '  '.join(codec_parts) if codec_parts else '—'

        elapsed_str = '00:00'
        show_waiting_msg = True
        if p.playback_start_time:
            elapsed = datetime.now() - p.playback_start_time
            total_seconds = int(elapsed.total_seconds())
            elapsed_str = f"{total_seconds // 60:02d}:{total_seconds % 60:02d}"
            if total_seconds >= 15:
                show_waiting_msg = False

        song_title = None
        if p.current_song:
            song_title = (p.current_song[:45] + '…') if len(p.current_song) > 45 else p.current_song
            song_part = f'{SEP}<ansiyellow>🎵  {song_title}</ansiyellow>'
        elif show_waiting_msg:
            song_part = f'{SEP}<ansibrightblack>🎵  {L.get("waiting_song")}</ansibrightblack>'
        else:
            song_part = ''

        genre_part = f'{SEP}🏷  {genre}' if genre else ''
        rec_part = f'  <ansired>🔴  {L.get("recording")}</ansired>' if p.is_recording() else ''

        if ui.is_current_theme("winamp-classic"):
            title = song_title or (L.get("waiting_song") if show_waiting_msg else "—")
            winamp_rec = '  <ansired>[REC]</ansired>' if p.is_recording() else ''
            return HTML(
                f'  <ansibrightgreen><b>▌▌  {station_name}</b></ansibrightgreen>'
                f'  <ansiyellow>▶  {title}</ansiyellow>'
                f'  <ansibrightblack>│</ansibrightblack>  <ansibrightgreen>{country}</ansibrightgreen>'
                f'  <ansibrightblack>│</ansibrightblack>  <ansibrightblue>{codec_str}</ansibrightblue>'
                f'  <ansibrightblack>│</ansibrightblack>  <ansiyellow>VOL {p.volume}%</ansiyellow>'
                f'  <ansibrightblack>│</ansibrightblack>  {elapsed_str}'
                f'{winamp_rec}  '
            )

        return HTML(
            f'  <ansicyan><b>📻  {station_name}</b></ansicyan>'
            f'{song_part}'
            f'{SEP}🌍  {country}'
            f'{genre_part}'
            f'{SEP}📡  {codec_str}'
            f'{SEP}<ansibrightblue>🔊  {p.volume}%</ansibrightblue>'
            f'{SEP}🕒  {elapsed_str}'
            f'{rec_part}  '
        )

    _RICH_TO_ANSI = {
        "cyan": "ansicyan", "bold cyan": "ansicyan",
        "bright_cyan": "ansicyan", "bold bright_cyan": "ansicyan",
        "blue": "ansiblue", "bold blue": "ansiblue", "bright_blue": "ansiblue",
        "green": "ansigreen", "bold green": "ansigreen",
        "bright_green": "ansigreen", "bold bright_green": "ansigreen",
        "magenta": "ansimagenta", "bold magenta": "ansimagenta",
        "bright_magenta": "ansimagenta", "bold bright_magenta": "ansimagenta",
        "yellow": "ansiyellow", "bold yellow": "ansiyellow", "bright_yellow": "ansiyellow",
        "white": "ansiwhite", "bold white": "ansiwhite", "bright_white": "ansiwhite",
        "#00ff66": "ansibrightgreen", "#2f5dff": "ansibrightblue",
        "#ffb000": "ansiyellow", "#ff4048": "ansired",
        "#ffffff": "ansibrightwhite", "#888888": "ansiwhite",
        "#e30513": "ansired", "#00cc44": "ansigreen",
    }

    def _get_prompt(self):
        if ui.is_current_theme("winamp-classic"):
            if not self.player or not self.player.is_playing():
                return HTML('<ansibrightgreen>▌▌ radio</ansibrightgreen> <ansiyellow>▶</ansiyellow> ')

            station = self.player.current_station
            station_name = station.name if station else "Radio"
            song = self.player.current_song

            if song:
                return HTML(f'<ansibrightgreen>▌▌ {station_name}</ansibrightgreen> <ansiyellow>({song})</ansiyellow> <ansiyellow>▶</ansiyellow> ')
            return HTML(f'<ansibrightgreen>▌▌ {station_name}</ansibrightgreen> <ansiyellow>▶</ansiyellow> ')

        if ui.is_current_theme("besiktas"):
            if not self.player or not self.player.is_playing():
                return HTML('<ansired>[BJK]</ansired> <ansibrightwhite>radio</ansibrightwhite> <ansired>❯</ansired> ')
            station = self.player.current_station
            station_name = station.name if station else "Radyo"
            song = self.player.current_song
            if song:
                return HTML(f'<ansired>[BJK]</ansired> <ansibrightwhite>{station_name}</ansibrightwhite> <ansiyellow>({song})</ansiyellow> <ansired>❯</ansired> ')
            return HTML(f'<ansired>[BJK]</ansired> <ansibrightwhite>{station_name}</ansibrightwhite> <ansired>❯</ansired> ')

        primary_color = ui.current_theme.primary
        ansi_primary = self._RICH_TO_ANSI.get(primary_color, "ansicyan")

        if not self.player or not self.player.is_playing():
            return HTML(f'<{ansi_primary}>📻 radio</{ansi_primary}> <ansired>❯</ansired> ')

        station = self.player.current_station
        station_name = station.name if station else "Radyo"
        song = self.player.current_song

        if song:
            return HTML(f'<{ansi_primary}>📻 {station_name}</{ansi_primary}> <ansiyellow>({song})</ansiyellow> <ansired>❯</ansired> ')
        else:
            return HTML(f'<{ansi_primary}>📻 {station_name}</{ansi_primary}> <ansired>❯</ansired> ')

    def run(self, player: Optional[AudioPlayer] = None):
        self.player = player
        ui.print_banner()

        # Center the welcome message relative to the banner width (approx 70 chars)
        welcome_msg = L.get("welcome_msg")
        ui.console.print(f"{' ' * 10}{welcome_msg}\n")

        while self.running:
            try:
                text = self.session.prompt(
                    message=self._get_prompt,
                    bottom_toolbar=self._get_bottom_toolbar if self.player else None,
                    refresh_interval=1.0
                ).strip()

                if not text:
                    continue

                parts = shlex.split(text)
                cmd_name = parts[0].lower()
                args = parts[1:]

                if cmd_name in ("exit", "q", "quit"):
                    break
                elif cmd_name in ("help", "?"):
                    self.print_help()
                elif cmd_name in self.commands:
                    try:
                        self.commands[cmd_name].func(args)
                    except Exception as e:
                        ui.print_error(L.get("error_executing", error=e))
                else:
                    ui.print_error(L.get("unknown_command", cmd=cmd_name))

            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            except Exception as e:
                ui.print_error(L.get("shell_error", error=e))
