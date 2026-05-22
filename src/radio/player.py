import os
import re
import subprocess
import threading
import time
from datetime import datetime
from typing import Optional, Callable

from src.radio.config import RadioConfig
from src.radio.models import RadioStation
from src.radio.services.notification_service import NotificationService
from src.radio.services.localization_service import L


class AudioPlayer:
    def __init__(self, config: RadioConfig, notification_service: NotificationService):
        self.config = config
        self.notification_service = notification_service
        self.process: Optional[subprocess.Popen] = None
        self.record_process: Optional[subprocess.Popen] = None
        self.current_record_path: Optional[str] = None
        self.current_station: Optional[RadioStation] = None
        self.current_song: Optional[str] = None
        self.volume: int = 100

        self.on_song_change: Optional[Callable[[str], None]] = None
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        self._watchdog_thread: Optional[threading.Thread] = None
        self.last_metadata_update: Optional[datetime] = None
        self.playback_start_time: Optional[datetime] = None
        self.codec: Optional[str] = None
        self.sample_rate: Optional[str] = None
        self.channels: Optional[str] = None
        self.bitrate: Optional[str] = None

    def play(self, station: RadioStation, initial_volume: int):
        self.stop()
        self.current_station = station
        self.volume = initial_volume
        self.current_song = None
        self.playback_start_time = datetime.now()
        self.last_metadata_update = None
        self._stop_event.clear()

        self._start_ffplay()

        # Start watchdog thread
        self._watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self._watchdog_thread.start()

    def _start_ffplay(self):
        if not self.current_station:
            return

        cmd = [self.config.player.command]
        cmd.extend(self.config.player.args)

        if "-loglevel" in cmd:
            idx = cmd.index("-loglevel")
            if idx + 1 < len(cmd):
                cmd[idx + 1] = "info"
        else:
            cmd.extend(["-loglevel", "info"])

        cmd.extend(["-volume", str(self.volume), self.current_station.url])

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            self._monitor_thread = threading.Thread(target=self._monitor_output, daemon=True)
            self._monitor_thread.start()
        except Exception as e:
            print(f"Player start error: {e}")

    def _watchdog_loop(self):
        retries = 0
        max_retries = 3
        while not self._stop_event.is_set():
            time.sleep(2)
            if self._stop_event.is_set():
                break

            # If process ended unexpectedly
            if self.process and self.process.poll() is not None:
                if retries < max_retries:
                    retries += 1
                    # Give a small delay before reconnecting
                    time.sleep(1)
                    if not self._stop_event.is_set():
                        # Restart the process
                        self._start_ffplay()
                else:
                    # Too many retries, give up
                    break
            else:
                # If running fine, we can reset retries (e.g. after a long successful uptime)
                # But for simplicity, we just keep the retry count as is unless we want to reset it on successful play.
                pass

    def stop(self):
        self._stop_event.set()
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except Exception:
                self.process.kill()
            self.process = None

        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1)

        if self._watchdog_thread and self._watchdog_thread.is_alive():
            self._watchdog_thread.join(timeout=1)

        self.current_station = None
        self.current_song = None
        self.codec = None
        self.sample_rate = None
        self.channels = None
        self.bitrate = None
        self.playback_start_time = None

        self.stop_recording()

    def set_volume(self, volume: int):
        self.volume = max(0, min(100, volume))
        if self.is_playing():
            # Restart the process so the new volume takes effect
            if self.process:
                try:
                    self.process.terminate()
                    self.process.wait(timeout=1)
                except Exception:
                    self.process.kill()
                self.process = None
            self._start_ffplay()

    def is_playing(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def start_recording(self) -> str:
        if not self.is_playing() or not self.current_station:
            return L.get("msg_not_playing")
        if self.is_recording():
            return L.get("msg_already_recording")

        self.config.ensure_dirs()
        safe_name = "".join(c if c.isalnum() else "_" for c in self.current_station.name.lower())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{timestamp}.mp3"
        filepath = os.path.join(self.config.recordings_dir, filename)

        cmd = [
            "ffmpeg", "-y",
            "-user_agent", "VLC/3.0.16 LibVLC/3.0.16",
            "-reconnect", "1", "-reconnect_at_eof", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "5",
            "-i", self.current_station.url,
            "-c:a", "libmp3lame", "-b:a", "128k",
            filepath
        ]

        try:
            self.record_process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self.current_record_path = filepath
            return L.get("msg_recording_started", file=filename)
        except Exception as e:
            return L.get("msg_recording_failed", error=e)

    def stop_recording(self) -> str:
        if not self.is_recording():
            return L.get("msg_no_active_record")

        saved_path = self.current_record_path
        if self.record_process:
            try:
                self.record_process.terminate()
                self.record_process.wait(timeout=2)
            except Exception:
                self.record_process.kill()

        self.record_process = None
        self.current_record_path = None

        if saved_path:
            return L.get("msg_recording_stopped", path=saved_path)
        return L.get("msg_recording_stopped_simple")

    def is_recording(self) -> bool:
        return self.record_process is not None and self.record_process.poll() is None

    def _monitor_output(self):
        if not self.process or not self.process.stderr:
            return

        icy_pattern = re.compile(r"StreamTitle\s*:\s*([^;]+)")
        audio_pattern = re.compile(r"Stream #.*Audio: ([^,]+), ([^,]+), ([^,]+)")
        bitrate_pattern = re.compile(r", ([0-9]+ [kK]b/s)")

        try:
            for line in iter(self.process.stderr.readline, ''):
                if self._stop_event.is_set():
                    break
                if not line:
                    continue

                # ICY Metadata check
                match = icy_pattern.search(line)
                if match:
                    title = match.group(1).strip()
                    if title in ("-", "Unknown", "null", "no title"):
                        continue

                    if title != self.current_song:
                        self.current_song = title
                        self.last_metadata_update = datetime.now()
                        if self.current_station:
                            self.notification_service.notify(self.current_station.name, title)
                        if self.on_song_change:
                            self.on_song_change(title)
                    continue

                # Audio stream info check
                match_audio = audio_pattern.search(line)
                if match_audio:
                    codec_raw = match_audio.group(1).split(' ')[0].strip().upper()
                    self.codec = "AAC" if "AAC" in codec_raw else codec_raw

                    sample_hz = match_audio.group(2).strip()
                    if "Hz" in sample_hz:
                        try:
                            hz_val = int(sample_hz.replace(" Hz", ""))
                            if hz_val >= 1000:
                                self.sample_rate = f"{hz_val / 1000:.1f} kHz".replace(".0 kHz", " kHz")
                            else:
                                self.sample_rate = sample_hz
                        except ValueError:
                            self.sample_rate = sample_hz
                    else:
                        self.sample_rate = sample_hz

                    self.channels = match_audio.group(3).strip()

                    # Try to find bitrate in the same line
                    match_bitrate = bitrate_pattern.search(line)
                    if match_bitrate:
                        self.bitrate = match_bitrate.group(1).strip()
        except Exception:
            pass
