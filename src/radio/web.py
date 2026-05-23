import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional

from src.radio.player import AudioPlayer
from src.radio.services.station_service import StationService
from src.radio.services.settings_service import SettingsService
from src.radio.models import RadioStation

class StationInfo(BaseModel):
    id: str
    name: str
    genre: Optional[str]
    country: Optional[str]
    is_favorite: bool

class PlayerStatus(BaseModel):
    is_playing: bool
    current_station: Optional[StationInfo]
    current_song: Optional[str]
    volume: int
    is_muted: bool
    is_recording: bool
    elapsed_seconds: Optional[int] = None

def create_app(player: AudioPlayer, station_service: StationService, settings_service: SettingsService):
    from src.radio.services.localization_service import L
    L.set_language(settings_service.get_language())
    if not player.is_playing():
        player.volume = settings_service.get_volume()
        player.muted = settings_service.is_muted()

    app = FastAPI(title="Radio Shell API")

    @app.get("/api/stations", response_model=List[StationInfo])
    def get_stations():
        stations = station_service.get_all_stations()
        return [
            StationInfo(
                id=s.id,
                name=s.name,
                genre=s.genre,
                country=s.country,
                is_favorite=s.favorite
            ) for s in stations
        ]

    @app.get("/api/status", response_model=PlayerStatus)
    def get_status():
        current_station_info = None
        if player.current_station:
            s = player.current_station
            current_station_info = StationInfo(
                id=s.id,
                name=s.name,
                genre=s.genre,
                country=s.country,
                is_favorite=s.id in station_service.favorites
            )
        
        elapsed_seconds = None
        if player.playback_start_time:
            elapsed_seconds = max(0, int((datetime.now() - player.playback_start_time).total_seconds()))

        return PlayerStatus(
            is_playing=player.is_playing(),
            current_station=current_station_info,
            current_song=player.current_song,
            volume=player.volume,
            is_muted=player.muted,
            is_recording=player.is_recording() if hasattr(player, 'is_recording') else False,
            elapsed_seconds=elapsed_seconds
        )

    @app.post("/api/play/{station_id}")
    def play_station(station_id: str):
        station = station_service.get_station(station_id)
        if not station:
            raise HTTPException(status_code=404, detail="Station not found")
        
        player.play(station, settings_service.get_volume(), settings_service.is_muted())
        return {"status": "playing", "station": station.name}

    @app.post("/api/stop")
    def stop_playback():
        player.stop()
        return {"status": "stopped"}

    @app.post("/api/volume/{level}")
    def set_volume(level: int):
        if not (0 <= level <= 100):
            raise HTTPException(status_code=400, detail="Volume must be between 0 and 100")
        settings_service.set_volume(level)
        if level > 0:
            settings_service.set_muted(False)
        player.set_volume(level, unmute=True)
        return {"status": "volume_set", "level": level, "is_muted": player.muted}

    @app.post("/api/mute/{muted}")
    def set_mute(muted: bool):
        player.set_muted(muted)
        settings_service.set_muted(muted)
        return {"status": "muted" if muted else "unmuted", "is_muted": muted}

    @app.post("/api/favorite/{station_id}")
    def toggle_favorite(station_id: str):
        station = station_service.get_station(station_id)
        if not station:
            raise HTTPException(status_code=404, detail="Station not found")
        is_fav = station_service.toggle_favorite(station.id)
        return {"status": "success", "is_favorite": is_fav}

    @app.post("/api/record/start")
    def start_recording():
        msg = player.start_recording()
        return {"status": "success", "message": msg}

    @app.post("/api/record/stop")
    def stop_recording():
        msg = player.stop_recording()
        return {"status": "success", "message": msg}

    @app.get("/api/system")
    def get_system_info():
        import psutil
        import platform
        process = psutil.Process()
        mem_info = process.memory_info()
        return {
            "os": platform.system(),
            "python_version": platform.python_version(),
            "memory_usage_mb": round(mem_info.rss / 1024 / 1024, 2),
            "cpu_percent": process.cpu_percent()
        }

    @app.get("/api/language")
    def get_language():
        from src.radio.services.localization_service import L
        return {
            "current": settings_service.get_language(),
            "available": L.LANGUAGES
        }

    @app.post("/api/language/{lang_code}")
    def set_language(lang_code: str):
        from src.radio.services.localization_service import L
        if lang_code not in L.LANGUAGES:
            raise HTTPException(status_code=400, detail="Language not supported")
        settings_service.set_language(lang_code)
        L.set_language(lang_code)
        return {"status": "success", "language": lang_code}

    @app.get("/api/locales")
    def get_locales():
        from src.radio.services.localization_service import L
        return L.STRINGS.get(L.current_lang, L.STRINGS["en"])

    # Mount static files
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir, exist_ok=True)
    
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app
