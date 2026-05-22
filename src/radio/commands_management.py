import argparse
import subprocess
from typing import List

from src.radio.shell import InteractiveShell
from src.radio.services.station_service import StationService
from src.radio.services.radio_browser_service import RadioBrowserService, OnlineStation
from src.radio.services.notification_service import NotificationService
from src.radio.services.settings_service import SettingsService
from src.radio.player import AudioPlayer
from src.radio.models import RadioStation
from src.radio import ui
from src.radio.services.localization_service import L


class ManagementCommands:
    def __init__(self, shell: InteractiveShell, station_service: StationService, radio_browser: RadioBrowserService, notification_service: NotificationService, player: AudioPlayer, settings_service: SettingsService):
        self.station_service = station_service
        self.radio_browser = radio_browser
        self.notification_service = notification_service
        self.player = player
        self.settings_service = settings_service
        self.last_online_search: List[OnlineStation] = []

        shell.register("favori", self.cmd_favori, "cmd_favori_desc", "cat_management")
        shell.register("favoriler", self.cmd_favoriler, "cmd_favoriler_desc", "cat_management")
        shell.register("kaydet", self.cmd_kaydet, "cmd_kaydet_desc", "cat_recording")
        shell.register("kayitdur", self.cmd_kayitdur, "cmd_kayitdur_desc", "cat_recording")
        shell.register("tema", self.cmd_tema, "cmd_tema_desc", "cat_management")
        shell.register("kontrol", self.cmd_kontrol, "cmd_kontrol_desc", "cat_management")
        shell.register("ekle", self.cmd_ekle, "cmd_ekle_desc", "cat_management")
        shell.register("duzenle", self.cmd_duzenle, "cmd_duzenle_desc", "cat_management")
        shell.register("sil", self.cmd_sil, "cmd_sil_desc", "cat_management")
        shell.register("iceaktar", self.cmd_iceaktar, "cmd_iceaktar_desc", "cat_management")
        shell.register("bildirim", self.cmd_bildirim, "cmd_bildirim_desc", "cat_management")
        shell.register("online-ara", self.cmd_online_ara, "cmd_online_ara_desc", "cat_listing")
        shell.register("online-ekle", self.cmd_online_ekle, "cmd_online_ekle_desc", "cat_management")
        shell.register("dil", self.cmd_dil, "cmd_dil_desc", "cat_management")
        shell.register("lang", self.cmd_dil, "cmd_dil_desc", "cat_management")

    def cmd_favori(self, args: List[str]):
        parser = argparse.ArgumentParser(prog="favori")
        parser.add_argument("id", nargs="?")
        parser.add_argument("-i", dest="id_flag", metavar="ID")
        try:
            parsed, _ = parser.parse_known_args(args)
            station_id = parsed.id_flag or parsed.id
            if not station_id:
                ui.print_error("Usage: favori <id>")
                return
            station = self.station_service.get_station(station_id)
            if not station:
                ui.print_error(L.get("msg_station_not_found"))
                return
            added = self.station_service.toggle_favorite(station.id)
            if added:
                ui.print_success(L.get("msg_fav_added", name=station.name))
            else:
                ui.print_info(L.get("msg_fav_removed", name=station.name))
        except SystemExit:
            ui.print_error("Usage: favori <id>")

    def cmd_favoriler(self, args: List[str]):
        favs = self.station_service.get_favorites()
        ui.print_station_table(L.get("cmd_favoriler_desc"), favs)

    def cmd_kaydet(self, args: List[str]):
        msg = self.player.start_recording()
        if "başladı" in msg:
            ui.print_success(msg)
        else:
            ui.print_error(msg)

    def cmd_kayitdur(self, args: List[str]):
        msg = self.player.stop_recording()
        ui.print_info(msg)

    def cmd_tema(self, args: List[str]):
        parser = argparse.ArgumentParser(prog="tema")
        parser.add_argument("isim", nargs="?")
        parser.add_argument("-i", dest="isim_flag", metavar="ISIM")
        try:
            parsed, _ = parser.parse_known_args(args)
            theme_name = parsed.isim_flag or parsed.isim
            if theme_name:
                if ui.set_theme(theme_name):
                    ui.print_success(f"Tema '{theme_name}' olarak ayarlandı.")
                else:
                    ui.print_error(f"Geçersiz tema. Mevcut: {', '.join(ui.get_themes())}")
            else:
                ui.console.print(f"[cyan]Mevcut Temalar:[/] {', '.join(ui.get_themes())}")
        except SystemExit:
            pass

    def cmd_kontrol(self, args: List[str]):
        parser = argparse.ArgumentParser(prog="kontrol")
        parser.add_argument("id", nargs="?")
        parser.add_argument("-i", dest="id_flag", metavar="ID")
        try:
            parsed, _ = parser.parse_known_args(args)
            station_id = parsed.id_flag or parsed.id
            stations = [self.station_service.get_station(
                station_id)] if station_id else self.station_service.get_all_stations()
            stations = [s for s in stations if s]

            if not stations:
                ui.print_error("Kontrol edilecek istasyon bulunamadı.")
                return

            ui.print_info(f"{len(stations)} istasyon kontrol ediliyor... (Bu işlem zaman alabilir)")

            success = 0
            for s in stations:
                try:
                    cmd = ["curl", "-s", "-I", "-m", "5", "-A", "VLC/3.0.16 LibVLC/3.0.16", s.url]
                    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                    if "HTTP/" in res.stdout and ("200" in res.stdout or "302" in res.stdout):
                        success += 1
                        if station_id:
                            ui.print_success(f"{s.name}: AKTİF")
                    else:
                        if station_id:
                            ui.print_error(f"{s.name}: BAŞARISIZ")
                except Exception:
                    if station_id:
                        ui.print_error(f"{s.name}: HATA")

            if not station_id:
                ui.print_info(f"Kontrol tamamlandı: {success}/{len(stations)} aktif.")
        except SystemExit:
            pass

    def cmd_ekle(self, args: List[str]):
        parser = argparse.ArgumentParser(prog="ekle")
        parser.add_argument("--id", required=True)
        parser.add_argument("--isim", required=True)
        parser.add_argument("--ulke", default="Türkiye")
        parser.add_argument("--tur", default="Çeşitli")
        parser.add_argument("--url", required=True)
        try:
            parsed = parser.parse_args(args)
            s = RadioStation(parsed.id, parsed.isim, parsed.ulke, parsed.tur, parsed.url)
            self.station_service.add_custom_station(s)
            ui.print_success(f"Özel istasyon eklendi: {s.name}")
        except SystemExit:
            ui.print_error("Kullanım: ekle --id <id> --isim <isim> --ulke <ulke> --tur <tur> --url <url>")

    def cmd_duzenle(self, args: List[str]):
        parser = argparse.ArgumentParser(prog="duzenle")
        parser.add_argument("--id", required=True)
        parser.add_argument("--isim")
        parser.add_argument("--ulke")
        parser.add_argument("--tur")
        parser.add_argument("--url")
        try:
            parsed = parser.parse_args(args)
            existing = self.station_service.get_station(parsed.id)
            if not existing or existing not in self.station_service.custom_stations:
                ui.print_error("Yalnızca özel istasyonlar düzenlenebilir.")
                return
            s = RadioStation(
                existing.id,
                parsed.isim or existing.name,
                parsed.ulke or existing.country,
                parsed.tur or existing.genre,
                parsed.url or existing.url
            )
            self.station_service.add_custom_station(s)
            ui.print_success("İstasyon güncellendi.")
        except SystemExit:
            ui.print_error("Kullanım: duzenle --id <id> [--isim ..] [--url ..] vs.")

    def cmd_sil(self, args: List[str]):
        parser = argparse.ArgumentParser(prog="sil")
        parser.add_argument("--id", required=True)
        try:
            parsed = parser.parse_args(args)
            if self.station_service.remove_custom_station(parsed.id):
                ui.print_success(f"İstasyon silindi: {parsed.id}")
            else:
                ui.print_error("Özel istasyon bulunamadı.")
        except SystemExit:
            pass

    def cmd_iceaktar(self, args: List[str]):
        parser = argparse.ArgumentParser(prog="iceaktar")
        parser.add_argument("-d", "--dosya", required=True)
        parser.add_argument("-u", "--ulke", default="İçe Aktarılan")
        parser.add_argument("-t", "--tur", default="Karma")
        parser.add_argument("-p", "--prefix", default="")
        try:
            parsed = parser.parse_args(args)
            count = self.station_service.import_playlist(parsed.dosya, parsed.ulke, parsed.tur, parsed.prefix)
            if count > 0:
                ui.print_success(f"{count} istasyon içe aktarıldı.")
            else:
                ui.print_error("İstasyon okunamadı veya dosya bulunamadı.")
        except SystemExit:
            pass

    def cmd_bildirim(self, args: List[str]):
        current = self.notification_service.is_enabled()
        self.notification_service.set_enabled(not current)
        state = "açık" if not current else "kapalı"
        ui.print_success(f"Masaüstü bildirimleri {state}.")

    def cmd_online_ara(self, args: List[str]):
        parser = argparse.ArgumentParser(prog="online-ara")
        parser.add_argument("-s", "--sorgu", default="")
        parser.add_argument("-u", "--ulke", default="")
        parser.add_argument("-t", "--tur", default="")
        parser.add_argument("-l", "--limit", type=int, default=15)
        try:
            parsed = parser.parse_args(args)
            if not parsed.sorgu and not parsed.ulke and not parsed.tur:
                ui.print_error("En az bir arama kriteri (-s, -u, -t) girin.")
                return

            ui.print_info("Aranıyor...")
            res = self.radio_browser.search(parsed.sorgu, parsed.ulke, parsed.tur, parsed.limit)
            self.last_online_search = res

            if not res:
                ui.print_error("İstasyon bulunamadı.")
                return

            from rich.table import Table
            table = Table(title="Online Arama Sonuçları")
            table.add_column("No")
            table.add_column("İsim")
            table.add_column("Ülke")
            table.add_column("Tür")

            for i, s in enumerate(res):
                table.add_row(str(i+1), s.name, s.country_display(), s.genre_display())
            ui.console.print(table)
            ui.print_info("Eklemek için: online-ekle -n <no>")
        except SystemExit:
            pass

    def cmd_online_ekle(self, args: List[str]):
        parser = argparse.ArgumentParser(prog="online-ekle")
        parser.add_argument("-n", "--no", type=int, required=True)
        try:
            parsed = parser.parse_args(args)
            idx = parsed.no - 1
            if idx < 0 or idx >= len(self.last_online_search):
                ui.print_error("Geçersiz numara. Önce 'online-ara' kullanın.")
                return

            os_station = self.last_online_search[idx]
            safe_id = f"rb-{os_station.uuid[:8]}"
            s = RadioStation(
                id=safe_id,
                name=os_station.name.strip() or "Bilinmeyen Radyo",
                country=os_station.country_display(),
                genre=os_station.genre_display(),
                url=os_station.url
            )
            self.station_service.add_custom_station(s)
            ui.print_success(f"İstasyon eklendi: {s.name} (ID: {s.id})")
        except SystemExit:
            ui.print_error("Kullanım: online-ekle -n <no>")

    def cmd_dil(self, args: List[str]):
        parser = argparse.ArgumentParser(prog="dil")
        parser.add_argument("-i", "--isim", choices=list(L.LANGUAGES.keys()))
        try:
            parsed, _ = parser.parse_known_args(args)
            if parsed.isim:
                self.settings_service.set_language(parsed.isim)
                L.set_language(parsed.isim)
                ui.print_success(L.get("lang_updated", lang=L.LANGUAGES[parsed.isim]))
            else:
                ui.console.print(f"[cyan]{L.get('cat_management')} > {L.get('lang_select_title')}:[/]")
                for code, name in L.LANGUAGES.items():
                    ui.console.print(f"  [bold cyan]{code}[/] - {name}")
                ui.print_info(f"Usage: lang -i <{'|'.join(L.LANGUAGES.keys())}>")
        except SystemExit:
            pass
