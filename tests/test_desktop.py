import asyncio
import io
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from desktop_controller import BotController, LogEntry, decode_event
from desktop_worker import emit_log, serve
from runtime_lock import AlreadyRunningError, InstanceLock


def test_process_lock_blocks_duplicate_and_is_reusable(tmp_path):
    path = tmp_path / "data" / ".bot.lock"
    with InstanceLock(path):
        with pytest.raises(AlreadyRunningError):
            InstanceLock(path).acquire()
    with InstanceLock(path):
        pass


def test_lock_released_after_crashed_process(tmp_path):
    path = tmp_path / "worker.lock"
    root = Path(__file__).resolve().parents[1]
    code = (
        "import os, sys; from pathlib import Path; from runtime_lock import InstanceLock; "
        "lock=InstanceLock(Path(sys.argv[1])).acquire(); os._exit(2)"
    )
    child = subprocess.run(
        [sys.executable, "-c", code, str(path)], cwd=root, capture_output=True, timeout=10
    )
    assert child.returncode == 2
    with InstanceLock(path):
        pass


def test_controller_missing_files_does_not_start_process(tmp_path, monkeypatch):
    popen = MagicMock()
    monkeypatch.setattr("desktop_controller.subprocess.Popen", popen)
    with pytest.raises(FileNotFoundError):
        BotController(tmp_path).start()
    popen.assert_not_called()


def fake_process():
    process = MagicMock()
    process.poll.return_value = None
    process.stdin = io.StringIO()
    process.stdout = io.StringIO()
    return process


def controller_with_process(tmp_path):
    controller = BotController(tmp_path)
    controller.process = fake_process()
    return controller


def test_stop_requests_graceful_exit_without_killing(tmp_path):
    controller = controller_with_process(tmp_path)
    controller.stop()
    assert controller.process.stdin.getvalue() == "STOP\n"
    assert controller.state == "stopping"
    controller.process.kill.assert_not_called()
    controller.stop()
    assert controller.process.stdin.getvalue() == "STOP\n"


def test_timeout_only_kills_owned_process(tmp_path, monkeypatch):
    monkeypatch.setattr("desktop_controller.time.monotonic", lambda: 100)
    controller = controller_with_process(tmp_path)
    controller.stop()
    monkeypatch.setattr("desktop_controller.time.monotonic", lambda: 111)
    controller.poll()
    controller.process.kill.assert_called_once_with()


def test_connected_is_not_inferred_from_running_process(tmp_path):
    controller = controller_with_process(tmp_path)
    controller.state = "starting"
    assert controller.poll() == "starting"
    controller.events.put("online")
    assert controller.poll() == "online"


def test_stop_ignores_late_connected_event(tmp_path):
    controller = controller_with_process(tmp_path)
    controller.stop()
    controller.events.put("online")
    assert controller.poll() == "stopping"


def test_exit_cleans_up_handles(tmp_path):
    controller = controller_with_process(tmp_path)
    process = controller.process
    controller.stop()
    process.poll.return_value = 0
    assert controller.poll() == "stopped"
    assert controller.process is None
    assert process.stdin.closed and process.stdout.closed


def test_unexpected_exit_shows_error(tmp_path):
    controller = controller_with_process(tmp_path)
    controller.process.poll.return_value = 1
    assert controller.poll() == "error"


def test_only_known_status_messages_are_exposed(tmp_path):
    controller = BotController(tmp_path)
    process = fake_process()
    process.stdout = io.StringIO("STATE:online\nsecret\nSTATE:unknown\n")
    controller._read_events(process, controller.events)
    assert controller.events.get() == "online"
    assert controller.events.empty()


def test_known_log_codes_become_fixed_text():
    entry = decode_event("LOG:login\n")
    assert isinstance(entry, LogEntry)
    assert entry.level == "info" and "HTTPS" in entry.text
    assert decode_event("LOG:ready:3").text == "Conectado e pronto em 3 servidor(es)."
    assert (
        decode_event("LOG:command:atributo definir").text == "Comando /atributo definir executado."
    )


@pytest.mark.parametrize(
    "line",
    [
        "LOG:unknown",
        "LOG:login:extra",  # código sem argumento não aceita argumento
        "LOG:ready",  # código com argumento exige argumento
        "LOG:ready:<@123> token",
        "LOG:command:" + "a" * 41,
        "LOG:command:DROP;TABLE",
        "Traceback (most recent call last):",
    ],
)
def test_unknown_or_unsafe_log_lines_are_dropped(line):
    assert decode_event(line) is None


def test_worker_never_writes_unsafe_argument(capsys):
    emit_log("command", "atributo definir")
    emit_log("command", "<@123> segredo!")
    emit_log("ready", 2)
    assert capsys.readouterr().out.splitlines() == ["LOG:command:atributo definir", "LOG:ready:2"]


