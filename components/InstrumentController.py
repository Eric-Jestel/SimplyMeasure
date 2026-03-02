# This is the Instrument Controller

try:
    from Sample import Sample
except ImportError:
    from components.Sample import Sample


import json
import time
import uuid
import winreg
import subprocess
from datetime import datetime
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
    TIMEOUT_S = 60.0

    def __init__(self, debug: bool = False):
        print(f"[InstrumentController][RECEIVED] __init__ payload={{'debug': {debug}}}")
        self.debug = bool(debug)
        self.blank_file = ""
        self.sample_wavelength_nm = 260
        self.scan_start_nm = 600
        self.scan_stop_nm = 500
        self.scan_bw = 2
        self.scan_sat = 0.1
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
    def _send_command(cls, command: str, params: dict) -> str:
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
        self, command: str, params: dict, timeout_s: float = None
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

    def setup(self):
        """
        Sets up the instrument
        """
        self._print_received("setup")
        try:
            self._debug("setup() starting mailbox clear + PING")

            self._clear_mailbox(reset_file_counter=False)
            # Launches the ADL file that communicates with the instrument
            subprocess.Popen(self.ADL_FILE, shell=True)

            # self._ensure_key(self.QUEUE_KEY)
            # self._ensure_key(self.PARAMS_KEY)
            # self._ensure_key(self.STATE_KEY)

            # reply = self._send_and_wait(
            #     "PING", {"ts": datetime.now().astimezone().isoformat()}, timeout_s=10.0
            # )
            # ok = self._is_success(reply)

            params = {
                "waveStart": self.scan_start_nm,
                "waveStop": self.scan_stop_nm,
                "saturation": self.scan_sat,
                "bandwidth": self.scan_bw,
            }
            reply = self._send_and_wait("SETUP", params)
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

        reply = self._send_and_wait(
            "PING", {"ts": datetime.now().astimezone().isoformat()}, timeout_s=10.0
        )
        result = self._is_success(reply)

        self._print_executed("ping", result)
        return result

    def changeParams(self, input_params: dict):
        """
        Changes the parameters of the instrument

        Args:
            input_params (dict): a dictionary of parameters to change. Valid keys:
                TBD - depends on what the instrument takes

        Returns:
            Boolean: True if successful
        """

        self._print_received("changeParams", input_params)
        self._debug(f"changeParams() input={input_params}")
        params_file = Path(__file__).parent / "storedParams.txt"

        # Load existing params if file exists
        existing_params = {}
        if params_file.exists():
            with open(params_file, "r") as f:
                for line in f:
                    key, value = line.strip().split(",", 1)
                    existing_params[key] = value

        # Update with new params
        existing_params.update(input_params)

        # Write all params back
        with open(params_file, "w") as f:
            for key, value in existing_params.items():
                f.write(f"{key},{value}\n")

        self._debug(f"changeParams() wrote {len(existing_params)} param entries")
        self._print_executed("changeParams", True)
        return True

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
        out_base = out_target.with_suffix("")

        params = {
            "start_nm": self.scan_start_nm,
            "stop_nm": self.scan_stop_nm,
            "out_base": str(out_base),
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
                "sample_wavelength_nm": self.sample_wavelength_nm,
                "blank_file": self.blank_file or None,
            },
        )

        params = {
            # "wavelength_nm": self.sample_wavelength_nm,
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

        sample_name = datetime.now().strftime("sample_%Y%m%d_%H%M%S")
        sample = Sample(sample_name, "uv-vis", [], 0.0)

        self._debug(f"take_sample() success sample={sample.name}")
        print(
            "[InstrumentController][TX] destination=SystemController/ServerPipeline, "
            f"command=sample_ready, payload={{'sample_name': '{sample.name}', 'type': '{sample.type}'}}"
        )
        self._print_executed("take_sample", sample)

        return sample

    def changeSettings(self, waveStart="", waveStop="", saturation="", bandwidth=""):
        params = {
            "waveStart": waveStart,
            "waveStop": waveStop,
            "saturation": saturation,
            "bandwidth": bandwidth,
        }
        reply = self._send_and_wait("SETTING", params)

        return self._is_success(reply)

    def reset(self):
        params = {}
        reply = self._send_and_wait("RESET", params)
        result = self._is_success(reply)
        return result

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

# ok = self._is_success(reply)
# self._debug(f"shutdown() -> {ok}")
# self._print_executed("shutdown", ok)
# return ok
