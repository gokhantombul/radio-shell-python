import pytest

pytest.importorskip("fastapi")

from fastapi import HTTPException

from src.radio.models import RadioStation
from src.radio.web import create_app


class DummyPlayer:
    current_station = None
    current_song = None
    playback_start_time = None
    volume = 100
    muted = False

    def is_playing(self):
        return False

    def is_recording(self):
        return False


class DummySettingsService:
    def get_language(self):
        return "en"

    def get_volume(self):
        return 100

    def is_muted(self):
        return False


class DummyStationService:
    def __init__(self):
        self.station = RadioStation("s1", "Station 1", "TR", "Pop", "http://example.com")
        self.favorites = set()

    def get_station(self, station_id):
        if station_id == self.station.id:
            return self.station
        return None

    def toggle_favorite(self, station_id):
        if station_id in self.favorites:
            self.favorites.remove(station_id)
            return False

        self.favorites.add(station_id)
        return True


def test_favorite_endpoint_returns_success_when_removing_favorite():
    station_service = DummyStationService()
    app = create_app(DummyPlayer(), station_service, DummySettingsService())
    toggle_favorite = next(
        route.endpoint
        for route in app.routes
        if getattr(route, "path", None) == "/api/favorite/{station_id}"
    )

    add_response = toggle_favorite("s1")
    assert add_response["is_favorite"] is True

    remove_response = toggle_favorite("s1")
    assert remove_response == {"status": "success", "is_favorite": False}
    assert "s1" not in station_service.favorites


def test_favorite_endpoint_returns_404_for_missing_station():
    app = create_app(DummyPlayer(), DummyStationService(), DummySettingsService())
    toggle_favorite = next(
        route.endpoint
        for route in app.routes
        if getattr(route, "path", None) == "/api/favorite/{station_id}"
    )

    with pytest.raises(HTTPException) as exc_info:
        toggle_favorite("missing")

    assert exc_info.value.status_code == 404
