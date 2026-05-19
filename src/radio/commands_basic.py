import argparse
from typing import List
from src.radio.models import RadioStation

from src.radio.shell import InteractiveShell
from src.radio.services.station_service import StationService
from src.radio.services.statistics_service import StatisticsService
from src.radio.services.system_service import SystemService
from src.radio.player import AudioPlayer
from src.radio import ui
from src.radio.services.localization_service import L

class BasicCommands:
    def __init__(self, shell: InteractiveShell, station_service: StationService, stats_service: StatisticsService, system_service: SystemService, player: AudioPlayer):
        self.station_service = station_service
        self.stats_service = stats_service
        self.system_service = system_service
        self.player = player
        self.last_list: List[RadioStation] = []

        shell.register("listele", self.cmd_listele, "cmd_listele_desc", "cat_listing",
                       hint="cmd_listele_hint")
        shell.register("turkiye", self.cmd_turkiye, "cmd_turkiye_desc", "cat_listing")
        shell.register("ulkeler", self.cmd_ulkeler, "cmd_ulkeler_desc", "cat_listing")
        shell.register("ulke", self.cmd_ulke, "cmd_ulke_desc", "cat_listing")
        shell.register("turler", self.cmd_turler, "cmd_turler_desc", "cat_listing")
        shell.register("tur", self.cmd_tur, "cmd_tur_desc", "cat_listing")
        shell.register("ara", self.cmd_ara, "cmd_ara_desc", "cat_listing")
        shell.register("istatistik", self.cmd_istatistik, "cmd_istatistik_desc", "cat_management")
        shell.register("durum", self.cmd_durum, "cmd_durum_desc", "cat_playback")
        shell.register("sistem", self.cmd_sistem, "cmd_sistem_desc", "cat_management")
        shell.register("clear", self.cmd_temizle, "cmd_temizle_desc", "cat_management")
        shell.register("temizle", self.cmd_temizle, "cmd_temizle_desc", "cat_management")

    def _update_last(self, stations: list):
        self.last_list = stations

    def cmd_listele(self, args: List[str]):
        parser = argparse.ArgumentParser(prog='listele', add_help=False)
        parser.add_argument('-n', type=int, default=50, metavar='SAYI')
        parser.add_argument('--hepsi', action='store_true')
        try:
            parsed = parser.parse_args(args)
        except SystemExit:
            ui.print_error("Usage: listele [-n SAYI] [--hepsi]")
            return

        stations = self.station_service.get_all_stations()
        total = len(stations)

        if parsed.hepsi:
            shown = stations
            subtitle = None
        else:
            limit = parsed.n
            shown = stations[:limit]
            subtitle = (L.get("list_subtitle", limit=limit, total=total)) if total > limit else None

        self._update_last(shown)
        ui.print_station_table(L.get("all_stations"), shown, subtitle=subtitle)

    def cmd_turkiye(self, args: List[str]):
        stations = [s for s in self.station_service.get_all_stations() if s.country and s.country.lower() in ("türkiye", "turkey")]
        self._update_last(stations)
        ui.print_station_table(L.get("tr_stations"), stations)

    def cmd_ulkeler(self, args: List[str]):
        countries = self.station_service.get_countries()
        if not countries:
            ui.print_info(L.get("msg_no_match"))
            return
        ui.console.print(f"[cyan]{L.get('countries_list')}:[/]")
        for c in countries:
            count = len([s for s in self.station_service.get_all_stations() if s.country == c])
            ui.console.print(f"  - {c} ({count} {L.get('station').lower()})")

    def cmd_ulke(self, args: List[str]):
        parser = argparse.ArgumentParser(prog="ulke")
        parser.add_argument("-i", "--isim", required=True)
        try:
            parsed = parser.parse_args(args)
            stations = [s for s in self.station_service.get_all_stations() if s.country and s.country.lower() == parsed.isim.lower()]
            self._update_last(stations)
            ui.print_station_table(f"{L.get('country')}: {parsed.isim}", stations)
        except SystemExit:
            ui.print_error("Usage: ulke -i <country>")

    def cmd_turler(self, args: List[str]):
        genres = self.station_service.get_genres()
        if not genres:
            ui.print_info(L.get("msg_no_match"))
            return
        ui.console.print(f"[cyan]{L.get('genres_list')}:[/]")
        for g in genres:
            count = len([s for s in self.station_service.get_all_stations() if s.genre and g.lower() in s.genre.lower()])
            ui.console.print(f"  - {g} ({count} {L.get('station').lower()})")

    def cmd_tur(self, args: List[str]):
        parser = argparse.ArgumentParser(prog="tur")
        parser.add_argument("-i", "--isim", required=True)
        try:
            parsed = parser.parse_args(args)
            stations = [s for s in self.station_service.get_all_stations() if s.genre and parsed.isim.lower() in s.genre.lower()]
            self._update_last(stations)
            ui.print_station_table(f"{L.get('genre')}: {parsed.isim}", stations)
        except SystemExit:
            ui.print_error("Usage: tur -i <genre>")

    def cmd_ara(self, args: List[str]):
        parser = argparse.ArgumentParser(prog="ara")
        parser.add_argument("-s", "--sorgu", required=True)
        try:
            parsed = parser.parse_args(args)
            stations = self.station_service.search(parsed.sorgu)
            self._update_last(stations)
            ui.print_station_table(f"{L.get('cat_listing')} > {parsed.sorgu}", stations)
        except SystemExit:
            ui.print_error("Usage: ara -s <query>")

    def cmd_istatistik(self, args: List[str]):
        top = self.stats_service.get_top_stations(10)
        total_time = self.stats_service.get_total_listen_time()
        sessions = self.stats_service.get_total_sessions()

        ui.console.print(f"[magenta]{L.get('stats_total_time')}:[/] {total_time}")
        ui.console.print(f"[magenta]{L.get('stats_total_sessions')}:[/] {sessions}")

        if not top:
            ui.print_info(L.get("stats_no_data"))
            return

        from rich.table import Table
        table = Table(title=L.get("stats_top_title"))
        table.add_column(L.get("station"))
        table.add_column(f"{L.get('cat_playback')} (s)")
        table.add_column(L.get("cat_general"))
        for s in top:
            table.add_row(s.stationName or s.stationId, str(s.totalSeconds), str(s.sessionCount))
        ui.console.print(table)

    def cmd_durum(self, args: List[str]):
        if not self.player.is_playing() or not self.player.current_station:
            ui.print_info(L.get("msg_no_playing_station"))
            return
        ui.print_now_playing(
            self.player.current_station,
            self.player.current_song,
            self.player.volume,
            self.player.is_recording()
        )

    def cmd_sistem(self, args: List[str]):
        mem = self.system_service.get_memory_info()
        stats = self.system_service.get_system_stats()
        
        from rich.panel import Panel
        from rich.table import Table
        from rich.columns import Columns

        # Memory Table
        mem_table = Table(show_header=False, box=None)
        mem_table.add_row("Radio Shell (Python):", self.system_service.format_bytes(mem["main_process"]))
        
        for child in mem["children_processes"]:
            mem_table.add_row(f"{child['name']} ({L.get('cat_playback')}):", self.system_service.format_bytes(child["memory"]))
        
        mem_table.add_section()
        mem_table.add_row(f"[bold]{L.get('sys_total_mem')}:[/]", f"[bold cyan]{self.system_service.format_bytes(mem['total_memory'])}[/]")

        # System Info Table
        sys_table = Table(show_header=False, box=None)
        sys_table.add_row(f"{L.get('sys_os')}:", stats["os"])
        sys_table.add_row(f"{L.get('sys_python')}:", stats["python_version"])
        sys_table.add_row(f"{L.get('sys_cpu')}:", f"%{stats['cpu_percent']}")
        
        sys_mem = stats["virtual_memory"]
        sys_table.add_row(f"{L.get('sys_ram')}:", f"{self.system_service.format_bytes(sys_mem['used'])} / {self.system_service.format_bytes(sys_mem['total'])}")

        ui.console.print(Panel(
            Columns([mem_table, sys_table]),
            title=f"[bold magenta]{L.get('sys_info_title')}[/]",
            border_style="cyan"
        ))

    def cmd_temizle(self, args: List[str]):
        ui.console.clear()
        ui.print_banner()
