# This is the server controller

import requests
from dotenv import load_dotenv
import os
import json
from pathlib import Path
from datetime import datetime, timezone

print("ServerController module loaded")


class ServerController:
    """
    Communicates with the Inter Chem Net Server
    """

    def __init__(self, file_dir=None, debug: bool = False):
        print(
            f"[ServerController][RECEIVED] __init__ payload={{'file_dir': {file_dir}, 'debug': {debug}}}"
        )

        load_dotenv()

        self.debug = bool(debug)

        self.api_key = os.getenv("ICN_PRIVATE_API_KEY")
        print(
            f"[ServerController][DEBUG] Loaded ICN_PRIVATE_API_KEY: {'set' if self.api_key else 'not set'}"
        )
        self.api_url = (
            "https://interchemnet.avibe-stag.com/spectra/api/{link_end}?key={api_key}"
        )

        self.user = None

        self.UUID = 0
        self.UUID_expiry = 0

        self.file_dir = file_dir or str(Path(__file__).parent / "sample_data")
        print("[ServerController][EXECUTED] __init__ result=initialized")

    def _debug(self, message: str) -> None:
        if self.debug:
            print(f"[ServerController] {message}")

    def _print_received(self, command: str, payload=None) -> None:
        print(f"[ServerController][RECEIVED] {command} payload={payload}")

    def _print_executed(self, command: str, result=None) -> None:
        print(f"[ServerController][EXECUTED] {command} result={result}")

    def _print_tx(self, method: str, url: str, payload=None) -> None:
        print(f"[ServerController][TX] method={method}, url={url}, payload={payload}")

    def connect(self) -> bool:
        """Compatibility wrapper used by `SystemController.startUp()`."""
        self._print_received("connect")
        try:
            connected = self.ping()
            self._debug(f"connect() -> {connected}")
            self._print_executed("connect", connected)
            return connected
        except Exception as exc:
            self._debug(f"connect() exception: {exc}")
            self._print_executed("connect", False)
            return False

    def ping(self):
        """
        Sends a basic get request to the ICN server

        Returns:
            Boolean: True if successful
        """

        self._print_received("ping")
        url_input = self.api_url.format(
            link_end="connection-check", api_key=self.api_key
        )

        self._debug(f"TX GET {url_input}")
        self._print_tx("GET", url_input)

        if not self.api_key:
            self._debug("ping() missing ICN_PRIVATE_API_KEY")
            self._print_executed("ping", False)
            return False

        response = requests.get(url_input, timeout=10)
        payload = response.json()
        self._debug(f"RX status_code={response.status_code}, payload={payload}")

        if payload.get("STATUS") == "alive":
            self._print_executed("ping", True)
            return True
        elif payload.get("STATUS") == "maintenance":
            self._print_executed("ping", False)
            return False
        else:
            self._print_executed("ping", "exception")
            raise Exception("Unexpected response from server: " + response.text)

    def login(self, username):
        """
        Attempts to login the user with that username

        If it passes, generates a session UUID and stores it

        Args:
            username (String): the username of the user currently accessing ICN

        Returns:
            Boolean: True if successful
        """
        self._print_received("login", {"username": username})
        # Reset info
        self.UUID = 0
        self.UUID_expiry = 0
        self.user = None

        url_input = self.api_url.format(link_end="user-session", api_key=self.api_key)

        json_input = {"studentUserName": username}

        self._debug(f"TX POST {url_input} payload={json_input}")
        self._print_tx("POST", url_input, json_input)

        response = requests.post(url_input, json=json_input, timeout=10)
        payload = response.json()
        self._debug(
            f"RX status_code={response.status_code}, success={payload.get('success')}, user={username}"
        )

        if payload.get("success"):
            # server returns ISO datetime string for expiresOn
            self.UUID = payload.get("sessionUUID")
            self.UUID_expiry = payload.get("expiresOn")
            self.user = username
            result = {"expiresOn": self.UUID_expiry}
            self._print_executed("login", result)
            return result
        else:
            self._print_executed("login", False)
            return False

    def logout(self):
        """
        Logs out a user

        Returns:
            Boolean: True if successful
        """
        self._print_received("logout")
        self.UUID = 0
        self.UUID_expiry = 0
        self.user = None
        self._debug("logout() cleared local session")
        self._print_executed("logout", True)
        return True

    def is_logged_in(self):
        """
        Checks if a user is logged in

        Returns:
            Boolean: True if a user is logged in
        """
        self._print_received("is_logged_in")
        result = self.validate()
        self._print_executed("is_logged_in", result)
        return result

    def validate(self) -> bool:
        """
        Validate session: three clauses
          1) session UUID exists (non-zero/non-empty)
          2) expiry time is in the future
          3) username exists

        Returns True if all clauses pass.
        """
        self._print_received(
            "validate",
            {
                "has_uuid": bool(self.UUID),
                "has_user": bool(self.user),
                "has_expiry": bool(self.UUID_expiry),
            },
        )
        # 1: session UUID
        if not self.UUID:
            self._print_executed("validate", False)
            return False

        # 3: username exists
        if not self.user:
            self._print_executed("validate", False)
            return False

        # 2: expiry in future
        if not self.UUID_expiry:
            self._print_executed("validate", False)
            return False
        try:
            exp = datetime.fromisoformat(self.UUID_expiry.replace("Z", "+00:00"))
            valid = datetime.now(timezone.utc) < exp
            self._print_executed("validate", valid)
            return valid
        except Exception:
            self._print_executed("validate", False)
            return False

    def send_all_data(self):
        """
        Attempts to send all unsent data to ICN

        Returns:
            list of filenames and boolean indicating if sent
        """

        self._print_received("send_all_data", {"file_dir": self.file_dir})
        successes = []

        p = Path(self.file_dir)
        if not p.exists():
            self._debug(f"send_all_data() skipped missing dir: {p}")
            self._print_executed("send_all_data", successes)
            return successes

        for filepath in p.iterdir():
            if not filepath.is_file():
                continue
            if filepath.suffix.lower() != ".json":
                continue

            stem = filepath.stem
            parts = stem.rsplit("_", 2)
            if len(parts) != 3:
                continue
            owner, dt_str, flag = parts
            if flag.lower() != "unsent":
                continue

            sent = False
            if self.user != owner or not self.is_logged_in():
                # attempt to login as that owner
                self.login(owner)

            if self.send_data(str(filepath)):
                sent = True

            successes.append((filepath.name, sent))

        self._debug(f"send_all_data() processed {len(successes)} files")
        self._print_executed("send_all_data", successes)

        return successes

    def send_data(self, samplePath):
        """
        Converts a sample to a file and sends all the unsent data to ICN

        Args:
            samplePath (String): The path to the sample that is being sent to ICN

        Returns:
            Boolean: True if it successful send all unsent data
        """

        filename_split = Path(samplePath).stem.split("_")

        if len(filename_split) < 3:
            self._debug(f"send_data() invalid filename format: {samplePath}")
            self._print_executed("send_data", False)
            return False

        username = filename_split[0]

        data_key = filename_split[1]

        self._print_received("send_data", {"samplePath": str(samplePath)})
        # ensure logged in as file owner and session valid
        if self.user != username or not self.is_logged_in():
            if not self.login(username):
                self._debug(f"send_data() login failed for owner={username}")
                self._print_executed("send_data", False)
                return False

        if not self.is_logged_in():
            self._debug("send_data() rejected: not logged in")
            self._print_executed("send_data", False)
            return False

        url_input = self.api_url.format(
            link_end="instrument-data-upload", api_key=self.api_key
        )

        with open(samplePath, "r") as f:
            dataArray = []
            for line in f:
                stripped = line.strip()
                if not stripped or stripped in {"[", "]"}:
                    continue
                if stripped.endswith(","):
                    stripped = stripped[:-1]
                dataArray.append(json.loads(stripped))

        json_input = {
            "sessionUUID": self.UUID,
            "dataKey": data_key,
            "dataArray": dataArray,
        }

        response = requests.post(url_input, json=json_input, timeout=10)
        payload = response.json()
        self._debug(f"TX POST {url_input} payload={json_input}")
        self._debug(
            f"RX status_code={response.status_code}, success={payload.get('success')}, user={username}"
        )

        if payload.get("success"):
            rename_to_sent = Path(samplePath).with_name(
                Path(samplePath).stem.replace("unsent", "sent")
                + Path(samplePath).suffix
            )
            Path(samplePath).rename(rename_to_sent)
            return True

        self._print_executed("send_data", False)
        return False

    def parse_csv(self, filepath):
        """
        Takes in a csv file, then converts it into a JSON file.
        username_datetime_unsent.json is the ouputted file in the to be sent folder
        Args:
            filepath (String): The path to the csv file that is being converted to JSON
        Returns:
            boolean: True if the file was successfully parsed, False if not
        """

        filename_datetime = Path(filepath).stem
        filename_username = self.user
        filename_suffix = "_unsent.json"

        out_path = (
            Path(self.file_dir)
            / f"{filename_username}_{filename_datetime}{filename_suffix}"
        )

        with open(filepath, "r") as f:
            lines = f.readlines()

        with open(out_path, "w") as f:
            f.write("[\n")
            for line in lines[2:-1]:
                f.write(
                    '{"nm": '
                    + line.split(",")[0]
                    + ', "abs": '
                    + line.split(",")[1]
                    + "}\n"
                )
            f.write("]")

        return True
