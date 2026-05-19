import sys
import shlex
import time
from datetime import datetime
from typing import Dict, Callable, List, Iterable, Optional
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion, WordCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.document import Document

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
            word = words[0] if words else ''
            commands = list(self.shell.commands.keys()) + ["help", "exit", "q", "?", "listele"]
            for cmd in commands:
                if cmd.startswith(word):
                    yield Completion(cmd, start_position=-len(word))
            return

        cmd = words[0].lower()
        last_word = words[-1]

        # Context-aware completion based on command
        if cmd in ('cal', 'kontrol', 'favori', 'sil'):
            # These commands often take a station ID. We complete IDs if after -i or directly
            # For simplicity, if not completing a flag like -i, provide station IDs.
            if last_word.startswith('-'):
                yield Completion('-i', start_position=-len(last_word))
            else:
                for s in self.station_service.get_all_stations():
                    if s.id.startswith(last_word):
                        yield Completion(s.id, start_position=-len(last_word), display_meta=s.name)

        elif cmd == 'ulke':
            if last_word.startswith('-'):
                yield Completion('-i', start_position=-len(last_word))
            else:
                for c in self.station_service.get_countries():
                    if c.lower().startswith(last_word.lower()):
                        yield Completion(c, start_position=-len(last_word))

        elif cmd == 'tur':
            if last_word.startswith('-'):
                yield Completion('-i', start_position=-len(last_word))
            else:
                for g in self.station_service.get_genres():
                    if g.lower().startswith(last_word.lower()):
                        yield Completion(g, start_position=-len(last_word))

        elif cmd == 'tema':
            for t in ui.get_themes():
                if t.startswith(last_word):
                    yield Completion(t, start_position=-len(last_word))

class InteractiveShell:
    def __init__(self, station_service: StationService):
        self.commands: Dict[str, ShellCommand] = {}
        self.station_service = station_service
        self.completer = RadioCompleter(self, station_service)
        self.session = PromptSession(history=InMemoryHistory(), completer=self.completer)
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
            return " [Radyo: Durduruldu] "
        
        p = self.player
        s = p.current_station
        
        station_name = s.name if s else "Bilinmiyor"
        song = p.current_song if p.current_song else "şarkı bilgisi bekleniyor"
        country = s.country if s and s.country else "Bilinmiyor"
        
        codec_info = f"{p.codec} ({p.sample_rate})" if p.codec and p.sample_rate else "..."
        vol = f"vol: {p.volume}%"
        
        # Elapsed time
        elapsed_str = "00:00"
        if p.playback_start_time:
            elapsed = datetime.now() - p.playback_start_time
            total_seconds = int(elapsed.total_seconds())
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            elapsed_str = f"{minutes:02d}:{seconds:02d}"
        
        rec = " • [KAYIT]" if p.is_recording() else ""
        
        # Minimalist Design: ♬ ❯❯ Kral Pop ❮❮  •  şarkı bilgisi bekleniyor  •  Türkiye  •  AAC (44.1 kHz)  •  vol: 100%  •  02:45
        return f" ♬ ❯❯ {station_name} ❮❮  •  {song}  •  {country}  •  {codec_info}  •  {vol}  •  {elapsed_str}{rec} "

    def run(self, player: Optional[AudioPlayer] = None):
        self.player = player
        ui.print_banner()
        
        # Center the welcome message relative to the banner width (approx 70 chars)
        welcome_msg = "Komutlar için [bold cyan]'help'[/], çıkmak için [bold red]'exit'[/] yazın."
        ui.console.print(f"{' ' * 10}{welcome_msg}\n")
        
        while self.running:
            try:
                text = self.session.prompt(
                    "radio> ", 
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

