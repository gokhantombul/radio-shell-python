from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RadioStation:
    id: str
    name: str
    country: str
    genre: str
    url: str
    favorite: bool = False

    def with_favorite(self, fav: bool) -> 'RadioStation':
        return RadioStation(self.id, self.name, self.country, self.genre, self.url, fav)


@dataclass
class UserSettings:
    volume: int = 100
    lastStationId: Optional[str] = None
    notificationsEnabled: bool = True
    language: str = "en"
    muted: bool = False

    @staticmethod
    def defaults() -> 'UserSettings':
        return UserSettings(100, None, True, "en", False)

    def with_volume(self, new_volume: int) -> 'UserSettings':
        return UserSettings(new_volume, self.lastStationId, self.notificationsEnabled, self.language, self.muted)

    def with_last_station_id(self, station_id: str) -> 'UserSettings':
        return UserSettings(self.volume, station_id, self.notificationsEnabled, self.language, self.muted)

    def with_notifications_enabled(self, enabled: bool) -> 'UserSettings':
        return UserSettings(self.volume, self.lastStationId, enabled, self.language, self.muted)

    def with_language(self, language: str) -> 'UserSettings':
        return UserSettings(self.volume, self.lastStationId, self.notificationsEnabled, language, self.muted)

    def with_muted(self, muted: bool) -> 'UserSettings':
        return UserSettings(self.volume, self.lastStationId, self.notificationsEnabled, self.language, muted)


@dataclass
class StationList:
    stations: List[RadioStation] = field(default_factory=list)
