# This is the Instrument Controller

# try:
#     from Sample import Sample
# except ImportError:
#     from components.Sample import Sample
# from datetime import datetime

import json
import time
import uuid
import winreg
import subprocess

from pathlib import Path

print("InstrumentController module loaded")


class InstrumentController:
    """
    Communicates with the instrument
    """

    ROOT = r"Software\GenChem\CaryBridge"
    QUEUE_KEY = ROOT + r"\Queue"
    PARAM_KEY = ROOT + r"\Param"
    STATE_KEY = ROOT + r"\State"

    REG_Q_COMMAND = "Command"
    REG_Q_COMMAND_ID = "CommandId"
    REG_P_FILENAME = "Filename"
    REG_P_WAVE_START = "WavelengthStart"
    REG_P_WAVE_STOP = "WavelengthStop"
    REG_P_SATURATION = "Saturation"
    REG_P_BANDWIDTH = "Bandwidth"
    REG_S_REPLY_ID = "ReplyId"
    REG_S_RESULT_PATH = "ResultPath"
    REG_S_ERROR = "Error"
    REG_S_STATUS = "Status"
    REG_S_FILE_COUNTER = "FileCounter"

    ADL_FILE = r".\components\MailboxCheck.adl"
    SCAN_FOLDER = "C:\\Users\\Agilent Cary 60\\Documents\\SoftwareDev - dont delete\\Scans\\"
    POLL_INTERVAL_S = 0.1
    TIMEOUT_S = 10.0

    def __init__(self, PROJECT_ROOT, debug: bool = False):
        self.PROJECT_ROOT = PROJECT_ROOT
        if debug:
            print(
                f"[InstrumentController][RECEIVED] __init__ payload={{'debug': {debug}}}"
            )

        self.debug = bool(debug)
        self.blank_file = ""

        self.instrumentParams = {
            self.REG_P_FILENAME: self.SCAN_FOLDER,
            self.REG_P_WAVE_START: 600,
            self.REG_P_WAVE_STOP: 500,
            self.REG_P_SATURATION: 0.1,
            self.REG_P_BANDWIDTH: 2,
        }

        if debug:
            print("[InstrumentController][EXECUTED] __init__ result=initialized")

    def _debug(self, message: str) -> None:
        if self.debug:
            print(f"[InstrumentController] {message}")

    def _print_received(self, command: str, payload=None) -> None:
        print(f"[InstrumentController][RECEIVED] {command} payload={payload}")

    def _print_executed(self, command: str, result=None) -> None:
        print(f"[InstrumentController][EXECUTED] {command} result={result}")

    def _print_tx(self, destination: str, command: str, payload=None) -> None:
        print(
            f"[InstrumentController][TX] destination={destination}, "
            f"command={command}, payload={payload}"
        )

    @staticmethod
    def _ensure_key(subkey: str) -> None:
        winreg.CreateKey(winreg.HKEY_CURRENT_USER, subkey)

    @classmethod
    def _reg_set(cls, subkey: str, name: str, value: str) -> None:
        cls._ensure_key(subkey)
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, subkey, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)

    @staticmethod
    def _reg_get(subkey: str, name: str, default: str = "") -> str:
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, subkey, 0, winreg.KEY_QUERY_VALUE
            ) as key:
                value, _ = winreg.QueryValueEx(key, name)
                return str(value)
        except FileNotFoundError:
            return default
        except OSError:
            return default

    @classmethod
    def _clear_mailbox(cls, reset_file_counter: bool = False) -> None:
        cls._ensure_key(cls.QUEUE_KEY)
        cls._ensure_key(cls.PARAM_KEY)
        cls._ensure_key(cls.STATE_KEY)

        status = cls._reg_get(cls.STATE_KEY, "Status", "")
        if status.upper() == "BUSY":
            print("WARNING: ADL bridge reports Status=BUSY. Clearing mailbox anyway.")

        cls._reg_set(cls.QUEUE_KEY, cls.REG_Q_COMMAND, "")
        cls._reg_set(cls.QUEUE_KEY, cls.REG_Q_COMMAND_ID, "")
        cls._reg_set(cls.PARAM_KEY, cls.REG_P_FILENAME, "")
        cls._reg_set(cls.PARAM_KEY, cls.REG_P_WAVE_START, "")
        cls._reg_set(cls.PARAM_KEY, cls.REG_P_WAVE_STOP, "")
        cls._reg_set(cls.PARAM_KEY, cls.REG_P_SATURATION, "")
        cls._reg_set(cls.PARAM_KEY, cls.REG_P_BANDWIDTH, "")
        cls._reg_set(cls.STATE_KEY, cls.REG_S_REPLY_ID, "")
        cls._reg_set(cls.STATE_KEY, cls.REG_S_RESULT_PATH, "")
        cls._reg_set(cls.STATE_KEY, cls.REG_S_ERROR, "")
        cls._reg_set(cls.STATE_KEY, cls.REG_S_STATUS, "IDLE")

        if reset_file_counter:
            cls._reg_set(cls.STATE_KEY, cls.REG_S_FILE_COUNTER, "0")

    @classmethod
    def _send_command(cls, command: str, params: dict = {}) -> str:
        cmd_id = str(uuid.uuid4())
        for reg in params:
            cls._reg_set(cls.PARAM_KEY, reg, str(params.get(reg, "")))
        cls._reg_set(cls.QUEUE_KEY, cls.REG_Q_COMMAND_ID, cmd_id)
        cls._reg_set(cls.QUEUE_KEY, cls.REG_Q_COMMAND, command)
        print(
            "[InstrumentController][TX] destination=ADL_Bridge_Registry, "
            f"command={command}, payload={{'cmd_id': '{cmd_id}', 'params': {params}}}"
        )
        return cmd_id

    @classmethod
    def _wait_for_reply(cls, cmd_id: str, timeout_s: float = None) -> dict:
        if timeout_s is None:
            timeout_s = cls.TIMEOUT_S

        deadline = time.time() + timeout_s
        while time.time() < deadline:
            reply_id = cls._reg_get(cls.STATE_KEY, cls.REG_S_REPLY_ID, "")
            if reply_id == cmd_id:
                return {
                    "reply_id": reply_id,
                    "status": cls._reg_get(cls.STATE_KEY, cls.REG_S_STATUS, ""),
                    "result_path": cls._reg_get(cls.STATE_KEY, cls.REG_S_RESULT_PATH, ""),
                    "error": cls._reg_get(cls.STATE_KEY, cls.REG_S_ERROR, ""),
                }
            time.sleep(cls.POLL_INTERVAL_S)

        return {
            "reply_id": "",
            "status": "TIMEOUT",
            "result_path": "",
            "error": "Timed out waiting for ADL reply",
        }

    @staticmethod
    def _is_success(reply: dict) -> bool:
        status = str(reply.get("status", "")).upper()
        return status not in {"", "TIMEOUT", "ERROR", "FAILED", "OFFLINE"}

    def _send_and_wait(
        self, command: str, params: dict = {}, timeout_s: float = None
    ) -> dict:
        self._print_received(
            "_send_and_wait",
            {
                "command": command,
                "params": params,
                "timeout_s": timeout_s or self.TIMEOUT_S,
            },
        )
        self._debug(
            f"TX command={command}, params={params}, timeout_s={timeout_s or self.TIMEOUT_S}"
        )
        self._print_tx("ADL_Bridge_Registry", command, params)

        cmd_id = self._send_command(command, params)
        reply = self._wait_for_reply(cmd_id, timeout_s=timeout_s)

        self._debug(f"RX reply={reply}")
        self._print_executed("_send_and_wait", {"cmd_id": cmd_id, "reply": reply})

        return reply

    def _get_result_path(self) -> str:
        return self._reg_get(self.STATE_KEY, self.REG_S_RESULT_PATH, "")

    def setup(self):
        """
        Sets up the instrument
        """
        self._print_received("setup")
        try:
            self._debug("setup() starting mailbox clear + PING")
            # Clears the windows registry
            self._clear_mailbox(reset_file_counter=False)

            # Launches the ADL file that communicates with the instrument
            subprocess.Popen(self.ADL_FILE, shell=True)

            params = self.instrumentParams
            reply = self._send_and_wait("SETUP", params, timeout_s=30.0)
            self._debug(f"setup() -> {reply}")

            result = self._is_success(reply)
            self._print_executed("setup", result)

            return result
        except OSError as exc:
            self._debug(f"setup() registry error: {exc}")
            self._print_executed("setup", False)
            return False

    def ping(self) -> bool:
        """
        Lightweight connectivity check against the instrument bridge.
        """
        self._print_received("ping")
        self._debug("ping() invoked")

        reply = self._send_and_wait("PING")
        result = self._is_success(reply)

        self._print_executed("ping", result)
        return result

    def take_blank(self, filename):
        """
        Sends a command to the instrument to take a blank sample and saves it to a file

        Args:
            filename (String): the name of the file that the blank will be saved to

        Returns:
            Boolean: True if successful
        """
        self._print_received("take_blank", {"filename": filename})
        self._debug(f"take_blank() requested filename={filename}")

        out_target = Path(filename)
        out_target.parent.mkdir(parents=True, exist_ok=True)
        # out_base = out_target.with_suffix("")

        params = {
            self.REG_PARAM_FILENAME: filename,
        }
        reply = self._send_and_wait("BLANK", params)
        if self._is_success(reply):
            print("Blank scan successful, result path:", reply.get("result_path"))

            self.blank_file = reply.get("result_path") or str(out_target)

            self._debug(f"take_blank() success blank_file={self.blank_file}")
            self._print_executed(
                "take_blank", {"success": True, "blank_file": self.blank_file}
            )

            return True
        else:
            self._debug(f"take_blank() failed reply={reply}")
            self._print_executed("take_blank", {"success": False, "reply": reply})

            return False

    def set_blank(self, filename):
        """
        Sets the blank that the machine will test the generated samples against

        Args:
            filename (String): the name of the file that the holds the blank's data

        Returns:
            Boolean: True if successful
        """
        self._print_received("set_blank", {"filename": filename})

        blank_path = Path(filename)
        if not blank_path.exists():
            self._debug(f"set_blank() failed missing file: {blank_path}")
            self._print_executed("set_blank", False)

            return False
        else:
            self.blank_file = str(blank_path)

            self._debug(f"set_blank() success blank_file={self.blank_file}")
            self._print_executed("set_blank", True)

            return True

    def clear_blank(self) -> None:
        self._print_received("clear_blank")
        self.blank_file = ""
        self._debug("clear_blank() blank reference removed")
        self._print_executed("clear_blank", True)

    def take_sample(self, filename):
        """
        Sends a command to the instrument to take a sample and converts the sample to a Sample object

        Args:
            filename (String): the name of the file that the sample will be saved to

        Returns:
            Sample: the sample that the instrument collected
        """
        self._print_received(
            "take_sample",
            {
                "blank_file": self.blank_file or None,
            },
        )

        params = {
            "filename": filename,
        }
        if self.blank_file:
            params["blank_file"] = self.blank_file

        self._debug(f"take_sample() params={params}")

        reply = self._send_and_wait("SCAN", params)
        if not self._is_success(reply):
            self._debug(f"take_sample() failed reply={reply}")
            self._print_executed("take_sample", None)

            return None

        sample = self._get_result_path()

        return sample

    def changeSettings(self, waveStart="", waveStop="", saturation="", bandwidth=""):

        self.instrumentParams[self.REG_P_WAVE_START] = (
            waveStart or self.instrumentParams[self.REG_P_WAVE_START]
        )
        self.instrumentParams[self.REG_P_WAVE_STOP] = (
            waveStop or self.instrumentParams[self.REG_P_WAVE_STOP]
        )
        self.instrumentParams[self.REG_P_SATURATION] = (
            saturation or self.instrumentParams[self.REG_P_SATURATION]
        )
        self.instrumentParams[self.REG_P_BANDWIDTH] = (
            bandwidth or self.instrumentParams[self.REG_P_BANDWIDTH]
        )

        reply = self._send_and_wait("SETUP", self.instrumentParams)

        return self._is_success(reply)

    def getSettings(self):
        """
        Returns a dictionairy containing the 4 parameters of the instrument

        Returns:
            dict: A dictionary containing the 4 parameters of the instrument
        """

        return self.instrumentParams

    def reset(self):
        params = {}
        reply = self._send_and_wait("RESET", params)
        result = self._is_success(reply)
        return result

    def resetSettings(self):
        self.instrumentParams = {
            "waveStart": 600,
            "waveStop": 500,
            "saturation": 0.1,
            "bandwidth": 2,
        }
        params = self.instrumentParams
        reply = self._send_and_wait("SETUP", params)

        return self._is_success(reply)

    def shutdown(self):
        """
        Shuts the instrument down

        Returns:
            Boolean: True if successful
        """
        self._print_received("shutdown")

        reply = self._send_and_wait("SHUTDOWN", {})
        return self._is_success(reply)


# print("Launched. Wait 10 seconds")
# time.sleep(10)
# print(testing.take_blank("test_blank.txt"))

# instrument_controller = InstrumentController()

# print(instrument_controller.setup())
# print(instrument_controller.ping())
# instrument_controller.take_sample("test_sample1.txt")
# instrument_controller.take_sample("test_sample2.txt")
# instrument_controller.take_sample("test_sample3.txt")
