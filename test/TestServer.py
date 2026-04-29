# tests for ServerController
from pathlib import Path
import json
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import components.ServerController as server_module
from components.ServerController import ServerController


class FakeResponse:
    def __init__(self, data):
        self.data = data
        self.status_code = 200
        self.text = json.dumps(data)

    def json(self):
        return self.data

def make_server(tmp_path, monkeypatch):
    monkeypatch.setenv("ICN_PRIVATE_API_KEY", "test-key")
    server = ServerController(str(tmp_path), debug=False)
    return server

def test_server_starts_with_no_user(tmp_path, monkeypatch):
    server = make_server(tmp_path, monkeypatch)

    assert server.user is None
    assert server.UUID == 0
    assert server.UUID_expiry == 0

def test_ping_alive(tmp_path, monkeypatch):
    server = make_server(tmp_path, monkeypatch)

    with patch.object(server_module.requests, "get",
                      return_value=FakeResponse({"STATUS": "alive"})):
        assert server.ping() is True

def test_ping_maintenance(tmp_path, monkeypatch):
    server = make_server(tmp_path, monkeypatch)

    with patch.object(server_module.requests, "get",
                      return_value=FakeResponse({"STATUS": "maintenance"})):
        assert server.ping() is False

def test_login_sets_session(tmp_path, monkeypatch):
    server = make_server(tmp_path, monkeypatch)
    expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

    fake_response = FakeResponse({
        "success": True,
        "sessionUUID": "abc123",
        "expiresOn": expires
    })

    with patch.object(server_module.requests, "post", return_value=fake_response):
        result = server.login("test")

    assert result is not False
    assert server.user == "test"
    assert server.UUID == "abc123"

def test_login_fails(tmp_path, monkeypatch):
    server = make_server(tmp_path, monkeypatch)

    with patch.object(server_module.requests, "post",
                      return_value=FakeResponse({"success": False})):
        assert server.login("baduser") is False

    assert server.user is None

def test_logout_clears_user(tmp_path, monkeypatch):
    server = make_server(tmp_path, monkeypatch)
    server.user = "test"
    server.UUID = "abc"

    assert server.logout() is True
    assert server.user is None
    assert server.UUID == 0

def test_validate_good_session(tmp_path, monkeypatch):
    server = make_server(tmp_path, monkeypatch)
    server.user = "test"
    server.UUID = "abc"
    server.UUID_expiry = (
        datetime.now(timezone.utc) + timedelta(minutes=30)
    ).isoformat()

    assert server.validate() is True

def test_validate_expired_session(tmp_path, monkeypatch):
    server = make_server(tmp_path, monkeypatch)
    server.user = "test"
    server.UUID = "abc"
    server.UUID_expiry = (
        datetime.now(timezone.utc) - timedelta(minutes=30)
    ).isoformat()

    assert server.validate() is False

def test_parse_csv_makes_json_file(tmp_path, monkeypatch):
    server = make_server(tmp_path, monkeypatch)
    server.user = "test"

    scans = tmp_path / "scans"
    scans.mkdir()
    server.file_dir = str(scans)

    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(
        "nm,abs\n"
        "units,units\n"
        "260,0.12\n"
        "261,0.15\n"
        "end,end\n"
    )

    result = server.parse_csv(str(csv_file))

    assert result is True

    output_file = scans / "test_sample_unsent.json"
    assert output_file.exists()

    text = output_file.read_text()
    assert "260" in text
    assert "0.12" in text

def test_parse_csv_without_user_fails(tmp_path, monkeypatch):
    server = make_server(tmp_path, monkeypatch)

    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("a,b\n")

    assert server.parse_csv(str(csv_file)) is False

def test_send_data_bad_file_name(tmp_path, monkeypatch):
    server = make_server(tmp_path, monkeypatch)

    file = tmp_path / "sample.json"
    file.write_text("[]")

    assert server.send_data(str(file)) is False

def test_send_data_success(tmp_path, monkeypatch):
    server = make_server(tmp_path, monkeypatch)
    server.user = "test"
    server.UUID = "abc"
    server.UUID_expiry = (
        datetime.now(timezone.utc) + timedelta(minutes=30)
    ).isoformat()

    data_file = tmp_path / "test_sample_unsent.json"
    data_file.write_text('[\n{"nm": 260, "abs": 0.12}\n]')

    with patch.object(server_module.requests, "post",
                      return_value=FakeResponse({"success": True})):
        result = server.send_data(str(data_file))

    assert result is True
    assert not data_file.exists()
    assert (tmp_path / "test_sample_sent.json").exists()

def test_send_all_data_empty_folder(tmp_path, monkeypatch):
    server = make_server(tmp_path, monkeypatch)
    server.file_dir = str(tmp_path / "missing_folder")

    assert server.send_all_data() == []

def test_send_all_data_finds_unsent_file(tmp_path, monkeypatch):
    server = make_server(tmp_path, monkeypatch)

    scans = tmp_path / "scans"
    scans.mkdir()
    server.file_dir = str(scans)

    good_file = scans / "test_sample_unsent.json"
    good_file.write_text("[]")

    (scans / "test_sample_sent.json").write_text("[]")
    (scans / "notes.txt").write_text("ignore")

    with patch.object(server, "send_data", return_value=True):
        result = server.send_all_data()

    assert result == [("test_sample_unsent.json", True)]
    