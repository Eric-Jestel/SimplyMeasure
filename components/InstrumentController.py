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
    ADL_FILE = ".\\components\\MailboxCheck.adl"
    POLL_INTERVAL_S = 0.1
    TIMEOUT_S = 10.0

    def __init__(self, debug: bool = False):
        if debug:
            print(
                f"[InstrumentController][RECEIVED] __init__ payload={{'debug': {debug}}}"
            )

        self.debug = bool(debug)
        self.blank_file = ""

        self.instrumentParams = {
            "waveStart": 600,
            "waveStop": 500,
            "saturation": 0.1,
            "bandwidth": 2,
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

        cls._reg_set(cls.QUEUE_KEY, "Command", "")
        cls._reg_set(cls.QUEUE_KEY, "CommandId", "")
        cls._reg_set(cls.PARAM_KEY, "Json", "")
        cls._reg_set(cls.PARAM_KEY, "Filename", "")
        cls._reg_set(cls.PARAM_KEY, "WavelengthStart", "")
        cls._reg_set(cls.PARAM_KEY, "WavelengthStop", "")
        cls._reg_set(cls.PARAM_KEY, "Satuation", "")
        cls._reg_set(cls.PARAM_KEY, "Banwidth", "")
        cls._reg_set(cls.STATE_KEY, "ReplyId", "")
        cls._reg_set(cls.STATE_KEY, "ResultPath", "")
        cls._reg_set(cls.STATE_KEY, "Error", "")
        cls._reg_set(cls.STATE_KEY, "Status", "IDLE")

        if reset_file_counter:
            cls._reg_set(cls.STATE_KEY, "FileCounter", "0")

    @classmethod
    def _send_command(cls, command: str, params: dict = {}) -> str:
        cmd_id = str(uuid.uuid4())
        cls._reg_set(cls.PARAM_KEY, "Json", json.dumps(params))
        cls._reg_set(cls.PARAM_KEY, "Filename", str(params.get("filename", "")))
        cls._reg_set(cls.PARAM_KEY, "WavelengthStart", str(params.get("waveStart", "")))
        cls._reg_set(cls.PARAM_KEY, "WavelengthStop", str(params.get("waveStop", "")))
        cls._reg_set(cls.PARAM_KEY, "Satuation", str(params.get("saturation", "")))
        cls._reg_set(cls.PARAM_KEY, "Banwidth", str(params.get("bandwidth", "")))
        cls._reg_set(cls.QUEUE_KEY, "CommandId", cmd_id)
        cls._reg_set(cls.QUEUE_KEY, "Command", command)
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
            reply_id = cls._reg_get(cls.STATE_KEY, "ReplyId", "")
            if reply_id == cmd_id:
                return {
                    "reply_id": reply_id,
                    "status": cls._reg_get(cls.STATE_KEY, "Status", ""),
                    "result_path": cls._reg_get(cls.STATE_KEY, "ResultPath", ""),
                    "error": cls._reg_get(cls.STATE_KEY, "Error", ""),
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
        return self._reg_get(self.STATE_KEY, "ResultPath", "")

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
            "filename": filename,
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

        self.instrumentParams["waveStart"] = (
            waveStart or self.instrumentParams["waveStart"]
        )
        self.instrumentParams["waveStop"] = (
            waveStop or self.instrumentParams["waveStop"]
        )
        self.instrumentParams["saturation"] = (
            saturation or self.instrumentParams["saturation"]
        )
        self.instrumentParams["bandwidth"] = (
            bandwidth or self.instrumentParams["bandwidth"]
        )

        reply = self._send_and_wait("SETTING", self.instrumentParams)

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
        reply = self._send_and_wait("SETTING", params)

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