def test_controller_collects_worker_and_own_logs(tmp_path):
    controller = controller_with_process(tmp_path)
    controller.events.put(decode_event("LOG:gateway"))
    controller.events.put("online")
    logs = controller.take_logs()
    assert [entry.level for entry in logs] == ["info"]
    assert controller.state == "online" and controller.online_since is not None
    controller.stop()
    controller.process.poll.return_value = 0
    controller.poll()
    texts = [entry.text for entry in controller.take_logs()]
    assert texts == ["Desligamento solicitado.", "Bot desligado."]
    assert controller.take_logs() == []
    assert controller.online_since is None


def test_error_state_is_logged_once(tmp_path):
    controller = controller_with_process(tmp_path)
    controller.events.put("missing_config")
    controller.process.poll.return_value = 1
    controller.poll()
    logs = controller.take_logs()
    assert [(entry.level, entry.text) for entry in logs] == [
        ("error", "Confira DISCORD_TOKEN (e DEV_GUILD_ID, se usado) no .env do projeto.")
    ]


def test_message_handler_reports_activity_without_content():
    from unittest.mock import AsyncMock

    from message_handler import MessageHandler

    reports = []
    handler = MessageHandler(SimpleNamespace(attributes=AsyncMock()), lambda *a: reports.append(a))

    def message(content):
        return SimpleNamespace(
            content=content,
            guild=SimpleNamespace(id=1),
            author=SimpleNamespace(bot=False),
            webhook_id=None,
            reply=AsyncMock(),
        )

    asyncio.run(handler.handle(message("d20 segredo do jogador")))
    asyncio.run(handler.handle(message("d1")))
    asyncio.run(handler.handle(message("olá")))
    assert reports == [("roll",), ("roll_rejected",)]


@pytest.mark.parametrize("command", ["STOP\n", ""])
def test_worker_closes_client_on_stop_or_parent_eof(command):
    class FakeClient:
        settings = SimpleNamespace(token="fake-token")
        closed = False

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            self.closed = True

        async def start(self, token):
            assert token == "fake-token"
            await asyncio.Event().wait()

    client = FakeClient()
    asyncio.run(serve(client, io.StringIO(command)))
    assert client.closed


def test_stop_before_connecting_is_safe(tmp_path):
    controller = BotController(tmp_path)
    controller.stop()
    assert controller.poll() == "stopped"


@pytest.mark.skipif(sys.platform != "win32", reason="Painel nativo para Windows")
def test_gui_start_stop_buttons_without_discord(monkeypatch, tmp_path):
    import tkinter as tk

    from desktop_app import ControlPanel

    root = tk.Tk()
    root.withdraw()
    try:
        panel = ControlPanel(root, tmp_path)
        panel.controller = MagicMock()
        panel.controller.running = False
        panel.controller.poll.return_value = "stopped"
        panel.controller.take_logs.return_value = [
            LogEntry(datetime(2026, 11, 5, 18, 30), "ok", "Conectado e pronto em 2 servidor(es).")
        ]
        panel.refresh()
        assert "18:30:00  Conectado e pronto em 2 servidor(es)." in panel.log.get("1.0", "end")
        panel.controller.take_logs.return_value = []
        panel.start_button.invoke()
        panel.controller.start.assert_called_once_with()
        panel.controller.running = True
        panel.controller.poll.return_value = "online"
        panel.refresh()
        assert str(panel.start_button["state"]) == "disabled"
        panel.stop_button.invoke()
        panel.controller.stop.assert_called_once_with()
        panel.close()
        assert panel.closing
        panel.controller.running = False
        panel.refresh()
    finally:
        try:
            root.destroy()
        except tk.TclError:
            pass


@pytest.mark.skipif(sys.platform != "win32", reason="Processo do painel Windows")
def test_real_hidden_process_start_stop_without_discord(tmp_path):
    scripts = tmp_path / ".venv" / "Scripts"
    scripts.mkdir(parents=True)
    shutil.copyfile(sys.executable, scripts / "python.exe")
    shutil.copyfile(
        Path(sys.executable).parents[1] / "pyvenv.cfg", tmp_path / ".venv" / "pyvenv.cfg"
    )
    (tmp_path / "desktop_worker.py").write_text(
        "import sys\nprint('STATE:online', flush=True)\n"
        "assert sys.stdin.readline().strip() == 'STOP'\n"
        "print('STATE:stopped', flush=True)\n",
        encoding="utf-8",
    )
    controller = BotController(tmp_path)
    try:
        controller.start()
        first_process = controller.process
        controller.start()  # Um segundo clique não cria outro processo.
        assert controller.process is first_process
        deadline = time.monotonic() + 5
        while controller.poll() != "online" and time.monotonic() < deadline:
            time.sleep(0.02)
        assert controller.state == "online"
        controller.stop()
        deadline = time.monotonic() + 5
        while controller.process is not None and time.monotonic() < deadline:
            controller.poll()
            time.sleep(0.02)
        assert controller.process is None
        assert controller.state == "stopped"
    finally:
        if controller.running:
            controller.process.kill()
            controller.process.wait(timeout=5)
            controller.poll()
