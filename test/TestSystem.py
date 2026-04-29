# This tests the system controller
# Integration Testing
from pathlib import Path
from unittest.mock import patch
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import components.SystemController as system_module
from components.SystemController import SystemController


class MockServerController:
    def __init__(self, project_root, file_dir=None, debug=True):
        self.project_root = project_root
        self.file_dir = file_dir
        self.debug = debug
        self.user = None
        self.connect_value = True
        self.login_value = True
        self.logout_value = True
        self.logged_in_value = False
        self.send_all_data_value = []
        self.parsed_csv_paths = []

    def connect(self):
        return self.connect_value

    def login(self, username):
        if self.login_value:
            self.user = username
        return self.login_value

    def logout(self):
        if self.logout_value:
            self.user = None
        return self.logout_value

    def is_logged_in(self):
        return self.logged_in_value

    def send_all_data(self):
        return self.send_all_data_value

    def parse_csv(self, csv_path):
        self.parsed_csv_paths.append(csv_path)

class MockInstrumentController:
    def __init__(self, PROJECT_ROOT=None, debug=True):
        self.PROJECT_ROOT = PROJECT_ROOT
        self.debug = debug
        self.setup_value = True
        self.ping_value = True
        self.take_sample_value = "sample.csv"
        self.take_blank_value = True
        self.set_blank_value = True
        self.shutdown_value = True
        self.blank_file = "blank.csv"
        self.take_sample_calls = []
        self.take_blank_calls = []
        self.set_blank_calls = []

    def setup(self):
        return self.setup_value

    def ping(self):
        return self.ping_value

    def take_sample(self, filename=None):
        self.take_sample_calls.append(filename)
        return self.take_sample_value

    def take_blank(self, filename):
        self.take_blank_calls.append(filename)
        return self.take_blank_value

    def set_blank(self, data):
        self.set_blank_calls.append(data)
        return self.set_blank_value

    def shutdown(self):
        return self.shutdown_value

def make_controller(tmp_path, **kwargs):
    return SystemController(
        PROJECT_ROOT=tmp_path,
        server_controller_cls=MockServerController,
        instrument_controller_cls=MockInstrumentController,
        file_dir=str(tmp_path / "sample_data"),
        debug=False,
        **kwargs,
    )

def test_init_creates_controllers(tmp_path):
    controller = make_controller(tmp_path)

    assert controller.PROJECT_ROOT == tmp_path
    assert controller.debug is False
    assert controller.ServController.project_root == tmp_path
    assert controller.ServController.file_dir == str(tmp_path / "sample_data")
    assert controller.ServController.debug is False
    assert controller.InstController.PROJECT_ROOT == tmp_path
    assert controller.InstController.debug is False
    assert controller.offline is False
    assert controller.offlineUsername is None
    assert controller.ErrorDictionary[0] == "Good to go"

def test_instrument_ping(tmp_path):
    controller = make_controller(tmp_path)
    controller.InstController.ping_value = True

    assert controller._instrument_ready() is True

    controller.InstController.ping_value = False
    assert controller._instrument_ready() is False

def test_server_connect(tmp_path):
    controller = make_controller(tmp_path)
    controller.ServController.connect_value = True

    assert controller._server_ready() is True

    controller.ServController.connect_value = False
    assert controller._server_ready() is False

def test_startup__success(tmp_path):
    controller = make_controller(tmp_path)

    assert controller.startUp() == 0

def test_startup_instrument_setup_fails(tmp_path):
    controller = make_controller(tmp_path)
    controller.InstController.setup_value = False

    assert controller.startUp() == 100

def test_startup_server_connect_fails(tmp_path):
    controller = make_controller(tmp_path)
    controller.ServController.connect_value = False

    assert controller.startUp() == 110

def test_signin_success(tmp_path):
    controller = make_controller(tmp_path)

    assert controller.signIn("test") == 0
    assert controller.ServController.user == "test"

def test_signin_login_fail(tmp_path):
    controller = make_controller(tmp_path)
    controller.ServController.login_value = False

    assert controller.signIn("test") == 220

def test_signin_server_unavailable(tmp_path):
    controller = make_controller(tmp_path)
    controller.ServController.connect_value = False

    assert controller.signIn("test") == 110
    assert controller.offlineUsername == "test"

def test_signout_sends_data_logs_out(tmp_path):
    controller = make_controller(tmp_path)
    controller.ServController.user = "test"
    controller.ServController.logged_in_value = True
    controller.ServController.send_all_data_value = [("test_sample_unsent.json", True)]

    assert controller.signOut() == 0
    assert controller.offlineUsername is None
    assert controller.ServController.user is None

