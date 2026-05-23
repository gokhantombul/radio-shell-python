import importlib.util
import unittest
from unittest.mock import MagicMock, patch

from src.radio.models import RadioStation
from src.radio.services.station_service import StationService

COMMAND_DEPS_AVAILABLE = all(
    importlib.util.find_spec(module) is not None
    for module in ("prompt_toolkit", "requests", "rich")
)

if COMMAND_DEPS_AVAILABLE:
    from src.radio.commands_management import ManagementCommands
    from src.radio.commands_playback import PlaybackCommands


def test_playback_registers_short_aliases():
    if not COMMAND_DEPS_AVAILABLE:
        raise unittest.SkipTest("command dependencies are not installed")

    shell = MagicMock()
    player = MagicMock()

    PlaybackCommands(
        shell,
        MagicMock(spec=StationService),
        MagicMock(),
        MagicMock(),
        player,
        MagicMock(),
    )

    registered_names = [call.args[0] for call in shell.register.call_args_list]
    assert "ileri" in registered_names
    assert "geri" in registered_names
    assert "rastgele" in registered_names


def test_favori_without_id_toggles_current_station():
    if not COMMAND_DEPS_AVAILABLE:
        raise unittest.SkipTest("command dependencies are not installed")

    shell = MagicMock()
    station = RadioStation("s1", "Station 1", "TR", "Pop", "http://example.com")
    station_service = MagicMock(spec=StationService)
    station_service.get_station.return_value = station
    station_service.toggle_favorite.return_value = True
    player = MagicMock()
    player.current_station = station

    commands = ManagementCommands(
        shell,
        station_service,
        MagicMock(),
        MagicMock(),
        player,
        MagicMock(),
    )

    with patch("src.radio.commands_management.ui.print_success"):
        commands.cmd_favori([])

    station_service.toggle_favorite.assert_called_once_with("s1")


def test_favori_without_id_requires_current_station():
    if not COMMAND_DEPS_AVAILABLE:
        raise unittest.SkipTest("command dependencies are not installed")

    shell = MagicMock()
    station_service = MagicMock(spec=StationService)
    player = MagicMock()
    player.current_station = None

    commands = ManagementCommands(
        shell,
        station_service,
        MagicMock(),
        MagicMock(),
        player,
        MagicMock(),
    )

    with patch("src.radio.commands_management.ui.print_error") as print_error:
        commands.cmd_favori([])

    station_service.toggle_favorite.assert_not_called()
    print_error.assert_called_once()
