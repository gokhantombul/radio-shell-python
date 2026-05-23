from types import SimpleNamespace

from src.radio import main


def test_main_accepts_kill_without_web(monkeypatch):
    called = {}

    class DummyConfig:
        web_pid_file = "unused"

        def ensure_dirs(self):
            called["ensured"] = True

    monkeypatch.setattr(main.sys, "argv", ["radio", "--kill"])
    monkeypatch.setattr(main, "RadioConfig", DummyConfig)
    monkeypatch.setattr(main, "stop_background_web_server", lambda config: called.setdefault("stopped", config))

    main.main()

    assert called["ensured"] is True
    assert isinstance(called["stopped"], DummyConfig)


def test_web_process_info_round_trip(tmp_path, monkeypatch):
    config = SimpleNamespace(web_pid_file=str(tmp_path / "web.pid"))
    monkeypatch.setattr(main, "_get_process_create_time", lambda pid: 123.45)

    main._write_web_process_info(config, 4242)

    assert main._read_web_process_info(config) == {
        "pid": 4242,
        "create_time": 123.45,
    }


def test_running_web_pid_removes_stale_file(tmp_path, monkeypatch):
    config = SimpleNamespace(web_pid_file=str(tmp_path / "web.pid"))
    main._write_web_process_info(config, 4242)
    monkeypatch.setattr(main, "_get_psutil_process", lambda pid: None)
    monkeypatch.setattr(main, "_pid_exists", lambda pid: False)

    assert main._get_running_web_pid(config) is None
    assert not (tmp_path / "web.pid").exists()


def test_remove_web_process_info_keeps_other_pid(tmp_path):
    config = SimpleNamespace(web_pid_file=str(tmp_path / "web.pid"))
    main._write_web_process_info(config, 4242)

    main._remove_web_process_info(config, expected_pid=9999)

    assert (tmp_path / "web.pid").exists()