def test_signout_no_user_logged_in(tmp_path):
    controller = make_controller(tmp_path)
    controller.ServController.logged_in_value = False

    assert controller.signOut() == 300

def test_signout_logout_fail(tmp_path):
    controller = make_controller(tmp_path)
    controller.ServController.logged_in_value = True
    controller.ServController.logout_value = False

    assert controller.signOut() == 330

def test_signout_server_unavailable(tmp_path):
    controller = make_controller(tmp_path)
    controller.ServController.connect_value = False

    assert controller.signOut() == 110

def test_run_lab_machine_no_active_user(tmp_path):
    controller = make_controller(tmp_path)
    controller.ServController.user = None
    controller.offline = False

    assert controller.runLabMachine() == (300, None)

def test_run_lab_machine_sample_fail(tmp_path):
    controller = make_controller(tmp_path)
    controller.ServController.user = "test"
    controller.InstController.take_sample_value = ""

    assert controller.runLabMachine() == (400, None)

def test_run_lab_machine_parses_csv_sends_data(tmp_path):
    controller = make_controller(tmp_path)
    controller.ServController.user = "test"
    controller.InstController.take_sample_value = "C:/out/test2026-04-28T12-00-00.csv"
    controller.ServController.send_all_data_value = [
        ("test_2026-04-28T12-00-00_unsent.json", True)
    ]

    assert controller.runLabMachine() == (
        0,
        "C:/out/test2026-04-28T12-00-00.csv",
    )
    assert controller.ServController.parsed_csv_paths == [
        "C:/out/test2026-04-28T12-00-00.csv"
    ]

def test_run_lab_machine_upload_missing(tmp_path):
    controller = make_controller(tmp_path)
    controller.ServController.user = "test"
    controller.InstController.take_sample_value = "C:/out/test2026-04-28T12-00-00.csv"
    controller.ServController.send_all_data_value = [("other_file_unsent.json", True)]

    assert controller.runLabMachine() == (
        110,
        "C:/out/test2026-04-28T12-00-00.csv",
    )

def test_take_blank_generates_default_filename(tmp_path):
    controller = make_controller(tmp_path)
    controller.InstController.blank_file = "C:/out/blank.csv"

    with patch.object(system_module, "datetime") as mocked_datetime:
        mocked_datetime.now.return_value.strftime.return_value = "20260428_120000"
        result = controller.takeBlank()

    assert result == (0, "C:/out/blank.csv")
    assert controller.InstController.take_blank_calls == [
        str(Path(controller.ServController.file_dir) / "blank_20260428_120000.csv")
    ]

def test_take_blank_uses_provided_filename(tmp_path):
    controller = make_controller(tmp_path)
    controller.InstController.blank_file = "C:/out/custom_blank.csv"

    assert controller.takeBlank("custom_blank.csv") == (0, "C:/out/custom_blank.csv")
    assert controller.InstController.take_blank_calls == ["custom_blank.csv"]

def test_take_blank_capture_fails(tmp_path):
    controller = make_controller(tmp_path)
    controller.InstController.take_blank_value = False

    assert controller.takeBlank("blank.csv") == (400, None)

def test_set_blank_success(tmp_path):
    controller = make_controller(tmp_path)

    assert controller.setBlank("blank-data") == 0
    assert controller.InstController.set_blank_calls == ["blank-data"]

def test_set_blank_data_missing(tmp_path):
    controller = make_controller(tmp_path)

    assert controller.setBlank("") == 400

def test_set_blank_rejects_blank(tmp_path):
    controller = make_controller(tmp_path)
    controller.InstController.set_blank_value = False

    assert controller.setBlank("blank-data") == 550

def test_set_blank_instrument_not_ready(tmp_path):
    controller = make_controller(tmp_path)
    controller.InstController.ping_value = False

    assert controller.setBlank("blank-data") == 100

def test_take_sample_instrument_not_ready(tmp_path):
    controller = make_controller(tmp_path)
    controller.InstController.ping_value = False

    assert controller.takeSample() == (100, None)

def test_stop_program_success(tmp_path):
    controller = make_controller(tmp_path)

    assert controller.stopProgram() == 0

def test_stop_program_shutdown_fail(tmp_path):
    controller = make_controller(tmp_path)
    controller.InstController.shutdown_value = False

    assert controller.stopProgram() == 100
