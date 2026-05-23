import argparse
import json
import os
import signal
import sys
import subprocess
import webbrowser
import threading
import time
from pathlib import Path
from rich.prompt import Prompt
from src.radio.config import RadioConfig
from src.radio.services.settings_service import SettingsService
from src.radio.services.station_service import StationService
from src.radio.services.statistics_service import StatisticsService
from src.radio.services.system_service import SystemService
from src.radio.services.radio_browser_service import RadioBrowserService
from src.radio.services.notification_service import NotificationService
from src.radio.services.localization_service import L
from src.radio.player import AudioPlayer
from src.radio.shell import InteractiveShell
from src.radio.commands_basic import BasicCommands
from src.radio.commands_playback import PlaybackCommands
from src.radio.commands_management import ManagementCommands
from src.radio import ui

from typing import Optional

WEB_URL = "http://127.0.0.1:8765"


def _get_psutil_process(pid: int):
    try:
        import psutil
        return psutil.Process(pid)
    except Exception:
        return None


def _pid_exists(pid: int) -> bool:
    process = _get_psutil_process(pid)
    if process:
        return process.is_running()
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _get_process_create_time(pid: int) -> Optional[float]:
    process = _get_psutil_process(pid)
    if not process:
        return None
    try:
        return process.create_time()
    except Exception:
        return None


def _read_web_process_info(config: RadioConfig) -> Optional[dict]:
    pid_path = Path(config.web_pid_file)
    if not pid_path.exists():
        return None

    try:
        content = pid_path.read_text(encoding="utf-8").strip()
        if not content:
            return None

        try:
            data = json.loads(content)
            pid = int(data["pid"])
            return {
                "pid": pid,
                "create_time": data.get("create_time"),
            }
        except json.JSONDecodeError:
            return {"pid": int(content), "create_time": None}
    except Exception:
        return None


def _write_web_process_info(config: RadioConfig, pid: int):
    pid_path = Path(config.web_pid_file)
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "pid": pid,
        "create_time": _get_process_create_time(pid),
        "url": WEB_URL,
    }
    pid_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _remove_web_process_info(config: RadioConfig, expected_pid: Optional[int] = None):
    pid_path = Path(config.web_pid_file)
    if expected_pid is not None:
        info = _read_web_process_info(config)
        if info and info["pid"] != expected_pid:
            return

    try:
        pid_path.unlink()
    except FileNotFoundError:
        pass


def _matches_recorded_process(info: dict, process) -> bool:
    expected_create_time = info.get("create_time")
    if expected_create_time is None or process is None:
        return True

    try:
        return abs(process.create_time() - expected_create_time) < 1
    except Exception:
        return True


def _get_running_web_pid(config: RadioConfig) -> Optional[int]:
    info = _read_web_process_info(config)
    if not info:
        return None

    pid = info["pid"]
    process = _get_psutil_process(pid)
    if not _pid_exists(pid):
        _remove_web_process_info(config, pid)
        return None

    if not _matches_recorded_process(info, process):
        _remove_web_process_info(config, pid)
        return None

    return pid


def _terminate_with_psutil(process) -> bool:
    try:
        children = process.children(recursive=True)
    except Exception:
        children = []

    try:
        process.terminate()
        process.wait(timeout=5)
    except Exception:
        try:
            process.kill()
            process.wait(timeout=2)
        except Exception:
            pass

    for child in children:
        try:
            if child.is_running():
                child.terminate()
        except Exception:
            pass

    for child in children:
        try:
            if child.is_running():
                child.wait(timeout=1)
        except Exception:
            try:
                child.kill()
            except Exception:
                pass

    try:
        return not process.is_running()
    except Exception:
        return True


def _terminate_with_os(pid: int) -> bool:
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return True
    except OSError:
        return False

    for _ in range(50):
        if not _pid_exists(pid):
            return True
        time.sleep(0.1)

    sigkill = getattr(signal, "SIGKILL", signal.SIGTERM)
    try:
        os.kill(pid, sigkill)
    except ProcessLookupError:
        return True
    except OSError:
        return False

    for _ in range(20):
        if not _pid_exists(pid):
            return True
        time.sleep(0.1)
    return not _pid_exists(pid)


def stop_background_web_server(config: RadioConfig) -> bool:
    info = _read_web_process_info(config)
    if not info:
        ui.print_info("Çalışan web sunucusu bulunamadı.")
        return False

    pid = info["pid"]
    process = _get_psutil_process(pid)
    if not _pid_exists(pid):
        _remove_web_process_info(config, pid)
        ui.print_info("Eski web PID dosyası temizlendi; çalışan web sunucusu yok.")
        return False

    if not _matches_recorded_process(info, process):
        _remove_web_process_info(config, pid)
        ui.print_info("Eski web PID dosyası temizlendi; PID artık farklı bir sürece ait.")
        return False

    ui.console.print(f"[bold yellow]Web sunucusu durduruluyor (PID: {pid})...[/]")
    stopped = _terminate_with_psutil(process) if process else _terminate_with_os(pid)
    if stopped:
        _remove_web_process_info(config, pid)
        ui.print_success("Web sunucusu durduruldu.")
        return True

    ui.print_error(f"Web sunucusu durdurulamadı (PID: {pid}).")
    return False


