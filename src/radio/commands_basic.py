import argparse
from typing import List

from src.radio.shell import InteractiveShell
from src.radio.services.station_service import StationService
from src.radio.services.statistics_service import StatisticsService
from src.radio.services.system_service import SystemService
from src.radio.player import AudioPlayer
from src.radio import ui

class BasicCommands:
    def __init__(self, shell: InteractiveShell, station_service: StationService, stats_service: StatisticsService, system_service: SystemService, player: AudioPlayer):
        self.station_service = station_service
        self.stats_service = stats_service
        self.system_service = system_service
        self.player = player
        self.last_list = []

        shell.register("listele", self.cmd_listele, "Tüm radyo istasyonlarını listeler", "İSTASYON LİSTELEME")
        shell.register("turkiye", self.cmd_turkiye, "Türkiye radyo istasyonlarını listeler", "İSTASYON LİSTELEME")
        shell.register("ulkeler", self.cmd_ulkeler, "Mevcut ülkeleri listeler", "İSTASYON LİSTELEME")
        shell.register("ulke", self.cmd_ulke, "Belirli bir ülkenin istasyonlarını listeler", "İSTASYON LİSTELEME")
        shell.register("turler", self.cmd_turler, "Mevcut müzik türlerini listeler", "İSTASYON LİSTELEME")
        shell.register("tur", self.cmd_tur, "Belirli bir müzik türündeki istasyonları listeler", "İSTASYON LİSTELEME")
        shell.register("ara", self.cmd_ara, "İstasyon arar (isim, ülke veya tür)", "İSTASYON LİSTELEME")
        shell.register("istatistik", self.cmd_istatistik, "Dinleme istatistiklerini gösterir", "YÖNETİM")
        shell.register("durum", self.cmd_durum, "Şu anki çalma durumunu gösterir", "OYNATMA")
        shell.register("sistem", self.cmd_sistem, "Sistem ve RAM kullanım bilgilerini gösterir", "YÖNETİM")
        shell.register("clear", self.cmd_temizle, "Terminal ekranını temizler", "YÖNETİM")
        shell.register("temizle", self.cmd_temizle, "Terminal ekranını temizler", "YÖNETİM")

    def _update_last(self, stations: list):
        self.last_list = stations

    def cmd_listele(self, args: List[str]):
        stations = self.station_service.get_all_stations()
        self._update_last(stations)
        ui.print_station_table("Tüm İstasyonlar", stations)

    def cmd_turkiye(self, args: List[str]):
        stations = [s for s in self.station_service.get_all_stations() if s.country and s.country.lower() in ("türkiye", "turkey")]
        self._update_last(stations)
        ui.print_station_table("Türkiye İstasyonları", stations)

    def cmd_ulkeler(self, args: List[str]):
        countries = self.station_service.get_countries()
        if not countries:
            ui.print_info("Ülke bulunamadı.")
            return
        ui.console.print("[cyan]Mevcut Ülkeler:[/]")
        for c in countries:
            count = len([s for s in self.station_service.get_all_stations() if s.country == c])
            ui.console.print(f"  - {c} ({count} istasyon)")

    def cmd_ulke(self, args: List[str]):
        parser = argparse.ArgumentParser(prog="ulke")
        parser.add_argument("-i", "--isim", required=True)
        try:
            parsed = parser.parse_args(args)
            stations = [s for s in self.station_service.get_all_stations() if s.country and s.country.lower() == parsed.isim.lower()]
            self._update_last(stations)
            ui.print_station_table(f"Ülke: {parsed.isim}", stations)
        except SystemExit:
            ui.print_error("Kullanım: ulke -i <ülke>")

    def cmd_turler(self, args: List[str]):
        genres = self.station_service.get_genres()
        if not genres:
            ui.print_info("Tür bulunamadı.")
            return
        ui.console.print("[cyan]Mevcut Türler:[/]")
        for g in genres:
            count = len([s for s in self.station_service.get_all_stations() if s.genre and g.lower() in s.genre.lower()])
            ui.console.print(f"  - {g} ({count} istasyon)")

    def cmd_tur(self, args: List[str]):
        parser = argparse.ArgumentParser(prog="tur")
        parser.add_argument("-i", "--isim", required=True)
        try:
            parsed = parser.parse_args(args)
            stations = [s for s in self.station_service.get_all_stations() if s.genre and parsed.isim.lower() in s.genre.lower()]
            self._update_last(stations)
            ui.print_station_table(f"Tür: {parsed.isim}", stations)
        except SystemExit:
            ui.print_error("Kullanım: tur -i <tür>")

    def cmd_ara(self, args: List[str]):
        parser = argparse.ArgumentParser(prog="ara")
        parser.add_argument("-s", "--sorgu", required=True)
        try:
            parsed = parser.parse_args(args)
            stations = self.station_service.search(parsed.sorgu)
            self._update_last(stations)
            ui.print_station_table(f"Arama: {parsed.sorgu}", stations)
        except SystemExit:
            ui.print_error("Kullanım: ara -s <kelime>")

    def cmd_istatistik(self, args: List[str]):
        top = self.stats_service.get_top_stations(10)
        total_time = self.stats_service.get_total_listen_time()
        sessions = self.stats_service.get_total_sessions()

        ui.console.print(f"[magenta]Toplam Dinleme:[/] {total_time}")
        ui.console.print(f"[magenta]Toplam Oturum:[/] {sessions}")

        if not top:
            ui.print_info("Henüz istatistik yok.")
            return

        from rich.table import Table
        table = Table(title="Top 10 İstasyon")
        table.add_column("İstasyon")
        table.add_column("Süre (sn)")
        table.add_column("Oturum")
        for s in top:
            table.add_row(s.stationName or s.stationId, str(s.totalSeconds), str(s.sessionCount))
        ui.console.print(table)

    def cmd_durum(self, args: List[str]):
        if not self.player.is_playing() or not self.player.current_station:
            ui.print_info("Şu an çalan bir radyo yok.")
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
        mem_table.add_row("Radyo Shell (Python):", self.system_service.format_bytes(mem["main_process"]))
        
        for child in mem["children_processes"]:
            mem_table.add_row(f"{child['name']} (Motor):", self.system_service.format_bytes(child["memory"]))
        
        mem_table.add_section()
        mem_table.add_row("[bold]Toplam Kullanım:[/]", f"[bold cyan]{self.system_service.format_bytes(mem['total_memory'])}[/]")

        # System Info Table
        sys_table = Table(show_header=False, box=None)
        sys_table.add_row("İşletim Sistemi:", stats["os"])
        sys_table.add_row("Python Sürümü:", stats["python_version"])
        sys_table.add_row("CPU Kullanımı:", f"%{stats['cpu_percent']}")
        
        sys_mem = stats["virtual_memory"]
        sys_table.add_row("Sistem RAM:", f"{self.system_service.format_bytes(sys_mem['used'])} / {self.system_service.format_bytes(sys_mem['total'])}")

        ui.console.print(Panel(
            Columns([mem_table, sys_table]),
            title="[bold magenta]Sistem Bilgileri[/]",
            border_style="cyan"
        ))

    def cmd_temizle(self, args: List[str]):
        ui.console.clear()
        ui.print_banner()
