import pytest
from unittest.mock import MagicMock
from prompt_toolkit.document import Document
from src.radio.shell import RadioCompleter, InteractiveShell
from src.radio.services.station_service import StationService
from src.radio.models import RadioStation


@pytest.fixture
def mock_station_service():
    service = MagicMock(spec=StationService)
    service.get_all_stations.return_value = [
        RadioStation(id="tr-powerturk", name="PowerTürk", url="url1", country="Turkey", genre="Pop"),
        RadioStation(id="tr-powerfm", name="Power FM", url="url2", country="Turkey", genre="Pop"),
        RadioStation(id="kralpop", name="Kral Pop", url="url3", country="Turkey", genre="Pop"),
    ]
    service.get_countries.return_value = ["Turkey", "Germany", "USA"]
    service.get_genres.return_value = ["Pop", "Rock", "Jazz"]
    return service


@pytest.fixture
def mock_shell():
    shell = MagicMock(spec=InteractiveShell)
    shell.commands = {"cal": MagicMock(), "ara": MagicMock()}
    return shell


def test_command_completion_substring(mock_shell, mock_station_service):
    completer = RadioCompleter(mock_shell, mock_station_service)

    # Case-insensitive substring match for 'al' should find 'cal'
    doc = Document("al", cursor_position=2)
    completions = list(completer.get_completions(doc, None))
    assert any(c.text == "cal" for c in completions)


def test_station_id_completion_substring(mock_shell, mock_station_service):
    completer = RadioCompleter(mock_shell, mock_station_service)

    # Typing 'cal power' should find both power stations
    doc = Document("cal power", cursor_position=9)
    completions = list(completer.get_completions(doc, None))
    assert len(completions) == 2
    assert any(c.text == "tr-powerturk" for c in completions)
    assert any(c.text == "tr-powerfm" for c in completions)


def test_station_name_completion_substring(mock_shell, mock_station_service):
    completer = RadioCompleter(mock_shell, mock_station_service)

    # Typing 'cal türk' should find 'tr-powerturk'
    doc = Document("cal türk", cursor_position=8)
    completions = list(completer.get_completions(doc, None))
    assert len(completions) == 1
    assert completions[0].text == "tr-powerturk"


def test_country_completion_substring(mock_shell, mock_station_service):
    completer = RadioCompleter(mock_shell, mock_station_service)

    # Typing 'ulke rk' should find 'Turkey'
    doc = Document("ulke rk", cursor_position=7)
    completions = list(completer.get_completions(doc, None))
    assert any(c.text == "Turkey" for c in completions)