def ensure_language(config: RadioConfig) -> Optional[str]:
    settings_path = Path(config.settings_file)
    if settings_path.exists():
        try:
            import json
            with open(settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'language' in data:
                    return None  # Language is already set
        except Exception:
            pass

    ui.print_header("LANGUAGE SELECTION / DİL SEÇİMİ")
    ui.console.print("\n  Please select your language / Lütfen dilinizi seçin:\n")

    options = []
    for code, name in L.LANGUAGES.items():
        ui.console.print(f"  [bold cyan]{code}[/] - {name}")
        options.append(code)

    choice = Prompt.ask("\n  Selection", choices=options, default="en")
    return choice


def main():
    parser = argparse.ArgumentParser(description="Radio Shell")
    parser.add_argument("--web", action="store_true", help="Start the web interface")
    parser.add_argument("--foreground", action="store_true", help="Run web server in foreground")
    parser.add_argument("--kill", action="store_true", help="Stop the background web server")
    parser.add_argument("--kill-web", action="store_true", help="Stop the background web server")
    args = parser.parse_args()

    # 1. Initialize Configuration
    config = RadioConfig()
    config.ensure_dirs()

    if args.kill_web or args.kill:
        stop_background_web_server(config)
        return

    # 2. First-run Language Selection
    initial_lang = ensure_language(config)

    # 3. Initialize Services
    settings_service = SettingsService(config)
    if initial_lang:
        settings_service.set_language(initial_lang)

    # Set the global localization language
    L.set_language(settings_service.get_language())

    # Load user theme (now that L is set, though theme is not localized yet)
    ui.load_theme()

    station_service = StationService(config)
    station_service.init()
    stats_service = StatisticsService(config)
    radio_browser = RadioBrowserService()
    notification_service = NotificationService(settings_service)

    # 3. Initialize Player
    player = AudioPlayer(config, notification_service)

    if args.web:
        # WEB MODE
        try:
            import uvicorn
            from src.radio.web import create_app
        except ImportError:
            ui.console.print("[bold red]Hata:[/] Web modu için 'fastapi' ve 'uvicorn' paketleri gerekli.")
            ui.console.print("Yüklemek için: [bold cyan]pip install fastapi uvicorn[/]")
            return

        if not args.foreground:
            running_pid = _get_running_web_pid(config)
            if running_pid:
                ui.console.print(f"[bold green]✔ Web sunucusu zaten çalışıyor (PID: {running_pid})[/]")
                ui.console.print(f"[bold cyan]Tarayıcı açılıyor: {WEB_URL}[/]")
                webbrowser.open(WEB_URL)
                return

            # Background mode: Start the same command with --foreground in a new process
            ui.console.print("[bold green]Web sunucusu arka planda başlatılıyor...[/]")
            
            env = os.environ.copy()
            env["RADIO_WEB_NO_BROWSER"] = "1"
            
            # Use sys.executable to run the same python interpreter
            # Use -m src.radio.main to run it as a module
            p = subprocess.Popen(
                [sys.executable, "-m", "src.radio.main", "--web", "--foreground"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True if os.name != 'nt' else False,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
                env=env
            )
            _write_web_process_info(config, p.pid)
            
            ui.console.print(f"[bold green]✔ Web sunucusu arka planda çalışıyor (PID: {p.pid})[/]")
            ui.console.print(f"[bold cyan]Tarayıcı açılıyor: {WEB_URL}[/]")
            
            # Wait a moment for uvicorn to start before opening browser
            time.sleep(1.5)
            if p.poll() is not None:
                _remove_web_process_info(config, p.pid)
                ui.print_error("Web sunucusu başlatılamadı.")
                return
            webbrowser.open(WEB_URL)
            return

        # Foreground mode (either explicitly requested or the background child process)
        running_pid = _get_running_web_pid(config)
        if running_pid and running_pid != os.getpid():
            ui.console.print(f"[bold green]✔ Web sunucusu zaten çalışıyor (PID: {running_pid})[/]")
            return

        _write_web_process_info(config, os.getpid())
        app = create_app(player, station_service, settings_service)
        
        # Only print if we are not the backgrounded child (stdout is DEVNULL anyway, but let's be clean)
        # However, we don't strictly need to check since stdout is redirected.
        ui.console.print("[bold green]Web sunucusu başlatılıyor...[/]")
        
        # Only open browser if not suppressed (parent process already did it)
        if os.environ.get("RADIO_WEB_NO_BROWSER") != "1":
            def open_browser():
                time.sleep(1.5)
                ui.console.print(f"[bold cyan]Tarayıcı açılıyor: {WEB_URL}[/]")
                webbrowser.open(WEB_URL)
                
            threading.Thread(target=open_browser, daemon=True).start()
        
        try:
            uvicorn.run(app, host="127.0.0.1", port=8765, log_level="error")
        finally:
            player.stop()
            _remove_web_process_info(config, os.getpid())
    else:
        # CLI MODE
        # System Service
        system_service = SystemService(player)

        # 4. Initialize Interactive Shell
        shell = InteractiveShell(station_service)

        # 5. Register Commands
        basic_cmds = BasicCommands(shell, station_service, stats_service, system_service, player)
        PlaybackCommands(shell, station_service, settings_service, stats_service, player, basic_cmds)
        ManagementCommands(shell, station_service, radio_browser, notification_service, player, settings_service)

        # 6. Run the Shell Loop
        try:
            shell.run(player)
        finally:
            # 7. Cleanup
            player.stop()


if __name__ == "__main__":
    main()
