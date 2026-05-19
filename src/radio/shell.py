import sys
import shlex
import time
from datetime import datetime
from typing import Dict, Callable, List, Iterable, Optional
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion, WordCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

from src.radio import ui
from src.radio.services.station_service import StationService
from src.radio.player import AudioPlayer

class ShellCommand:
    def __init__(self, name: str, func: Callable, desc: str, category: str = "DİĞER"):
        self.name = name
        self.func = func
        self.desc = desc
        self.category = category

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
            commands = list(self.shell.commands.keys()) + ["help", "exit", "q", "?", "listele"]
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
        
        # Define a consistent style for the UI elements
        self.style = Style.from_dict({
            'bottom-toolbar': 'bg:#1a1a1a fg:#ffffff',  # Dark background, white default text
        })
        
        self.session = PromptSession(
            history=InMemoryHistory(), 
            completer=self.completer,
            style=self.style
        )
        self.running = True
        self.player: Optional[AudioPlayer] = None

    def register(self, name: str, func: Callable, desc: str, category: str = "DİĞER"):
        self.commands[name] = ShellCommand(name, func, desc, category)

    def print_help(self):
        ui.print_header("KOMUT LİSTESİ")
        
        categories = {
            "İSTASYON LİSTELEME": ["listele", "turkiye", "ulkeler", "ulke", "turler", "tur", "ara", "online-ara"],
            "OYNATMA": ["cal", "son", "dur", "durum", "ses", "sonraki", "onceki", "karistir", "uyku", "gecmis"],
            "KAYIT": ["kaydet", "kayitdur"],
            "YÖNETİM": ["favori", "favoriler", "ekle", "duzenle", "sil", "iceaktar", "tema", "bildirim", "online-ekle", "kontrol", "temizle"]
        }

        for cat_name, cmd_names in categories.items():
            ui.console.print(f"\n  [bold {ui.current_theme.primary}]{cat_name}[/]")
            for name in cmd_names:
                if name in self.commands:
                    cmd = self.commands[name]
                    ui.console.print(f"    [cyan]{name:<20}[/] - {cmd.desc}")
        
        ui.console.print(f"\n  [bold {ui.current_theme.primary}]GENEL[/]")
        ui.console.print("    [cyan]help / ?            [/] - Bu yardım menüsünü gösterir")
        ui.console.print("    [cyan]exit / q / quit     [/] - Uygulamadan çıkar")

    def _get_bottom_toolbar(self):
        if not self.player or not self.player.is_playing():
            return HTML(' <ansired>■ Radyo: Durduruldu</ansired> ')
        
        p = self.player
        s = p.current_station
        
        station_name = s.name if s else "Bilinmiyor"
        country = s.country if s and s.country else "Bilinmiyor"
        codec_info = f"{p.codec} ({p.sample_rate})" if p.codec and p.sample_rate else "..."
        vol = f"{p.volume}%"
        
        # Elapsed time and Song Info logic
        elapsed_str = "00:00"
        show_waiting_msg = True
        if p.playback_start_time:
            elapsed = datetime.now() - p.playback_start_time
            total_seconds = int(elapsed.total_seconds())
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            elapsed_str = f"{minutes:02d}:{seconds:02d}"
            if total_seconds >= 15:
                show_waiting_msg = False
        
        song_part = ""
        if p.current_song:
            song_part = f'<ansiwhite>•</ansiwhite>  <ansiyellow>🎵 {p.current_song}</ansiyellow>  '
        elif show_waiting_msg:
            song_part = f'<ansiwhite>•</ansiwhite>  <ansiyellow>🎵 şarkı bilgisi bekleniyor</ansiyellow>  '
        
        rec = " <ansired>● KAYIT</ansired>" if p.is_recording() else ""
        
        return HTML(
            f' <ansicyan><b>📻 {station_name}</b></ansicyan>  '
            f'{song_part}'
            f'<ansiwhite>•</ansiwhite>  <ansigreen>🌍 {country}</ansigreen>  '
            f'<ansiwhite>•</ansiwhite>  <ansimagenta>⚙️ {codec_info}</ansimagenta>  '
            f'<ansiwhite>•</ansiwhite>  <ansibrightblue>🔊 {vol}</ansibrightblue>  '
            f'<ansiwhite>•</ansiwhite>  <ansiwhite>⏱️ {elapsed_str}</ansiwhite>{rec} '
        )

    def _get_prompt(self):
        primary_color = ui.current_theme.primary
        # Map rich colors to prompt_toolkit ansi colors roughly
        # Defaulting to some safe ones if theme doesn't match perfectly
        ansi_primary = "ansicyan" if primary_color == "cyan" else "ansigreen"
        
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
        welcome_msg = "Komutlar için [bold cyan]'help'[/], çıkmak için [bold red]'exit'[/] yazın."
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
                        ui.print_error(f"Komut çalıştırılırken hata: {e}")
                else:
                    ui.print_error(f"Bilinmeyen komut: '{cmd_name}'. Yardım için 'help' yazın.")

            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            except Exception as e:
                ui.print_error(f"Shell hatası: {e}")

