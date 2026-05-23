import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from src.radio.player import AudioPlayer
from src.radio.config import RadioConfig
from src.radio.services.notification_service import NotificationService
from src.radio.models import RadioStation


class TestAudioPlayer(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock(spec=RadioConfig)
        self.config.recordings_dir = "/tmp/radio-recordings"
        self.notification_service = MagicMock(spec=NotificationService)
        self.player = AudioPlayer(self.config, self.notification_service)

    @patch("subprocess.Popen")
    @patch("src.radio.player.datetime")
    def test_recording_flow(self, mock_datetime, mock_popen):
        # Mocking station and playback state
        station = RadioStation("test-id", "Test Station", "TR", "Pop", "http://test.url")
        self.player.current_station = station
        self.player.process = MagicMock()  # Simulate radio is playing
        self.player.process.poll.return_value = None

        mock_datetime.now.return_value.strftime.return_value = "20231027_120000"

        # Test start_recording
        res_start = self.player.start_recording()
        self.assertIn("Kayıt başladı", res_start)
        self.assertIsNotNone(self.player.current_record_path)
        self.assertIn("test_station_20231027_120000.mp3", self.player.current_record_path)

        # Mocking record process for stop_recording
        mock_record_process = MagicMock()
        mock_record_process.poll.return_value = None
        self.player.record_process = mock_record_process

        # Test stop_recording
        res_stop = self.player.stop_recording()
        self.assertIn("Kayıt durduruldu", res_stop)
        self.assertIn("/tmp/radio-recordings/test_station_20231027_120000.mp3", res_stop)
        self.assertIsNone(self.player.current_record_path)
        self.assertIsNone(self.player.record_process)

    @patch("subprocess.Popen")
    def test_muted_player_starts_ffplay_with_zero_effective_volume(self, mock_popen):
        station = RadioStation("test-id", "Test Station", "TR", "Pop", "http://test.url")
        mock_process = MagicMock()
        mock_process.stderr = None
        mock_popen.return_value = mock_process
        self.config.player = SimpleNamespace(command="ffplay", args=["-nodisp"])

        self.player.current_station = station
        self.player.volume = 80
        self.player.muted = True

        self.player._start_ffplay()

        cmd = mock_popen.call_args.args[0]
        self.assertEqual(cmd[cmd.index("-volume") + 1], "0")

    def test_setting_volume_can_unmute_without_losing_volume(self):
        self.player.muted = True

        self.player.set_volume(40, unmute=True)

        self.assertEqual(self.player.volume, 40)
        self.assertFalse(self.player.muted)


if __name__ == "__main__":
    unittest.main()
