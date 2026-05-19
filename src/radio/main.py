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

def ensure_language(config: RadioConfig) -> Optional[str]:
    settings_path = Path(config.settings_file)
    if settings_path.exists():
        try:
            import json
            with open(settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'language' in data:
                    return None # Language is already set
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
    # 1. Initialize Configuration
    config = RadioConfig()
    config.ensure_dirs()

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
